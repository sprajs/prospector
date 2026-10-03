"""Public chronology is a view of sourced ideas, not inferred ancestry."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import site_data


class PublicChronology(unittest.TestCase):
    def test_contract_export_keeps_conditioning_and_excludes_acquisition(self):
        path = site_data.ROOT / 'register/contracts/next05-released-fixed44-row3213-conditional-source-v1.json'
        source = json.loads(path.read_text())
        source['agent_id'] = 'PRIVATE_WORKER'
        source['source_assets'][0]['credential'] = 'SECRET_TEST_VALUE'
        public = site_data.public_contract(source)
        self.assertIn('full-fit', ' '.join(public['limitations']))
        self.assertIn('C_TT', public['scopes'][1]['checked_claim'])
        self.assertEqual(public['sources'][0]['sha256'], source['source_assets'][0]['sha256'])
        for private in ['.work/', 'PRIVATE_WORKER', 'SECRET_TEST_VALUE', 'local_path', 'Luna', 'stage promotion']:
            self.assertNotIn(private, json.dumps(public))

    def test_optical_export_keeps_unread_coverage_and_physical_limits(self):
        path = site_data.ROOT / 'register/contracts/optical-calibration-template-source-contract-v1.json'
        source = json.loads(path.read_text())
        public = site_data.public_contract(source)
        limits = ' '.join(public['limitations'])
        self.assertIn('are unread', limits)
        self.assertIn('sigma_k=1/3', limits)
        self.assertIn('shift_0.dat has nonzero', limits)
        self.assertIn('not measured quantum efficiency', limits)
        self.assertIn('Covariances/uncertainties depend on training', limits)
        for private in ['Luna', 'paper promotions', '.work/']:
            self.assertNotIn(private, json.dumps(public))

    def test_investigation_export_keeps_formal_and_physical_limits(self):
        path = site_data.ROOT / 'designs/next05-released-fixed44-row3213-conditional-diagnostic-20261003.json'
        source = json.loads(path.read_text())
        source['consumer']['credential'] = 'SECRET_TEST_VALUE'
        public = site_data.public_investigation(source)
        self.assertEqual(public['readiness'], 'blocked')
        self.assertIn('C_FT', public['equations'][1]['expression'])
        self.assertIn('full-fit', ' '.join(public['unknowns']).lower())
        self.assertEqual(set(public['test']), {'question', 'observables'})
        self.assertNotIn('consumer', public)
        self.assertNotIn('executable_request', public)
        self.assertNotIn('parameter_choices', public['test'])
        for private in ['.work/', 'SECRET_TEST_VALUE']:
            self.assertNotIn(private, json.dumps(public))

    def test_transfer_export_preserves_limits_without_packet_bookkeeping(self):
        source = json.loads((site_data.ROOT / 'register/contracts/next14-pure-massless-fd-cdm-lambda-unit-zeta-transfer-v2.json').read_text())
        public = site_data.public_contract(source)
        limits = ' '.join(public['limitations'])
        self.assertIn('Shared MB equations/thermal/mode ancestry', limits)
        self.assertIn('growing Hamiltonian residual', limits)
        self.assertIn('differs from regular growing', limits)
        for private in ['39cf0ba', 'ccde', 'de5', 'private proposal', 'public slug', 'Root externally']:
            self.assertNotIn(private, json.dumps(public))

    def test_navigation_projects_bound_scalars_without_duplicates(self):
        from validate_register import records, strict_load
        data = site_data.website_data(records('register/papers', 'paper_id'),
                    records('register/ideas', 'id'), records('register/topics', 'id'),
                    strict_load(site_data.ROOT / 'register/graph.json'))
        prospect = next(p for p in data['prospects'] if p['id'] == 'lcdm-baseline-reference-audit')
        scalars = [s for record in prospect['scalar_sources'] for s in record['scalars']]
        self.assertEqual(sum(s['id'] == 'sigma_T_CODATA2022' for s in scalars), 1)
        hydrogen = next(s for s in scalars if s['id'] == 'm_H1_Pitrou_reported')
        self.assertEqual(hydrogen['value_class'], 'reported_compilation_value')
        self.assertIsNone(hydrogen['uncertainty']['decimal_value'])
        unrelated = next(p for p in data['prospects'] if p['id'] == 'ede-fixed-endpoint-ruler')
        self.assertNotIn('sigma_T_CODATA2022', json.dumps(unrelated['scalar_sources']))

    def test_scalar_export_preserves_uncertainty_and_omits_private_fields(self):
        path = site_data.ROOT / 'register/source-data/hhe-atomic-central-asd512-codata2022-v1.json'
        source = json.loads(path.read_text())
        source['agent_id'] = 'PRIVATE_WORKER'
        source['source_assets'][0]['archive_path'] = '.work/private-source.html'
        public = site_data.public_serialization(source)
        hydrogen = next(s for s in public['scalars'] if s['id'] == 'chi_HI')
        self.assertTrue(hydrogen['asd_parenthesized_theory_flag'])
        self.assertIsNone(hydrogen['uncertainty']['distribution'])
        self.assertIsNone(hydrogen['uncertainty']['coverage'])
        self.assertEqual(hydrogen['decimal_value'], '13.598434599702')
        helium = next(s for s in public['sources'] if s['id'] == 'HeII_levels')
        self.assertIn('ASD5.10', helium['dataset_provenance'])
        self.assertIn('CODATA2018', helium['dataset_provenance'])
        self.assertNotIn('PRIVATE_WORKER', json.dumps(public))
        self.assertNotIn('.work/', json.dumps(public))

    def test_metrics_export_preserves_missingness_and_omits_private_receipts(self):
        work = site_data.ROOT / '.work'
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as folder:
            root = Path(folder)
            metrics = root / 'register/bibliometrics'
            metrics.mkdir(parents=True)
            source = next((site_data.ROOT / 'register/bibliometrics').glob('2609.37437v1-*.json'))
            snapshot = json.loads(source.read_text())
            snapshot['citation_snapshot']['source']['archive_path'] = '.work/private-evidence.json'
            snapshot['unexported_token'] = 'SECRET_TEST_VALUE'
            (metrics / 'snapshot.json').write_text(json.dumps(snapshot))
            with patch.object(site_data, 'ROOT', root):
                result = site_data.visibility_snapshots()['arxiv:2609.37437v1'][0]
            self.assertEqual(result['citation_count'], 0)
            self.assertIsNone(result['max_h_index'])
            self.assertIsNone(result['cohort_percentile'])
            self.assertNotIn('.work/', json.dumps(result))
            self.assertNotIn('SECRET_TEST_VALUE', json.dumps(result))

    def test_publication_dates_and_reviewed_relationships(self):
        work = site_data.ROOT / ".work"
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as folder:
            root = Path(folder)
            (root / "register/prospects").mkdir(parents=True)
            (root / 'register/contracts').mkdir()
            (root / 'register/contracts/example.json').write_text(json.dumps({'scopes': [{
                'scope_id': 'NEXT-01', 'title': 'Located convention', 'paper_ids': ['arxiv:1009.5855v2'],
                'checked_claim': 'Checked definition', 'unresolved': 'Unknown covariance',
                'agent_id': 'PRIVATE_WORKER', 'raw_source': '.work/source.html',
            }]}))
            (root / 'register/prospects/example.json').write_text(json.dumps(dict(
                id='example',title='Example',kind='single_mechanism',readiness='blocked',
                baseline={},cosmology={},scope=[],unknowns=[],idea_ids=[],model_idea_ids=[],topic_ids=[],source_evidence=[],
                source_contract_ids=['example'])))
            (root / "register/citations.json").write_text(json.dumps({"citations": [{
                "from_paper_id": "arxiv:1009.5855v2", "cited_arxiv_id": "1811.04083",
                "cited_version": None, "reference": "example",
            }]}))
            papers = {}
            for ident, published, updated in [
                ("arxiv:1009.5855v2", "2010-09-29T00:00:00Z", "2026-09-01T00:00:00Z"),
                ("arxiv:1811.04083v2", "2018-11-09T00:00:00Z", "2019-01-01T00:00:00Z"),
            ]:
                base = ident[6:-2]
                papers[ident] = dict(arxiv_id=base, version=2, title=ident, authors=["A"],
                                    published_utc=published, updated_utc=updated,
                                    urls={"abstract": "https://arxiv.org/abs/" + ident[6:],
                                          "pdf": "https://arxiv.org/pdf/" + ident[6:]}, extraction=None)
            ideas = {"old": dict(title="Old", family="f", assumptions=[], predictions=[],
                                  source_evidence=[{"paper_id": "arxiv:1009.5855v2"}]),
                     "new": dict(title="New", family="f", assumptions=[], predictions=[],
                                  source_evidence=[{"paper_id": "arxiv:1811.04083v2"}])}
            topics = {ident: dict(id=ident, title=ident, paper_ids=list(papers), idea_ids=list(ideas))
                      for ident in site_data.ORDER}
            edge = dict(status="provisional", **{"from": "new", "to": "old"},
                        type="updates", rationale="Unverified", evidence=[])
            with patch.object(site_data, "ROOT", root):
                data = site_data.website_data(papers, ideas, topics, {"edges": [edge]})
            dates = {event["idea_id"]: event["first_source_date"] for event in data["timeline"]}
            self.assertEqual(dates, {"old": "2010-09-29", "new": "2018-11-09"})
            self.assertEqual(data["edges"], [])
            self.assertEqual(len(data["citations"]), 1)
            self.assertNotIn(".work/", json.dumps(data))
            self.assertEqual(data['prospects'][0]['source_gates'][0]['unresolved'], 'Unknown covariance')
            self.assertNotIn('PRIVATE_WORKER', json.dumps(data))


if __name__ == "__main__":
    unittest.main()
