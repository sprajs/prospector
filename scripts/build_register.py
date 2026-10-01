#!/usr/bin/env python3
"""Generate browsing views from canonical records, without network or models."""
from collections import defaultdict
import json

from validate_register import ROOT, records, strict_load, validate


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
    prospects = records('register/prospects', 'id')
    graph = strict_load(ROOT / 'register/graph.json')
    full = sum(bool(p['extraction'] and p['extraction']['reading_level'] == 'full_text') for p in papers.values())
    reviewed = sum(bool(p['review_id']) for p in papers.values())
    lines = ['# Prospect register', '',
             f'{len(papers)} paper versions · {full} full Luna reads · {reviewed} Sol-reviewed papers · '
             f'{len(ideas)} reviewed ideas · {len(prospects)} prospect groups.', '',
             '[Interactive map](map.html) · [Canonical graph](graph.json) · [Continuation queue](../state.json)', '',
             'Topic groups are navigation. Abstract screens do not establish physical equivalence.',
             'Source reviews are conditional checks, not independent reproductions or scientific qualification.', '',
             '## Prospects', '', '| Group | Versions | Reviewed papers | Reviewed ideas |', '| --- | ---: | ---: | ---: |']
    for ident, group in sorted(prospects.items()):
        lines.append(f"| [{group['title']}](#{ident}) | {len(group['paper_ids'])} | "
                     f"{sum(bool(papers[p]['review_id']) for p in group['paper_ids'])} | {len(group['idea_ids'])} |")
    lines += ['', '## Readings and reviews', '', '| Paper / pinned source | Luna coverage | Sol check |', '| --- | --- | --- |']
    for ident, paper in sorted(papers.items()):
        if not paper['extraction']:
            continue
        coverage = paper['extraction']['coverage']
        review = paper['review_id']
        stage = f'[{review}](reviews/{review}.json)' if review else 'Pending'
        lines.append(f"| [{md(paper['title'])}]({paper['urls']['abstract']}) | "
                     f"[{paper['extraction']['reading_level']}; {len(coverage['pdf_pages_read'])} pages; limits]({paper_path(ident)}) | {stage} |")
    lines += ['', '## Idea browsing tree', '',
              'Reviewed specialization runs from parent to child here. Other overlap and data relationships',
              'remain in the typed graph and map; the tree does not collapse distinct mechanisms.', '']
    children = defaultdict(list)
    specialized = set()
    for edge in graph['edges']:
        if edge['type'] == 'specializes' and edge['status'] == 'reviewed':
            children[edge['to']].append(edge['from'])
            specialized.add(edge['from'])
    def render_node(ident, depth=0):
        idea = ideas[ident]
        lines.append(f"{'  ' * depth}- [{idea['title']}](ideas/{ident}.json) — {idea['status'].replace('_', ' ')}")
        for child in sorted(set(children.get(ident, []))):
            render_node(child, depth + 1)
    families = defaultdict(list)
    for ident, idea in ideas.items():
        if ident not in specialized:
            families[idea['family']].append(ident)
    labels = {'early_expansion': 'Early expansion', 'timescape': 'Averaging and observer clocks',
              'observation_lineage': 'Measurement lineage', 'kinematics': 'Kinematic reconstruction',
              'scalar_unification': 'Early and late scalar histories', 'interacting_sectors': 'Interacting sectors'}
    for family, roots in sorted(families.items()):
        lines += [f"### {labels.get(family, family.replace('_', ' ').replace('-', ' '))}", '']
        for ident in sorted(roots):
            render_node(ident)
        lines.append('')
    lines += ['## Candidate investigations', '',
              'Readiness and blockers are recorded per design. No numerical paper reproduction has been run.', '']
    for design in sorted(designs.values(), key=lambda d: d['design_id']):
        lines.append(f"- [{design['title']}](../designs/{design['design_id']}.json) — {design['readiness']}.")
    lines += ['', '## Source corrections', '']
    for review in sorted(reviews.values(), key=lambda r: r['review_id']):
        lines += [f"[{review['review_id']}: {len(review.get('corrections', []))} recorded corrections](reviews/{review['review_id']}.json)", '']
        for correction in review.get('corrections', []):
            if isinstance(correction, dict) and correction.get('display_summary'):
                lines.append(f"- **{correction.get('paper_id', 'Review')}**: {md(correction['display_summary'])}")
        lines.append('')
    for ident, group in sorted(prospects.items()):
        lines += [f'<a id="{ident}"></a>', f"## {group['title']}", '', group['scope'], '',
                  '| Paper / source | Reading stage | Screen or review reason |', '| --- | --- | --- |']
        for pid in group['paper_ids']:
            paper = papers[pid]
            stage = {'reviewed': 'Sol reviewed', 'read': 'Luna full read; review pending',
                     'partial': 'Partial Luna reading', 'screened': 'Abstract screen',
                     'discovered': 'Metadata only'}[reading_stage(paper)]
            lines.append(f"| [{md(paper['title'])}]({paper['urls']['abstract']}) · [record]({paper_path(pid)}) | "
                         f"{stage} | {md(paper['screen']['reason'])} |")
        lines.append('')
    lines += ['See [scan receipts](../scans/) for exact queries, admitted versions, decisions and limitations.', '']
    (ROOT / 'register/README.md').write_text('\n'.join(lines))
    nodes = []
    for ident, paper in sorted(papers.items()):
        nodes.append({'id': ident, 'kind': 'paper', 'title': paper['title'],
                      'stage': reading_stage(paper),
                      'summary': paper['extraction']['summary'] if paper['extraction'] else paper['screen']['reason'],
                      'url': paper['urls']['abstract'], 'record': paper_path(ident),
                      'coverage': paper['extraction']['coverage'] if paper['extraction'] else None,
                      'groups': [g['id'] for g in prospects.values() if ident in g['paper_ids']],
                      'review': paper['review_id'],
                      'corrections': [c.get('display_summary', '') for r in reviews.values() for c in r.get('corrections', []) if c.get('paper_id') == ident]})
    for ident, idea in sorted(ideas.items()):
        nodes.append({'id': ident, 'kind': 'idea', 'title': idea['title'], 'stage': 'reviewed',
                      'summary': '\n'.join(idea['assumptions'] + idea['predictions']),
                      'record': f'ideas/{ident}.json', 'status': idea['status'],
                      'groups': [g['id'] for g in prospects.values() if ident in g['idea_ids']],
                      'review': idea['review_id'], 'evidence': idea['source_evidence']})
    payload = json.dumps({'nodes': nodes, 'edges': graph['edges'], 'groups': list(prospects.values())},
                         ensure_ascii=False, sort_keys=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = (ROOT / 'scripts/map.template.html').read_text()
    (ROOT / 'register/map.html').write_text(template.replace('/* REGISTER_DATA */ null', payload))
    print('Updated register/README.md and register/map.html')


if __name__ == '__main__':
    build()
