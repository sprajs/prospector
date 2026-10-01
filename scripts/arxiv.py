#!/usr/bin/env python3
"""Bounded arXiv acquisition for Codex readers; no model or scientific inference."""
import argparse
import fcntl
import hashlib
import json
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = {"a": "http://www.w3.org/2005/Atom", "ar": "http://arxiv.org/schemas/atom"}
ID = re.compile(r"(?:[0-9]{4}\.[0-9]{4,5}|[a-z-]+(?:\.[A-Z]{2})?/[0-9]{7})v[1-9][0-9]*\Z")
BASE_ID = re.compile(r"(?:[0-9]{4}\.[0-9]{4,5}|[a-z-]+(?:\.[A-Z]{2})?/[0-9]{7})\Z")


def official_url(url):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in {"arxiv.org", "export.arxiv.org"}
            or parsed.username or parsed.password or parsed.port not in {None, 443}):
        raise ValueError("Only official HTTPS arXiv acquisition is supported")


class OfficialRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        official_url(newurl)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def now():
    return datetime.now(timezone.utc).isoformat()


def atom_entries(body):
    root = ET.fromstring(body)
    if root.tag != "{http://www.w3.org/2005/Atom}feed":
        raise ValueError("arXiv response is not an Atom feed")
    entries = []
    for item in root.findall("a:entry", NS):
        vid = item.findtext("a:id", namespaces=NS).split("/abs/")[-1]
        if not ID.fullmatch(vid):
            raise ValueError(f"arXiv did not return a versioned paper identity: {vid}")
        entries.append({"versioned_id": vid, "title": " ".join(item.findtext("a:title", namespaces=NS).split()),
                        "authors": [x.findtext("a:name", namespaces=NS) for x in item.findall("a:author", NS)],
                        "categories": [x.get("term") for x in item.findall("a:category", NS)],
                        "published": item.findtext("a:published", namespaces=NS),
                        "updated": item.findtext("a:updated", namespaces=NS),
                        "abstract": " ".join(item.findtext("a:summary", namespaces=NS).split()),
                        "license_url": item.findtext("ar:license", namespaces=NS)})
    return entries


