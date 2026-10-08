#!/usr/bin/env python3
"""One-page arXiv discovery and a rebuildable local index of public evidence."""
import argparse
import hashlib
import json
import re
import sqlite3
import urllib.parse
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import arxiv

ROOT = Path(__file__).resolve().parents[1]
DISPOSITIONS = {'pending', 'duplicate', 'selected', 'excluded', 'deferred', 'unknown'}
INDEX_VERSION = '1'


def strict_load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(f'invalid JSON number: {value}')
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                      parse_constant=invalid, parse_float=lambda value: finite_float(value))


def finite_float(value):
    import math
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError('nonfinite JSON number')
    return parsed


def normalize_query(query):
    # Preserve internal whitespace, case, quoting and Boolean syntax. Even
    # apparent synonyms must not silently become the same discovery request.
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be nonempty')
    return query.strip()


def request_window(query, order='lastUpdatedDate', direction='descending', start=0, limit=10):
    if order not in {'lastUpdatedDate', 'submittedDate', 'relevance'}:
        raise ValueError('invalid arXiv sort order')
    if direction not in {'ascending', 'descending'}:
        raise ValueError('invalid arXiv sort direction')
    if type(start) is not int or start < 0 or type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError('search supports one page of 1–20 entries at a nonnegative offset')
    normalized = normalize_query(query)
    identity = dict(query=normalized, order=order, direction=direction, start=start, limit=limit)
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return dict(query=query, normalized_query=normalized, order=order, direction=direction,
                start=start, limit=limit, window_sha256=digest)


def validate_receipt(record, root=ROOT):
    schema = strict_load(root / 'schemas/search.schema.json')
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(record)
    request = record['request']
    if request_window(request['query'], request['order'], request['direction'], request['start'],
                      request['limit']) != request:
        raise ValueError('search window identity does not match request')
    ids = [result['paper_id'] for result in record['results']]
    if len(ids) != len(set(ids)) or len(ids) > request['limit']:
        raise ValueError('duplicate results or results beyond requested page')
    if [result['position'] for result in record['results']] != list(range(len(ids))):
        raise ValueError('result positions must preserve contiguous API order')
    for result in record['results']:
        if not arxiv.ID.fullmatch(result['paper_id'].removeprefix('arxiv:')):
            raise ValueError('result lacks exact versioned arXiv identity')
        if result['decision_history']:
            latest = result['decision_history'][-1]
            if (latest['disposition'], latest['reason']) != (result['disposition'], result['reason']):
                raise ValueError('current disposition differs from decision history')
    if record['status'] != 'completed' and record['results']:
        raise ValueError('failed or interrupted query cannot claim a complete result snapshot')
    if record['coverage']['dispositions_complete'] and any(result['disposition'] in {'pending', 'unknown'} for result in record['results']):
        raise ValueError('completed disposition coverage cannot include pending/unknown hits')
    if record['status'] == 'completed' and record['source']['error']:
        raise ValueError('completed query has a source error')
    if record['provenance']['kind'] == 'live' and record['status'] == 'completed':
        if not all(record['source'][field] for field in ['url', 'retrieved_utc', 'sha256']):
            raise ValueError('completed live query requires original metadata receipt provenance')
        if record['source']['http_status'] != 200 or not record['coverage']['result_ids_complete']:
            raise ValueError('completed live query requires a successful complete result snapshot')
    source_path = record['source']['local_path']
    if source_path and (Path(source_path).is_absolute() or '..' in Path(source_path).parts
                        or not source_path.startswith('.work/')):
        raise ValueError('cached search source path must be relative inside .work')
    if bool(record['retry_of']) != bool(record['retry_reason']):
        raise ValueError('failure retry must preserve its reason')
    if record['refresh'] and record['retry_of']:
        raise ValueError('a query cannot be both retry and refresh')
    return record


