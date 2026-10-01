#!/usr/bin/env python3
"""Provider-scoped citation snapshots and conservative visibility filtering.

This module records descriptive metrics. It never treats them as evidence of
scientific correctness, novelty, or usefulness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from collections.abc import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # pragma: no cover - the project pins jsonschema
    Draft202012Validator = None  # type: ignore[assignment,misc]
    FormatChecker = None  # type: ignore[assignment,misc]


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "bibliometrics.schema.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "register" / "bibliometrics"
DEFAULT_ARCHIVE_ROOT = REPO_ROOT / ".work" / "bibliometrics"
INSPIRE_API = "https://inspirehep.net/api/literature"
INSPIRE_FIELDS = (
    "arxiv_eprints,titles,authors.full_name,authors.record,citation_count,"
    "citation_count_without_self_citations,earliest_date,dois,publication_info"
)
YEAR_DAYS = 365.2425


def read_json(path: Path) -> dict[str, Any]:
    def object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def finite_float(token: str) -> float:
        value = float(token)
        if not math.isfinite(value):
            raise ValueError(f"non-finite JSON number: {token}")
        return value

    def reject_constant(token: str) -> None:
        raise ValueError(f"non-finite JSON constant: {token}")

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=object_without_duplicates,
        parse_float=finite_float,
        parse_constant=reject_constant,
    )


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def finalize_snapshot(sidecar: dict[str, Any]) -> dict[str, Any]:
    """Assign a stable ID from the complete immutable JSON payload."""
    sidecar.setdefault("snapshot_created_utc", datetime.now(timezone.utc).isoformat())
    sidecar["snapshot_id"] = snapshot_id_for(sidecar)
    return sidecar


def snapshot_id_for(sidecar: dict[str, Any]) -> str:
    """Derive the immutable ID from the timestamp and full payload."""
    data = dict(sidecar)
    data.pop("snapshot_id", None)
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()[:12]
    created = sidecar.get("snapshot_created_utc")
    timestamp = parse_time(created).strftime("%Y%m%dT%H%M%S%fZ") if created else "undated"
    return f"{timestamp}-{digest}"


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must include a timezone: {value}")
    return parsed.astimezone(timezone.utc)


def age_at_snapshot(first_publication_utc: str, snapshot_utc: str) -> tuple[float, float]:
    age_days = (parse_time(snapshot_utc) - parse_time(first_publication_utc)).total_seconds() / 86400
    if age_days < 0:
        raise ValueError("snapshot precedes first publication")
    return age_days, age_days / YEAR_DAYS


def age_band(age_years: float, width_years: float = 1.0) -> dict[str, float]:
    """Return a half-open publication-age band [lower, upper)."""
    if not math.isfinite(age_years) or age_years < 0:
        raise ValueError("age_years must be finite and nonnegative")
    if not math.isfinite(width_years) or width_years <= 0:
        raise ValueError("width_years must be finite and positive")
    lower = math.floor(age_years / width_years) * width_years
    return {"lower_inclusive": lower, "upper_exclusive": lower + width_years}


def _normalize_arxiv_id(value: str) -> str:
    return value.removeprefix("arXiv:").removeprefix("arxiv:").strip().removesuffix(".pdf")


def _normalize_author_name(value: str) -> str:
    value = " ".join(value.replace(".", " ").split()).casefold()
    if "," in value:
        family, given = (part.strip() for part in value.split(",", 1))
        value = f"{given} {family}"
    return " ".join(value.split())


def _entry_arxiv_ids(metadata: dict[str, Any]) -> list[str]:
    return [
        _normalize_arxiv_id(str(item.get("value", "")))
        for item in metadata.get("arxiv_eprints", [])
        if isinstance(item, dict) and item.get("value")
    ]


def _author_record_id(author: dict[str, Any]) -> str | None:
    ref = (author.get("record") or {}).get("$ref")
    if not isinstance(ref, str):
        return None
    return ref.rstrip("/").split("/")[-1]


def _author_identity_key(author: dict[str, Any]) -> str:
    scholar = author.get("google_scholar", {})
    profile_url = scholar.get("profile_url")
    if scholar.get("profile_identity_verified") is True and isinstance(profile_url, str):
        profile_id = parse_qs(urlparse(profile_url).query).get("user", [None])[0]
        if profile_id:
            return f"scholar:{profile_id}"
    return author.get("source_author_id") or f"name:{_normalize_author_name(author['paper_author_name'])}"


def _source_receipt(
    *,
    provider: str,
    url: str,
    retrieved_utc: str | None,
    http_status: int | None,
    digest: str | None,
    byte_count: int | None,
    archive_path: str | None,
) -> dict[str, Any]:
    return {
        "provider": provider,
        "request_url": url,
        "retrieved_utc": retrieved_utc,
        "http_status": http_status,
        "response_sha256": digest,
        "response_bytes": byte_count,
        "archive_path": archive_path,
    }


def _sidecar_from_payload(
    paper: dict[str, Any],
    payload: dict[str, Any],
    receipt: dict[str, Any],
    *,
    snapshot_batch_id: str,
) -> dict[str, Any]:
    arxiv_id = _normalize_arxiv_id(paper["arxiv_id"])
    hits = payload.get("hits", {}).get("hits", [])
    matches = [
        hit
        for hit in hits
        if arxiv_id in _entry_arxiv_ids(hit.get("metadata", {}))
    ]
    retrieved = receipt["retrieved_utc"]
    match_status = "unmatched"
    matched = None
    if len(matches) == 1:
        candidate = matches[0]
        metadata = candidate.get("metadata", {})
        provider_title = " ".join((metadata.get("titles") or [{}])[0].get("title", "").split()).casefold()
        registered_title = " ".join(paper["title"].split()).casefold()
        if provider_title and provider_title == registered_title:
            match_status = "exact"
            matched = candidate
        else:
            match_status = "ambiguous"
    elif len(matches) > 1:
        match_status = "ambiguous"

    source = _source_receipt(
        provider="INSPIRE-HEP REST API",
        url=receipt["request_url"],
        retrieved_utc=retrieved,
        http_status=receipt["http_status"],
        digest=receipt["response_sha256"],
        byte_count=receipt["response_bytes"],
        archive_path=receipt["archive_path"],
    )
    metadata = (matched or {}).get("metadata", {})
    dois = sorted({item.get("value") for item in metadata.get("dois", []) if item.get("value")}) if matched else []
    journal_metadata = []
    if matched:
        for info in metadata.get("publication_info") or []:
            journal_title = info.get("journal_title")
            year = info.get("year")
            volume = info.get("journal_volume")
            article_or_page = info.get("artid") or info.get("page_start")
            if journal_title or year is not None or volume or article_or_page:
                journal_metadata.append({
                    "journal_title": journal_title,
                    "year": year,
                    "volume": str(volume) if volume is not None else None,
                    "article_or_page": str(article_or_page) if article_or_page is not None else None,
                })
    provider_authors = metadata.get("authors", [])
    author_index: dict[str, list[dict[str, Any]]] = {}
    for author in provider_authors:
        name = author.get("full_name")
        if name:
            author_index.setdefault(_normalize_author_name(name), []).append(author)

    authors = []
    for name in paper.get("authors", []):
        candidates = author_index.get(_normalize_author_name(name), []) if matched else []
        candidate_ids = [_author_record_id(candidate) for candidate in candidates]
        provider_author = (
            candidates[0]
            if candidates and all(candidate_id is not None for candidate_id in candidate_ids) and len(set(candidate_ids)) == 1
            else None
        )
        source_author_id = _author_record_id(provider_author) if provider_author else None
        identity_ok = match_status == "exact" and provider_author is not None and source_author_id is not None
        authors.append(
            {
                "paper_author_name": name,
                "source_author_id": source_author_id,
                "author_identity_verified": identity_ok,
                "identity_evidence": (
                    "The normalized author name has one linked INSPIRE author record in the exact base-arXiv-ID provider record."
                    if identity_ok
                    else "No exact author-record match was established from the provider response."
                ),
                "google_scholar": {
                    "profile_url": None,
                    "profile_link_evidence": None,
                    "profile_identity_evidence": None,
                    "profile_attempt": None,
                    "status": "unqueried",
                    "profile_identity_verified": False,
                    "h_index_status": "unavailable",
                    "h_index": None,
                    "h_index_scope": None,
                    "profile_batch_id": None,
                    "retrieved_utc": None,
                    "missing_reason": "No Google Scholar profile was checked in this bounded work snapshot; unknown does not mean zero.",
                },
            }
        )

    pub = paper["published_utc"]
    age_days, age_years = age_at_snapshot(pub, retrieved) if retrieved else (0.0, 0.0)
    primary_category = (paper.get("categories") or ["unknown"])[0]
    citation_count = metadata.get("citation_count") if matched else None
    citation_no_self = metadata.get("citation_count_without_self_citations") if matched else None
    count_is_int = isinstance(citation_count, int) and not isinstance(citation_count, bool)
    citation_status = "observed" if match_status == "exact" and count_is_int else "unavailable"
    if citation_status == "unavailable":
        citation_count = None
        citation_no_self = None

    cohort_reason = (
        "No provider population was queried for this provider, snapshot batch, arXiv primary category, and publication-age band. "
        "The deliberately selected Prospector sample is not a percentile reference population."
    )
    base_work_id = str((matched or {}).get("id")) if matched else None
    sidecar = {
        "schema_version": 1,
        "paper_id": paper["paper_id"],
        "work_identity": {
            "arxiv_id": arxiv_id,
            "registered_version": paper["version"],
            "title": paper["title"],
            "match_status": match_status,
            "provider": "INSPIRE-HEP",
            "provider_record_id": base_work_id,
            "matched_arxiv_ids": _entry_arxiv_ids(metadata) if matched else [],
            "linked_dois": dois,
            "journal_metadata": journal_metadata,
            "journal_scope": "linked_journal_metadata_returned" if dois or journal_metadata else "no_linked_journal_metadata_in_response",
            "count_scope": "provider_base_work_record" if matched else "unknown",
            "version_scope": "versions_not_disaggregated" if matched else "unknown",
            "publication_scope_note": "Citation counts are totals for this provider literature record. They are not split between the registered arXiv version, other arXiv versions, and linked journal publication records.",
            "source": source,
        },
        "citation_snapshot": {
            "status": citation_status,
            "count": citation_count,
            "count_without_self_citations": citation_no_self if isinstance(citation_no_self, int) else None,
            "retrieved_utc": retrieved,
            "source": source,
            "missing_reason": None if citation_status == "observed" else "Provider count was absent or the exact arXiv work match was not established.",
        },
        "comparison": {
            "first_publication_utc": pub,
            "age_days_at_snapshot": age_days,
            "age_years_at_snapshot": age_years,
            "field_categories": paper.get("categories", []),
            "cohort": {
                "provider": "INSPIRE-HEP",
                "snapshot_batch_id": snapshot_batch_id,
                "field_definition": f"arXiv primary category: {primary_category}",
                "age_band_years": age_band(age_years),
                "population_size": None,
                "minimum_population_size": 100,
                "population_evidence": None,
                "percentile": None,
                "status": "not_queried",
                "reason": cohort_reason,
            },
        },
        "authors": authors,
        "team_visibility": team_visibility(authors),
    }
    return finalize_snapshot(sidecar)


def team_visibility(authors: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize unique, verified profile h-indices without adding them."""
    unique: dict[str, dict[str, Any]] = {}
    for author in authors:
        key = _author_identity_key(author)
        prior = unique.get(key)
        if prior is not None:
            prior_h = prior.get("google_scholar", {}).get("h_index")
            current_h = author.get("google_scholar", {}).get("h_index")
            if prior_h is not None and current_h is not None and prior_h != current_h:
                raise ValueError(f"duplicate author identity has conflicting h-index values: {key}")
            if prior_h is None and current_h is not None:
                unique[key] = author
        else:
            unique[key] = author

    values = [
        item["google_scholar"]["h_index"]
        for item in unique.values()
        if item.get("author_identity_verified") is True
        and item.get("google_scholar", {}).get("status") == "verified"
        and item.get("google_scholar", {}).get("profile_identity_verified") is True
        and item.get("google_scholar", {}).get("h_index_status") == "observed"
        and isinstance(item.get("google_scholar", {}).get("h_index"), int)
        and not isinstance(item["google_scholar"]["h_index"], bool)
    ]
    total = len(unique)
    observed = len(values)
    scopes = {
        (item["google_scholar"].get("h_index_scope"), item["google_scholar"].get("profile_batch_id"))
        for item in unique.values()
        if item.get("author_identity_verified") is True
        and item.get("google_scholar", {}).get("status") == "verified"
        and item.get("google_scholar", {}).get("profile_identity_verified") is True
        and item.get("google_scholar", {}).get("h_index_status") == "observed"
        and item.get("google_scholar", {}).get("h_index") is not None
    }
    common_scope, common_batch = next(iter(scopes)) if len(scopes) == 1 else (None, None)
    if observed and len(scopes) > 1:
        status = "incomparable_scope"
    else:
        status = "complete" if total and observed == total else "partial" if observed else "none"
    comparable = observed > 0 and len(scopes) == 1
    missing_reason = None if status == "complete" else (
        "Observed author h-indices have different scopes and are not combined."
        if status == "incomparable_scope"
        else "Team maximum and median use verified, observed, same-scope h-indices only; missing author metrics are unknown."
    )
    return {
        "status": status,
        "unique_author_count": total,
        "verified_h_index_author_count": observed,
        "coverage_fraction": observed / total if total else 0.0,
        "h_index_scope": common_scope,
        "h_index_snapshot_batch_id": common_batch,
        "max_h_index": max(values) if values and comparable else None,
        "median_h_index": statistics.median(values) if values and comparable else None,
        "missing_reason": missing_reason,
    }


