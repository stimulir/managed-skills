"""Offline contract tests; never contact a provider or access real credentials."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/audience-research/helpers'))
import evidence
import run


def artifact(stage='vendor-research'):
    return {'schema_version': 1, 'stage': stage, 'status': 'complete',
            'evidence': [{'id': stage + ':1', 'text': 'A supplied public case study says this.',
                          'kind': 'observed', 'source_url': 'https://example.com/case',
                          'retrieved_at': '2026-09-24T12:00:00+00:00'}],
            'claims': [{'text': 'A possible buyer hypothesis', 'kind': 'inferred',
                        'evidence_ids': [stage + ':1']}]}


def feedback_artifact():
    row = artifact('experiment-feedback')
    row['evidence'][0]['ownership'] = 'owned'
    row['experiments'] = [{'experiment_id': 'e', 'avatar_id': 'a', 'creative_id': 'c',
                          'metric': 'qualified_reply_rate', 'window_start': '2026-09-01',
                          'window_end': '2026-09-24', 'numerator': 2, 'denominator': 20,
                          'evidence_id': 'experiment-feedback:1'}]
    return row


class EvidenceTests(unittest.TestCase):
    def test_rejects_uncited_claim(self):
        row = artifact()
        row['claims'][0]['evidence_ids'] = ['missing']
        with self.assertRaisesRegex(ValueError, 'existing evidence'):
            evidence.validate(row)

    def test_synthetic_never_observed(self):
        row = artifact()
        row['evidence'][0]['kind'] = 'synthetic'
        row['claims'][0]['kind'] = 'observed'
        with self.assertRaisesRegex(ValueError, 'cannot prove'):
            evidence.validate(row)

    def test_no_data_cannot_disguise_results(self):
        row = artifact()
        row.update(status='no_data', reason='empty')
        with self.assertRaisesRegex(ValueError, 'must not contain'):
            evidence.validate(row)

    def test_feedback_requires_owned_outcomes(self):
        with self.assertRaisesRegex(ValueError, 'owned experiment'):
            evidence.validate(artifact('experiment-feedback'))

    def test_boolean_schema_version_is_not_version_one(self):
        row = artifact()
        row['schema_version'] = True
        with self.assertRaisesRegex(ValueError, 'schema_version'):
            evidence.validate(row)

    def test_ids_and_references_do_not_coerce_types(self):
        for bad in (True, 1, [], {}):
            with self.subTest(bad=bad):
                row = artifact()
                row['evidence'][0]['id'] = bad
                with self.assertRaises(ValueError):
                    evidence.validate(row)
                row = feedback_artifact()
                row['experiments'][0]['evidence_id'] = bad
                with self.assertRaises(ValueError):
                    evidence.validate(row)

    def test_feedback_window_validation(self):
        for first, last in [('yesterday', 'today'), ('2026-02-30', '2026-03-01'),
                            ('2026-09-24', '2026-09-01'),
                            ('2026-09-01', '2026-09-24T00:00:00Z'),
                            ('2026-09-01T00:00:00', '2026-09-24T00:00:00'),
                            ('2026-09-01T00:00:00Z', '2026-09-01T00:00:00Z')]:
            with self.subTest(first=first, last=last):
                row = feedback_artifact()
                row['experiments'][0].update(window_start=first, window_end=last)
                with self.assertRaises(ValueError):
                    evidence.validate(row)
        row = feedback_artifact()
        row['experiments'][0].update(window_start='2026-09-01', window_end='2026-09-01')
        self.assertEqual(evidence.validate(row)['status'], 'complete')

    def test_timezone_order_uses_instants(self):
        row = feedback_artifact()
        row['experiments'][0].update(window_start='2026-09-01T10:00:00+02:00',
                                     window_end='2026-09-01T09:00:00Z')
        self.assertEqual(evidence.validate(row)['status'], 'complete')

    def test_public_observation_is_not_owned_result(self):
        row = feedback_artifact()
        del row['evidence'][0]['ownership']
        with self.assertRaisesRegex(ValueError, 'owned-data'):
            evidence.validate(row)

    def test_nested_avatar_claim_observation_requires_observed_sources(self):
        row = artifact('avatar-synthesis')
        row['evidence'][0]['kind'] = 'inferred'
        row['avatars'] = [{'id': 'a', 'buyer': 'CTO', 'trigger': 'Release regression',
                           'pain': 'Repeated failures', 'offer': 'Diagnostic', 'channels': ['Search'],
                           'claims': [{'text': 'An asserted fact', 'kind': 'observed',
                                       'evidence_ids': ['avatar-synthesis:1']}]}]
        with self.assertRaisesRegex(ValueError, 'cannot prove'):
            evidence.validate(row)

    def test_every_stage_helper_runs_independently(self):
        for stage in evidence.STAGES:
            path = ROOT / 'skills' / stage / 'helpers/evidence.py'
            spec = importlib.util.spec_from_file_location(stage, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(module.validate(artifact())['status'], 'complete')


class RunTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.env = patch.dict(os.environ, {'TREG_TOKEN': 'offline-test-token'})
        self.env.start()
        run.init(self.root, 'test-run', {'budget_micro_usd': 100, 'read_only_endpoint_ids': ['example.read']})

    def tearDown(self):
        self.env.stop()
        self.directory.cleanup()

    def test_calls_are_capped_and_deduped(self):
        with patch.object(run, 'request_json', return_value=({'items': [1]}, {'x-treg-cost-micro': '20', 'x-treg-call-id': 'receipt'})) as request:
            first = run.collect(self.root, 'example.read', {'q': 'a'}, 30)
            second = run.collect(self.root, 'example.read', {'q': 'a'}, 30)
            self.assertEqual(first, second)
            self.assertEqual(request.call_count, 1)
            self.assertEqual(request.call_args.args[2]['X-Treg-Route-Max-Cost'], '0.00003')
            self.assertEqual(first['status'], 'unvalidated')
        self.assertNotIn('offline-test-token', (self.root / 'run.json').read_text())

    def test_budget_refused_before_network(self):
        with patch.object(run, 'request_json') as request:
            with self.assertRaisesRegex(ValueError, 'budget'):
                run.collect(self.root, 'example.read', {}, 101)
            request.assert_not_called()

    def test_allowlist_refused_before_network(self):
        with patch.object(run, 'request_json') as request:
            with self.assertRaisesRegex(ValueError, 'allowlist'):
                run.collect(self.root, 'example.publish', {}, 1)
            request.assert_not_called()

    def test_uncertain_call_is_not_retried(self):
        with patch.object(run, 'request_json', side_effect=ValueError('timeout')) as request:
            with self.assertRaisesRegex(ValueError, 'timeout'):
                run.collect(self.root, 'example.read', {}, 30)
            with self.assertRaisesRegex(ValueError, 'reconcile'):
                run.collect(self.root, 'example.read', {}, 30)
            self.assertEqual(request.call_count, 1)
        self.assertEqual(next(iter(run.read_state(self.root)['calls'].values()))['status'], 'reserved')

    def test_provider_inner_error_is_only_raw_unvalidated_data(self):
        with patch.object(run, 'request_json', return_value=({'error': 'upstream failed'}, {'x-treg-cost-micro': '0'})):
            result = run.collect(self.root, 'example.read', {}, 20)
        self.assertEqual(result['status'], 'unvalidated')
        final = run.export(self.root)
        self.assertEqual(final['status'], 'needs_input')
        self.assertEqual(final['evidence'], [])

    def test_missing_receipt_keeps_reservation(self):
        with patch.object(run, 'request_json', return_value=({}, {})):
            with self.assertRaisesRegex(ValueError, 'receipt'):
                run.collect(self.root, 'example.read', {}, 20)
        self.assertEqual(next(iter(run.read_state(self.root)['calls'].values()))['status'], 'reserved')

    def test_complete_stage_is_idempotent_and_immutable(self):
        first = run.commit(self.root, artifact())
        self.assertEqual(run.commit(self.root, artifact()), first)
        changed = artifact()
        changed['claims'][0]['text'] = 'different hypothesis'
        with self.assertRaisesRegex(ValueError, 'immutable'):
            run.commit(self.root, changed)

    def test_modified_artifact_cannot_export(self):
        record = run.commit(self.root, artifact())
        changed = artifact()
        changed['claims'][0]['text'] = 'changed after commit'
        (self.root / record['path']).write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError, 'changed after commit'):
            run.export(self.root)

    def test_avatar_cannot_invent_evidence(self):
        run.commit(self.root, artifact())
        row = artifact('avatar-synthesis')
        row['avatars'] = [{'id': 'a', 'buyer': 'CTO', 'trigger': 'Release regression', 'pain': 'Repeated failures',
                           'offer': 'Diagnostic', 'channels': ['Search'], 'claims': row['claims']}]
        with self.assertRaisesRegex(ValueError, 'must match'):
            run.commit(self.root, row)

    def test_partial_avatar_drafts_are_not_exported_as_valid_avatars(self):
        row = {'schema_version': 1, 'stage': 'avatar-synthesis', 'status': 'blocked',
               'reason': 'Need evidence', 'evidence': [], 'claims': [],
               'avatars': [{'id': True, 'claims': []}]}
        run.commit(self.root, row)
        result = run.export(self.root)
        self.assertEqual(result['status'], 'needs_input')
        self.assertEqual(result['avatars'], [])

    def test_complete_flow_with_cited_avatar_and_owned_experiment(self):
        for stage in evidence.STAGES[:4]:
            run.commit(self.root, artifact(stage))
        row = artifact()
        row['stage'] = 'avatar-synthesis'
        row['avatars'] = [{'id': 'a', 'buyer': 'CTO', 'trigger': 'Release regression', 'pain': 'Repeated failures',
                           'offer': 'Diagnostic', 'channels': ['Search'], 'claims': copy.deepcopy(row['claims'])}]
        run.commit(self.root, row)
        self.assertEqual(run.export(self.root)['status'], 'needs_input')
        feedback = feedback_artifact()
        run.commit(self.root, feedback)
        output = run.export(self.root)
        self.assertEqual(output['status'], 'completed')
        self.assertEqual(len(output['checkpoints']['stage_artifacts']), 6)
        self.assertEqual(output['missing_inputs'], [])


if __name__ == '__main__':
    unittest.main()
