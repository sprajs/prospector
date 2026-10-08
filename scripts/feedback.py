"""Versioned consumer findings inform bounded work, never scientific promotion."""
from datetime import datetime
from pathlib import Path

import jsonschema


def receipts(root):
    # Reuse the strict JSON reader without adding another authoritative index.
    from crawl import strict_load
    paths = sorted((root / 'register/feedback').glob('*.json'))
    state = strict_load(root / 'state.json')
    if not paths:
        if state.get('experiment_feedback_ids'):
            raise ValueError('state references missing feedback receipt')
        return []
    schema = strict_load(root / 'schemas/experiment-feedback.schema.json')
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    known_targets = {
        'paper': {strict_load(p)['paper_id'] for p in (root / 'register/papers').glob('*.json')},
        'design': {strict_load(p)['design_id'] for p in (root / 'designs').glob('*.json')},
        'prospect': {strict_load(p)['id'] for p in (root / 'register/prospects').glob('*.json')},
    }
    lanes = {lane['id'] for lane in state.get('lanes', [])}
    records = []
    for path in paths:
        record = strict_load(path)
        validator.validate(record)
        if path.stem != record['feedback_id']:
            raise ValueError('feedback filename differs from feedback_id')
        evidence_ids = [item['evidence_id'] for item in record['evidence']]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError('duplicate feedback evidence ID')
        finding_ids = [item['finding_id'] for item in record['findings']]
        if len(finding_ids) != len(set(finding_ids)):
            raise ValueError('duplicate feedback finding ID')
        for evidence in record['evidence']:
            rel = Path(evidence['path'])
            if rel.is_absolute() or '..' in rel.parts or str(rel) != evidence['path']:
                raise ValueError('feedback evidence requires canonical repository-relative path')
        for finding in record['findings']:
            if not set(finding['evidence_ids']).issubset(evidence_ids):
                raise ValueError('feedback finding references missing evidence')
        for priority in record['priorities']:
            if priority['lane'] not in lanes:
                raise ValueError('feedback priority references missing lane')
            if priority['target_id'] not in known_targets[priority['target_kind']]:
                raise ValueError('feedback priority references missing target')
            if not set(priority['finding_ids']).issubset(finding_ids):
                raise ValueError('feedback priority references missing finding')
        records.append(record)
    known = {r['feedback_id']: r for r in records}
    for record in records:
        previous = record['supersedes']
        if previous:
            old = known.get(previous)
            if (old is None or old['programme_id'] != record['programme_id']
                    or datetime.fromisoformat(old['recorded_utc'].replace('Z', '+00:00'))
                    >= datetime.fromisoformat(record['recorded_utc'].replace('Z', '+00:00'))):
                raise ValueError('feedback predecessor must exist in same programme and be earlier')
    if len([r['supersedes'] for r in records if r['supersedes']]) != len({r['supersedes'] for r in records if r['supersedes']}):
        raise ValueError('feedback predecessor has competing successors')
    for ident in state.get('experiment_feedback_ids', []):
        if ident not in known:
            raise ValueError('state references missing feedback receipt')
    return records


def priorities(root):
    records = receipts(root)
    superseded = {r['supersedes'] for r in records if r['supersedes']}
    return [dict(feedback_id=r['feedback_id'], programme_id=r['programme_id'],
                 recorded_utc=r['recorded_utc'], findings=r['findings'],
                 priorities=r['priorities'])
            for r in records if r['feedback_id'] not in superseded]