def receipts(root=ROOT):
    records = []
    for path in sorted((root / 'register/searches').glob('*.json')):
        record = validate_receipt(strict_load(path), root)
        if path.stem != record['search_id']:
            raise ValueError(f'receipt filename differs from search_id: {path}')
        records.append(record)
    known = {record['search_id']: record for record in records}
    for record in records:
        for reference in [record['retry_of'], (record['refresh'] or {}).get('previous_search_id')]:
            if reference:
                if reference not in known or known[reference]['request']['window_sha256'] != record['request']['window_sha256']:
                    raise ValueError('retry/refresh must reference a recorded identical request window')
                if reference == record['search_id']:
                    raise ValueError('retry/refresh cannot reference itself')
                predecessor = known[reference]
                previous_time = datetime.fromisoformat(predecessor['requested_utc'].replace('Z', '+00:00'))
                current_time = datetime.fromisoformat(record['requested_utc'].replace('Z', '+00:00'))
                if previous_time >= current_time:
                    raise ValueError('retry/refresh predecessor must be strictly earlier')
                if record['retry_of'] and predecessor['status'] == 'completed':
                    raise ValueError('retry predecessor must be failed or interrupted')
                if record['refresh'] and predecessor['status'] != 'completed':
                    raise ValueError('refresh predecessor must be completed')
    return records


def write_receipt(record, root=ROOT, replace=False):
    validate_receipt(record, root)
    folder = root / 'register/searches'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (record['search_id'] + '.json')
    if path.exists() and not replace:
        raise ValueError(f'search receipt already exists: {record["search_id"]}')
    staging = root / '.work/crawl-staging'
    staging.mkdir(parents=True, exist_ok=True)
    staged = staging / (record['search_id'] + '.json.partial')
    staged.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
    staged.replace(path)
    return path


def save_snapshot(entries, source_receipt, query, *, lane=None, work_mode='fresh', order='lastUpdatedDate',
                  direction='descending', start=0, limit=10, search_id=None, refresh=None,
                  retry_of=None, retry_reason=None, discovery_reason=None, requested_utc=None, root=ROOT, status=None, provenance=None, replace=False):
    """Import one existing central acquisition. Does not fetch, admit or read papers."""
    request = request_window(query, order, direction, start, limit)
    timestamp = requested_utc or source_receipt.get('retrieved_utc') or arxiv.now()
    search_id = search_id or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-') + request['window_sha256'][:12]
    known_ids = {strict_load(path)['paper_id'] for path in (root / 'register/papers').glob('*.json')}
    source = {key: source_receipt.get(key) for key in ['url', 'retrieved_utc', 'sha256', 'http_status', 'error', 'retry_after']}
    source['local_path'] = source_receipt.get('path')
    status = status or ('failed' if source['error'] else 'completed')
    results = []
    for position, entry in enumerate(entries):
        paper_id = 'arxiv:' + entry['versioned_id'].removeprefix('arxiv:')
        duplicate = paper_id in known_ids
        results.append(dict(paper_id=paper_id, position=position,
                            disposition='duplicate' if duplicate else 'pending',
                            reason='Exact version already registered at discovery.' if duplicate else 'Screen this saved metadata snapshot.',
                            title=entry.get('title'), decision_history=[]))
    record = dict(schema_version=1, search_id=search_id, lane=lane, work_mode=work_mode,
                  status=status, requested_utc=timestamp, request=request, refresh=refresh, retry_of=retry_of,
                  retry_reason=retry_reason, discovery_reason=discovery_reason, source=source, results=results,
                  coverage=dict(result_ids_complete=status == 'completed',
                                dispositions_complete=status == 'completed' and not any(result['disposition'] in {'pending', 'unknown'} for result in results),
                                metadata_complete=status == 'completed', limitations=[
                                    'One changing API window; no gap-free or exhaustive coverage claim.',
                                    'Metadata discovery and duplicate checks establish no scientific usefulness or reading.']),
                  provenance=provenance or dict(kind='live', scan_id=None, query_id=None))
    write_receipt(record, root, replace=replace)
    return record


