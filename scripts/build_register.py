#!/usr/bin/env python3
"""Generate browsing views from canonical records, without network or models."""
from collections import defaultdict
from validate_register import ROOT, records, strict_load, validate
from site_data import website_data, write_site


def paper_path(ident):
    return 'papers/' + ident.removeprefix('arxiv:').replace('/', '__') + '.json'


def md(value):
    return str(value).replace('|', '/').replace('\n', ' ')


def reading_stage(paper):
    if paper['review_id']:
        return 'reviewed'
    extraction = paper['extraction']
    if extraction and extraction['reading_level'] == 'full_text':
        return 'read'
    if extraction and extraction['reading_level'] == 'partial':
        return 'partial'
    return 'screened' if paper['screen']['basis'] != 'metadata' else 'discovered'


def build():
    validate()
    papers = records('register/papers', 'paper_id')
    ideas = records('register/ideas', 'id')
    designs = records('designs', 'design_id')
    reviews = records('register/reviews', 'review_id')
    topics = records('register/topics', 'id')
    prospects = records('register/prospects', 'id')
    graph = strict_load(ROOT / 'register/graph.json')
    citations = strict_load(ROOT / 'register/citations.json')
    lines = ['# Register', '',
             f'{len(papers)} paper versions · {len(ideas)} ideas · {len(topics)} topics · {len(prospects)} candidate prospects.', '',
             '[Open Prospector](https://prospector-cosmology.sprajs.chatgpt.site) · [Local map](map.html)', '',
             '## Topics', '', '| Topic | Papers | Ideas |', '| --- | ---: | ---: |']
    for ident, topic in sorted(topics.items()):
        lines.append(f"| [{topic['title']}](topics/{ident}.json) | {len(topic['paper_ids'])} | {len(topic['idea_ids'])} |")
    lines += ['', 'Topics are navigation groups. Membership does not establish equivalent physics.', '',
              '## Prospects', '', '| Candidate cosmology | Baseline |', '| --- | --- |']
    for ident, p in sorted(prospects.items()):
        lines.append(f"| [{p['title']}](prospects/{ident}.json) | {md(p['baseline']['label'])} |")
    lines += ['', 'Each prospect preserves its scope, alternative branches, unresolved physics and candidate investigation.',
              'Combined models require compatibility checks before promotion.', '', '## Idea tree', '']
    children = defaultdict(list)
    specialized = set()
    for edge in graph['edges']:
        if edge['type'] == 'specializes' and edge['status'] == 'reviewed':
            children[edge['to']].append(edge['from'])
            specialized.add(edge['from'])
    def render_node(ident, depth=0):
        lines.append(f"{'  ' * depth}- [{ideas[ident]['title']}](ideas/{ident}.json)")
        for child in sorted(set(children.get(ident, []))):
            render_node(child, depth + 1)
    for ident in sorted(set(ideas) - specialized):
        render_node(ident)
    lines += ['', '[Typed relationships](graph.json) preserve overlap, distinctions, critique, shared data and prospect links.',
              f'[Bibliographic citations](citations.json): {len(citations["citations"])} explicit links; the index is incomplete.', '',
              '## Papers', '', '| Paper | Version | Reading |', '| --- | --- | --- |']
    for ident, p in sorted(papers.items()):
        lines.append(f"| [{md(p['title'])}]({p['urls']['abstract']}) | [{ident.removeprefix('arxiv:')}]({paper_path(ident)}) | {reading_stage(p)} |")
    lines += ['', '## Investigations', '', '| Design | Readiness |', '| --- | --- |']
    for ident, d in sorted(designs.items()):
        lines.append(f"| [{d['title']}](../designs/{ident}.json) | {d['readiness']} |")
    lines += ['', 'Source checks and structural validation do not establish independent reproduction or scientific qualification.', '',
              '## Corrections', '']
    for ident, review in sorted(reviews.items()):
        for correction in review.get('corrections', []):
            if isinstance(correction, dict) and correction.get('display_summary'):
                lines.append(f"- [{correction.get('paper_id', ident)}](reviews/{ident}.json): {md(correction['display_summary'])}")
    lines += ['', '[Scan receipts](../scans/) · [Continuation queue](../state.json) · [Record conventions](../docs/records.md)', '']
    (ROOT / 'register/README.md').write_text('\n'.join(lines))
    write_site(website_data(papers, ideas, topics, graph))
    print('Updated register/README.md, register/map.html and site/data.json')


if __name__ == '__main__':
    build()