def cohort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    cohort = row["comparison"]["cohort"]
    band = cohort["age_band_years"]
    return (
        cohort["provider"],
        cohort["snapshot_batch_id"],
        cohort["field_definition"],
        band["lower_inclusive"],
        band["upper_exclusive"],
    )


def cohort_percentile(
    target: dict[str, Any],
    population_rows: Iterable[dict[str, Any]],
    *,
    minimum_population_size: int = 100,
    population_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute a tie-aware midrank only from a source-backed cohort response.

    The target work itself and duplicate provider records (including multiple
    registered arXiv versions) are excluded from the peer population.
    """
    if minimum_population_size < 100:
        raise ValueError("minimum_population_size must be at least 100 unique peer works")
    if population_evidence is None:
        return {
            "status": "not_queried",
            "percentile": None,
            "population_size": None,
            "excluded_missing_counts": 0,
            "reason": "No source-backed provider population query was supplied.",
        }
    required_evidence = {
        "scope_description", "provider", "snapshot_batch_id", "field_definition",
        "age_band_years", "provider_record_ids", "source",
    }
    if not required_evidence.issubset(population_evidence):
        raise ValueError("population evidence lacks a population definition or source receipt")
    target_key = cohort_key(target)
    age = population_evidence["age_band_years"]
    evidence_key = (
        population_evidence["provider"],
        population_evidence["snapshot_batch_id"],
        population_evidence["field_definition"],
        age.get("lower_inclusive"),
        age.get("upper_exclusive"),
    )
    if evidence_key != target_key:
        return {
            "status": "incomparable",
            "percentile": None,
            "population_size": 0,
            "excluded_missing_counts": 0,
            "reason": "Population source definition does not match the target provider, snapshot, field, and age band.",
        }
    receipt = population_evidence["source"]
    if (
        not receipt.get("response_sha256")
        or not receipt.get("archive_path")
        or not isinstance(receipt.get("http_status"), int)
        or not 200 <= receipt["http_status"] < 300
    ):
        raise ValueError("population evidence requires an archived successful provider response and SHA-256")
    declared_ids = population_evidence["provider_record_ids"]
    if len(declared_ids) != len(set(declared_ids)):
        raise ValueError("population evidence repeats provider record IDs")
    if target["work_identity"].get("provider_record_id") in declared_ids:
        raise ValueError("peer population evidence must exclude the target provider record")
    target_work = target["work_identity"].get("provider_record_id")
    peers: dict[tuple[str, str], int] = {}
    seen_ids: set[str] = set()
    missing = 0
    for row in population_rows:
        errors = validate_sidecar(row)
        if errors:
            raise ValueError("invalid peer sidecar: " + "; ".join(errors))
        if cohort_key(row) != target_key:
            raise ValueError("peer row falls outside the declared provider/time/field/age cohort")
        identity = (row["work_identity"]["provider"], str(row["work_identity"].get("provider_record_id")))
        if identity[1] == "None" or row["work_identity"].get("match_status") != "exact":
            raise ValueError("peer row lacks an exact provider work identity")
        if row["citation_snapshot"]["source"].get("response_sha256") != receipt.get("response_sha256"):
            raise ValueError("peer row does not cite the declared population response")
        if row["work_identity"].get("provider_record_id") == target_work:
            raise ValueError("peer rows must exclude the target provider record")
        seen_ids.add(identity[1])
        count = row.get("citation_snapshot", {}).get("count")
        if count is None:
            missing += 1
            continue
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError("citation counts must be nonnegative integers or null")
        previous = peers.get(identity)
        if previous is not None and previous != count:
            raise ValueError(f"duplicate provider work has conflicting counts: {identity[1]}")
        peers[identity] = count
    if seen_ids != set(declared_ids):
        raise ValueError("source response provider record IDs do not match the supplied peer rows")
    n = len(peers)
    if n < minimum_population_size:
        return {
            "status": "insufficient_population",
            "percentile": None,
            "population_size": n,
            "excluded_missing_counts": missing,
            "reason": f"Only {n} unique, same-provider, same-snapshot, same-field, same-age peers have observed counts; {minimum_population_size} are required.",
        }
    target_count = target.get("citation_snapshot", {}).get("count")
    if not isinstance(target_count, int) or isinstance(target_count, bool) or target_count < 0:
        return {
            "status": "incomparable",
            "percentile": None,
            "population_size": n,
            "excluded_missing_counts": missing,
            "reason": "The target has no observed citation count; missing is not zero.",
        }
    less = sum(value < target_count for value in peers.values())
    equal = sum(value == target_count for value in peers.values())
    percentile = 100.0 * (less + 0.5 * equal) / n
    return {
        "status": "computed",
        "percentile": percentile,
        "population_size": n,
        "excluded_missing_counts": missing,
        "reason": None,
    }


def validate_sidecar(sidecar: dict[str, Any]) -> list[str]:
    if Draft202012Validator is None:
        raise RuntimeError("jsonschema is required; install the project dependencies with uv sync")
    schema = read_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [
        "/" + "/".join(map(str, error.absolute_path)) + ": " + error.message
        for error in sorted(validator.iter_errors(sidecar), key=lambda e: list(map(str, e.absolute_path)))
    ]
    if errors:
        return errors

    try:
        expected_snapshot_id = snapshot_id_for(sidecar)
        if sidecar["snapshot_id"] != expected_snapshot_id:
            errors.append("/snapshot_id: does not match the immutable timestamp and payload hash")
    except (TypeError, ValueError) as exc:
        errors.append(f"/snapshot_id: cannot derive immutable snapshot ID: {exc}")

    def check_local_archive(relative_path: str | None, expected_hash: str | None, locator: str) -> None:
        if not relative_path or not expected_hash:
            return
        archive = (REPO_ROOT / relative_path).resolve()
        try:
            archive_root = _trusted_root(REPO_ROOT / ".work", "ignored archive root")
        except ValueError as exc:
            errors.append(f"{locator}: {exc}")
            return
        try:
            archive.relative_to(archive_root)
        except ValueError:
            errors.append(f"{locator}: raw evidence archive must resolve inside ignored .work/")
            return
        if archive.is_file() and hashlib.sha256(archive.read_bytes()).hexdigest() != expected_hash:
            errors.append(f"{locator}: local archive SHA-256 mismatch")

    work = sidecar["work_identity"]
    check_local_archive(work["source"]["archive_path"], work["source"]["response_sha256"], "/work_identity/source")
    for index, author in enumerate(sidecar["authors"]):
        scholar = author["google_scholar"]
        for evidence_key in ("profile_link_evidence", "profile_identity_evidence", "profile_attempt"):
            evidence = scholar.get(evidence_key)
            if evidence is None:
                continue
            check_local_archive(
                evidence.get("archive_path"),
                evidence.get("observation_sha256"),
                f"/authors/{index}/google_scholar/{evidence_key}",
            )

    if work["match_status"] == "exact":
        if work["arxiv_id"] not in work["matched_arxiv_ids"]:
            errors.append("/work_identity/matched_arxiv_ids: exact match does not include the registered base arXiv ID")
        expected_paper_id = f"arxiv:{work['arxiv_id']}v{work['registered_version']}"
        if sidecar["paper_id"] != expected_paper_id:
            errors.append("/paper_id: does not agree with the exact base ID and registered version")
    elif sidecar["citation_snapshot"]["status"] == "observed":
        errors.append("/citation_snapshot/status: an observed count requires an exact work identity")

    if sidecar["citation_snapshot"]["status"] == "observed":
        receipt = sidecar["citation_snapshot"]["source"]
        if (
            not isinstance(receipt.get("http_status"), int)
            or isinstance(receipt.get("http_status"), bool)
            or not 200 <= receipt["http_status"] < 300
            or not isinstance(receipt.get("response_sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", receipt["response_sha256"])
            or not isinstance(receipt.get("response_bytes"), int)
            or isinstance(receipt.get("response_bytes"), bool)
            or receipt["response_bytes"] < 0
            or not receipt.get("archive_path")
        ):
            errors.append("/citation_snapshot/source: observed counts require a successful response with hash, byte count, and ignored archive path")

    for index, author in enumerate(sidecar["authors"]):
        scholar = author["google_scholar"]
        if scholar["h_index_status"] == "observed":
            evidence = scholar["profile_identity_evidence"]
            if author["author_identity_verified"] is not True or scholar["profile_identity_verified"] is not True:
                errors.append(f"/authors/{index}/google_scholar: observed h-index lacks verified work-author identity")
            if evidence is None or evidence.get("paper_id") != sidecar["paper_id"]:
                errors.append(f"/authors/{index}/google_scholar: identity evidence does not name this pinned paper")
            elif evidence.get("paper_author_name") != author["paper_author_name"]:
                errors.append(f"/authors/{index}/google_scholar: identity evidence names a different paper author")
            if scholar["profile_url"] != (evidence or {}).get("source_url"):
                errors.append(f"/authors/{index}/google_scholar: h-index profile URL differs from the inspected identity source")
            if (evidence or {}).get("work_title") != work["title"]:
                errors.append(f"/authors/{index}/google_scholar: identity evidence names a different work title")
        elif scholar["h_index"] is not None:
            errors.append(f"/authors/{index}/google_scholar: unavailable h-index must remain null")
        link_evidence = scholar.get("profile_link_evidence")
        if scholar.get("profile_url") is not None and (
            link_evidence is None or link_evidence.get("linked_profile_url") != scholar["profile_url"]
        ):
            errors.append(f"/authors/{index}/google_scholar: profile URL lacks evidence of that exact link")

    expected_team = team_visibility(sidecar["authors"])
    if sidecar["team_visibility"] != expected_team:
        errors.append("/team_visibility: aggregate does not match unique verified author observations")

    cohort = sidecar["comparison"]["cohort"]
    citation = sidecar["citation_snapshot"]
    if citation["retrieved_utc"] != citation["source"]["retrieved_utc"]:
        errors.append("/citation_snapshot/retrieved_utc: differs from the source receipt timestamp")
    if work["source"] != citation["source"]:
        errors.append("/citation_snapshot/source: differs from the exact work identity receipt")
    if (
        citation["count"] is not None
        and citation["count_without_self_citations"] is not None
        and citation["count_without_self_citations"] > citation["count"]
    ):
        errors.append("/citation_snapshot/count_without_self_citations: exceeds the provider total")
    if citation["retrieved_utc"] is not None:
        try:
            actual_days, actual_years = age_at_snapshot(
                sidecar["comparison"]["first_publication_utc"], citation["retrieved_utc"]
            )
            if abs(actual_days - sidecar["comparison"]["age_days_at_snapshot"]) > 1e-6:
                errors.append("/comparison/age_days_at_snapshot: inconsistent with first publication and snapshot times")
            if abs(actual_years - sidecar["comparison"]["age_years_at_snapshot"]) > 1e-9:
                errors.append("/comparison/age_years_at_snapshot: inconsistent with first publication and snapshot times")
            band = cohort["age_band_years"]
            width = band["upper_exclusive"] - band["lower_inclusive"]
            if (
                not math.isfinite(width)
                or width <= 0
                or band != age_band(actual_years, width)
            ):
                errors.append("/comparison/cohort/age_band_years: inconsistent with age and declared band width")
        except ValueError as exc:
            errors.append(f"/comparison: {exc}")
    if cohort["provider"] != work["provider"]:
        errors.append("/comparison/cohort/provider: differs from the citation provider")
    expected_field = f"arXiv primary category: {sidecar['comparison']['field_categories'][0]}"
    if cohort["field_definition"] != expected_field:
        errors.append("/comparison/cohort/field_definition: differs from the registered primary arXiv category")
    if cohort["percentile"] is not None:
        evidence = cohort["population_evidence"]
        if cohort["status"] != "computed" or evidence is None:
            errors.append("/comparison/cohort/percentile: a computed percentile requires source-backed population evidence")
        elif (
            evidence["provider"] != cohort["provider"]
            or evidence["snapshot_batch_id"] != cohort["snapshot_batch_id"]
            or evidence["field_definition"] != cohort["field_definition"]
            or evidence["age_band_years"] != cohort["age_band_years"]
            or cohort["population_size"] < cohort["minimum_population_size"]
            or len(evidence["provider_record_ids"]) < cohort["population_size"]
            or sidecar["work_identity"].get("provider_record_id") in evidence["provider_record_ids"]
            or not evidence["source"].get("response_sha256")
            or not evidence["source"].get("archive_path")
            or not isinstance(evidence["source"].get("http_status"), int)
            or not 200 <= evidence["source"]["http_status"] < 300
        ):
            errors.append("/comparison/cohort: percentile lacks a matching adequate population definition")
        else:
            check_local_archive(
                evidence["source"]["archive_path"],
                evidence["source"]["response_sha256"],
                "/comparison/cohort/population_evidence/source",
            )
    return errors


def classify_visibility(
    paper: dict[str, Any],
    sidecar: dict[str, Any] | None,
    threshold: int,
    profile_batch_id: str,
) -> str:
    if threshold < 0:
        raise ValueError("threshold must be nonnegative")
    if paper.get("screen", {}).get("status") != "reviewed" or not paper.get("review_id") or not paper.get("idea_ids"):
        return "not_reviewed"
    if sidecar is None or not profile_batch_id:
        return "unresolved_visibility"
    if validate_sidecar(sidecar):
        return "unresolved_visibility"
    if sidecar.get("paper_id") != paper.get("paper_id"):
        return "unresolved_visibility"
    work = sidecar["work_identity"]
    if (
        work["match_status"] != "exact"
        or work["arxiv_id"] != paper.get("arxiv_id")
        or work["registered_version"] != paper.get("version")
        or work["title"] != paper.get("title")
        or sidecar["comparison"]["first_publication_utc"] != paper.get("published_utc")
    ):
        return "unresolved_visibility"
    expected_names = {_normalize_author_name(name) for name in paper.get("authors", [])}
    sidecar_names = {_normalize_author_name(item["paper_author_name"]) for item in sidecar["authors"]}
    if not expected_names or expected_names != sidecar_names or not all(item["author_identity_verified"] for item in sidecar["authors"]):
        return "unresolved_visibility"
    team = sidecar.get("team_visibility", {})
    expected = team.get("unique_author_count")
    observed = team.get("verified_h_index_author_count")
    max_h = team.get("max_h_index")
    if (
        not isinstance(expected, int)
        or not isinstance(observed, int)
        or observed != expected
        or max_h is None
        or team.get("status") != "complete"
        or team.get("h_index_scope") != "all_time"
        or team.get("h_index_snapshot_batch_id") != profile_batch_id
    ):
        return "unresolved_visibility"
    return "low_visibility" if max_h < threshold else "not_low_visibility"


def _request_inspire(paper: dict[str, Any], archive_root: Path, snapshot_batch_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    archive_root = _require_within(archive_root, REPO_ROOT / ".work", "archive root")
    query = urlencode({"q": f"arxiv:{paper['arxiv_id']}", "size": "10", "fields": INSPIRE_FIELDS})
    url = f"{INSPIRE_API}?{query}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Prospector bibliometrics/0.1 (bounded single-work metadata lookup)",
        },
    )
    retrieved = datetime.now(timezone.utc).isoformat()
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read(10 * 1024 * 1024 + 1)
            status = response.status
        if len(body) > 10 * 1024 * 1024:
            raise ValueError("INSPIRE response exceeded 10 MiB; response was not archived")
    except HTTPError as exc:
        body = exc.read(64 * 1024)
        status = exc.code
    except (URLError, TimeoutError) as exc:
        body = json.dumps({"error": str(exc)}).encode("utf-8")
        status = None

    digest = hashlib.sha256(body).hexdigest()
    day = datetime.now(timezone.utc).date().isoformat()
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", paper["arxiv_id"])
    archive_path = archive_root / day / f"inspire-{safe_id}-{digest[:12]}.json"
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(body)
    receipt = {
        "provider": "INSPIRE-HEP REST API",
        "request_url": url,
        "retrieved_utc": retrieved,
        "http_status": status,
        "response_sha256": digest,
        "response_bytes": len(body),
        "archive_path": archive_path.relative_to(REPO_ROOT).as_posix(),
    }
    if status is not None and 200 <= status < 300:
        payload = json.loads(body)
    else:
        payload = {"hits": {"hits": []}}
    sidecar = _sidecar_from_payload(paper, payload, receipt, snapshot_batch_id=snapshot_batch_id)
    return sidecar, receipt


def _load_papers_and_sidecars() -> list[tuple[dict[str, Any], dict[str, Any] | None]]:
    paper_dir = REPO_ROOT / "register" / "papers"
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for path in DEFAULT_OUTPUT_DIR.rglob("*.json"):
        item = read_json(path)
        if item.get("schema_version") != 1:
            continue
        work = item.get("work_identity", {})
        key = (item.get("paper_id", ""), work.get("provider", ""))
        old = latest.get(key)
        current_time = item.get("snapshot_created_utc") or ""
        old_time = (old or {}).get("snapshot_created_utc") or ""
        if old is None or (current_time, item.get("snapshot_id", "")) > (old_time, old.get("snapshot_id", "")):
            latest[key] = item
    rows = []
    for path in sorted(paper_dir.glob("*.json")):
        paper = read_json(path)
        sidecar = latest.get((paper.get("paper_id", ""), "INSPIRE-HEP"))
        rows.append((paper, sidecar))
    return rows


def _cmd_fetch(args: argparse.Namespace) -> int:
    args.archive_root = _require_within(args.archive_root, REPO_ROOT / ".work", "archive root")
    args.output_dir = _require_within(args.output_dir, DEFAULT_OUTPUT_DIR, "sidecar output directory")
    paper = read_json(args.paper_record)
    batch_id = args.batch_id or datetime.now(timezone.utc).strftime("inspire-%Y%m%dT%H%M%SZ")
    sidecar, _receipt = _request_inspire(paper, args.archive_root, batch_id)
    errors = validate_sidecar(sidecar)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2
    arxiv_name = re.sub(r"[^A-Za-z0-9._-]+", "__", paper["arxiv_id"])
    path = args.output_dir / f"{arxiv_name}v{paper['version']}-{sidecar['snapshot_id']}.json"
    rendered = json.dumps(sidecar, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != rendered:
            print(f"refusing to overwrite immutable snapshot: {path}", file=sys.stderr)
            return 2
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    print(path.relative_to(REPO_ROOT).as_posix())
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    paths = args.paths or sorted(DEFAULT_OUTPUT_DIR.glob("*.json"))
    failures = 0
    for path in paths:
        try:
            sidecar = read_json(path)
            errors = validate_sidecar(sidecar)
        except Exception as exc:
            errors = [str(exc)]
        if errors:
            failures += 1
            print(f"{path}: " + "; ".join(errors), file=sys.stderr)
        else:
            print(f"{path}: valid")
    return 1 if failures else 0


def _cmd_discover(args: argparse.Namespace) -> int:
    result = []
    for paper, sidecar in _load_papers_and_sidecars():
        status = classify_visibility(paper, sidecar, args.threshold, args.profile_batch_id)
        if status in {"low_visibility", "unresolved_visibility"} or args.include_other:
            result.append({
                "paper_id": paper["paper_id"],
                "title": paper["title"],
                "status": status,
                "usefulness": (paper.get("extraction") or {}).get("usefulness"),
                "idea_ids": paper.get("idea_ids", []),
                "team_visibility": sidecar.get("team_visibility") if sidecar else None,
            })
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(required=True, dest="command")

    fetch = commands.add_parser("fetch-inspire", help="fetch one exact arXiv work record from INSPIRE")
    fetch.add_argument("paper_record", type=Path, help="registered version JSON; one work per invocation")
    fetch.add_argument("--batch-id", help="shared snapshot batch label for explicit cohort collection")
    fetch.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    fetch.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    fetch.set_defaults(func=_cmd_fetch)

    validate = commands.add_parser("validate", help="validate sidecars against the canonical JSON schema")
    validate.add_argument("paths", nargs="*", type=Path)
    validate.set_defaults(func=_cmd_validate)

    discover = commands.add_parser("discover", help="find reviewed low-visibility and unresolved candidates")
    discover.add_argument("--threshold", required=True, type=int, help="strict upper h-index threshold")
    discover.add_argument("--profile-batch-id", required=True, help="require this shared Google Scholar metric snapshot batch")
    discover.add_argument("--include-other", action="store_true")
    discover.set_defaults(func=_cmd_discover)
    return parser


def _trusted_root(base: Path, label: str) -> Path:
    resolved = base.resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"{label} resolves outside the Prospector checkout") from exc
    return resolved


def _require_within(path: Path, base: Path, label: str) -> Path:
    trusted_base = _trusted_root(base, label + " boundary")
    resolved = path.resolve()
    try:
        resolved.relative_to(trusted_base)
    except ValueError as exc:
        raise ValueError(f"{label} must resolve inside {trusted_base}") from exc
    return resolved


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if hasattr(args, "output_dir"):
            args.output_dir = _require_within(args.output_dir, DEFAULT_OUTPUT_DIR, "sidecar output directory")
        if hasattr(args, "archive_root"):
            args.archive_root = _require_within(args.archive_root, REPO_ROOT / ".work", "archive root")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
