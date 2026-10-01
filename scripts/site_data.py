"""Project scientific values into the public interface; leave workflow records in Git."""
import base64
import json
from pathlib import Path
from validate_register import ROOT, strict_load

ORDER = ['early-energy', 'late-dark-energy', 'interacting-sectors', 'inhomogeneity',
         'kinematics', 'modified-gravity', 'bounces-cycles', 'measurement-lineage']


def website_data(papers, ideas, prospects, graph):
    citations_path = ROOT / 'register/citations.json'
    citations = strict_load(citations_path)['citations'] if citations_path.exists() else []
    by_base = {}
    for ident, p in sorted(papers.items(), key=lambda item: item[1]['version']):
        by_base[p['arxiv_id']] = ident
    return {
        'prospects': [{k: strict_load(p)[k] for k in ['id','title','kind','baseline','cosmology','scope','unknowns','idea_ids','model_idea_ids','topic_ids','source_evidence']} for p in sorted((ROOT / 'register/prospects').glob('*.json'))],
        'groups': [{k: prospects[id][k] for k in ['id', 'title', 'paper_ids', 'idea_ids']}
                   for id in ORDER],
        'papers': [{'id': id, 'base_id': p['arxiv_id'], 'title': p['title'],
                    'authors': p['authors'], 'date': p['published_utc'][:10],
                    'url': p['urls']['abstract'], 'pdf': p['urls']['pdf'],
                    'read': bool(p['extraction'] and p['extraction']['reading_level'] == 'full_text')}
                   for id, p in sorted(papers.items())],
        'ideas': [{'id': id, 'title': p['title'], 'family': p['family'],
                   'assumptions': p['assumptions'], 'predictions': p['predictions'],
                   'sources': p['source_evidence']}
                  for id, p in sorted(ideas.items())],
        'edges': [{k: e[k] for k in ['from', 'to', 'type', 'rationale', 'evidence']}
                  for e in graph['edges'] if e['status'] == 'reviewed'
                  and e['from'] in ideas and e['to'] in ideas],
        'citations': [{'from': c['from_paper_id'], 'to': (f"arxiv:{c['cited_arxiv_id']}v{c['cited_version']}" if c['cited_version'] else by_base[c['cited_arxiv_id']]),
                       'reference': c['reference'], 'cited_version': c['cited_version']}
                      for c in citations],
    }


def write_site(data):
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True)
    (ROOT / 'site/data.json').write_text(payload + '\n')
    escaped = payload.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    logo = 'data:image/svg+xml;base64,' + base64.b64encode((ROOT / 'site/logo.svg').read_bytes()).decode()
    template = (ROOT / 'site/index.template.html').read_text().replace('/* LOGO_DATA */', logo)
    (ROOT / 'register/map.html').write_text(template.replace('/* REGISTER_DATA */ null', escaped))
