"""Discovery memory, interruption and public-index integrity, without network/model calls."""
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import crawl


class FakeClient:
    def __init__(self, entries=None, failure=False, interrupted=False):
        self.entries = entries or []
        self.failure = failure
        self.interrupted = interrupted
        self.receipts = []
        self.calls = []

    def search(self, query, **kwargs):
        self.calls.append((query, kwargs))
        if self.interrupted:
            raise KeyboardInterrupt()
        source = dict(url='https://export.arxiv.org/api/query', retrieved_utc=crawl.arxiv.now(),
                      http_status=503 if self.failure else 200, sha256='1' * 64)
        if self.failure:
            source['error'] = 'HTTPError: temporary unavailable'
        self.receipts.append(source)
        if self.failure:
            raise RuntimeError(source['error'])
        return self.entries, source


class CrawlTests(unittest.TestCase):
    def setUp(self):
        work = crawl.ROOT / '.work'
        work.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='crawl-test-', dir=work)
        self.root = Path(self.temp.name)
        for folder in ['register/searches', 'register/papers', 'schemas', 'scans', '.work']:
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(crawl.ROOT / 'schemas/search.schema.json', self.root / 'schemas/search.schema.json')
        self.write('state.json', {'queue': [], 'lanes': [
            {'id': 'old', 'last_searched_utc': '2025-01-01T00:00:00Z'},
            {'id': 'new', 'last_searched_utc': None}], 'next_work_mode': 'foundations'})
        self.source = dict(url='https://export.arxiv.org/api/query', retrieved_utc='2025-01-01T00:00:00Z', sha256='1' * 64, http_status=200)
        self.entry = {'versioned_id': '2202.08291v3', 'title': 'Perturbation microphysics', 'abstract': 'Private abstract must never be published.'}

    def tearDown(self):
        self.temp.cleanup()

    def write(self, path, record):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(record))

    def snapshot(self, **kwargs):
        return crawl.save_snapshot([self.entry], self.source, 'ti:"early dark energy"', root=self.root, **kwargs)

    def test_completed_window_reuses_exact_saved_snapshot(self):
        record = self.snapshot(search_id='first')
        client = FakeClient()
        result = crawl.search(' ti:"early dark energy" ', root=self.root, client=client)
        self.assertEqual(result['action'], 'reused_snapshot')
        self.assertEqual(result['receipt']['search_id'], record['search_id'])
        self.assertEqual(client.calls, [])
        self.assertEqual(crawl.resume('first', self.root)['receipt']['results'][0]['disposition'], 'pending')

    def test_query_window_normalization_is_conservative(self):
        baseline = crawl.request_window('ti:"early dark energy"')
        self.assertEqual(baseline['window_sha256'], crawl.request_window(' ti:"early dark energy" ')['window_sha256'])
        variants = ['ti:"Early dark energy"', 'ti:"early  dark energy"', 'abs:"early dark energy"']
        for query in variants:
            self.assertNotEqual(baseline['window_sha256'], crawl.request_window(query)['window_sha256'])
        for changed in [dict(start=10), dict(limit=20), dict(order='relevance'), dict(direction='ascending')]:
            self.assertNotEqual(baseline['window_sha256'], crawl.request_window('ti:"early dark energy"', **changed)['window_sha256'])

    def test_explicit_refresh_retains_old_snapshot_and_reason(self):
        self.snapshot(search_id='first')
        client = FakeClient([{'versioned_id': '2202.08291v4', 'title': 'Revised perturbations'}])
        result = crawl.search('ti:"early dark energy"', root=self.root, client=client,
                              refresh_reason='Check revisions after the saved snapshot.', discovery_reason='Previous screen deferred for source acquisition.')
        self.assertEqual(result['action'], 'searched')
        self.assertEqual(result['receipt']['refresh']['previous_search_id'], 'first')
        self.assertEqual(result['receipt']['results'][0]['paper_id'], 'arxiv:2202.08291v4')
        self.assertEqual(len(crawl.receipts(self.root)), 2)
        self.assertEqual(len(client.calls), 1)

    def test_failure_persists_and_requires_reasoned_single_retry(self):
        failed = crawl.search('ti:coasting', root=self.root, client=FakeClient(failure=True))
        self.assertEqual(failed['action'], 'failed')
        client = FakeClient()
        self.assertEqual(crawl.search('ti:coasting', root=self.root, client=client)['action'], 'resume_failure')
        self.assertEqual(client.calls, [])
        with self.assertRaisesRegex(ValueError, '30 seconds'):
            crawl.search('ti:coasting', root=self.root, client=client, retry_reason='Temporary service failure.', discovery_reason='Retry pending failure only.')
        record = failed['receipt']
        record['source']['retrieved_utc'] = (datetime.now(timezone.utc) - timedelta(seconds=40)).isoformat()
        crawl.write_receipt(record, self.root, replace=True)
        result = crawl.search('ti:coasting', root=self.root, client=FakeClient(failure=True),
                              retry_reason='One bounded transient retry.', discovery_reason='Retry pending failure only.')
        self.assertEqual(result['receipt']['retry_of'], record['search_id'])
        self.assertEqual(result['receipt']['retry_reason'], 'One bounded transient retry.')
        with self.assertRaisesRegex(ValueError, 'one retry already used'):
            crawl.search('ti:coasting', root=self.root, client=client, retry_reason='Again', discovery_reason='retry')

    def test_retry_after_and_rate_limit_are_respected(self):
        for code, retry_after, message in [(429, None, 'stops acquisition'), (503, '120', '120 seconds')]:
            record = crawl.save_snapshot([], dict(self.source, http_status=code, error='failed', retry_after=retry_after,
                                        retrieved_utc=(datetime.now(timezone.utc) - timedelta(seconds=40)).isoformat()),
                                         f'ti:retry{code}', root=self.root, status='failed')
            with self.assertRaisesRegex(ValueError, message):
                crawl.search(f'ti:retry{code}', root=self.root, client=FakeClient(), retry_reason='Retry', discovery_reason='retry')
            self.assertEqual(record['status'], 'failed')

    def test_interruption_has_durable_pending_attempt(self):
        with self.assertRaises(KeyboardInterrupt):
            crawl.search('ti:interrupted', root=self.root, client=FakeClient(interrupted=True))
        records = crawl.receipts(self.root)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['status'], 'interrupted')
        self.assertFalse(records[0]['coverage']['result_ids_complete'])

    def test_rate_limited_batch_stays_stopped_and_new_batch_retains_log(self):
        folder = self.root / '.work/crawl-acquisition/first'
        folder.mkdir(parents=True)
        log = folder / 'acquisition.jsonl'
        log.write_text('{"http_status":429}\n')
        created = []
        def client_for(path):
            created.append(path)
            if (path / 'acquisition.jsonl').exists():
                client = FakeClient(failure=True)
                def stopped(*args, **kwargs):
                    raise RuntimeError('Acquisition stopped after HTTP 429')
                client.search = stopped
                return client
            return FakeClient()
        with patch.object(crawl.arxiv, 'Client', side_effect=client_for):
            result = crawl.search('ti:blocked', root=self.root, batch_id='first')
            self.assertEqual(result['action'], 'failed')
            self.assertIn('stopped after HTTP 429', result['receipt']['source']['error'])
            later = crawl.search('ti:later', root=self.root, batch_id='later-authorized', discovery_reason='Later separately authorized batch.')
            self.assertEqual(later['action'], 'searched')
        self.assertTrue(log.exists())
        self.assertEqual(later['receipt']['batch_id'], 'later-authorized')
        self.assertEqual(created, [folder, self.root / '.work/crawl-acquisition/later-authorized'])
        with self.assertRaisesRegex(ValueError, 'batch identifier'):
            crawl.search('ti:invalid', root=self.root, batch_id='../elsewhere')

    def test_same_window_429_recovery_requires_later_explicit_batch_and_reason(self):
        failed = crawl.save_snapshot([], dict(self.source, http_status=429, error='HTTP 429',
                                    retrieved_utc=(datetime.now(timezone.utc)-timedelta(seconds=40)).isoformat()),
                                     'ti:limited', root=self.root, status='failed', search_id='limited')
        failed['batch_id']='first'
        crawl.write_receipt(failed,self.root,replace=True)
        with self.assertRaisesRegex(ValueError,'stops acquisition'):
            crawl.search('ti:limited',root=self.root,client=FakeClient(),batch_id='first',retry_reason='Retry',discovery_reason='Retry')
        later = crawl.search('ti:limited',root=self.root,client=FakeClient(),batch_id='later-authorized',
                             retry_reason='Later authorized batch after cooldown.',discovery_reason='Resume failed window only.')
        self.assertEqual(later['action'],'searched')
        self.assertEqual(later['receipt']['retry_of'],'limited')
        self.assertEqual(later['receipt']['batch_id'],'later-authorized')

    def test_pending_work_requires_explicit_discovery_rationale(self):
        self.snapshot(search_id='first')
        with self.assertRaisesRegex(ValueError, 'resume existing queue first'):
            crawl.search('ti:new', root=self.root, client=FakeClient())
        result = crawl.search('ti:new', root=self.root, client=FakeClient(), discovery_reason='Pending screen explicitly deferred for source access.')
        self.assertEqual(result['receipt']['discovery_reason'], 'Pending screen explicitly deferred for source access.')

    def test_screen_correction_preserves_history_and_abstract_is_private(self):
        record = self.snapshot(search_id='first')
        crawl.screen('first', 'arxiv:2202.08291v3', 'deferred', 'Need pinned source.', self.root)
        updated = crawl.screen('first', 'arxiv:2202.08291v3', 'selected', 'Source acquired; candidate for reading.', self.root)
        self.assertEqual([event['disposition'] for event in updated['results'][0]['decision_history']], ['pending', 'deferred', 'selected'])
        self.assertNotIn('Private abstract', (self.root / 'register/searches/first.json').read_text())
        self.assertEqual(record['results'][0]['disposition'], 'pending')

    def test_hash_mismatch_blocks_resume_without_overwriting_provenance(self):
        record = self.snapshot(search_id='first')
        cache = self.root / '.work/source.xml'
        cache.write_text('Changed bytes')
        record['source']['local_path'] = '.work/source.xml'
        crawl.write_receipt(record, self.root, replace=True)
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            crawl.resume('first', self.root)
        self.assertEqual(crawl.receipts(self.root)[0]['source']['sha256'], '1' * 64)

    def test_stale_or_corrupt_database_is_rebuildable(self):
        self.snapshot(search_id='first')
        connection = crawl.ensure_index(self.root)
        original = connection.execute('SELECT value FROM meta').fetchone()[0]
        connection.close()
        crawl.screen('first', 'arxiv:2202.08291v3', 'excluded', 'Outside scoped mechanism.', self.root)
        connection = crawl.ensure_index(self.root)
        self.assertNotEqual(connection.execute('SELECT value FROM meta').fetchone()[0], original)
        self.assertEqual(connection.execute('SELECT disposition FROM hits').fetchone()[0], 'excluded')
        connection.close()
        (self.root / '.work/crawl.sqlite3').write_bytes(b'broken database')
        connection = crawl.ensure_index(self.root)
        self.assertEqual(connection.execute('SELECT COUNT(*) FROM searches').fetchone()[0], 1)
        connection.close()

    def test_malformed_receipt_rejected_before_database_import(self):
        record = self.snapshot(search_id='first')
        for mutate in [lambda item: item['request'].update(start=9),
                       lambda item: item['results'].append(copy.deepcopy(item['results'][0])),
                       lambda item: item['source'].update(local_path='../secret.xml'),
                       lambda item: item.update(retry_of='missing', retry_reason='missing predecessor')]:
            changed = copy.deepcopy(record)
            mutate(changed)
            self.write('register/searches/first.json', changed)
            with self.assertRaises((ValueError, crawl.jsonschema.ValidationError)):
                crawl.ensure_index(self.root)
        self.write('register/searches/first.json', record)
        (self.root / 'register/searches/first.json').write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            crawl.ensure_index(self.root)

    def test_backfill_does_not_invent_old_dispositions(self):
        self.write('scans/old.json', dict(scan_id='old', started_utc='2025-01-01T00:00:00Z',
            registered_papers=['arxiv:2202.08291v3'], queries=[dict(id='query',
            url='https://export.arxiv.org/api/query?search_query=ti%3Acoasting&sortBy=relevance&start=0&max_results=2&sortOrder=ascending',
            result_ids=['arxiv:2202.08291v3', 'arxiv:2202.08291v4'])]))
        self.assertEqual(crawl.backfill(self.root), ['old--query'])
        record = crawl.receipts(self.root)[0]
        self.assertEqual([item['disposition'] for item in record['results']], ['selected', 'unknown'])
        self.assertIsNone(record['source']['retrieved_utc'])
        self.assertIsNone(record['source']['sha256'])
        self.assertFalse(record['coverage']['dispositions_complete'])
        self.assertEqual(record['request']['direction'], 'ascending')
        self.assertEqual(crawl.backfill(self.root), [])

    def test_backfill_preserves_explicit_live_search_and_decisions(self):
        record = self.snapshot(search_id='live', provenance=dict(kind='live', scan_id='batch', query_id='query'))
        crawl.screen('live', 'arxiv:2202.08291v3', 'excluded', 'Outside scope.', self.root)
        query = dict(id='query', search_id='live', query=record['request']['query'],
                     url=self.source['url'], retrieved_utc=self.source['retrieved_utc'],
                     sha256=self.source['sha256'], result_ids=['arxiv:2202.08291v3'])
        self.write('scans/batch.json', dict(scan_id='batch', started_utc=self.source['retrieved_utc'], queries=[query]))
        self.assertEqual(crawl.backfill(self.root), [])
        self.assertEqual(len(crawl.receipts(self.root)), 1)
        self.assertEqual(crawl.receipts(self.root)[0]['results'][0]['disposition'], 'excluded')
        query['sha256'] = '2' * 64
        self.write('scans/batch.json', dict(scan_id='batch', started_utc=self.source['retrieved_utc'], queries=[query]))
        with self.assertRaisesRegex(ValueError, 'source identity mismatch'):
            crawl.backfill(self.root)

    def test_receipt_predecessor_order_rejects_cycles(self):
        first = self.snapshot(search_id='first')
        second = self.snapshot(search_id='second', requested_utc='2025-01-02T00:00:00Z',
                               refresh=dict(reason='Check new versions.', previous_search_id='first'))
        first['refresh'] = dict(reason='A cycle must be rejected.', previous_search_id='second')
        crawl.write_receipt(first, self.root, replace=True)
        with self.assertRaisesRegex(ValueError, 'strictly earlier'):
            crawl.receipts(self.root)

    def test_successful_retry_removes_only_pending_failure_not_history(self):
        first = crawl.save_snapshot([], dict(self.source, error='503 failure', http_status=503), 'ti:retry-success',
                                    root=self.root, status='failed', search_id='failure')
        result = crawl.search('ti:retry-success', root=self.root, client=FakeClient(),
                              retry_reason='Service recovered.', discovery_reason='Finish the pending failure.')
        self.assertEqual(result['action'], 'searched')
        self.assertEqual(crawl.queue(self.root)['failed_searches'], [])
        self.assertEqual(len(crawl.receipts(self.root)), 2)
        self.assertEqual(first['status'], 'failed')

    def test_timeline_groups_versions_and_separates_link_semantics(self):
        for version in [3, 4]:
            self.write(f'register/papers/p{version}.json', dict(paper_id=f'arxiv:2202.08291v{version}',
                       arxiv_id='2202.08291', version=version, title=f'Version {version}',
                       published_utc='2022-02-16T00:00:00Z', updated_utc=f'202{version}-02-16T00:00:00Z'))
        self.write('register/graph.json', dict(edges=[dict(id='edge', **{'from': 'arxiv:2202.08291v4', 'to': 'idea'},
                   type='describes', status='reviewed')]))
        self.write('register/citations.json', dict(citations=[dict(id='cite', from_paper_id='arxiv:2202.08291v3',
                   cited_arxiv_id='2202.08291', cited_version=None)]))
        self.snapshot(search_id='first')
        result = crawl.timeline('2202.08291', self.root)
        self.assertEqual(len(result['groups']), 1)
        group = result['groups'][0]
        self.assertEqual([version['version'] for version in group['versions']], [3, 4])
        self.assertEqual(group['physical_relationships'][0]['type'], 'describes')
        self.assertIsNone(group['bibliography'][0]['cited_version'])
        self.assertEqual(len(group['bibliography']), 1)
        self.assertEqual(sum(event['kind'] == 'discovery_snapshot' for event in group['events']), 1)
        self.assertEqual(crawl.find('Version 4', self.root, kind='papers')[0]['identity'], 'arxiv:2202.08291v4')
        self.assertEqual(crawl.status(self.root)['lanes_least_recent_first'][0]['id'], 'new')


if __name__ == '__main__':
    unittest.main()
