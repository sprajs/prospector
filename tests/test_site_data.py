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


if __name__ == "__main__":
    unittest.main()