def backfill(root=ROOT):
    """Recover recorded queries; never reconstruct missing screens or timestamps."""
    created = []
    known = {record['search_id']: record for record in receipts(root)}
    for scan_path in sorted((root / 'scans').glob('*.json')):
        scan = strict_load(scan_path)
        for index, query in enumerate(scan.get('queries', [])):
            query_id = query.get('id', str(index))
            search_id = re.sub(r'[^A-Za-z0-9_.-]', '-', scan['scan_id'] + '--' + query_id)
            if not query.get('search_id') and search_id in known:
                continue
            params = urllib.parse.parse_qs(urllib.parse.urlsplit(query.get('url', '')).query)
            value = lambda name, default=None: params.get(name, [default])[0]
            expression = query.get('query') or value('search_query')
            if not expression:
                continue  # Known-ID acquisition is not a topic search.
            limit = int(query.get('max_results', value('max_results', 10)))
            start = int(query.get('start', value('start', 0)))
            if query.get('search_id'):
                linked = known.get(query['search_id'])
                expected = request_window(expression, query.get('order', value('sortBy', 'lastUpdatedDate')),
                                          query.get('direction', value('sortOrder', 'descending')), start, limit)
                if linked is None or linked['request'] != expected:
                    raise ValueError('scan links a missing or different search window')
                if linked['provenance']['scan_id'] != scan['scan_id'] or linked['provenance']['query_id'] != query_id:
                    raise ValueError('linked search scan/query provenance mismatch')
                for field in ['url', 'retrieved_utc', 'sha256']:
                    if query.get(field) is not None and query[field] != linked['source'][field]:
                        raise ValueError('linked search original-source identity mismatch')
                if 'result_ids' in query and query['result_ids'] != [r['paper_id'] for r in linked['results']]:
                    raise ValueError('linked search result order differs from scan')
                continue
            entries = [{'versioned_id': ident.removeprefix('arxiv:')} for ident in query.get('result_ids', [])]
            source = dict(url=query.get('url'), retrieved_utc=query.get('retrieved_utc'),
                          sha256=query.get('sha256'), http_status=None, error=query.get('error'))
            record = save_snapshot(entries, source, expression, lane=scan.get('lane'),
                                   work_mode=scan.get('work_mode', 'legacy_unknown'),
                                   order=query.get('order', value('sortBy', 'lastUpdatedDate')),
                                   direction=query.get('direction', value('sortOrder', 'descending')),
                                   start=start, limit=limit, search_id=search_id,
                                   requested_utc=query.get('retrieved_utc') or scan['started_utc'], root=root,
                                   provenance=dict(kind='legacy_scan', scan_id=scan['scan_id'], query_id=query_id),
                                   status='failed' if query.get('error') else 'completed')
            duplicates = {item['paper_id']: item.get('reason') for item in scan.get('duplicates', [])}
            registered = set(scan.get('registered_papers', []))
            for result in record['results']:
                ident = result['paper_id']
                if ident in duplicates:
                    result.update(disposition='duplicate', reason=duplicates[ident] or 'Explicit duplicate in original scan.')
                elif ident in registered:
                    result.update(disposition='selected', reason='Listed as registered/worked on in original scan; precise screen decision not preserved here.')
                else:
                    result.update(disposition='unknown', reason='Original scan preserved this hit but no disposition; screening coverage unknown.')
            record['coverage'].update(metadata_complete=False, dispositions_complete=False,
                                      result_ids_complete='result_ids' in query,
                                      limitations=['Backfilled from an existing scan, not a new query.',
                                                   'Missing source time/hash and per-hit screens remain unknown; batch start is only the request-time fallback.'])
            write_receipt(record, root, replace=True)
            created.append(search_id)
    return created


def public_paths(root):
    paths = list((root / 'register').rglob('*.json')) + list((root / 'scans').glob('*.json'))
    paths += list((root / 'designs').glob('*.json')) + list((root / 'references').rglob('*.json'))
    paths += [root / 'state.json', root / 'schemas/search.schema.json']
    return sorted(path for path in paths if path.is_file())


