"""Exercise integrity failures; these checks do not certify scientific claims."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import arxiv
import validate_register as registry
from build_register import reading_stage


class RegisterIntegrity(unittest.TestCase):
    def setUp(self):
        work = registry.ROOT / ".work"
        work.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="integrity-", dir=work)
        self.root = Path(self.temp.name)
        for folder in ["register", "schemas", "designs", "scans", "requests", "handoffs"]:
            shutil.copytree(registry.ROOT / folder, self.root / folder)
        if (registry.ROOT / 'references').exists():
            shutil.copytree(registry.ROOT / 'references', self.root / 'references')
        shutil.copyfile(registry.ROOT / "state.json", self.root / "state.json")

    def tearDown(self):
        self.temp.cleanup()

    def mutate(self, path, fn):
        file = self.root / path
        record = json.loads(file.read_text())
        fn(record)
        file.write_text(json.dumps(record))

    def validate(self):
        with patch.object(registry, "ROOT", self.root), contextlib.redirect_stdout(io.StringIO()):
            registry.validate()

    def test_reference_variant_requires_explicit_acceptance(self):
        def change(record):
            record["accepted_records"]["reference_ids"].remove("flat-massless-synthetic-controls-v1")
        self.mutate("register/reviews/2026-10-01-lcdm-baseline-source-claims.json", change)
        with self.assertRaisesRegex(ValueError, "targeted review does not accept reference_ids"):
            self.validate()

    def test_current_records(self):
        self.validate()

    def test_handoff_roles_cannot_swap_valid_artifacts(self):
        path = 'handoffs/foundation-primary-reference-v1.json'
        original = (self.root / path).read_text()
        record = json.loads(original)
        for role in ['candidate', 'reference', 'source_review', 'contracts']:
            with self.subTest(role=role):
                changed = json.loads(original)
                pin = changed[role][0] if role == 'contracts' else changed[role]
                replacement = record['reference' if role == 'candidate' else 'candidate']
                pin.update(path=replacement['path'], sha256=replacement['sha256'])
                self.assertEqual(hashlib.sha256((self.root / pin['path']).read_bytes()).hexdigest(),
                                 pin['sha256'])
                (self.root / path).write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError, 'handoff role path does not match registered identity'):
                    self.validate()
        (self.root / path).write_text(original)

    def test_contract_requires_explicit_acceptance(self):
        self.mutate('register/reviews/2026-10-02-standard-model-source-claims.json',
                    lambda r: r['accepted_records']['contract_ids'].clear())
        with self.assertRaisesRegex(ValueError, 'targeted review does not accept contract_ids'):
            self.validate()

    def test_joint_primary_pin_cannot_swap_valid_reference(self):
        path = 'designs/candidate-class-planck-primary-desi-exploratory-v1.json'
        record = json.loads((self.root / path).read_text())
        joint = record['minimal_test']['parameter_choices']['working_joint_contract']
        replacement = joint['primary_reference']
        joint['primary_candidate'].update(path=replacement['path'], bytes=replacement['bytes'],
                                          sha256=replacement['sha256'])
        (self.root / path).write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'joint consumer role path does not match registered identity'):
            self.validate()

    def test_joint_cannot_change_primary_calibration_ownership(self):
        self.mutate('designs/candidate-class-planck-primary-desi-exploratory-v1.json',
                    lambda r: r['minimal_test']['parameter_choices']['working_joint_contract']
                    ['primary_consumer_contract']['calibration_prior'].update(applications=2))
        with self.assertRaisesRegex(ValueError, 'joint consumer changes frozen primary semantics'):
            self.validate()

    def test_joint_bao_order_cannot_change(self):
        def change(record):
            rows = record['minimal_test']['parameter_choices']['working_joint_contract']['bao']['rows']
            rows[-2], rows[-1] = rows[-1], rows[-2]
        self.mutate('designs/candidate-class-planck-primary-desi-exploratory-v1.json', change)
        from jsonschema.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.validate()

    def test_scalar_serialization_requires_explicit_acceptance(self):
        self.mutate('register/reviews/2026-10-03-atomic-source-claims.json',
                    lambda r: r['accepted_records']['serialization_ids'].clear())
        with self.assertRaisesRegex(ValueError, 'targeted review does not accept serialization_ids'):
            self.validate()

    def test_changed_scalar_serialization_invalidates_contract_binding(self):
        self.mutate('register/source-data/hhe-atomic-central-asd512-codata2022-v1.json',
                    lambda r: r['unknowns'].append('Changed interpretation'))
        with self.assertRaisesRegex(ValueError, 'source serialization digest mismatch'):
            self.validate()

    def test_scalar_cannot_claim_unlisted_source_asset(self):
        self.mutate('register/source-data/hhe-atomic-central-asd512-codata2022-v1.json',
                    lambda r: r['scalars'][0]['source_asset_ids'].append('unacquired-source'))
        with self.assertRaisesRegex(ValueError, 'scalar source outside serialization assets'):
            self.validate()

    def test_scalar_asset_must_match_reviewed_source(self):
        self.mutate('register/source-data/hhe-atomic-central-asd512-codata2022-v1.json',
                    lambda r: r['source_assets'][0].update(sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'serialization source asset not reviewed'):
            self.validate()

    def test_duplicate_contract_scope_rejected(self):
        self.mutate('register/contracts/standard-model-source-gates-v1.json',
                    lambda r: r['scopes'].append(r['scopes'][0]))
        with self.assertRaisesRegex(ValueError, 'duplicate source contract scope'):
            self.validate()

    def test_contract_scope_cannot_add_unreviewed_paper(self):
        self.mutate('register/contracts/standard-model-source-gates-v1.json',
                    lambda r: r['scopes'][0]['paper_ids'].append('arxiv:astro-ph/9709112v1'))
        with self.assertRaisesRegex(ValueError, 'source scope outside contract papers'):
            self.validate()

    def test_navigation_association_does_not_claim_paper_review(self):
        review = json.loads((self.root / 'register/reviews/2026-10-03-sdss-b1608-targeted-source-claims-v1.json').read_text())
        self.assertEqual(review['reviewed_papers'], ['arxiv:0910.2773v2'])
        self.validate()

    def test_navigation_requires_explicit_contract_association(self):
        self.mutate('register/reviews/2026-10-03-sdss-b1608-targeted-source-claims-v1.json',
                    lambda r: r.pop('source_contract_associations'))
        with self.assertRaisesRegex(ValueError, 'source contract sources not reviewed'):
            self.validate()

    def test_navigation_association_requires_matching_source_evidence(self):
        self.mutate('register/reviews/2026-10-03-sdss-b1608-targeted-source-claims-v1.json',
                    lambda r: r['reviewed_source_assets'][3].update(sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'source contract association asset not reviewed'):
            self.validate()

    def test_navigation_association_cannot_extend_to_another_contract(self):
        self.mutate('register/reviews/2026-10-03-sdss-b1608-targeted-source-claims-v1.json',
                    lambda r: r['source_contract_associations'][0].update(contract_id='standard-model-source-gates-v1'))
        with self.assertRaisesRegex(ValueError, 'source contract association lacks targeted acceptance'):
            self.validate()

    def test_navigation_association_must_match_unreviewed_contract_ids(self):
        self.mutate('register/reviews/2026-10-03-sdss-b1608-targeted-source-claims-v1.json',
                    lambda r: r['source_contract_associations'][0]['paper_ids'].pop())
        with self.assertRaisesRegex(ValueError, 'source contract navigation does not match unreviewed associations'):
            self.validate()

    def test_changed_contract_invalidates_candidate_binding(self):
        self.mutate('register/contracts/standard-model-source-gates-v1.json',
                    lambda r: r['limitations'].append('Changed source scope'))
        with self.assertRaisesRegex(ValueError, 'design source contract digest mismatch'):
            self.validate()

    def test_duplicate_keys_rejected(self):
        file = self.root / "duplicate.json"
        file.write_text('{"id":1,"id":2}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            registry.strict_load(file)

    def test_nonfinite_and_overflow_rejected(self):
        file = self.root / "invalid-number.json"
        for value in ["NaN", "Infinity", "1e999"]:
            file.write_text('{"value":' + value + '}')
            with self.assertRaises(ValueError):
                registry.strict_load(file)

    def test_missing_prospect_member_rejected(self):
        self.mutate("register/topics/early-energy.json", lambda p: p["paper_ids"].append("arxiv:0000.00000v1"))
        with self.assertRaisesRegex(ValueError, "prospect missing paper"):
            self.validate()

    def test_unreceipted_read_hash_rejected(self):
        self.mutate("register/papers/1811.04083v2.json", lambda p: p["extraction"]["source_hashes"].update(pdf="0" * 64))
        with self.assertRaisesRegex(ValueError, "read-object hash lacks original-source receipt"):
            self.validate()

    def test_unreviewed_idea_source_rejected(self):
        def change(p):
            p["source_evidence"][0]["paper_id"] = "arxiv:2609.39039v1"
        self.mutate("register/ideas/ede-oscillating-scalar.json", change)
        with self.assertRaisesRegex(ValueError, "idea source was not reviewed"):
            self.validate()

    def test_specialization_cycle_rejected(self):
        def change(p):
            edge = next(e for e in p["edges"] if e["type"] == "specializes")
            p["edges"].append(dict(edge, id="cycle-test", **{"from": edge["to"], "to": edge["from"]}))
        self.mutate("register/graph.json", change)
        with self.assertRaisesRegex(ValueError, "specialization graph contains a cycle"):
            self.validate()

    def test_ready_design_with_blockers_rejected(self):
        self.mutate("designs/candidate-ede-fixed-endpoint-ruler.json", lambda p: p.update(readiness="ready_for_consumer_review"))
        with self.assertRaises(Exception):
            self.validate()

    def test_missing_review_details_rejected(self):
        self.mutate("register/reviews/2026-10-01-initial-science.json", lambda p: p.update(reviewed_paper_details=[]))
        with self.assertRaisesRegex(ValueError, "review details do not cover"):
            self.validate()

    def test_review_source_hash_must_have_receipt(self):
        def change(p):
            p["reviewed_paper_details"][0]["source_hashes"] = {"pdf": "0" * 64}
        self.mutate("register/reviews/2026-10-01-initial-science.json", change)
        with self.assertRaisesRegex(ValueError, "review lacks receipted original-source hashes"):
            self.validate()

    def test_reading_cannot_hash_only_metadata(self):
        def change(p):
            p["extraction"]["source_hashes"] = {"metadata": p["artifacts"][0]["sha256"]}
        self.mutate("register/papers/1811.04083v2.json", change)
        with self.assertRaisesRegex(ValueError, "read-object hash lacks original-source receipt"):
            self.validate()

    def test_scan_cannot_claim_an_unread_paper(self):
        self.mutate("scans/2026-10-01-late-expansion.json", lambda p: p["full_reads"].append("arxiv:2609.39039v1"))
        with self.assertRaisesRegex(ValueError, "scan claims unread paper"):
            self.validate()

    def test_unfinished_scan_cannot_be_last_completed(self):
        scan_id = json.loads((self.root / "state.json").read_text())["last_completed_scan"]
        self.mutate(f"scans/{scan_id}.json", lambda p: p.update(status="interrupted"))
        with self.assertRaisesRegex(ValueError, "last completed scan is not completed"):
            self.validate()

    def test_unfinished_work_cannot_disappear(self):
        self.mutate("state.json", lambda p: p.update(queue=[]))
        with self.assertRaisesRegex(ValueError, "unfinished papers lost from queue"):
            self.validate()

    def test_review_cannot_precede_full_reading(self):
        def change(p):
            next(q for q in p["queue"] if q["paper_id"] == "arxiv:2609.39039v1")["stage"] = "review"
        self.mutate("state.json", change)
        with self.assertRaisesRegex(ValueError, "review queued before full reading"):
            self.validate()

    def test_canonical_filename_required_for_generated_links(self):
        (self.root / "register/papers/1811.04083v2.json").rename(self.root / "register/papers/renamed.json")
        with self.assertRaisesRegex(ValueError, "noncanonical record filename"):
            self.validate()

    def test_partial_read_stays_partial_in_views(self):
        paper = json.loads((self.root / "register/papers/1811.04083v2.json").read_text())
        paper["review_id"] = None
        paper["extraction"]["reading_level"] = "partial"
        self.assertEqual(reading_stage(paper), "partial")

    def test_prospect_review_must_cover_its_sources(self):
        self.mutate('register/prospects/ede-fixed-endpoint-ruler.json', lambda p: p.update(review_id='2026-10-01-late-expansion-science'))
        with self.assertRaisesRegex(ValueError, 'prospect review does not cover'):
            self.validate()

    def test_prospect_cannot_attach_an_unrelated_design(self):
        self.mutate('register/prospects/ede-fixed-endpoint-ruler.json', lambda p: p.update(design_ids=['candidate-timescape-tracker-distance-lineage']))
        with self.assertRaisesRegex(ValueError, 'prospect design uses unrelated'):
            self.validate()

    def test_prospect_links_must_have_the_composition_review(self):
        def change(g):
            edge=next(e for e in g['edges'] if e['type']=='informs')
            edge.update(status='provisional', review_id=None)
        self.mutate('register/graph.json', change)
        with self.assertRaisesRegex(ValueError, 'prospect accepted link lacks'):
            self.validate()

    def test_combined_prospect_cannot_skip_compatibility(self):
        def change(p):
            p.update(kind='combination', readiness='ready_for_consumer_review', unknowns=[])
        self.mutate('register/prospects/ede-fixed-endpoint-ruler.json', change)
        with self.assertRaisesRegex(ValueError, 'combined prospect has unchecked compatibility'):
            self.validate()

    def test_citation_cannot_use_metadata_as_original_evidence(self):
        def change(p):
            p['citations'][0]['source']['sha256'] = '0' * 64
        self.mutate('register/citations.json', change)
        with self.assertRaisesRegex(ValueError, 'citation lacks original-source receipt'):
            self.validate()

    def test_citation_cannot_claim_an_unregistered_version(self):
        self.mutate('register/citations.json', lambda p: p['citations'][0].update(cited_version=99))
        with self.assertRaisesRegex(ValueError, 'cited version missing'):
            self.validate()

    def test_duplicate_citation_rejected(self):
        self.mutate('register/citations.json', lambda p: p['citations'].append(dict(p['citations'][0], id='duplicate')))
        with self.assertRaisesRegex(ValueError, 'duplicate citation'):
            self.validate()

    def test_targeted_review_cannot_accept_unlisted_idea(self):
        self.mutate('register/reviews/2026-10-01-lcdm-baseline-source-claims.json',
                    lambda r: r['accepted_records'].update(idea_ids=[]))
        with self.assertRaisesRegex(ValueError, 'targeted review does not accept idea_ids'):
            self.validate()

    def test_targeted_review_requires_high_effort_confirmation(self):
        self.mutate('register/reviews/2026-10-01-lcdm-baseline-source-claims.json',
                    lambda r: r['model_confirmation'].update(effort='low'))
        with self.assertRaisesRegex(ValueError, 'required model/reasoning confirmation'):
            self.validate()

    def test_targeted_review_accepts_confirmed_xhigh(self):
        def update(review):
            review['requested_reasoning'] = 'xhigh'
            review['model_confirmation']['effort'] = 'xhigh'
        self.mutate('register/reviews/2026-10-01-lcdm-baseline-source-claims.json', update)
        self.validate()

    def test_targeted_review_rejects_mismatched_effort(self):
        self.mutate('register/reviews/2026-10-01-lcdm-baseline-source-claims.json',
                    lambda r: r.update(requested_reasoning='xhigh'))
        with self.assertRaisesRegex(ValueError, 'required model/reasoning confirmation'):
            self.validate()

    def test_targeted_review_cannot_expand_idea_source_coverage(self):
        self.mutate('register/ideas/planck-conditioned-base-lcdm.json',
                    lambda r: r['source_evidence'][0].update(locator='Unexamined appendix'))
        with self.assertRaisesRegex(ValueError, 'idea locator outside targeted review'):
            self.validate()

    def test_targeted_check_is_not_a_full_paper_read(self):
        paper = json.loads((self.root / 'register/papers/1807.06209v4.json').read_text())
        self.assertIsNone(paper['extraction'])
        self.assertIsNone(paper['review_id'])
        self.assertEqual(reading_stage(paper), 'screened')
        self.mutate('scans/2026-10-01-lcdm-baseline.json',
                    lambda s: s['full_reads'].append(paper['paper_id']))
        with self.assertRaisesRegex(ValueError, 'scan claims unread paper'):
            self.validate()

    def test_candidate_cannot_use_changed_reference_bytes(self):
        self.mutate('references/lcdm/planck2018-reference.json',
                    lambda r: r.update(conditioning=r['conditioning']+' changed'))
        with self.assertRaisesRegex(ValueError, 'design reference digest mismatch'):
            self.validate()

    def test_reference_cannot_use_unreceipted_original_source(self):
        self.mutate('references/lcdm/planck2018-reference.json',
                    lambda r: r['source_sha256'].update(pdf='0'*64))
        with self.assertRaisesRegex(ValueError, 'reference source hash lacks receipt'):
            self.validate()


class AcquisitionBoundaries(unittest.TestCase):
    def test_xml_error_cannot_be_reported_as_an_empty_search(self):
        with self.assertRaisesRegex(ValueError, "not an Atom feed"):
            arxiv.atom_entries(b'<error>Temporarily unavailable</error>')

    def test_version_required_in_atom(self):
        body = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/1811.04083</id></entry></feed>'
        with self.assertRaisesRegex(ValueError, "versioned paper identity"):
            arxiv.atom_entries(body)

    def test_official_https_boundary(self):
        arxiv.official_url("https://export.arxiv.org/api/query")
        for url in ["http://arxiv.org/pdf/1811.04083v2", "https://example.com/", "https://arxiv.org:8080/", "https://user@arxiv.org/"]:
            with self.assertRaises(ValueError):
                arxiv.official_url(url)

    def test_external_redirect_rejected(self):
        with self.assertRaises(ValueError):
            arxiv.OfficialRedirects().redirect_request(None, None, 302, "Found", {}, "https://example.com/paper")

    def test_working_files_cannot_escape(self):
        with self.assertRaisesRegex(ValueError, "Prospector/.work"):
            arxiv.Client(arxiv.ROOT / "downloads")

    def test_wrong_html_is_not_a_reading_source(self):
        body = b'<html><title>Error page</title><article class="ltx_document"><math>0</math></article></html>'
        self.assertFalse(arxiv.matching_html(body, "Expected paper"))
        self.assertFalse(arxiv.matching_html(b'<title>Expected paper</title>', "Expected paper"))
        self.assertTrue(arxiv.matching_html(b'<title>Expected paper</title><article class="ltx_document">body</article>', "Expected paper"))

    def test_429_preserves_partial_manifest_and_stops(self):
        work = arxiv.ROOT / ".work"
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="acquisition-", dir=work) as folder:
            client = arxiv.Client(folder)
            def limited(*args):
                if client.rate_limited:
                    raise RuntimeError("Acquisition stopped after HTTP 429")
                client.rate_limited = True
                receipt = {"http_status": 429, "error": "rate limited"}
                client.receipts.append(receipt)
                return None, receipt
            with patch.object(client, "fetch", side_effect=limited):
                result = client.paper({"versioned_id": "1811.04083v2", "title": "Expected paper"})
            self.assertTrue(result["acquisition_stopped_after_429"])
            self.assertFalse(result["full_text_available"])
            self.assertTrue((Path(folder) / "1811.04083v2-sources.json").is_file())
            self.assertEqual(result["acquisition_attempts"][0]["http_status"], 429)

    def test_new_client_cannot_resume_rate_limited_batch(self):
        work = arxiv.ROOT / ".work"
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="acquisition-", dir=work) as folder:
            (Path(folder) / "acquisition.jsonl").write_text('{"http_status":429}\n')
            client = arxiv.Client(folder)
            with self.assertRaisesRegex(RuntimeError, "stopped after HTTP 429"):
                client.fetch("retry", "https://arxiv.org/", ".html")


if __name__ == "__main__":
    unittest.main()