def matching_html(body, title):
    """Conservative title/body screen; actual paper/version coverage is a reader check."""
    class Identity(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_title = False
            self.title = []
            self.document = False

        def handle_starttag(self, tag, attrs):
            if tag == "title":
                self.in_title = True
            if tag == "article" and "ltx_document" in dict(attrs).get("class", "").split():
                self.document = True

        def handle_endtag(self, tag):
            if tag == "title":
                self.in_title = False

        def handle_data(self, data):
            if self.in_title:
                self.title.append(data)
    parsed = Identity()
    parsed.feed(body.decode("utf-8", errors="replace"))
    normalized = lambda value: re.sub(r"\W+", "", value).casefold()
    return parsed.document and normalized("".join(parsed.title)) == normalized(title)


class Client:
    def __init__(self, work):
        self.work = Path(work).resolve()
        if not self.work.is_relative_to(ROOT / ".work"):
            raise ValueError("Acquisition working files must be inside Prospector/.work")
        self.work.mkdir(parents=True, exist_ok=True)
        self.receipts = []
        log = self.work / "acquisition.jsonl"
        self.rate_limited = log.exists() and any(json.loads(line).get("http_status") == 429
                                                for line in log.read_text().splitlines())

    def fetch(self, label, url, suffix):
        if self.rate_limited:
            raise RuntimeError("Acquisition stopped after HTTP 429")
        official_url(url)
        if suffix not in {".xml", ".html", ".pdf"}:
            raise ValueError("Unsupported cache object suffix")
        lock_path = ROOT / ".work/acquisition.lock"
        with lock_path.open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            lock.seek(0)
            last = float(lock.read() or 0)
            time.sleep(max(0, last + 3.1 - time.time()))
            receipt = {"label": label, "url": url, "retrieved_utc": now(), "timeout_seconds": 20,
                       "byte_limit": 10 * 1024 * 1024}
            start = time.monotonic()
            body = None
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "Prospector/0.1 (https://github.com/sprajs/prospector)"})
                opener = urllib.request.build_opener(OfficialRedirects())
                with opener.open(request, timeout=20) as response:
                    body = response.read(receipt["byte_limit"] + 1)
                    if len(body) > receipt["byte_limit"]:
                        raise ValueError("Response exceeds 10 MiB intake allowance")
                    receipt.update(http_status=response.status, final_url=response.url,
                                   content_type=response.headers.get("Content-Type"), bytes=len(body),
                                   sha256=hashlib.sha256(body).hexdigest())
                    path = self.work / "objects" / (receipt["sha256"] + suffix)
                    path.parent.mkdir(exist_ok=True)
                    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() != receipt["sha256"]:
                        raise ValueError("Cached object hash mismatch")
                    if not path.exists():
                        path.write_bytes(body)
                    receipt["path"] = str(path.relative_to(ROOT))
            except Exception as exc:
                body = None
                receipt["error"] = f"{type(exc).__name__}: {exc}"
                if isinstance(exc, urllib.error.HTTPError):
                    receipt["http_status"] = exc.code
                    receipt["retry_after"] = exc.headers.get("Retry-After")
                    if exc.code == 429:
                        self.rate_limited = True
            finally:
                lock.seek(0)
                lock.truncate()
                lock.write(str(time.time()))
                lock.flush()
            receipt["elapsed_seconds"] = round(time.monotonic() - start, 3)
            self.receipts.append(receipt)
            with (self.work / "acquisition.jsonl").open("a") as stream:
                stream.write(json.dumps(receipt) + "\n")
        print(json.dumps({k: receipt.get(k) for k in ["label", "http_status", "bytes", "error"]}), flush=True)
        return body, receipt

    def metadata(self, ids):
        if not 1 <= len(ids) <= 20:
            raise ValueError("Metadata lookup supports 1–20 IDs per request")
        if not all(ID.fullmatch(ident) or BASE_ID.fullmatch(ident) for ident in ids):
            raise ValueError("Invalid arXiv metadata identity")
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate arXiv metadata identities")
        url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": ",".join(ids), "max_results": len(ids)})
        body, receipt = self.fetch("metadata", url, ".xml")
        if body is None:
            raise RuntimeError(receipt["error"])
        entries = atom_entries(body)
        requested = set(ids)
        received = {entry["versioned_id"] for entry in entries}
        require_exact = {ident for ident in requested if ID.fullmatch(ident)}
        if not require_exact.issubset(received):
            raise ValueError("Metadata did not return every requested exact version")
        base = lambda ident: re.sub(r"v[1-9][0-9]*$", "", ident)
        if {base(i) for i in received} != {base(i) for i in requested}:
            raise ValueError("Metadata identities do not match the lookup")
        return entries, receipt

    def search(self, query, limit=10, order="lastUpdatedDate", start=0, direction="descending"):
        if (not 1 <= limit <= 20 or start < 0
                or order not in {"lastUpdatedDate", "submittedDate", "relevance"}
                or direction not in {"ascending", "descending"}):
            raise ValueError("Invalid bounded search parameters")
        params = {"search_query": query, "start": start, "max_results": limit, "sortBy": order, "sortOrder": direction}
        body, receipt = self.fetch("search", "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params), ".xml")
        if body is None:
            raise RuntimeError(receipt["error"])
        return atom_entries(body), receipt

    def paper(self, entry):
        vid = entry["versioned_id"]
        if not ID.fullmatch(vid):
            raise ValueError("Paper acquisition requires an admitted exact version")
        manifest = {"entry": entry, "sources": [], "rejected_candidates": [], "errors": [],
                    "source_identity_verified": False,
                    "identity_note": "Reader must confirm pinned version, title/authors and body/figure coverage before admission as a full read."}
        sources = manifest["sources"]
        receipt_start = len(self.receipts)
        try:
            html, receipt = self.fetch(vid + "-html", "https://arxiv.org/html/" + vid, ".html")
            if html:
                if matching_html(html, entry["title"]):
                    sources.append(dict(receipt, role="html", identity_status="title_matched_reader_checks_pending"))
                else:
                    manifest["rejected_candidates"].append({"role": "html", "sha256": receipt["sha256"],
                                                            "reason": "Metadata title or full-document body did not match; not a reading source."})
            pdf = None
            for host in ["arxiv.org", "export.arxiv.org"]:
                pdf, receipt = self.fetch(vid + "-pdf", "https://" + host + "/pdf/" + vid, ".pdf")
                if pdf and pdf.startswith(b"%PDF"):
                    sources.append(dict(receipt, role="pdf", identity_status="reader_check_required"))
                    break
                if pdf:
                    manifest["rejected_candidates"].append({"role": "pdf", "sha256": receipt["sha256"],
                                                            "reason": "Response lacks PDF signature."})
            if pdf and pdf.startswith(b"%PDF"):
                text_path = self.work / (vid.replace("/", "__") + "-" + receipt["sha256"][:16] + ".partial.txt")
                subprocess.run(["pdftotext", "-layout", str(ROOT / receipt["path"]), str(text_path)], check=True, timeout=20)
                digest = hashlib.sha256(text_path.read_bytes()).hexdigest()
                target = self.work / "objects" / (digest + ".txt")
                target.parent.mkdir(exist_ok=True)
                if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                    raise ValueError("Cached derived-text hash mismatch")
                if not target.exists():
                    text_path.rename(target)
                else:
                    text_path.unlink()
                sources.append({"role": "extracted_text", "url": receipt["url"], "retrieved_utc": now(),
                                "path": str(target.relative_to(ROOT)), "sha256": digest,
                                "bytes": target.stat().st_size, "derived_from_sha256": receipt["sha256"],
                                "tool": "pdftotext -layout"})
        except Exception as exc:
            manifest["errors"].append(f"{type(exc).__name__}: {exc}")
        finally:
            manifest["acquisition_attempts"] = self.receipts[receipt_start:]
            manifest["full_text_available"] = any(s["role"] in {"pdf", "html"} for s in sources)
            manifest["acquisition_stopped_after_429"] = bool(self.rate_limited)
            path = self.work / (vid.replace("/", "__") + "-sources.json")
            if path.exists():
                old = path.read_bytes()
                history = self.work / "manifest-history"
                history.mkdir(exist_ok=True)
                (history / (hashlib.sha256(old).hexdigest() + ".json")).write_bytes(old)
            path.write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--work", required=True)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--order", default="lastUpdatedDate")
    args = parser.parse_args()
    client = Client(args.work)
    entries, receipt = client.search(args.query, args.limit, args.order)
    (client.work / "search.json").write_text(json.dumps({"entries": entries, "receipt": receipt}, indent=2) + "\n")
    print(json.dumps([{"id": x["versioned_id"], "title": x["title"]} for x in entries], indent=2))
