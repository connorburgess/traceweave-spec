#!/usr/bin/env python3
"""Offline negative probes for M5 requirement-map time-policy boundaries.

These exercise the fixture checker's policy layer, not a production verifier.
No fixtures or historical result counts are changed.
"""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'test-vectors/registration/check_registration.py'
spec = importlib.util.spec_from_file_location('registration', PATH)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def check():
    policy = json.loads((r.HERE / 'fixtures/verification-result-real.json').read_text())['object']['policy']
    root = next(x for x in policy['timeRoots'] if 'headerFile' in x)
    chain = r.RF.headers_from_file((r.HERE / root['headerFile']).read_bytes())
    cp = root['checkpoint']['height']
    event = dict(pending=False, real=True, anchors=[root['anchorSha256']], kind=root['kind'],
                 type='opentimestamps', ots=[(cp, chain[cp][36:68])])
    cases = []
    def probe(name, e, p, expected):
        actual = r._outcome(None, e, [e], p, False, {})
        if actual != (expected, None):
            raise ValueError(f'{name}: expected {(expected, None)}, got {actual}')
        cases.append(name)
    probe('insufficient-confirmations', event, policy, 'insufficient-confirmations')
    unpinned = copy.deepcopy(policy)
    next(x for x in unpinned['timeRoots'] if 'headerFile' in x).pop('checkpoint')
    probe('unpinned-ots', event, unpinned, 'unsupported')
    probe('unlisted-root', event, dict(policy, timeRoots=[]), 'untrusted-root')
    probe('pending-refused', dict(event, pending=True), policy, 'pending')
    probe('unsupported-algorithm', dict(event, unsupported=True), policy, 'unsupported')
    # Negative output mutations: a refused token is incorrectly called valid.
    for name in ('verification-result-no-revocation-data', 'verification-result-real-ecdsa'):
        doc = json.loads((r.HERE / 'fixtures' / (name + '.json')).read_text())
        obj = copy.deepcopy(doc['object'])
        target = next(x for x in obj['outcomes']['timeEvidence'] if x['outcome'] in ('no-revocation-data', 'unsupported'))
        target['outcome'] = 'valid'
        codes = r.check_object(doc['fixture']['kind'], obj, doc['fixture'])
        if 'result-mismatch' not in codes:
            raise ValueError(f'{name}: invalid outcome mutation escaped: {codes}')
        cases.append(name)
    # A public commitment object cannot carry private opening material.
    doc = json.loads((r.HERE / 'fixtures/statement.json').read_text())
    for name, field, value in [('private-nonce-disclosed', 'nonceHex', '01' * 32),
                               ('private-catalogue-disclosed', 'catalogue', {'references': []})]:
        obj = copy.deepcopy(doc['object'])
        obj['predicate']['catalogue'][field] = value
        if not r.check_object(doc['fixture']['kind'], obj, doc['fixture']):
            raise ValueError(f'{name}: private opening material accepted in public record')
        cases.append(name)
    return cases


if __name__ == '__main__':
    try:
        cases = check()
    except (ValueError, KeyError, StopIteration) as exc:
        raise SystemExit(f'FAIL release boundary probes: {exc}')
    print(f'PASS release boundary probes: {len(cases)}/{len(cases)} negative cases')
