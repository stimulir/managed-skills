#!/usr/bin/env python3
"""Resolve one saved response's retrieval observation; never use replay time."""
import argparse
from datetime import datetime
import json
from pathlib import Path


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be timezone-aware ISO text')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timestamp requires timezone')
    return value


def resolve(envelope):
    # The caller must persist this envelope from the same tool-call response.
    response = envelope['response']
    if not isinstance(response, dict):
        raise ValueError('response must be an object')
    provider_time = response.get('retrieved_at')
    if provider_time is not None:
        return {'retrieved_at': timestamp(provider_time),
                'retrieved_at_basis': 'provider_response.retrieved_at',
                'provider_retrieved_at': provider_time}
    receipt = envelope.get('tool_receipt')
    if receipt is not None:
        if (not isinstance(receipt, dict) or receipt.get('provider') != 'openseo'
                or receipt.get('tool') != envelope.get('tool')
                or receipt.get('tool_call_id') != envelope.get('tool_call_id')
                or not receipt.get('tool_call_id') or not receipt.get('tool')):
            raise ValueError('receipt must identify this OpenSEO tool call')
        return {'retrieved_at': timestamp(receipt.get('received_at')),
                'retrieved_at_basis': 'captured_tool_response_receipt',
                'provider_retrieved_at': None,
                'tool_call_id': receipt['tool_call_id'], 'tool': receipt['tool']}
    return {'retrieved_at': None, 'retrieved_at_basis': 'unknown',
            'provider_retrieved_at': None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('envelope', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(resolve(json.loads(args.envelope.read_text()))))
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f'Invalid retrieval provenance: {exc}\n')


if __name__ == '__main__':
    main()
