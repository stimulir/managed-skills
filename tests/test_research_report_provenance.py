"""Offline semantic regressions for advertiser denominators and response clocks."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(slug, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'skills' / slug / 'helpers' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ads = load('competitor-ad-research', 'count_ads')
retrieval = load('search-demand', 'retrieval')


class ReportProvenanceTests(unittest.TestCase):
    def test_excluded_ad_does_not_inflate_matched_media_count(self):
        result = ads.summarize({'ads': [
            {'ad_id': '1', 'page_name': 'Vendor', 'media': []},
            {'ad_id': '2', 'page_name': 'Vendor', 'media': ['image']},
            {'ad_id': '3', 'page_name': 'Other', 'media': []}]}, 'Vendor')
        self.assertEqual(result['all']['media_absent_records'], 2)
        self.assertEqual(result['matched']['media_absent_records'], 1)
        self.assertEqual(result['matched']['records'], 2)
        self.assertEqual(result['excluded']['media_absent_records'], 1)

    def test_duplicates_and_unknown_media_are_separate(self):
        result = ads.summarize({'ads': [
            {'ad_id': '1', 'page_name': 'Vendor', 'media': []},
            {'ad_id': '1', 'page_name': 'Vendor', 'media': []},
            {'page_name': 'Vendor', 'media': None},
            {'ad_id': '2', 'page_name': 'Vendor'}]}, 'Vendor')['matched']
        self.assertEqual(result['records'], 4)
        self.assertEqual(result['unique_ad_ids'], 2)
        self.assertEqual(result['duplicate_id_records'], 1)
        self.assertEqual(result['missing_ad_id_records'], 1)
        self.assertEqual(result['media_absent_records'], 2)
        self.assertEqual(result['media_unknown_records'], 2)

    def envelope(self):
        return {'response': {}, 'tool': 'research_keywords', 'tool_call_id': 'keyword-call',
                'tool_receipt': {'provider': 'openseo', 'tool': 'research_keywords',
                                 'tool_call_id': 'keyword-call', 'received_at': '2026-10-11T12:13:07.564Z'}}

    def test_provider_timestamp_retained_in_later_replay(self):
        envelope = self.envelope()
        envelope['response']['retrieved_at'] = '2026-10-10T09:00:00+01:00'
        envelope['replay_started_at'] = '2026-10-11T13:00:00Z'
        resolved = retrieval.resolve(envelope)
        self.assertEqual(resolved['retrieved_at'], '2026-10-10T09:00:00+01:00')
        self.assertEqual(resolved['retrieved_at_basis'], 'provider_response.retrieved_at')

    def test_same_call_receipt_is_not_upstream_metric_date(self):
        envelope = self.envelope()
        envelope['adradar_retrieved_at'] = '2026-10-11T12:14:23.121Z'
        resolved = retrieval.resolve(envelope)
        self.assertEqual(resolved['retrieved_at'], '2026-10-11T12:13:07.564Z')
        self.assertEqual(resolved['retrieved_at_basis'], 'captured_tool_response_receipt')
        self.assertIsNone(resolved['provider_retrieved_at'])

    def test_receipt_from_other_provider_or_call_rejected(self):
        for field, value in [('provider', 'adradar'), ('tool', 'get_project_context'), ('tool_call_id', 'other-call')]:
            with self.subTest(field=field):
                envelope = self.envelope(); envelope['tool_receipt'][field] = value
                with self.assertRaises(ValueError):
                    retrieval.resolve(envelope)

    def test_missing_original_provenance_stays_unknown(self):
        result = retrieval.resolve({'response': {}, 'replay_started_at': '2026-10-11T13:00:00Z'})
        self.assertIsNone(result['retrieved_at'])
        self.assertEqual(result['retrieved_at_basis'], 'unknown')

    def test_invalid_or_timezone_free_dates_rejected(self):
        for value in ['2026-10-11', '2026-10-11T12:13:07', 'yesterday']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                retrieval.resolve({'response': {'retrieved_at': value}})


if __name__ == '__main__':
    unittest.main()
