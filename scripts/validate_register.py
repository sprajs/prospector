#!/usr/bin/env python3
"""Strict record/schema and cross-reference checks; not scientific validation."""
import hashlib
import json
import math
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_load(path):
    def bad_constant(value):
        raise ValueError(f"nonfinite JSON number: {value}")
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"unrepresentable JSON number: {value}")
        return number
    return json.loads(path.read_text(), object_pairs_hook=unique_pairs,
                      parse_constant=bad_constant, parse_float=finite_float)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def records(folder, key):
    result = {}
    for path in sorted((ROOT / folder).glob("*.json")):
        item = strict_load(path)
        ident = item[key]
        require(ident not in result, f"duplicate {key}: {ident}")
        filename = ident.removeprefix("arxiv:").replace("/", "__") + ".json"
        require(path.name == filename, f"noncanonical record filename: {path.name}")
        result[ident] = item
    return result


def validate():
    schemas = {name: strict_load(ROOT / "schemas" / (name + ".schema.json"))
               for name in ["paper", "candidate-design", "prospect"]}
    validators = {}
    for name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        validators[name] = Draft202012Validator(schema, format_checker=FormatChecker())
    papers = records("register/papers", "paper_id")
    ideas = records("register/ideas", "id")
    reviews = records("register/reviews", "review_id")
    designs = records("designs", "design_id")
    scans = records("scans", "scan_id")
    prospects = records("register/prospects", "id")
    require(papers, "empty paper register")
    for ident, review in reviews.items():
        require(review["requested_model"] == "gpt-6.1-sol", f"wrong review model: {ident}")
        require(review.get("agent_id"), f"missing review agent: {ident}")
        require(len(review["reviewed_papers"]) == len(set(review["reviewed_papers"])), "duplicate reviewed paper")
        details = review.get("reviewed_paper_details", [])
        require({d["paper_id"] for d in details} == set(review["reviewed_papers"])
                and len(details) == len(review["reviewed_papers"]), f"review details do not cover papers: {ident}")
        for paper_id in review["reviewed_papers"]:
            require(paper_id in papers, f"review references missing paper: {paper_id}")
        for detail in details:
            paper = papers[detail["paper_id"]]
            hashes = set(detail.get("source_hashes", {}).values())
            receipts = {a["sha256"] for a in paper["artifacts"]}
            sources = {a["sha256"] for a in paper["artifacts"] if a["role"] in {"html", "pdf"}}
            require(hashes and hashes.issubset(receipts) and hashes & sources,
                    f"review lacks receipted original-source hashes: {ident}")
            require(detail.get("coverage", {}).get("main_text"), f"review lacks coverage: {ident}")
            require(paper["extraction"] and paper["extraction"]["reading_level"] == "full_text",
                    f"review detail refers to unread paper: {ident}")
    for ident, paper in papers.items():
        validators["paper"].validate(paper)
        require(ident == f"arxiv:{paper['arxiv_id']}v{paper['version']}", f"paper identity mismatch: {ident}")
        versioned_id = ident.removeprefix("arxiv:")
        for url in paper["urls"].values():
            require(url.endswith("/" + versioned_id), f"unpinned paper URL: {ident}")
        extraction = paper["extraction"]
        if extraction:
            require(extraction["paper_id"] == ident, f"extraction identity mismatch: {ident}")
            if extraction["reading_level"] == "full_text":
                require(any(a["role"] in {"pdf", "html"} for a in paper["artifacts"]),
                        f"full read without source receipt: {ident}")
                hashes = extraction.get("source_hashes", {})
                require(hashes, f"full read lacks read-object hashes: {ident}")
                receipts = {a["sha256"] for a in paper["artifacts"] if a["role"] in {"html", "pdf", "extracted_text"}}
                original = {a["sha256"] for a in paper["artifacts"] if a["role"] in {"html", "pdf"}}
                require(set(hashes.values()).issubset(receipts) and set(hashes.values()) & original,
                        f"read-object hash lacks original-source receipt: {ident}")
                for role, digest in hashes.items():
                    require(any(a["role"] == role and a["sha256"] == digest for a in paper["artifacts"]),
                            f"read-object role/hash mismatch: {ident}")
        if paper["review_id"]:
            require(extraction is not None and extraction["reading_level"] == "full_text",
                    f"reviewed paper lacks a full-text reading packet: {ident}")
            require(paper["review_id"] in reviews, f"missing review: {ident}")
            require(ident in reviews[paper["review_id"]]["reviewed_papers"], f"review doesn't cover {ident}")
        if paper["screen"]["status"] == "reviewed":
            require(paper["review_id"] is not None, f"reviewed state without review: {ident}")
        for idea_id in paper["idea_ids"]:
            require(idea_id in ideas, f"paper references missing idea: {idea_id}")
    for ident, idea in ideas.items():
        require(idea.get("title") and idea.get("family") and idea.get("source_evidence"), f"incomplete idea: {ident}")
        require(idea["review_id"] in reviews, f"idea lacks review: {ident}")
        for evidence in idea["source_evidence"]:
            require(evidence["paper_id"] in papers and evidence.get("locator"), f"invalid idea evidence: {ident}")
            require(evidence["paper_id"] in reviews[idea["review_id"]]["reviewed_papers"],
                    f"idea source was not reviewed: {ident}")
    graph = strict_load(ROOT / "register/graph.json")
    nodes = set(papers) | set(ideas)
    require(len(graph["nodes"]) == len(set(graph["nodes"])), "duplicate graph node")
    require(set(graph["nodes"]) == nodes, "graph node inventory mismatch")
    edge_ids = set()
    parents = {}
    types = {"describes", "motivates", "specializes", "partial_overlap", "physically_distinct", "shares_data", "critiques", "updates"}
    for edge in graph["edges"]:
        require(edge["id"] not in edge_ids, "duplicate graph edge")
        edge_ids.add(edge["id"])
        require(edge["from"] in nodes and edge["to"] in nodes and edge["from"] != edge["to"], "invalid edge endpoints")
        require(edge["type"] in types and edge["status"] in {"reviewed", "provisional"}, "invalid edge type/status")
        require(edge.get("rationale") and edge.get("evidence"), "edge lacks evidence")
        if edge["status"] == "reviewed":
            require(edge.get("review_id") in reviews, "reviewed edge lacks Sol review")
        for evidence in edge["evidence"]:
            require(evidence["paper_id"] in papers and evidence.get("locator"), "invalid edge evidence")
            if edge["status"] == "reviewed":
                reviewed = set(reviews[edge["review_id"]]["reviewed_papers"])
                # Comparisons may use sources checked in an earlier review.
                reviewed.update(p for r in reviews.values() for p in r["reviewed_papers"])
                require(evidence["paper_id"] in reviewed, "reviewed edge uses an unread source")
        if edge["type"] == "specializes":
            parents.setdefault(edge["from"], []).append(edge["to"])
    visiting, visited = set(), set()
    def visit(node):
        require(node not in visiting, "specialization graph contains a cycle")
        if node in visited:
            return
        visiting.add(node)
        for parent in parents.get(node, []):
            visit(parent)
        visiting.remove(node)
        visited.add(node)
    for node in parents:
        visit(node)
    for ident, design in designs.items():
        validators["candidate-design"].validate(design)
        require(all(p in papers for p in design["paper_ids"]), f"design missing paper: {ident}")
        require(all(i in ideas for i in design["idea_ids"]), f"design missing idea: {ident}")
        require(design["review_id"] is None or design["review_id"] in reviews, f"design missing review: {ident}")
        if design["review_id"]:
            require(set(design["paper_ids"]).issubset(reviews[design["review_id"]]["reviewed_papers"]), f"design sources not reviewed: {ident}")
        for equation in design["equations"]:
            require(equation["paper_id"] in design["paper_ids"], f"design equation source mismatch: {ident}")
        request = design["executable_request"]
        if request:
            path = (ROOT / request["path"]).resolve()
            require(path.is_relative_to(ROOT) and path.is_file(), f"invalid executable path: {ident}")
            require(hashlib.sha256(path.read_bytes()).hexdigest() == request["sha256"], f"request digest mismatch: {ident}")
    grouped = set()
    for ident, prospect in prospects.items():
        validators["prospect"].validate(prospect)
        require(set(prospect["paper_ids"]).issubset(papers), f"prospect missing paper: {ident}")
        require(set(prospect["idea_ids"]).issubset(ideas), f"prospect missing idea: {ident}")
        require(set(prospect["design_ids"]).issubset(designs), f"prospect missing design: {ident}")
        grouped.update(prospect["paper_ids"])
    require(grouped == set(papers), "some paper versions lack a prospect group")
    state = strict_load(ROOT / "state.json")
    require(state["last_completed_scan"] in scans, "missing completed scan")
    require(scans[state["last_completed_scan"]]["status"] == "completed", "last completed scan is not completed")
    lanes = {lane["id"] for lane in state["lanes"]}
    require(len(lanes) == len(state["lanes"]) and state["next_lane"] in lanes, "invalid lane inventory")
    queued = set()
    for item in state["queue"]:
        require(item["paper_id"] in papers, "queue references missing paper")
        key = (item["paper_id"], item["stage"])
        require(key not in queued, "duplicate queued stage")
        queued.add(key)
        require(item["stage"] in {"screen", "acquire", "read", "review", "design"} and item.get("reason"), "invalid queued stage")
        paper = papers[item["paper_id"]]
        require(paper["screen"]["status"] != "excluded", "queue repeats excluded work")
        require(paper["screen"]["status"] != "reviewed" or item["stage"] == "design", "queue repeats finished work")
        if item["stage"] == "review":
            require(paper["extraction"] and paper["extraction"]["reading_level"] == "full_text",
                    "review queued before full reading")
        if item["stage"] == "design":
            require(paper["review_id"], "design queued before scientific review")
    unfinished = {p for p, d in papers.items() if d["screen"]["status"] not in {"excluded", "reviewed"}}
    require(unfinished.issubset({p for p, stage in queued if stage != "design"}), "unfinished papers lost from queue")
    for scan in scans.values():
        for key in ["registered_papers", "full_reads", "reviewed_papers"]:
            require(all(p in papers for p in scan[key]), f"scan references missing paper: {scan['scan_id']}")
        require(set(scan["full_reads"]).issubset(scan["registered_papers"]), "scan read not registered")
        require(set(scan["reviewed_papers"]).issubset(scan["full_reads"]), "scan review not read")
        require(len(scan["full_reads"]) == len(set(scan["full_reads"])), "duplicate scan read")
        for paper_id in scan["full_reads"]:
            extraction = papers[paper_id]["extraction"]
            require(extraction and extraction["reading_level"] == "full_text", "scan claims unread paper as full read")
        for paper_id in scan["reviewed_papers"]:
            require(papers[paper_id]["review_id"], "scan claims unreviewed paper as reviewed")
        require(all(i in ideas for i in scan["idea_ids"]), "scan missing idea")
        require(all(i in designs for i in scan["design_ids"]), "scan missing design")
        if "abstract_screens" in scan:
            require(set(scan["abstract_screens"]).issubset(papers), "scan screen missing paper")
        if "new_versions" in scan:
            require(set(scan["new_versions"]).issubset(scan["registered_papers"]), "scan new version not registered")
    print(f"Valid register: {len(papers)} paper versions, {len(ideas)} ideas, "
          f"{len(graph['edges'])} edges, {len(prospects)} prospects, {len(designs)} designs, {len(scans)} scans.")


if __name__ == "__main__":
    try:
        validate()
    except Exception as exc:
        print(f"Invalid register: {exc}", file=sys.stderr)
        sys.exit(1)
