#!/usr/bin/env python3
"""Validate portable stage artifacts without a model or external service."""
from __future__ import annotations
import argparse
import json
import math
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

STAGES = ('vendor-research', 'search-demand', 'competitor-ad-research',
          'creator-community-research', 'avatar-synthesis', 'experiment-feedback')
KINDS = ('observed', 'inferred', 'synthetic')


def required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be nonempty text')
    return value


def experiment_window(start: object, end: object) -> None:
    """Require comparable calendar dates or timezone-aware timestamps."""
    def parse(value: object):
        text = required_text(value, 'experiment window')
        try:
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}', text):
                return date.fromisoformat(text)
            parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
        except ValueError as exc:
            raise ValueError('experiment window must use valid ISO dates or timestamps') from exc
        if parsed.tzinfo is None:
            raise ValueError('experiment timestamp requires timezone')
        return parsed
    first, last = parse(start), parse(end)
    if type(first) is not type(last):
        raise ValueError('experiment window must use matching date or timestamp precision')
    if last < first or (isinstance(first, datetime) and last == first):
        raise ValueError('experiment window end must follow start (same calendar date is allowed)')


def validate(document: dict) -> dict:
    if not isinstance(document, dict) or type(document.get('schema_version')) is not int or document.get('schema_version') != 1:
        raise ValueError('schema_version must be 1')
    if document.get('stage') not in STAGES:
        raise ValueError('unknown stage')
    if document.get('status') not in ('complete', 'no_data', 'blocked'):
        raise ValueError('status must be complete, no_data or blocked')
    rows, claims = document.get('evidence'), document.get('claims')
    if not isinstance(rows, list) or not isinstance(claims, list):
        raise ValueError('evidence and claims must be arrays')
    evidence = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('evidence must contain objects')
        key = required_text(row.get('id'), 'evidence.id')
        if key in evidence:
            raise ValueError('duplicate evidence id')
        required_text(row.get('text'), 'evidence.text')
        if row.get('kind') not in KINDS:
            raise ValueError('invalid evidence kind')
        source = urlsplit(required_text(row.get('source_url'), 'source_url'))
        if source.scheme not in {'https', 'http'} or not source.hostname or source.username or source.password:
            raise ValueError('source_url must be an HTTP(S) citation without credentials')
        try:
            timestamp = datetime.fromisoformat(row['retrieved_at'].replace('Z', '+00:00'))
        except (KeyError, ValueError, TypeError, AttributeError) as exc:
            raise ValueError('retrieved_at must be an ISO timestamp') from exc
        if timestamp.tzinfo is None:
            raise ValueError('retrieved_at requires timezone')
        evidence[key] = row
    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError('claims must contain objects')
        required_text(claim.get('text'), 'claim.text')
        if claim.get('kind') not in KINDS:
            raise ValueError('invalid claim kind')
        refs = claim.get('evidence_ids')
        if not isinstance(refs, list) or not refs or any(not isinstance(ref, str) or ref not in evidence for ref in refs):
            raise ValueError('every claim requires existing evidence citations')
        if claim['kind'] == 'observed' and any(evidence[ref]['kind'] != 'observed' for ref in refs):
            raise ValueError('inferred or synthetic evidence cannot prove an observed claim')
        if claim['kind'] != 'synthetic' and any(evidence[ref]['kind'] == 'synthetic' for ref in refs):
            raise ValueError('synthetic evidence requires synthetic claim labeling')
    if document['status'] == 'complete' and (not rows or not claims):
        raise ValueError('complete requires evidence and claims')
    if document['status'] != 'complete':
        required_text(document.get('reason'), 'reason')
    if document['status'] == 'no_data' and (rows or claims):
        raise ValueError('no_data must not contain evidence or claims')
    if document['stage'] == 'avatar-synthesis' and document['status'] == 'complete':
        avatars = document.get('avatars')
        if not isinstance(avatars, list) or not avatars:
            raise ValueError('avatar synthesis requires candidate avatars')
        avatar_ids = set()
        for avatar in avatars:
            if not isinstance(avatar, dict):
                raise ValueError('avatars must contain objects')
            for key in ('id', 'buyer', 'trigger', 'pain', 'offer'):
                required_text(avatar.get(key), f'avatar.{key}')
            if avatar['id'] in avatar_ids:
                raise ValueError('duplicate avatar id')
            avatar_ids.add(avatar['id'])
            if not isinstance(avatar.get('channels'), list) or not avatar['channels'] or not all(isinstance(x, str) and x.strip() for x in avatar['channels']):
                raise ValueError('avatar channels required')
            if not isinstance(avatar.get('claims'), list) or not avatar['claims']:
                raise ValueError('avatar claims required')
            validate({'schema_version': 1, 'stage': 'vendor-research', 'status': 'complete',
                      'evidence': rows, 'claims': avatar['claims']})
    if document['stage'] == 'experiment-feedback' and document['status'] == 'complete':
        experiments = document.get('experiments')
        if not isinstance(experiments, list) or not experiments:
            raise ValueError('feedback requires owned experiment outcomes')
        for item in experiments:
            if not isinstance(item, dict):
                raise ValueError('experiments must contain objects')
            for key in ('experiment_id', 'avatar_id', 'creative_id', 'metric', 'window_start', 'window_end'):
                required_text(item.get(key), key)
            experiment_window(item['window_start'], item['window_end'])
            denominator, numerator = item.get('denominator'), item.get('numerator')
            if (type(denominator) not in {int, float} or type(numerator) not in {int, float}
                    or not math.isfinite(numerator) or not math.isfinite(denominator)
                    or not 0 <= numerator <= denominator or denominator <= 0):
                raise ValueError('rate metrics require 0 <= numerator <= positive denominator')
            ref = required_text(item.get('evidence_id'), 'experiment.evidence_id')
            if (ref not in evidence or evidence[ref]['kind'] != 'observed'
                    or evidence[ref].get('ownership') != 'owned'):
                raise ValueError('experiment outcome requires observed owned-data citation')
    return document


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path)
    args = parser.parse_args()
    try:
        result = validate(json.loads(args.artifact.read_text()))
    except (ValueError, OSError) as exc:
        parser.exit(2, f'Invalid artifact: {exc}\n')
    print(json.dumps({'valid': True, 'stage': result['stage'], 'status': result['status']}))


if __name__ == '__main__':
    main()
