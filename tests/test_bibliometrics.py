"""Structural and boundary checks for provider-scoped bibliometrics."""
from __future__ import annotations

import copy
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bibliometrics


def author(name: str, author_id: str, h_index: int | None = None, *, identity=True):
    has_profile = h_index is not None
    return {
        "paper_author_name": name,
        "source_author_id": author_id,
        "author_identity_verified": identity,
        "identity_evidence": "Exact provider work record and linked author record.",
        "google_scholar": {
            "profile_url": f"https://scholar.google.com/citations?user={author_id}" if has_profile else None,
            "profile_link_evidence": {
                "source_url": "https://example.org/profile",
                "locator": "Publications link",
                "linked_profile_url": f"https://scholar.google.com/citations?user={author_id}",
                "description": "Author's institutional page links this exact profile.",
                "observation_sha256": "b" * 64,
                "archive_path": ".work/bibliometrics/profile-link.json",
            } if has_profile else None,
            "profile_identity_evidence": {
                "source_url": f"https://scholar.google.com/citations?user={author_id}",
                "paper_id": "arxiv:2401.01234v1",
                "paper_author_name": name,
                "work_title": "Example paper",
                "locator": "Profile publications list, exact title and author entry",
                "exact_work_verified": True,
                "observation_sha256": "c" * 64,
                "archive_path": ".work/bibliometrics/profile-work.json",
            } if has_profile else None,
            "profile_attempt": None,
            "status": "verified" if has_profile else "unqueried",
            "profile_identity_verified": has_profile,
            "h_index_status": "observed" if has_profile else "unavailable",
            "h_index": h_index,
            "h_index_scope": "all_time" if has_profile else None,
            "profile_batch_id": "gs-batch-2026-10-01" if has_profile else None,
            "retrieved_utc": "2026-10-01T12:00:00Z" if has_profile else None,
            "missing_reason": None if has_profile else "Profile was not checked; unknown, not zero.",
        },
    }


def row(arxiv_id="2401.01234", version=1, count=12, age=2.0, field="astro-ph.CO", provider_id="123"):
    retrieved = "2026-10-01T12:00:00Z"
    publication = datetime(2026, 10, 1, 12, tzinfo=timezone.utc) - timedelta(days=age * bibliometrics.YEAR_DAYS)
    first_publication = publication.isoformat().replace("+00:00", "Z")
    src = {
        "provider": "INSPIRE-HEP REST API",
        "request_url": "https://inspirehep.net/api/literature?q=arxiv%3A2401.01234",
        "retrieved_utc": retrieved,
        "http_status": 200,
        "response_sha256": "a" * 64,
        "response_bytes": 20,
        "archive_path": ".work/bibliometrics/response.json",
    }
    authors = [author("Ada Example", "a1", None), author("Bea Example", "a2", None)]
    return bibliometrics.finalize_snapshot({
        "schema_version": 1,
        "snapshot_id": "snapshot-fixture",
        "snapshot_created_utc": "2026-10-01T12:00:00Z",
        "paper_id": f"arxiv:{arxiv_id}v{version}",
        "work_identity": {
            "arxiv_id": arxiv_id,
            "registered_version": version,
            "title": "Example paper",
            "match_status": "exact",
            "provider": "INSPIRE-HEP",
            "provider_record_id": provider_id,
            "matched_arxiv_ids": [arxiv_id],
            "linked_dois": [],
            "journal_metadata": [],
            "journal_scope": "no_linked_journal_metadata_in_response",
            "count_scope": "provider_base_work_record",
            "version_scope": "versions_not_disaggregated",
            "publication_scope_note": "Provider record count, not split by arXiv/journal version.",
            "source": src,
        },
        "citation_snapshot": {
            "status": "observed" if count is not None else "unavailable",
            "count": count,
            "count_without_self_citations": count,
            "retrieved_utc": retrieved,
            "source": src,
            "missing_reason": None if count is not None else "Provider count is unavailable; unknown is not zero.",
        },
        "comparison": {
            "first_publication_utc": first_publication,
            "age_days_at_snapshot": age * bibliometrics.YEAR_DAYS,
            "age_years_at_snapshot": age,
            "field_categories": [field],
            "cohort": {
                "provider": "INSPIRE-HEP",
                "snapshot_batch_id": "snapshot-2026-10-01",
                "field_definition": f"arXiv primary category: {field}",
                "age_band_years": bibliometrics.age_band(age),
                "population_size": None,
                "minimum_population_size": 100,
                "population_evidence": None,
                "percentile": None,
                "status": "not_queried",
                "reason": "A same-provider, same-time, same-field and same-age population was not collected.",
            },
        },
        "authors": authors,
        "team_visibility": bibliometrics.team_visibility(authors),
    })