def ensure_index(root=ROOT, force=False):
    """JSON is authoritative. Any public byte change rebuilds the disposable DB."""
    records = receipts(root)  # Validate authoritative evidence even if index looks current.
    paths = public_paths(root)
    fingerprint = hashlib.sha256(INDEX_VERSION.encode())
    parsed = []
    for path in paths:
        content = path.read_bytes()
        fingerprint.update(str(path.relative_to(root)).encode() + b'\0' + content + b'\0')
        parsed.append((path, strict_load(path)))
    digest = fingerprint.hexdigest()
    folder = root / '.work'
    folder.mkdir(exist_ok=True)
    db_path = folder / 'crawl.sqlite3'
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        current = connection.execute('SELECT value FROM meta WHERE key="fingerprint"').fetchone()
    except sqlite3.DatabaseError:
        connection.close()
        db_path.unlink(missing_ok=True)
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        current = None
    if force or not current or current[0] != digest:
        with connection:
            connection.executescript('''
            DROP TABLE IF EXISTS meta; DROP TABLE IF EXISTS documents;
            DROP TABLE IF EXISTS searches; DROP TABLE IF EXISTS hits;
            DROP TABLE IF EXISTS graph_edges; DROP TABLE IF EXISTS bibliography;
            CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE documents(path TEXT PRIMARY KEY, kind TEXT, identity TEXT, body TEXT);
            CREATE TABLE searches(id TEXT PRIMARY KEY, window TEXT, utc TEXT, lane TEXT, status TEXT, body TEXT);
            CREATE TABLE hits(search_id TEXT, paper_id TEXT, disposition TEXT, position INTEGER);
            CREATE TABLE graph_edges(id TEXT PRIMARY KEY, source TEXT, target TEXT, type TEXT, status TEXT, body TEXT);
            CREATE TABLE bibliography(id TEXT PRIMARY KEY, citing_version TEXT, cited_base TEXT, cited_version INTEGER, body TEXT);
            ''')
            for path, value in parsed:
                relative = str(path.relative_to(root))
                parts = Path(relative).parts
                kind = parts[1] if parts[0] == 'register' and len(parts) > 2 else parts[0]
                identity = value.get('paper_id') or value.get('id') or value.get('search_id') or value.get('scan_id') or path.stem
                connection.execute('INSERT INTO documents VALUES(?,?,?,?)',
                                   (relative, kind, identity, json.dumps(value, ensure_ascii=False)))
                if relative == 'register/graph.json':
                    for edge in value.get('edges', []):
                        connection.execute('INSERT INTO graph_edges VALUES(?,?,?,?,?,?)',
                                           (edge['id'], edge['from'], edge['to'], edge['type'], edge['status'], json.dumps(edge)))
                elif relative == 'register/citations.json':
                    for citation in value.get('citations', []):
                        connection.execute('INSERT INTO bibliography VALUES(?,?,?,?,?)',
                                           (citation['id'], citation['from_paper_id'], citation['cited_arxiv_id'],
                                            citation['cited_version'], json.dumps(citation)))
            for record in records:
                connection.execute('INSERT INTO searches VALUES(?,?,?,?,?,?)',
                                   (record['search_id'], record['request']['window_sha256'], record['requested_utc'],
                                    record['lane'], record['status'], json.dumps(record)))
                connection.executemany('INSERT INTO hits VALUES(?,?,?,?)',
                                       [(record['search_id'], result['paper_id'], result['disposition'], result['position'])
                                        for result in record['results']])
            connection.execute('INSERT INTO meta VALUES("fingerprint",?)', (digest,))
    return connection


def queue(root=ROOT):
    state = strict_load(root / 'state.json')
    saved = receipts(root)
    superseded = {record['retry_of'] for record in saved if record['retry_of']}
    superseded.update(record['refresh']['previous_search_id'] for record in saved if record['refresh'])
    return dict(registered=state.get('queue', []),
                screens=[dict(search_id=record['search_id'], **result)
                         for record in saved for result in record['results']
                         if result['disposition'] in {'pending', 'unknown'}],
                failed_searches=[record['search_id'] for record in saved if record['status'] != 'completed' and record['search_id'] not in superseded])


