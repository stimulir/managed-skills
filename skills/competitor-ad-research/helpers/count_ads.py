#!/usr/bin/env python3
"""Count saved AdRadar records by explicit advertiser scope; no provider I/O."""
import argparse
import json
from pathlib import Path


def counts(rows):
    ids = [str(row['ad_id']) for row in rows if row.get('ad_id')]
    absent = sum(isinstance(row.get('media'), list) and not row['media'] for row in rows)
    present = sum(isinstance(row.get('media'), list) and bool(row['media']) for row in rows)
    return {'records': len(rows), 'unique_ad_ids': len(set(ids)),
            'duplicate_id_records': len(ids) - len(set(ids)),
            'missing_ad_id_records': len(rows) - len(ids),
            'media_absent_records': absent, 'media_present_records': present,
            'media_unknown_records': len(rows) - absent - present}


def summarize(result, advertiser):
    if not isinstance(advertiser, str) or not advertiser.strip():
        raise ValueError('advertiser must be a verified nonempty page_name')
    ads = result.get('ads')
    if not isinstance(ads, list) or any(not isinstance(row, dict) for row in ads):
        raise ValueError('ads must be an array of records')
    matched = [row for row in ads if row.get('page_name') == advertiser]
    excluded = [row for row in ads if row.get('page_name') != advertiser]
    return {'advertiser': advertiser, 'match_basis': 'exact page_name',
            'count_basis': 'returned records (unique IDs reported separately)',
            'all': counts(ads), 'matched': counts(matched), 'excluded': counts(excluded)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('result', type=Path)
    parser.add_argument('--advertiser', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(summarize(json.loads(args.result.read_text()), args.advertiser)))
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Invalid collection: {exc}\n')


if __name__ == '__main__':
    main()
