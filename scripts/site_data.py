"""Project scientific values into the public interface; leave workflow records in Git."""
import base64
import json
from pathlib import Path
from validate_register import ROOT, strict_load

ORDER = ['baseline-reference', 'early-energy', 'late-dark-energy', 'interacting-sectors', 'inhomogeneity',
         'kinematics', 'modified-gravity', 'bounces-cycles', 'measurement-lineage']


def public_contract(item):
    """Expose checked source scope without local storage or worker provenance."""
    return {
        'title': item['title'], 'limitations': item['limitations'],
        'scopes': [{k: scope[k] for k in ['scope_id', 'title', 'paper_ids', 'checked_claim', 'unresolved']}
                   for scope in item['scopes']],
        'sources': [{k: source[k] for k in ['id', 'url', 'sha256', 'role', 'conditioning']}
                    for source in item['source_assets']],
    }


def public_investigation(item):
    """Export scientific conditioning, omitting consumer requests and private input paths."""
    return ({k: item[k] for k in ['title', 'readiness', 'faithful_claim', 'assumptions',
                                'simplifications', 'unknowns']}
           | {'test': {k: item['minimal_test'][k] for k in ['question', 'observables']},
              'equations': [{k: eq[k] for k in ['expression', 'locator', 'paper_id', 'definitions', 'domain', 'status']}
                            for eq in item['equations']]})


def public_serialization(item):
    """Publish scalar conditioning and primary links, excluding worker/acquisition fields."""
    return {
        'title': item['title'], 'unknowns': item['unknowns'],
        'scalars': [{k: scalar[k] for k in ['id', 'decimal_value', 'unit', 'value_class',
                    'source_asset_ids', 'locator']}
                    | {'asd_parenthesized_theory_flag': scalar.get('asd_parenthesized_theory_flag'),
                       'uncertainty': {k: scalar['uncertainty'][k] for k in
                       ['decimal_value', 'interpretation', 'distribution', 'coverage', 'reason']}}
                    for scalar in item['scalars']],
        'sources': [{k: source[k] for k in ['id', 'title', 'url', 'sha256', 'source_version',
                    'coverage', 'unread']}
                    | {'dataset_provenance': source.get('dataset_provenance')}
                    for source in item['source_assets']],
    }


def visibility_snapshots():
    """Latest per-paper/provider metrics, excluding acquisition and worker details."""
    latest = {}
    for path in sorted((ROOT / 'register/bibliometrics').glob('*.json')):
        item = strict_load(path)
        key = (item['paper_id'], item['work_identity']['provider'])
        old = latest.get(key)
        if old is None or (item['snapshot_created_utc'], item['snapshot_id']) > (old['snapshot_created_utc'], old['snapshot_id']):
            latest[key] = item
    public = {}
    for (ident, provider), item in sorted(latest.items()):
        citation, cohort, team = item['citation_snapshot'], item['comparison']['cohort'], item['team_visibility']
        public.setdefault(ident, []).append({
            'provider': provider, 'date': citation['retrieved_utc'],
            'url': 'https://inspirehep.net/literature/' + item['work_identity']['provider_record_id'] if provider == 'INSPIRE-HEP' and item['work_identity']['provider_record_id'] else citation['source']['request_url'],
            'citation_count': citation['count'], 'count_without_self_citations': citation['count_without_self_citations'],
            'count_scope': item['work_identity']['count_scope'],
            'version_scope': item['work_identity']['version_scope'],
            'age_days': item['comparison']['age_days_at_snapshot'],
            'cohort_percentile': cohort['percentile'], 'cohort_reason': cohort['reason'],
            'author_count': team['unique_author_count'],
            'verified_author_metrics': team['verified_h_index_author_count'],
            'max_h_index': team['max_h_index'], 'median_h_index': team['median_h_index'],
            'author_metric_reason': team['missing_reason'],
        })
    return public


def website_data(papers, ideas, prospects, graph):
    citations_path = ROOT / 'register/citations.json'
    citations = strict_load(citations_path)['citations'] if citations_path.exists() else []
    by_base = {}
    for ident, p in sorted(papers.items(), key=lambda item: item[1]['version']):
        by_base[p['arxiv_id']] = ident
    metrics = visibility_snapshots()
    contracts = {p.stem: strict_load(p) for p in (ROOT / 'register/contracts').glob('*.json')}
    designs = {p.stem: strict_load(p) for p in (ROOT / 'designs').glob('*.json')}
    serializations = {p.stem: public_serialization(strict_load(p))
                      for p in (ROOT / 'register/source-data').glob('*.json')}
    def public_prospect(path):
        item = strict_load(path)
        public = {k: item[k] for k in ['id','title','kind','readiness','baseline','cosmology','scope','unknowns','idea_ids','model_idea_ids','topic_ids','source_evidence']}
        public['source_gates'] = [{k: scope[k] for k in ['scope_id','title','paper_ids','checked_claim','unresolved']}
                                 for ident in item.get('source_contract_ids', [])
                                 for scope in contracts[ident]['scopes']]
        public['scalar_sources'] = [serializations[ident] for ident in sorted({
            source['serialization_id'] for contract in item.get('source_contract_ids', [])
            for source in contracts[contract].get('source_serializations', [])})]
        # Paper-set association is navigation, not a new physical graph relation.
        public['additional_source_contracts'] = [public_contract(contract)
            for ident, contract in sorted(contracts.items())
            if ident not in item.get('source_contract_ids', [])
            and contract.get('paper_ids')
            and set(contract['paper_ids']).issubset(item.get('paper_ids', []))]
        public['investigations'] = [public_investigation(designs[ident])
                                    for ident in item.get('design_ids', [])]
        return public
    return {
        'prospects': [public_prospect(p) for p in sorted((ROOT / 'register/prospects').glob('*.json'))],
        'groups': [{k: prospects[id][k] for k in ['id', 'title', 'paper_ids', 'idea_ids']}
                   for id in ORDER],
        'papers': [{'id': id, 'base_id': p['arxiv_id'], 'title': p['title'],
                    'authors': p['authors'], 'date': p['published_utc'][:10],
                    'updated_date': p['updated_utc'][:10],
                    'url': p['urls']['abstract'], 'pdf': p['urls']['pdf'],
                    'visibility': metrics.get(id, []),
                    'read': bool(p['extraction'] and p['extraction']['reading_level'] == 'full_text')}
                   for id, p in sorted(papers.items())],
        'ideas': [{'id': id, 'title': p['title'], 'family': p['family'],
                   'assumptions': p['assumptions'], 'predictions': p['predictions'],
                   'sources': p['source_evidence']}
                  for id, p in sorted(ideas.items())],
        'edges': [{k: e[k] for k in ['from', 'to', 'type', 'rationale', 'evidence']}
                  for e in graph['edges'] if e['status'] == 'reviewed'
                  and e['from'] in ideas and e['to'] in ideas],
        'timeline': [{'idea_id': ident,
                      'first_source_date': min(papers[s['paper_id']]['published_utc'][:10]
                                               for s in idea['source_evidence']),
                      'source_paper_ids': sorted({s['paper_id'] for s in idea['source_evidence']})}
                     for ident, idea in sorted(ideas.items())],
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