def status(root=ROOT):
    from feedback import priorities
    experiment_priorities = priorities(root)
    connection = ensure_index(root)
    state = strict_load(root / 'state.json')
    lanes = []
    for lane in state.get('lanes', []):
        dates = [lane.get('last_searched_utc')]
        dates += [row[0] for row in connection.execute('SELECT utc FROM searches WHERE lane=? AND status="completed"', (lane['id'],))]
        latest = max((date for date in dates if date), default=None)
        lanes.append(dict(id=lane['id'], last_searched_utc=latest))
    lanes.sort(key=lambda lane: (lane['last_searched_utc'] is not None, lane['last_searched_utc'] or ''))
    counts = dict(connection.execute('SELECT disposition,COUNT(*) FROM hits GROUP BY disposition').fetchall())
    connection.close()
    return dict(queue=queue(root), lanes_least_recent_first=lanes, dispositions=counts,
                experiment_priorities=experiment_priorities,
                next_work_mode=state.get('next_work_mode'),
                limits='Queue before discovery; experiment findings suggest bounded work without changing queues or paper stages. Lane ordering and counts are navigation, not scientific scores.')


def screen(search_id, paper_id, disposition, reason, root=ROOT):
    if disposition not in DISPOSITIONS - {'unknown', 'pending'} or not reason.strip():
        raise ValueError('screen requires a terminal/deferred disposition and reason')
    record = next((record for record in receipts(root) if record['search_id'] == search_id), None)
    if record is None:
        raise ValueError('unknown saved search snapshot')
    result = next((result for result in record['results'] if result['paper_id'] == paper_id), None)
    if result is None:
        raise ValueError('paper is not in saved search snapshot')
    if not result['decision_history']:
        result['decision_history'].append(dict(utc=record['requested_utc'], disposition=result['disposition'], reason=result['reason']))
    result.update(disposition=disposition, reason=reason)
    result['decision_history'].append(dict(utc=arxiv.now(), disposition=disposition, reason=reason))
    record['coverage']['dispositions_complete'] = not any(result['disposition'] in {'pending', 'unknown'} for result in record['results'])
    write_receipt(record, root, replace=True)
    return record