class Bibliometrics(unittest.TestCase):
    def test_duplicate_provider_author_names_do_not_verify_ambiguous_identity(self):
        paper = {
            "paper_id": "arxiv:2401.01234v1",
            "arxiv_id": "2401.01234",
            "version": 1,
            "title": "Example paper",
            "published_utc": "2024-01-01T00:00:00Z",
            "categories": ["astro-ph.CO"],
            "authors": ["Alex Lee"],
        }
        payload = {
            "hits": {"hits": [{"id": "record-1", "metadata": {
                "arxiv_eprints": [{"value": "2401.01234"}],
                "titles": [{"title": "Example paper"}],
                "authors": [
                    {"full_name": "Alex Lee", "record": {"$ref": "https://inspirehep.net/api/authors/1"}},
                    {"full_name": "Alex Lee", "record": {"$ref": "https://inspirehep.net/api/authors/2"}},
                ],
                "citation_count": 1,
            }}]},
        }
        receipt = {
            "request_url": "https://inspirehep.net/api/literature?q=arxiv%3A2401.01234",
            "retrieved_utc": "2026-10-01T12:00:00Z",
            "http_status": 200,
            "response_sha256": "a" * 64,
            "response_bytes": 10,
            "archive_path": ".work/bibliometrics/response.json",
        }
        result = bibliometrics._sidecar_from_payload(paper, payload, receipt, snapshot_batch_id="batch")
        self.assertFalse(result["authors"][0]["author_identity_verified"])
        self.assertIsNone(result["authors"][0]["source_author_id"])

    def test_invalid_profile_identity_cannot_supply_h_index(self):
        candidate = row()
        candidate["authors"][0] = author("Ada Example", "a1", 8)
        profile = candidate["authors"][0]["google_scholar"]
        profile["profile_identity_verified"] = False
        candidate["team_visibility"] = bibliometrics.team_visibility(candidate["authors"])
        self.assertTrue(bibliometrics.validate_sidecar(candidate))

    def test_aggregate_must_match_author_metrics(self):
        candidate = row()
        candidate["team_visibility"]["unique_author_count"] = 0
        self.assertTrue(bibliometrics.validate_sidecar(candidate))

    def test_percentile_without_population_evidence_is_invalid(self):
        candidate = row()
        candidate["comparison"]["cohort"].update(
            status="computed", population_size=100, percentile=50.0, reason=None
        )
        self.assertTrue(bibliometrics.validate_sidecar(candidate))

    def test_observed_count_requires_successful_archived_receipt(self):
        candidate = row()
        candidate["citation_snapshot"]["source"].update(
            http_status=503, response_sha256=None, response_bytes=None, archive_path=None
        )
        candidate["work_identity"]["source"] = copy.deepcopy(candidate["citation_snapshot"]["source"])
        candidate = bibliometrics.finalize_snapshot(candidate)
        self.assertTrue(bibliometrics.validate_sidecar(candidate))

    def test_cohort_must_match_work_provider_and_category(self):
        candidate = row()
        candidate["comparison"]["cohort"]["provider"] = "Different-provider"
        candidate = bibliometrics.finalize_snapshot(candidate)
        errors = bibliometrics.validate_sidecar(candidate)
        self.assertTrue(any("cohort/provider" in error for error in errors))
        candidate = row()
        candidate["comparison"]["cohort"]["field_definition"] = "arXiv primary category: gr-qc"
        candidate = bibliometrics.finalize_snapshot(candidate)
        errors = bibliometrics.validate_sidecar(candidate)
        self.assertTrue(any("cohort/field_definition" in error for error in errors))

    def test_declared_narrow_age_band_is_checked_against_its_width(self):
        candidate = row(age=2.4)
        candidate["comparison"]["cohort"]["age_band_years"] = bibliometrics.age_band(2.4, 0.25)
        candidate = bibliometrics.finalize_snapshot(candidate)
        self.assertFalse(bibliometrics.validate_sidecar(candidate))
        candidate["comparison"]["cohort"]["age_band_years"]["upper_exclusive"] = 2.9
        candidate = bibliometrics.finalize_snapshot(candidate)
        self.assertTrue(bibliometrics.validate_sidecar(candidate))

    def test_snapshot_payload_change_invalidates_immutable_id(self):
        candidate = row()
        candidate["citation_snapshot"]["count"] += 1
        self.assertTrue(any("immutable timestamp and payload hash" in error for error in bibliometrics.validate_sidecar(candidate)))

    def test_fetch_paths_must_remain_in_ignored_archive_and_sidecar_roots(self):
        with self.assertRaises(ValueError):
            bibliometrics._require_within(bibliometrics.REPO_ROOT.parent / "elsewhere", bibliometrics.REPO_ROOT / ".work", "archive root")
        with self.assertRaises(ValueError):
            bibliometrics._require_within(bibliometrics.REPO_ROOT / ".work" / "published", bibliometrics.DEFAULT_OUTPUT_DIR, "sidecar output directory")

    def test_missing_count_remains_null_and_zero_is_observed(self):
        missing = row(count=None)
        self.assertIsNone(missing["citation_snapshot"]["count"])
        self.assertEqual(missing["citation_snapshot"]["status"], "unavailable")
        observed_zero = row(count=0)
        self.assertEqual(observed_zero["citation_snapshot"]["count"], 0)
        self.assertEqual(observed_zero["citation_snapshot"]["status"], "observed")
        self.assertFalse(bibliometrics.validate_sidecar(missing))

    def test_partial_team_uses_max_and_median_with_coverage(self):
        authors = [author("Ada Example", "a1", 8), author("Bea Example", "a2", None)]
        result = bibliometrics.team_visibility(authors)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["unique_author_count"], 2)
        self.assertEqual(result["verified_h_index_author_count"], 1)
        self.assertEqual(result["coverage_fraction"], 0.5)
        self.assertEqual(result["max_h_index"], 8)
        self.assertEqual(result["median_h_index"], 8)

    def test_duplicate_author_does_not_vote_twice(self):
        duplicate = author("Ada Example", "a1", 8)
        alias = copy.deepcopy(duplicate)
        alias["paper_author_name"] = "Ada Example duplicate"
        alias["source_author_id"] = "different-provider-author-id"
        result = bibliometrics.team_visibility([duplicate, alias])
        self.assertEqual(result["unique_author_count"], 1)
        self.assertEqual(result["verified_h_index_author_count"], 1)
        self.assertEqual(result["max_h_index"], 8)

    def test_mixed_author_metric_scopes_are_not_aggregated(self):
        first = author("Ada Example", "a1", 8)
        second = author("Bea Example", "a2", 20)
        second["google_scholar"]["h_index_scope"] = "since_2021"
        result = bibliometrics.team_visibility([first, second])
        self.assertEqual(result["status"], "incomparable_scope")
        self.assertIsNone(result["max_h_index"])
        self.assertIsNone(result["median_h_index"])

    def test_age_bands_are_half_open_at_boundaries(self):
        self.assertEqual(bibliometrics.age_band(4.999), {"lower_inclusive": 4.0, "upper_exclusive": 5.0})
        self.assertEqual(bibliometrics.age_band(5.0), {"lower_inclusive": 5.0, "upper_exclusive": 6.0})

    def test_insufficient_same_age_population_has_no_percentile(self):
        target = row(count=50, provider_id="target")
        peers = [row(arxiv_id=f"2401.{i:05d}", count=i, provider_id=f"p{i}") for i in range(99)]
        evidence = self.population_evidence(peers)
        result = bibliometrics.cohort_percentile(target, peers, population_evidence=evidence)
        self.assertEqual(result["status"], "insufficient_population")
        self.assertIsNone(result["percentile"])
        self.assertEqual(result["population_size"], 99)

    def test_different_field_or_age_is_not_compared(self):
        target = row(count=50, provider_id="target")
        peers = [row(arxiv_id=f"2401.{i:05d}", count=i, field="gr-qc", provider_id=f"p{i}") for i in range(120)]
        evidence = self.population_evidence(peers)
        result = bibliometrics.cohort_percentile(target, peers, population_evidence=evidence)
        self.assertEqual(result["population_size"], 0)
        self.assertIsNone(result["percentile"])

    def test_duplicate_registered_versions_count_as_one_provider_work(self):
        target = row(count=50, provider_id="target")
        peers = [row(arxiv_id=f"2401.{i:05d}", count=i, provider_id=f"p{i}") for i in range(99)]
        duplicate_version = copy.deepcopy(peers[0])
        duplicate_version["paper_id"] = duplicate_version["paper_id"].replace("v1", "v2")
        duplicate_version["work_identity"]["registered_version"] = 2
        duplicate_version = bibliometrics.finalize_snapshot(duplicate_version)
        evidence = self.population_evidence(peers)
        result = bibliometrics.cohort_percentile(target, peers + [duplicate_version], population_evidence=evidence)
        self.assertEqual(result["status"], "insufficient_population")
        self.assertEqual(result["population_size"], 99)

    def test_unproven_selected_rows_cannot_become_percentile_population(self):
        target = row(count=100, provider_id="target")
        peers = [row(arxiv_id=f"2401.{i:05d}", count=i, provider_id=f"p{i}") for i in range(100)]
        result = bibliometrics.cohort_percentile(target, peers)
        self.assertEqual(result["status"], "not_queried")
        self.assertIsNone(result["percentile"])

    def test_source_backed_cohort_percentile_uses_one_hundred_unique_peers(self):
        target = row(count=100, provider_id="target")
        peers = [row(arxiv_id=f"2401.{i:05d}", count=i, provider_id=f"p{i}") for i in range(100)]
        evidence = self.population_evidence(peers)
        result = bibliometrics.cohort_percentile(target, peers, population_evidence=evidence)
        self.assertEqual(result["status"], "computed")
        self.assertEqual(result["population_size"], 100)
        self.assertEqual(result["percentile"], 100.0)

    def population_evidence(self, peers):
        cohort = peers[0]["comparison"]["cohort"]
        return {
            "scope_description": "INSPIRE cohort query fixture with exact category and publication-age range.",
            "provider": cohort["provider"],
            "snapshot_batch_id": cohort["snapshot_batch_id"],
            "field_definition": cohort["field_definition"],
            "age_band_years": cohort["age_band_years"],
            "provider_record_ids": [peer["work_identity"]["provider_record_id"] for peer in peers],
            "source": peers[0]["work_identity"]["source"],
        }

    def test_low_visibility_requires_review_and_complete_metrics(self):
        paper = {
            "paper_id": "arxiv:2401.01234v1",
            "arxiv_id": "2401.01234",
            "version": 1,
            "title": "Example paper",
            "published_utc": row()["comparison"]["first_publication_utc"],
            "authors": ["Ada Example", "Bea Example"],
            "screen": {"status": "reviewed"},
            "review_id": "review-1",
            "idea_ids": ["idea"],
        }
        sidecar = row()
        self.assertEqual(bibliometrics.classify_visibility(paper, sidecar, 10, "gs-batch-2026-10-01"), "unresolved_visibility")
        sidecar["authors"][0] = author("Ada Example", "a1", 8)
        sidecar["authors"][1] = author("Bea Example", "a2", 5)
        sidecar["team_visibility"] = bibliometrics.team_visibility(sidecar["authors"])
        sidecar = bibliometrics.finalize_snapshot(sidecar)
        self.assertEqual(bibliometrics.classify_visibility(paper, sidecar, 10, "gs-batch-2026-10-01"), "low_visibility")
        self.assertEqual(bibliometrics.classify_visibility(paper, sidecar, 10, "gs-batch-2026-10-02"), "unresolved_visibility")
        self.assertEqual(bibliometrics.classify_visibility({**paper, "review_id": None}, sidecar, 10, "gs-batch-2026-10-01"), "not_reviewed")


if __name__ == "__main__":
    unittest.main()
