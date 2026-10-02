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
               for name in ["paper", "candidate-design", "topic", "prospect", "citations", "reference", "source-contract"]}
    validators = {}
    for name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        validators[name] = Draft202012Validator(schema, format_checker=FormatChecker())
    papers = records("register/papers", "paper_id")
    ideas = records("register/ideas", "id")
    reviews = records("register/reviews", "review_id")
    designs = records("designs", "design_id")
    scans = records("scans", "scan_id")
    topics = records("register/topics", "id")
    prospects = records("register/prospects", "id")
    require(papers, "empty paper register")
    from bibliometrics import validate_sidecar, finalize_snapshot
    metric_ids = set()
    for path in sorted((ROOT / 'register/bibliometrics').glob('*.json')):
        metric = strict_load(path)
        errors = validate_sidecar(metric)
        require(not errors, f"invalid bibliometric snapshot {path.name}: {errors}")
        require(metric['paper_id'] in papers, 'bibliometric snapshot references missing paper')
        paper = papers[metric['paper_id']]
        work = metric['work_identity']
        require(work['arxiv_id'] == paper['arxiv_id'] and work['registered_version'] == paper['version'],
                'bibliometric snapshot paper identity mismatch')
        require(metric['comparison']['first_publication_utc'] == paper['published_utc'],
                'bibliometric age uses a different first-publication date')
        require(work['title'] == paper['title'], 'bibliometric title differs from registered source')
        require({a['paper_author_name'] for a in metric['authors']} == set(paper['authors']),
                'bibliometric author coverage differs from registered source')
        ident = metric['snapshot_id']
        key = (metric['paper_id'], work['provider'], ident)
        require(key not in metric_ids, 'duplicate bibliometric snapshot')
        metric_ids.add(key)
        require(finalize_snapshot(dict(metric))['snapshot_id'] == ident,
                'bibliometric snapshot ID differs from its immutable contents')
        filename = metric['paper_id'].removeprefix('arxiv:').replace('/', '__') + '-' + ident + '.json'
        require(path.name == filename, 'noncanonical bibliometric snapshot filename')
    # Durable discovery coverage is independent of admission into the paper register.
    from crawl import receipts as search_receipts
    searches = search_receipts(ROOT)
    for search in searches:
        require(search['lane'] is None or search['lane'] in topics,
                'search references missing topic lane')
        if search['provenance']['scan_id']:
            require(search['provenance']['scan_id'] in scans,
                    'search references missing scan receipt')
        for hit in search['results']:
            if hit['disposition'] == 'duplicate':
                require(hit['paper_id'] in papers,
                        'search claims registered disposition for missing paper')
    targeted = lambda review: review.get("review_kind") == "targeted_source_claims"
    def accepted_record(review_id, kind, ident):
        review = reviews[review_id]
        if targeted(review):
            require(ident in review.get('accepted_records', {}).get(kind, []),
                    f"targeted review does not accept {kind}: {ident}")
    for ident, review in reviews.items():
        require(review["requested_model"] == "gpt-6.1-sol", f"wrong review model: {ident}")
        require(review.get("agent_id"), f"missing review agent: {ident}")
        if targeted(review):
            require(review.get('packet_sha256') and review.get('model_confirmation'),
                    f"targeted review lacks packet/model provenance: {ident}")
            confirmation = review['model_confirmation']
            require(review.get('requested_reasoning') in {'high', 'xhigh'}
                    and confirmation.get('model') == 'gpt-6.1-sol'
                    and confirmation.get('effort') == review.get('requested_reasoning'),
                    f"targeted review lacks required model/reasoning confirmation: {ident}")
            require(review.get('limitations') and review.get('accepted_records'),
                    f"targeted review lacks claim scope/limits: {ident}")
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
            if targeted(review):
                for role, digest in detail.get('source_hashes', {}).items():
                    require(any(a['role'] == role and a['sha256'] == digest for a in paper['artifacts']),
                            f"review source role/hash mismatch: {ident}")
                require(detail['coverage'].get('checked_locators') and detail['coverage'].get('unread'),
                        f"targeted review lacks located coverage/unread scope: {ident}")
            else:
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
            require(not targeted(reviews[paper['review_id']]),
                    f"targeted review cannot promote full-paper stage: {ident}")
            require(ident in reviews[paper["review_id"]]["reviewed_papers"], f"review doesn't cover {ident}")
        if paper["screen"]["status"] == "reviewed":
            require(paper["review_id"] is not None, f"reviewed state without review: {ident}")
        for idea_id in paper["idea_ids"]:
            require(idea_id in ideas, f"paper references missing idea: {idea_id}")
    for ident, idea in ideas.items():
        require(idea.get("title") and idea.get("family") and idea.get("source_evidence"), f"incomplete idea: {ident}")
        require(idea["review_id"] in reviews, f"idea lacks review: {ident}")
        accepted_record(idea['review_id'], 'idea_ids', ident)
        for evidence in idea["source_evidence"]:
            require(evidence["paper_id"] in papers and evidence.get("locator"), f"invalid idea evidence: {ident}")
            require(evidence["paper_id"] in reviews[idea["review_id"]]["reviewed_papers"],
                    f"idea source was not reviewed: {ident}")
            review = reviews[idea['review_id']]
            if targeted(review):
                detail = next(d for d in review['reviewed_paper_details'] if d['paper_id'] == evidence['paper_id'])
                require(evidence['locator'] in detail['coverage']['checked_locators'],
                        f"idea locator outside targeted review: {ident}")
    references = {}
    for path in sorted((ROOT / 'references').rglob('*.json')):
        reference = strict_load(path)
        validators['reference'].validate(reference)
        ident = reference['reference_id']
        require(ident not in references, 'duplicate reference identity')
        references[ident] = (path, reference)
        require(reference['paper_id'] in papers, 'reference missing source paper')
        paper = papers[reference['paper_id']]
        require(any(r in {'html', 'pdf'} for r in reference['source_sha256']), 'reference lacks original source')
        for role, digest in reference['source_sha256'].items():
            require(any(a['role'] == role and a['sha256'] == digest for a in paper['artifacts']),
                    'reference source hash lacks receipt')
        require(len({p['name'] for p in reference['parameters']}) == len(reference['parameters']),
                'duplicate reference parameter')
        if reference['status'] == 'targeted_reviewed':
            require(reference['review_id'] in reviews, 'reference lacks review')
            accepted_record(reference['review_id'], 'reference_ids', ident)
            accepted_record(reference['review_id'], 'reference_ids', reference['supported_variant']['id'])
            require(reference['paper_id'] in reviews[reference['review_id']]['reviewed_papers'],
                    'reference source not reviewed')
        else:
            require(reference['review_id'] is None, 'pending reference has review')
    contracts = records('register/contracts', 'contract_id')
    for ident, contract in contracts.items():
        validators['source-contract'].validate(contract)
        require(contract['review_id'] in reviews, 'source contract lacks review')
        accepted_record(contract['review_id'], 'contract_ids', ident)
        require(set(contract['paper_ids']).issubset(papers), 'source contract missing paper')
        require(set(contract['paper_ids']).issubset(reviews[contract['review_id']]['reviewed_papers']),
                'source contract sources not reviewed')
        scope_ids = [scope['scope_id'] for scope in contract['scopes']]
        require(len(scope_ids) == len(set(scope_ids)), 'duplicate source contract scope')
        for scope in contract['scopes']:
            require(set(scope['paper_ids']).issubset(contract['paper_ids']),
                    'source scope outside contract papers')
        asset_ids = [asset['id'] for asset in contract['source_assets']]
        require(len(asset_ids) == len(set(asset_ids)), 'duplicate source contract asset')
    citations = strict_load(ROOT / "register/citations.json")
    validators["citations"].validate(citations)
    require(set(citations['inspected_paper_ids']).issubset(papers), "citation inspection references missing paper")
    base_ids = {p['arxiv_id'] for p in papers.values()}
    citation_ids, citation_pairs = set(), set()
    for citation in citations['citations']:
        ident, base = citation['from_paper_id'], citation['cited_arxiv_id']
        require(ident in papers and base in base_ids, "citation references missing paper")
        require(ident in citations['inspected_paper_ids'], "citation source was not inspected")
        if citation['cited_version'] is not None:
            require(f"arxiv:{base}v{citation['cited_version']}" in papers, "cited version missing from register")
        require(base != papers[ident]['arxiv_id'], "self citation")
        pair = (ident, base, citation['cited_version'])
        require(citation['id'] not in citation_ids and pair not in citation_pairs, "duplicate citation")
        citation_ids.add(citation['id']); citation_pairs.add(pair)
        source = citation['source']
        require(any(a['role'] == source['role'] and a['sha256'] == source['sha256']
                    for a in papers[ident]['artifacts']), "citation lacks original-source receipt")
        require(source['url'].split('#')[0] == papers[ident]['urls'][source['role']]
                and '#' in source['url'], "citation source URL is not pinned or located")
    graph = strict_load(ROOT / "register/graph.json")
    nodes = set(papers) | set(ideas) | set(prospects)
    require(len(graph["nodes"]) == len(set(graph["nodes"])), "duplicate graph node")
    require(set(graph["nodes"]) == nodes, "graph node inventory mismatch")
    edge_ids = set()
    parents = {}
    types = {"describes", "motivates", "specializes", "partial_overlap", "physically_distinct", "shares_data", "critiques", "updates", "informs"}
    for edge in graph["edges"]:
        require(edge["id"] not in edge_ids, "duplicate graph edge")
        edge_ids.add(edge["id"])
        require(edge["from"] in nodes and edge["to"] in nodes and edge["from"] != edge["to"], "invalid edge endpoints")
        require(edge["type"] in types and edge["status"] in {"reviewed", "provisional"}, "invalid edge type/status")
        require(edge.get("rationale") and edge.get("evidence"), "edge lacks evidence")
        if edge["type"] == "informs":
            require(edge["from"] in ideas and edge["to"] in prospects, "invalid prospect edge")
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
            accepted_record(design['review_id'], 'design_ids', ident)
            require(set(design["paper_ids"]).issubset(reviews[design["review_id"]]["reviewed_papers"]), f"design sources not reviewed: {ident}")
        for equation in design["equations"]:
            require(equation["paper_id"] in design["paper_ids"], f"design equation source mismatch: {ident}")
        for source in design.get('source_references', []):
            require(source['reference_id'] in references, 'design missing source reference')
            path, reference = references[source['reference_id']]
            require(source['path'] == str(path.relative_to(ROOT)), 'noncanonical reference path')
            require(hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256'],
                    'design reference digest mismatch')
            require(reference['paper_id'] in design['paper_ids'], 'design reference source mismatch')
            if design['review_id']:
                require(reference['review_id'] == design['review_id'], 'design reference review mismatch')
        for source in design.get('source_contracts', []):
            require(source['contract_id'] in contracts, 'design missing source contract')
            contract = contracts[source['contract_id']]
            path = ROOT / 'register/contracts' / (source['contract_id'] + '.json')
            require(source['path'] == str(path.relative_to(ROOT)), 'noncanonical source contract path')
            require(hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256'],
                    'design source contract digest mismatch')
            require(set(design['paper_ids']).issubset(contract['paper_ids']), 'design source contract paper mismatch')
            require(design['review_id'] == contract['review_id'], 'design source contract review mismatch')
        request = design["executable_request"]
        if request:
            path = (ROOT / request["path"]).resolve()
            require(path.is_relative_to(ROOT) and path.is_file(), f"invalid executable path: {ident}")
            require(hashlib.sha256(path.read_bytes()).hexdigest() == request["sha256"], f"request digest mismatch: {ident}")
    for ident, prospect in prospects.items():
        validators['prospect'].validate(prospect)
        require(set(prospect['model_idea_ids']).issubset(prospect['idea_ids']), 'prospect model idea is outside its evidence ideas')
        require(set(prospect['idea_ids']).issubset(ideas), 'prospect references missing idea')
        require(set(prospect['paper_ids']).issubset(papers), 'prospect references missing paper')
        require(set(prospect['design_ids']).issubset(designs), 'prospect references missing design')
        require(set(prospect['topic_ids']).issubset(topics), 'prospect references missing topic')
        for contract_id in prospect.get('source_contract_ids', []):
            require(contract_id in contracts, 'prospect missing source contract')
            require(set(contracts[contract_id]['paper_ids']).issubset(prospect['paper_ids']),
                    'prospect source contract paper mismatch')
            require(contracts[contract_id]['review_id'] == prospect['review_id'],
                    'prospect source contract review mismatch')
        if prospect['review_id'] is not None:
            require(prospect['review_id'] in reviews, 'prospect lacks scientific review')
            accepted_record(prospect['review_id'], 'prospect_ids', ident)
            require(set(prospect['paper_ids']).issubset(reviews[prospect['review_id']]['reviewed_papers']),
                    'prospect review does not cover its papers')
        for source in prospect['source_evidence']:
            require(source['paper_id'] in prospect['paper_ids'], 'prospect evidence outside its paper set')
            paper = papers[source['paper_id']]
            require(source['url'] == paper['urls']['abstract'], 'prospect source URL is not pinned')
            hashes = source['source_sha256']
            require(any(role in {'pdf','html'} for role in hashes), 'prospect lacks original source')
            for role, digest in hashes.items():
                require(any(a['role'] == role and a['sha256'] == digest for a in paper['artifacts']),
                        'prospect source hash lacks receipt')
        for design_id in prospect['design_ids']:
            design = designs[design_id]
            require(set(design['paper_ids']).issubset(prospect['paper_ids'])
                    and set(design['idea_ids']).issubset(prospect['idea_ids']),
                    'prospect design uses unrelated sources or ideas')
        for edge in graph['edges']:
            if edge['type'] != 'informs' or edge['to'] != ident:
                continue
            require(all(s['paper_id'] in prospect['paper_ids'] for s in edge['evidence']),
                    'prospect edge uses unrelated source evidence')
            if prospect['review_id'] is not None:
                require(edge['status'] == 'reviewed' and edge['review_id'] == prospect['review_id'],
                        'prospect accepted link lacks its scientific review')
        links = {e['from'] for e in graph['edges'] if e['type'] == 'informs' and e['to'] == ident}
        require(links == set(prospect['idea_ids']), 'prospect graph links disagree with ideas')
        if prospect['readiness'] == 'ready_for_consumer_review':
            require(prospect['review_id'] is not None and not prospect['unknowns'], 'prospect promotion has unresolved science')
            if prospect['kind'] == 'combination':
                require(prospect['combination_compatibility']['status'] == 'checked_compatible',
                        'combined prospect has unchecked compatibility')
            require(all(designs[d]['readiness'] == 'ready_for_consumer_review' for d in prospect['design_ids']),
                    'prospect promotion lacks accepted design')
    grouped = set()
    for ident, prospect in topics.items():
        validators["topic"].validate(prospect)
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
        for review_id in scan.get('targeted_source_reviews', []):
            require(review_id in reviews and targeted(reviews[review_id]), 'scan lacks targeted review')
        require(all(i in ideas for i in scan["idea_ids"]), "scan missing idea")
        require(all(i in designs for i in scan["design_ids"]), "scan missing design")
        if "abstract_screens" in scan:
            require(set(scan["abstract_screens"]).issubset(papers), "scan screen missing paper")
        if "new_versions" in scan:
            require(set(scan["new_versions"]).issubset(scan["registered_papers"]), "scan new version not registered")
    print(f"Valid register: {len(papers)} paper versions, {len(ideas)} ideas, "
          f"{len(graph['edges'])} edges, {len(topics)} topics, {len(prospects)} prospects, {len(designs)} designs, {len(scans)} scans.")


if __name__ == "__main__":
    try:
        validate()
    except Exception as exc:
        print(f"Invalid register: {exc}", file=sys.stderr)
        sys.exit(1)