def search(query, *, root=ROOT, lane=None, work_mode='fresh', order='lastUpdatedDate',
           direction='descending', start=0, limit=10, refresh_reason=None, retry_reason=None,
           discovery_reason=None, client=None, batch_id=None):
    batch_id = batch_id or datetime.now(timezone.utc).strftime('%Y-%m-%d')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', batch_id):
        raise ValueError('invalid acquisition batch identifier')
    request = request_window(query, order, direction, start, limit)
    prior = sorted([record for record in receipts(root) if record['request']['window_sha256'] == request['window_sha256']],
                   key=lambda record: (record['requested_utc'], record['search_id']))
    latest = prior[-1] if prior else None
    refresh = retry_of = None
    if refresh_reason and retry_reason:
        raise ValueError('choose refresh or failure retry')
    if latest:
        if latest['status'] == 'completed':
            if retry_reason:
                raise ValueError('completed window needs refresh, not failure retry')
            if not refresh_reason:
                return dict(action='reused_snapshot', receipt=latest)
            if not refresh_reason.strip():
                raise ValueError('refresh needs a concrete reason')
            refresh = dict(reason=refresh_reason, previous_search_id=latest['search_id'])
        else:
            if refresh_reason:
                raise ValueError('failed/interrupted window needs retry, not completed-window refresh')
            if not retry_reason:
                return dict(action='resume_failure', receipt=latest)
            if not retry_reason.strip():
                raise ValueError('retry needs a concrete reason')
            if latest['retry_of']:
                raise ValueError('one retry already used; defer or change route/request')
            if latest['source']['http_status'] in {403, 406} or (
                    latest['source']['http_status'] == 429
                    and (not latest.get('batch_id') or latest['batch_id'] == batch_id)):
                raise ValueError('403/406 requires changed route; 429 stops acquisition')
            time_text = latest['source']['retrieved_utc'] or latest['requested_utc']
            elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(time_text.replace('Z', '+00:00'))).total_seconds()
            wait_seconds = 30
            retry_after = latest['source'].get('retry_after')
            if retry_after:
                try:
                    wait_seconds = max(wait_seconds, int(retry_after))
                except ValueError:
                    try:
                        wait_seconds = max(wait_seconds, (parsedate_to_datetime(retry_after) - datetime.fromisoformat(time_text.replace('Z', '+00:00'))).total_seconds())
                    except (ValueError, TypeError):
                        raise ValueError('unparseable Retry-After; defer acquisition')
            if elapsed < wait_seconds:
                raise ValueError(f'transient failure retry requires at least {wait_seconds:g} seconds')
            retry_of = latest['search_id']
    elif refresh_reason or retry_reason:
        raise ValueError('refresh/retry requires a prior identical window')
    pending = queue(root)
    if any(pending.values()) and not (discovery_reason and discovery_reason.strip()):
        raise ValueError('resume existing queue first; a new window needs --discovery-reason to document its bounded exception')
    client = client or arxiv.Client(root / '.work/crawl-acquisition' / batch_id)
    requested_utc = arxiv.now()
    parameters = dict(search_query=query, start=start, max_results=limit, sortBy=order, sortOrder=direction)
    attempt = save_snapshot([], dict(url='https://export.arxiv.org/api/query?' + urllib.parse.urlencode(parameters)), query,
                            lane=lane, work_mode=work_mode, order=order, direction=direction, start=start, limit=limit,
                            refresh=refresh, retry_of=retry_of, retry_reason=retry_reason, discovery_reason=discovery_reason,
                            requested_utc=requested_utc, root=root, status='interrupted')
    attempt['batch_id'] = batch_id
    write_receipt(attempt, root, replace=True)
    receipt_offset = len(client.receipts)
    try:
        entries, receipt = client.search(query, limit=limit, order=order, start=start, direction=direction)
    except Exception as exc:
        receipt = dict(client.receipts[-1]) if len(client.receipts) > receipt_offset else {}
        receipt['error'] = receipt.get('error') or f'{type(exc).__name__}: {exc}'
        record = save_snapshot([], receipt, query, lane=lane, work_mode=work_mode, order=order,
                               direction=direction, start=start, limit=limit, refresh=refresh, retry_of=retry_of,
                               requested_utc=requested_utc, retry_reason=retry_reason, discovery_reason=discovery_reason,
                               search_id=attempt['search_id'], replace=True, root=root, status='failed')
        record['batch_id'] = batch_id
        write_receipt(record, root, replace=True)
        return dict(action='failed', receipt=record)
    record = save_snapshot(entries, receipt, query, lane=lane,
                           work_mode=work_mode, order=order,
                           direction=direction, start=start, limit=limit, refresh=refresh, retry_of=retry_of,
                           requested_utc=requested_utc, retry_reason=retry_reason, discovery_reason=discovery_reason,
                           search_id=attempt['search_id'], replace=True, root=root)
    record['batch_id'] = batch_id
    write_receipt(record, root, replace=True)
    return dict(action='searched', receipt=record)


