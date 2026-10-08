"""Consumer evidence cannot silently erase queues or manufacture promotion."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import crawl
import feedback
import site_data


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        work = crawl.ROOT / '.work'
        work.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='feedback-test-', dir=work)
        self.root = Path(self.temp.name)
        for folder in ['schemas', 'register/feedback', 'register/papers',
                       'register/searches', 'designs', 'register/prospects']:
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        for name in ['experiment-feedback', 'search']:
            shutil.copyfile(crawl.ROOT / f'schemas/{name}.schema.json',
                            self.root / f'schemas/{name}.schema.json')
        self.queue = [{'paper_id': 'arxiv:1009.5855v2', 'stage': 'read', 'reason': 'Full reading pending.'}]
        self.write('state.json', {'queue': self.queue, 'lanes': [{'id': 'late-dark-energy'}]})
        self.write('register/papers/paper.json', {'paper_id': 'arxiv:1009.5855v2'})
        self.write('designs/design.json', {'design_id': 'candidate-test'})
        self.record = {
            'schema_version': 1, 'feedback_id': 'test-findings-v1', 'programme_id': 'conditional-comparison',
            'recorded_utc': '2026-10-08T00:00:00Z', 'supersedes': None,
            'evidence': [{'evidence_id': 'result', 'repository': 'sprajs/reproducible',
                'revision': 'a' * 40, 'path': 'experiments/test/result.json',
                'sha256': 'b' * 64, 'role': 'Conditional fit summary'}],
            'findings': [{'finding_id': 'limited', 'kind': 'conditional_fit',
                'statement': 'One conditional fit completed.', 'evidence_ids': ['result'],
                'limits': ['Unknown cross-probe covariance; no joint posterior.']}],
            'priorities': [{'lane': 'late-dark-energy', 'target_kind': 'design',
                'target_id': 'candidate-test', 'finding_ids': ['limited'],
                'next_action': 'Check numerical refinement.', 'scope': 'One retained point.',
                'stage': 'consumer_review'}],
            'qualification': {'scientifically_qualified': False, 'changes_paper_stages': False,
                'limits': 'Consumer diagnostics only.'},
        }

    def tearDown(self):
        self.temp.cleanup()

    def write(self, path, value):
        (self.root / path).write_text(json.dumps(value))

    def save(self, record=None):
        record = record or self.record
        self.write('register/feedback/' + record['feedback_id'] + '.json', record)

    def test_status_keeps_queue_and_shows_active_findings(self):
        self.save()
        state_before = (self.root / 'state.json').read_bytes()
        result = crawl.status(self.root)
        self.assertEqual(result['queue']['registered'], self.queue)
        self.assertEqual(result['experiment_priorities'][0]['findings'][0]['statement'],
                         'One conditional fit completed.')
        self.assertEqual((self.root / 'state.json').read_bytes(), state_before)
        successor = copy.deepcopy(self.record)
        successor.update(feedback_id='test-findings-v2', recorded_utc='2026-10-09T00:00:00Z',
                         supersedes=self.record['feedback_id'])
        self.save(successor)
        self.assertEqual(len(feedback.receipts(self.root)), 2)
        self.assertEqual([p['feedback_id'] for p in feedback.priorities(self.root)], ['test-findings-v2'])

    def test_malformed_pin_and_promotion_are_rejected(self):
        for mutate in [lambda r: r['evidence'][0].update(sha256='unknown'),
                       lambda r: r['qualification'].update(scientifically_qualified=True),
                       lambda r: r['qualification'].update(changes_paper_stages=True)]:
            value = copy.deepcopy(self.record)
            mutate(value)
            self.save(value)
            with self.assertRaises(jsonschema.ValidationError):
                feedback.receipts(self.root)

    def test_missing_target_evidence_and_unsafe_path_are_rejected(self):
        cases = [(lambda r: r['priorities'][0].update(target_id='missing'), 'missing target'),
                 (lambda r: r['findings'][0].update(evidence_ids=['missing']), 'missing evidence'),
                 (lambda r: r['evidence'][0].update(path='../private.json'), 'relative path')]
        for mutate, message in cases:
            value = copy.deepcopy(self.record)
            mutate(value)
            self.save(value)
            with self.assertRaisesRegex(ValueError, message):
                feedback.receipts(self.root)

    def test_supersession_cannot_fork_or_cross_programmes(self):
        self.save()
        successor = copy.deepcopy(self.record)
        successor.update(feedback_id='test-findings-v2', recorded_utc='2026-10-09T00:00:00Z',
                         supersedes=self.record['feedback_id'], programme_id='another')
        self.save(successor)
        with self.assertRaisesRegex(ValueError, 'same programme'):
            feedback.receipts(self.root)
        successor['programme_id'] = self.record['programme_id']
        self.save(successor)
        successor.update(feedback_id='test-findings-v3', recorded_utc='2026-10-10T00:00:00Z')
        self.save(successor)
        with self.assertRaisesRegex(ValueError, 'competing successors'):
            feedback.receipts(self.root)

    def test_public_projection_keeps_conditioning_and_omits_storage(self):
        public = site_data.public_feedback(self.record, {'candidate-test'})
        self.assertEqual(public['findings'][0]['limits'], self.record['findings'][0]['limits'])
        self.assertIn('Check numerical refinement.', json.dumps(public))
        for private in ['experiments/test/result.json', 'revision', 'sha256', 'evidence_ids']:
            self.assertNotIn(private, json.dumps(public))
        self.assertEqual(site_data.public_feedback(self.record, {'unrelated'})['findings'], [])

    def test_deleting_all_receipts_cannot_leave_a_dangling_state_pin(self):
        state = json.loads((self.root / 'state.json').read_text())
        state['experiment_feedback_ids'] = [self.record['feedback_id']]
        self.write('state.json', state)
        with self.assertRaisesRegex(ValueError, 'state references missing feedback receipt'):
            crawl.status(self.root)
