#!/usr/bin/env python3
"""Durable single-run checkpoints and bounded, read-only Treg collection.

Run directory must be on the deployment's durable volume. Local policy/locking
is defense in depth, not isolation from an agent with arbitrary shell access.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request
from evidence import STAGES, validate


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.write-')
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


@contextmanager
def locked(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def read_state(root: Path) -> dict:
    return json.loads((root / 'run.json').read_text())


def init(root: Path, run_id: str, policy: dict) -> dict:
    """Policy is provided by deployment configuration, never inferred by a skill."""
    if not run_id.strip():
        raise ValueError('run_id required')
    if type(policy.get('budget_micro_usd')) is not int or policy['budget_micro_usd'] < 0:
        raise ValueError('budget_micro_usd must be a nonnegative integer')
    endpoints = policy.get('read_only_endpoint_ids')
    if not isinstance(endpoints, list) or any(not isinstance(x, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', x) for x in endpoints):
        raise ValueError('explicit read_only_endpoint_ids array required')
    with locked(root):
        if (root / 'run.json').exists():
            state = read_state(root)
            if state['run_id'] != run_id or state['policy'] != policy:
                raise ValueError('existing run identity/policy differs; use a new run directory')
            return state
        state = {'schema_version': 1, 'run_id': run_id, 'policy': policy,
                 'created_at': now(), 'calls': {}, 'stages': {}}
        atomic_json(root / 'run.json', state)
        return state


def commit(root: Path, artifact: dict) -> dict:
    validate(artifact)
    with locked(root):
        state = read_state(root)
        stage = artifact['stage']
        if stage == 'avatar-synthesis' and artifact['status'] == 'complete':
            if not any(state['stages'].get(s, {}).get('status') == 'complete' for s in STAGES[:4]):
                raise ValueError('avatar synthesis requires completed collection evidence')
            known = {}
            for source_stage in STAGES[:4]:
                record = state['stages'].get(source_stage)
                if record:
                    saved = json.loads((root / record['path']).read_text())
                    known.update({row['id']: row for row in saved['evidence']})
            for row in artifact['evidence']:
                if row['id'] not in known or known[row['id']] != row:
                    raise ValueError('avatar evidence must match committed collection evidence')
        fingerprint = digest(artifact)
        previous = state['stages'].get(stage)
        if previous and previous['status'] == 'complete':
            if previous['fingerprint'] == fingerprint:
                return previous
            raise ValueError('completed stage is immutable; start a new run to revise it')
        relative = f'artifacts/{stage}-{fingerprint}.json'
        atomic_json(root / relative, artifact)
        record = {'status': artifact['status'], 'path': relative, 'fingerprint': fingerprint, 'updated_at': now()}
        state['stages'][stage] = record
        atomic_json(root / 'run.json', state)
        return record


def request_json(path: str, query: dict, headers: dict) -> tuple[object, dict]:
    token = os.environ.get('TREG_TOKEN', '').strip()
    if not token:
        raise ValueError('TREG_TOKEN missing from Vault-bound environment')
    request = Request('https://treg.to' + path + ('?' + urlencode(query, doseq=True) if query else ''),
                      headers={'X-Treg-Token': token, 'Accept': 'application/json', **headers}, method='GET')
    # Redirects are refused: auth must never follow a provider-controlled location.
    from urllib.request import HTTPRedirectHandler, build_opener
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            return None
    try:
        with build_opener(NoRedirect()).open(request, timeout=30) as response:
            raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB; reconcile call before retrying')
            return json.loads(raw), {key.lower(): value for key, value in response.headers.items()}
    except HTTPError as exc:
        raise ValueError(f'Treg HTTP {exc.code}; no automatic retry') from None
    except (URLError, TimeoutError, json.JSONDecodeError):
        raise ValueError('Treg response unavailable; reconcile reserved call before retrying') from None


def endpoint_id(value: str) -> str:
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', value):
        raise ValueError('catalog endpoint id required, not a URL or tool path')
    return value


def catalog(endpoint: str) -> object:
    # Publicly documented authenticated route: current price/access, not a call.
    return request_json(f'/catalog/endpoints/{endpoint_id(endpoint)}/access', {}, {})[0]


def collect(root: Path, endpoint: str, query: dict, max_cost_micro: int) -> dict:
    endpoint_id(endpoint)
    if not isinstance(query, dict) or any(not isinstance(key, str) for key in query):
        raise ValueError('query must be a JSON object')
    if type(max_cost_micro) is not int or max_cost_micro < 0:
        raise ValueError('max cost must be nonnegative integer micro-USD')
    # Check presence before making a durable reservation; do not record the secret.
    if not os.environ.get('TREG_TOKEN', '').strip():
        raise ValueError('TREG_TOKEN missing from Vault-bound environment')
    fingerprint = digest({'endpoint': endpoint, 'query': query})
    with locked(root):
        state = read_state(root)
        if endpoint not in state['policy']['read_only_endpoint_ids']:
            raise ValueError('endpoint not in deployment read-only allowlist')
        previous = state['calls'].get(fingerprint)
        if previous:
            if previous['status'] == 'complete':
                return json.loads((root / previous['path']).read_text())
            raise ValueError('call already reserved or needs review; reconcile before retrying')
        if len(state['calls']) >= 100:
            raise ValueError('run call limit reached (100); start a separately authorized run')
        charged = sum(call.get('cost_micro_usd', call['max_cost_micro_usd']) for call in state['calls'].values())
        if charged + max_cost_micro > state['policy']['budget_micro_usd']:
            raise ValueError('run budget exhausted')
        entry = {'status': 'reserved', 'endpoint': endpoint, 'max_cost_micro_usd': max_cost_micro,
                 'created_at': now(), 'idempotency_key': digest([state['run_id'], fingerprint])}
        state['calls'][fingerprint] = entry
        atomic_json(root / 'run.json', state)
        # Keep lock across the bounded request so concurrent invocations cannot
        # overspend. A crash leaves the reservation durable and blocks replay.
        data, headers = request_json(f'/call/{endpoint}', query, {
            'X-Treg-Route-Max-Cost': str(Decimal(max_cost_micro) / Decimal(1_000_000)),
            'Idempotency-Key': entry['idempotency_key'],
        })
        cost = headers.get('x-treg-cost-micro')
        if cost is None or not cost.isdigit() or int(cost) > max_cost_micro:
            raise ValueError('missing or unexpected cost receipt; reservation retained for reconciliation')
        receipt = {'endpoint': endpoint, 'request_fingerprint': fingerprint, 'fetched_at': now(),
                   'call_id': headers.get('x-treg-call-id'), 'cost_micro_usd': int(cost),
                   'status': 'unvalidated', 'data': data}
        relative = f'raw/{fingerprint}.json'
        atomic_json(root / relative, receipt)
        # Raw provider data is never automatically promoted into observations.
        entry.update(status='complete', path=relative, cost_micro_usd=int(cost))
        atomic_json(root / 'run.json', state)
        return receipt


def export(root: Path) -> dict:
    with locked(root):
        state = read_state(root)
        rows, avatars, stages, missing, documents = {}, [], [], [], {}
        for stage in STAGES:
            record = state['stages'].get(stage)
            if not record:
                stages.append({'stage': stage, 'status': 'blocked', 'artifact_path': ''})
                missing.append(f'{stage}: no committed artifact')
                continue
            document = validate(json.loads((root / record['path']).read_text()))
            if digest(document) != record['fingerprint']:
                raise ValueError('checkpoint artifact changed after commit')
            documents[stage] = document
            stages.append({'stage': stage, 'status': document['status'], 'artifact_path': record['path']})
            if document['status'] != 'complete':
                missing.append(f"{stage}: {document['reason']}")
            for row in document['evidence']:
                if row['id'] in rows and rows[row['id']] != row:
                    raise ValueError('evidence id collision across stages')
                rows[row['id']] = row
            if stage == 'avatar-synthesis' and document['status'] == 'complete':
                avatars = document.get('avatars', [])
        known_avatars = {avatar['id'] for avatar in avatars}
        feedback = documents.get('experiment-feedback', {})
        for experiment in feedback.get('experiments', []) if feedback.get('status') == 'complete' else []:
            if experiment['avatar_id'] not in known_avatars:
                raise ValueError('experiment references an unknown avatar')
        receipts = {key: {k: v for k, v in entry.items() if k != 'idempotency_key'}
                    for key, entry in state['calls'].items()}
        output = {'schema_version': 1, 'run_id': state['run_id'],
                  'status': 'needs_input' if missing else 'completed',
                  'stages': stages, 'evidence': list(rows.values()), 'avatars': avatars,
                  'missing_inputs': missing,
                  'summary': 'Research requires inputs' if missing else 'Six research stages completed',
                  'artifacts': {'stage_count': len(documents)},
                  'checkpoints': {'manifest': state, 'stage_artifacts': documents, 'call_receipts': receipts}}
        atomic_json(root / 'output.json', output)
        return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    start = sub.add_parser('init')
    start.add_argument('--run-id', required=True)
    start.add_argument('--policy', type=Path, required=True)
    sub.add_parser('status')
    sub.add_parser('export')
    save = sub.add_parser('commit')
    save.add_argument('artifact', type=Path)
    access = sub.add_parser('catalog')
    access.add_argument('endpoint')
    fetch = sub.add_parser('collect')
    fetch.add_argument('endpoint')
    fetch.add_argument('--query', type=Path, required=True)
    fetch.add_argument('--max-cost-micro', type=int, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            result = init(args.run_dir, args.run_id, json.loads(args.policy.read_text()))
        elif args.command == 'status':
            result = read_state(args.run_dir)
        elif args.command == 'export':
            result = export(args.run_dir)
        elif args.command == 'commit':
            result = commit(args.run_dir, json.loads(args.artifact.read_text()))
        elif args.command == 'catalog':
            result = catalog(args.endpoint)
        else:
            result = collect(args.run_dir, args.endpoint, json.loads(args.query.read_text()), args.max_cost_micro)
        print(json.dumps(result, indent=2, allow_nan=False))
    except (ValueError, OSError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    main()