def find(text, root=ROOT, kind=None, limit=30):
    if not 1 <= limit <= 100:
        raise ValueError('local search supports 1–100 records')
    connection = ensure_index(root)
    escaped = text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    rows = connection.execute('SELECT path,kind,identity FROM documents WHERE body LIKE ? ESCAPE "\\" AND (? IS NULL OR kind=?) ORDER BY path LIMIT ?',
                              ('%' + escaped + '%', kind, kind, limit)).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def timeline(base_id=None, root=ROOT):
    """Version-aware source dates and register events, with explicit link semantics."""
    connection = ensure_index(root)
    papers = [strict_load(path) for path in (root / 'register/papers').glob('*.json')]
    groups = {}
    for paper in papers:
        base = paper['arxiv_id']
        if base_id and base != base_id.removeprefix('arxiv:'):
            continue
        group = groups.setdefault(base, dict(arxiv_id=base, versions=[], events=[], physical_relationships=[], bibliography=[]))
        group['versions'].append(dict(paper_id=paper['paper_id'], version=paper['version'], title=paper['title']))
        for field, kind in [('published_utc', 'source_published'), ('updated_utc', 'source_version_updated')]:
            if paper.get(field):
                group['events'].append(dict(utc=paper[field], kind=kind, paper_id=paper['paper_id']))
        for row in connection.execute('SELECT s.id,s.utc,h.disposition FROM searches s JOIN hits h ON h.search_id=s.id WHERE h.paper_id=?', (paper['paper_id'],)):
            group['events'].append(dict(utc=row['utc'], kind='discovery_snapshot', paper_id=paper['paper_id'],
                                        search_id=row['id'], disposition=row['disposition']))
        for row in connection.execute('SELECT body FROM graph_edges WHERE source=? OR target=?', (paper['paper_id'], paper['paper_id'])):
            edge = json.loads(row['body'])
            if edge not in group['physical_relationships']:
                group['physical_relationships'].append(edge)
    for group in groups.values():
        group['versions'].sort(key=lambda version: version['version'])
        group['events'].sort(key=lambda event: (event['utc'], event['kind'], event['paper_id']))
        identities = [item['paper_id'] for item in group['versions']]
        for row in connection.execute('SELECT body FROM bibliography WHERE cited_base=?', (group['arxiv_id'],)):
            group['bibliography'].append(json.loads(row['body']))
        for identity in identities:
            for row in connection.execute('SELECT body FROM bibliography WHERE citing_version=?', (identity,)):
                citation = json.loads(row['body'])
                if citation not in group['bibliography']:
                    group['bibliography'].append(citation)
    connection.close()
    return dict(groups=[groups[key] for key in sorted(groups)],
                limits='Versions of one paper are grouped, not independent papers. Graph relationships and explicit bibliography links remain separate; unknown cited versions stay null. Dates describe publication/update/discovery, not priority or scientific merit.')


def resume(search_id, root=ROOT):
    record = next((record for record in receipts(root) if record['search_id'] == search_id), None)
    if record is None:
        raise ValueError('unknown search snapshot')
    source = record['source']
    cache = root / source['local_path'] if source['local_path'] else None
    if cache and cache.exists():
        if hashlib.sha256(cache.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('cached search source hash mismatch; retain receipt and reacquire explicitly')
        cache_status = 'verified'
    else:
        cache_status = 'unavailable_locally'
    return dict(receipt=record, cache_status=cache_status,
                limits='Resume reads the saved result IDs and decisions without querying arXiv. Missing raw metadata must be explicitly reacquired before a metadata/abstract screen.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ['status', 'rebuild', 'backfill']:
        sub.add_parser(command)
    resume = sub.add_parser('resume')
    resume.add_argument('search_id')
    discovery = sub.add_parser('search')
    discovery.add_argument('query')
    discovery.add_argument('--lane')
    discovery.add_argument('--work-mode', default='fresh')
    discovery.add_argument('--order', default='lastUpdatedDate')
    discovery.add_argument('--direction', default='descending')
    discovery.add_argument('--start', type=int, default=0)
    discovery.add_argument('--limit', type=int, default=10)
    discovery.add_argument('--refresh-reason')
    discovery.add_argument('--retry-reason')
    discovery.add_argument('--discovery-reason')
    discovery.add_argument('--batch-id', help='Authorized bounded acquisition batch; defaults to UTC date')
    screening = sub.add_parser('screen')
    screening.add_argument('search_id')
    screening.add_argument('paper_id')
    screening.add_argument('disposition', choices=sorted(DISPOSITIONS - {'unknown', 'pending'}))
    screening.add_argument('--reason', required=True)
    lookup = sub.add_parser('find')
    lookup.add_argument('text')
    lookup.add_argument('--kind')
    lookup.add_argument('--limit', type=int, default=30)
    chronology = sub.add_parser('timeline')
    chronology.add_argument('base_id', nargs='?')
    args = vars(parser.parse_args())
    command = args.pop('command')
    if command == 'rebuild':
        connection = ensure_index(force=True)
        connection.close()
        result = {'rebuilt': '.work/crawl.sqlite3'}
    elif command == 'resume':
        result = resume(args['search_id'])
    else:
        try:
            result = globals()[command](**args)
        except (ValueError, jsonschema.ValidationError) as exc:
            parser.exit(2, f'{exc}\n')
    print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
