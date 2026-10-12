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

    def test_raw_export_preserves_body_and_separate_receipt_clocks(self):
        data = {'results': [{'url': 'https://example.com/community',
                             'body': 'A public question about creator briefs.',
                             'published_at': '2025-01-01T12:00:00Z'}]}
        headers = {'x-treg-cost-micro': '0', 'x-treg-call-id': 'receipt',
                   'x-treg-cache': 'hit', 'x-treg-fetched-at': '2026-10-10T08:00:00Z',
                   'x-treg-age': '86400', 'authorization': 'do-not-persist'}
        with patch.object(run, 'request_json', return_value=(data, headers)), \
                patch.object(run, 'now', return_value='2026-10-11T08:00:00+00:00'):
            receipt = run.collect(self.root, 'example.read', {'fetch': '{}'}, 0)
        output = run.export(self.root, include_raw=True)
        embedded = next(iter(output['checkpoints']['raw_responses'].values()))
        self.assertEqual(embedded, receipt)
        self.assertEqual(embedded['data'], data)
        self.assertEqual(embedded['query'], {'fetch': '{}'})
        self.assertEqual(embedded['fetched_at'], '2026-10-11T08:00:00+00:00')
        self.assertEqual(embedded['gateway_cache_headers'], {
            'x-treg-cache': 'hit', 'x-treg-fetched-at': '2026-10-10T08:00:00Z',
            'x-treg-age': '86400'})
        self.assertNotIn('do-not-persist', json.dumps(output))
        self.assertNotIn('raw_responses', run.export(self.root)['checkpoints'])

    def test_raw_export_rejects_modified_body_and_legacy_receipt(self):
        with patch.object(run, 'request_json', return_value=({'body': 'original'}, {'x-treg-cost-micro': '0'})):
            receipt = run.collect(self.root, 'example.read', {}, 0)
        key = receipt['request_fingerprint']
        state = run.read_state(self.root)
        path = self.root / state['calls'][key]['path']
        altered = copy.deepcopy(receipt); altered['data']['body'] = 'changed'
        run.atomic_json(path, altered)
        with self.assertRaisesRegex(ValueError, 'changed after collection'):
            run.export(self.root, include_raw=True)
        run.atomic_json(path, receipt)
        del state['calls'][key]['raw_response_fingerprint']
        run.atomic_json(self.root / 'run.json', state)
        with self.assertRaisesRegex(ValueError, 'legacy raw files'):
            run.export(self.root, include_raw=True)
        self.assertEqual(run.export(self.root)['status'], 'needs_input')

    def test_raw_export_rejects_wrong_identity_and_external_path(self):
        with patch.object(run, 'request_json', return_value=({}, {'x-treg-cost-micro': '0'})):
            receipt = run.collect(self.root, 'example.read', {}, 0)
        state = run.read_state(self.root)
        key = receipt['request_fingerprint']
        path = self.root / state['calls'][key]['path']
        altered = copy.deepcopy(receipt); altered['endpoint'] = 'different.read'
        run.atomic_json(path, altered)
        with self.assertRaisesRegex(ValueError, 'identity differs'):
            run.export(self.root, include_raw=True)
        altered = copy.deepcopy(receipt); altered['query'] = {'q': 'different public search'}
        run.atomic_json(path, altered)
        # Even updating the saved body hash cannot replace the request identity.
        state['calls'][key]['raw_response_fingerprint'] = run.digest(altered)
        run.atomic_json(self.root / 'run.json', state)
        with self.assertRaisesRegex(ValueError, 'identity differs'):
            run.export(self.root, include_raw=True)
        state['calls'][key]['path'] = 'artifacts/not-a-raw-receipt.json'
        run.atomic_json(self.root / 'run.json', state)
        with self.assertRaisesRegex(ValueError, 'inside the run raw directory'):
            run.export(self.root, include_raw=True)

    def test_raw_export_size_limits_fail_without_partial_output(self):
        with patch.object(run, 'request_json', return_value=({'body': 'source text'}, {'x-treg-cost-micro': '0'})):
            run.collect(self.root, 'example.read', {}, 0)
        baseline = run.export(self.root)
        saved = (self.root / 'output.json').read_text()
        for limit in ('RAW_EXPORT_LIMIT', 'OUTPUT_EXPORT_LIMIT'):
            with self.subTest(limit=limit), patch.object(run, limit, 1):
                with self.assertRaisesRegex(ValueError, 'exceeds'):
                    run.export(self.root, include_raw=True)
                self.assertEqual((self.root / 'output.json').read_text(), saved)
        self.assertEqual(baseline['status'], 'needs_input')

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

    def test_adradar_checkpoint_preserves_unknowns_and_runtime_provenance(self):
        row = artifact('competitor-ad-research')
        observation = row['evidence'][0]
        observation['source_url'] = 'https://www.facebook.com/ads/library/?id=123456789'
        observation['provenance'] = {
            'provider': 'adradar', 'tool': 'adradar_collect',
            'cli_revision': '607341149061e7ac159407dabe01c9fa3c14ee61',
            'adapter_version': '1', 'page_id': '987654321', 'country': 'GB',
            'playwright_version': '1.61.0', 'bundle_sha256': 'a' * 64,
            'request_arguments': {'page_id': '987654321', 'country': 'GB', 'max_scrolls': 3},
            'artifact_uri': '/api/v1/compute/agents/connector-artifacts/00000000-0000-4000-8000-000000000001',
            'snapshot_uri': '/api/v1/compute/agents/connector-artifacts/00000000-0000-4000-8000-000000000001?raw=true',
            'first_seen': '2026-10-11T12:00:00+00:00',
            'last_seen': '2026-10-11T12:00:00+00:00',
            'publisher_start_date': None, 'impressions': None, 'roas': None,
        }
        run.commit(self.root, row)
        exported = run.export(self.root)
        stage = next(item for item in exported['stages'] if item['stage'] == 'competitor-ad-research')
        persisted = json.loads((self.root / stage['artifact_path']).read_text())
        self.assertEqual(persisted['evidence'][0], observation)
        self.assertEqual(exported['evidence'], row['evidence'])
        self.assertEqual(exported['status'], 'needs_input')

    def test_avatar_cannot_change_adradar_snapshot_provenance(self):
        row = artifact('competitor-ad-research')
        row['evidence'][0]['provenance'] = {
            'provider': 'adradar', 'tool': 'adradar_collect',
            'cli_revision': '607341149061e7ac159407dabe01c9fa3c14ee61',
            'adapter_version': '1', 'raw_artifact_path': 'raw/adradar-snapshot.json',
        }
        run.commit(self.root, row)
        avatar = copy.deepcopy(row)
        avatar['stage'] = 'avatar-synthesis'
        avatar['avatars'] = [{'id': 'a', 'buyer': 'CTO', 'trigger': 'Release regression',
                              'pain': 'Repeated failures', 'offer': 'Diagnostic',
                              'channels': ['Search'], 'claims': copy.deepcopy(row['claims'])}]
        avatar['evidence'][0]['provenance']['raw_artifact_path'] = 'raw/different-snapshot.json'
        with self.assertRaisesRegex(ValueError, 'must match'):
            run.commit(self.root, avatar)


if __name__ == '__main__':
    unittest.main()
