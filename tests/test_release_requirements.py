"""Executable M5 requirement oracles and negative cases, not product certification.

The numeric/policy/cap tests exercise repository checker code directly. Display
and selection tests define an explicit fixture adapter for observing a renderer
or selector: passing these examples does not establish any implementation has
connected that adapter. No held corpus is read or acquired.
"""
import copy
import hashlib
import importlib.util
import inspect
import io
import json
import re
from pathlib import Path
import textwrap
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


r = module('m5_registration', 'test-vectors/registration/check_registration.py')
ts = module('m5_tslex', 'test-vectors/extraction-typescript/tslex.py')


RADIX_BAD = [prefix + body for prefix, invalid in [('0x', 'G'), ('0X', 'G'),
             ('0b', '2'), ('0B', '2'), ('0o', '8'), ('0O', '8')]
             for body in ('', invalid, '_1', '1_', '1__1', 'nn', '1nn', '1n2')]
RADIX_GOOD = [(prefix + digits + suffix, 'bigint' if suffix else 'number')
              for prefix, digits in [('0x', 'a_F'), ('0X', 'F_0'), ('0b', '1_0'),
                                     ('0B', '0_1'), ('0o', '7_0'), ('0O', '0_7')]
              for suffix in ('', 'n')]


def radix_failures(lexer=ts.Lexer):
    failures = []
    for text in RADIX_BAD:
        try:
            result = ts.lex(text, 'ts-tokens', lexer)
        except (IndexError, ValueError):
            result = ('crash',)
        if result != ('error', 'malformed-literal', 0):
            failures.append(text)
    for text, cls in RADIX_GOOD:
        if ts.lex(text, 'ts-tokens', lexer) != ('ok', [(cls, 0, len(text))]):
            failures.append(text)
    return failures


def validate_display(body, lines):
    """Fixture adapter: one line per listed reportable region, identified by key.

    The chosen text syntax is test-only, not a new normative rendering format.
    The output must show evidence and floor together; equality needs its label.
    """
    # Every line is one complete record in this test-only grammar. Canonical
    # ASCII integers and an exact optional label prevent prefix/negation matches.
    displayed = {}
    for line in lines:
        match = re.fullmatch(
            r'region (0|[1-9][0-9]*): evidence (0|[1-9][0-9]*); '
            r'minimum (0|[1-9][0-9]*)(; at the minimum)?', line)
        if match is None:
            raise ValueError('invalid display record')
        region_id, evidence, floor = map(int, match.group(1, 2, 3))
        if region_id in displayed:
            raise ValueError('duplicate display region')
        displayed[region_id] = (evidence, floor, match.group(4) is not None)
    expected = {}
    floor = body['minRegionDistinctHashes']
    for i, region in enumerate(body['regions']):
        if region['status'] == 'reportable':
            evidence = region['distinctHashes'] - region['distinctCommonHashes']
            expected[i] = (evidence, floor, evidence == floor)
    if displayed != expected:
        raise ValueError('displayed regions, evidence, floor or minimum label disagree with report')


def validate_selection(inputs, records):
    """Test-only selector adapter: one disposition per input, never silent drops."""
    by_path = {x['path']: x for x in records}
    if len(by_path) != len(records) or set(by_path) != set(inputs):
        raise ValueError('missing, extra or duplicate selection disposition')
    for path, expectation in inputs.items():
        row = by_path[path]
        if expectation == 'jsx-in-js' and row['disposition'] != 'deferred-to-stage-2':
            raise ValueError('JSX must be deferred, never an ordinary lexical rejection')
        if expectation == 'python2-error' and row['disposition'] != 'lexical-error':
            raise ValueError('failed Python-2 source must remain accounted for')


class ReleaseRequirementTests(unittest.TestCase):
    def test_ts_draft1_is_not_the_frozen_wire_version(self):
        checker = module('m5_ts_checker', 'test-vectors/extraction-typescript/check_vectors.py')
        raw = (ROOT / 'test-vectors/extraction-typescript/config-ts.json').read_bytes()
        self.assertEqual(checker.validate_config(raw)['profileVersion'], 'draft-2')
        with self.assertRaises(checker.CheckError):
            checker.validate_config(raw.replace(b'"draft-2"', b'"draft-1"'))

    def test_radix_literals(self):
        self.assertEqual(radix_failures(), [])

    def test_radix_mutants_are_killed(self):
        source = textwrap.dedent(inspect.getsource(ts.Lexer.number))
        replacements = [
            ('ch not in radix and ch != "_"', 'False'),
            ('not body or ', ''),
            ('body[0] == "_" or ', ''),
            ('body[-1] == "_" or ', ''),
            ('"__" in body or ', ''),
            ('body, cls = body[:-1], "bigint"', 'body, cls = body[:-1], "number"'),
            ('if body.endswith("n"):', 'if False:'),
        ]
        for before, after in replacements:
            with self.subTest(mutant=before):
                self.assertIn(before, source)
                namespace = dict(ts.__dict__)
                exec(source.replace(before, after, 1), namespace)
                mutant = type('RadixMutant', (ts.Lexer,), {'number': namespace['number']})
                self.assertTrue(radix_failures(mutant), 'mapped cases failed to kill mutant')
                if before.startswith('ch not in radix'):
                    # Reproduce F3: old cited empty-body case survives this mutant.
                    self.assertEqual(ts.lex('0x', 'ts-tokens', mutant), ('error', 'malformed-literal', 0))
                    self.assertEqual(ts.lex('0xG', 'ts-tokens', mutant)[0], 'ok')

    def test_policy_conditions_abort_before_evidence(self):
        base = json.loads((r.HERE / 'fixtures/verification-result-real.json').read_text())
        cases = []
        def add(name, change):
            result = copy.deepcopy(base['object'])
            change(result['policy'])
            cases.append((name, result))
        for key, values in [('quorum', [0, 1.5, True]), ('compromiseLookbackSeconds', [-1, 1.5, True]),
                            ('verificationTime', ['', '2026-02-31T00:00:00Z', '2026-11-24'])]:
            for value in values:
                add(f'{key}-{value}', lambda p, k=key, v=value: p.__setitem__(k, v))
        add('missing-verification-time', lambda p: p.pop('verificationTime'))
        for key in ('trustedKeys', 'recoveryKeys'):
            add(f'hint-{key}', lambda p, k=key: p.__setitem__(k, ['a' * 16]))
        add('deprecated-hints', lambda p: p.__setitem__('trustedKeyids', ['a' * 16]))
        recovery = {'keySha256': 'a' * 64, 'recovers': 'b' * 64, 'notBefore': '2026-11-24T00:00:00Z'}
        for key in recovery:
            bad = dict(recovery); bad.pop(key)
            add(f'recovery-missing-{key}', lambda p, b=bad: p.__setitem__('recoveryKeys', [b]))
        for key, value in [('keySha256', 'not-hex'), ('recovers', 'not-hex'), ('notBefore', '2026-02-31T00:00:00Z')]:
            bad = dict(recovery, **{key: value})
            add(f'recovery-invalid-{key}', lambda p, b=bad: p.__setitem__('recoveryKeys', [b]))
        for key in ('anchorSha256', 'kind', 'independenceGroup'):
            add(f'root-missing-{key}', lambda p, k=key: p['timeRoots'][0].pop(k))
        add('root-invalid-anchor', lambda p: p['timeRoots'][0].__setitem__('anchorSha256', 'bad'))
        for value in (0, True, 1.5):
            add('root-confirmations', lambda p, v=value: p['timeRoots'][1].__setitem__('minConfirmations', v))
        add('root-missing-confirmations', lambda p: p['timeRoots'][1].pop('minConfirmations'))
        add('root-missing-checkpoint', lambda p: p['timeRoots'][1].pop('checkpoint'))
        for key in ('height', 'headerSha256'):
            add('root-missing-checkpoint-field', lambda p, k=key: p['timeRoots'][1]['checkpoint'].pop(k))
        for key, value in [('height', -1), ('height', True), ('headerSha256', 'bad')]:
            add('root-invalid-checkpoint', lambda p, k=key, v=value: p['timeRoots'][1]['checkpoint'].__setitem__(k, v))
        def no_headers(p):
            p['timeRoots'][1].pop('headerFile')
            p['timeRoots'][1].pop('checkpoint')
        add('root-missing-checkpoint-without-header-file', no_headers)
        def bad_confirmations_no_headers(p):
            p['timeRoots'][1].pop('headerFile')
            p['timeRoots'][1]['minConfirmations'] = 0
        add('root-invalid-confirmations-without-header-file', bad_confirmations_no_headers)
        for name, result in cases:
            with self.subTest(case=name), patch.object(Path, 'read_text', side_effect=AssertionError('evidence inspected')):
                out = set()
                r.check_result(result, base['fixture'], out)
                self.assertTrue(out, 'invalid policy accepted')
        # Strict parsing happens before a policy object can reach check_result.
        for raw in ['{"quorum":2,"quorum":1}', '{"quorum":2,"quor\\u0075m":1}',
                    '{"quorum":NaN}', '{"quorum":Infinity}', '{"quorum":-Infinity}']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                r.strict_loads(raw)

    def test_catalogue_cap(self):
        nonce = bytes(range(32))
        self.assertEqual(r.MAX_CATALOGUE_BYTES, 1048576)
        at = b'x' * 1048576
        expected = hashlib.sha256(r.CATALOGUE_DOMAIN + nonce + len(at).to_bytes(8, 'big') + at).hexdigest()
        self.assertEqual(r.catalogue_commitment(nonce, at), expected)
        with self.assertRaisesRegex(ValueError, 'catalogue size'):
            r.catalogue_commitment(nonce, at + b'x')
        doc = json.loads((r.HERE / 'fixtures/report-link.json').read_text())
        with patch.object(r, 'load_source', return_value=at + b'x'), patch.object(
                r, 'catalogue_commitment', side_effect=AssertionError('oversized catalogue hashed')):
            out = set()
            r.check_link(doc['object'], doc['fixture'], out)
            self.assertIn('catalogue-does-not-open', out)

    def test_artifact_hash_is_streamed(self):
        class Guarded(io.BytesIO):
            def read(self, n=-1):
                if not 0 < n <= 65536:
                    raise AssertionError('unbounded or oversized read')
                return super().read(n)
        data = b'abcd' * 50000
        self.assertEqual(r.artifact_sha256(Guarded(data)), hashlib.sha256(data).hexdigest())
        nonce = bytes(range(32))
        prefix = r.POSSESSION_DOMAIN + nonce + len(data).to_bytes(8, 'big')
        with patch.object(r.io, 'BytesIO', Guarded):
            self.assertEqual(r.possession_digest(nonce.hex(), data), hashlib.sha256(prefix + data).hexdigest())
        with self.assertRaises(AssertionError):
            # A violating implementation is killed by the same guarded input.
            Guarded(data).read()

    def test_rendered_region_floor(self):
        body = {'minRegionDistinctHashes': 2, 'regions': [
            {'status': 'reportable', 'distinctHashes': 3, 'distinctCommonHashes': 1},
            {'status': 'reportable', 'distinctHashes': 4, 'distinctCommonHashes': 0}]}
        good = ['region 0: evidence 2; minimum 2; at the minimum', 'region 1: evidence 4; minimum 2']
        validate_display(body, good)
        validate_display(body, list(reversed(good)))  # Line order is not semantic.
        # Multi-digit values remain valid when they are the actual report values.
        large = {'minRegionDistinctHashes': 20, 'regions': [
            {'status': 'reportable', 'distinctHashes': 21, 'distinctCommonHashes': 1},
            {'status': 'reportable', 'distinctHashes': 24, 'distinctCommonHashes': 0}]}
        validate_display(large, ['region 0: evidence 20; minimum 20; at the minimum',
                                 'region 1: evidence 24; minimum 20'])
        validate_display({'minRegionDistinctHashes': 2, 'regions': [
            {'status': 'below-minimum-evidence', 'distinctHashes': 1, 'distinctCommonHashes': 0}]}, [])
        bad_cases = {
            # Original five negatives remain required.
            'missing region': good[1:],
            'separated evidence and floor': ['region 0: evidence 2', 'minimum 2; at the minimum', good[1]],
            'raw rather than unsuppressed evidence': ['region 0: evidence 3; minimum 2', good[1]],
            'missing equality label': ['region 0: evidence 2; minimum 2', good[1]],
            'incorrect nonminimum floor': [good[0], 'region 1: evidence 4; minimum 3'],
            # Both independently demonstrated R1 bypasses.
            'floor 20 accepted as prefix 2': ['region 0: evidence 2; minimum 20; at the minimum', good[1]],
            'negated equality label': ['region 0: evidence 2; minimum 2; NOT at the minimum', good[1]],
            # Audit all fields and the non-equality branch for the same defect.
            'nonminimum floor prefix': [good[0], 'region 1: evidence 4; minimum 20'],
            'nonminimum falsely labelled equal': [good[0], good[1] + '; at the minimum'],
            'incorrect evidence prefix': ['region 0: evidence 20; minimum 2; at the minimum', good[1]],
            'wrong region id': [good[0], 'region 10: evidence 4; minimum 2'],
            'duplicate region': good + [good[0]],
            'contradictory duplicate': good + ['region 0: evidence 999; minimum 2'],
            'unlisted region': good + ['region 2: evidence 4; minimum 2'],
            'nonrecord commentary': good + ['NOT at the minimum'],
        }
        for floor in ('02', '+2', '-2', '2.0', '2e0', '２'):
            bad_cases['noncanonical floor ' + floor] = [
                f'region 0: evidence 2; minimum {floor}; at the minimum', good[1]]
        for label in ('not at the minimum', 'never at the minimum', 'at the minimum NOT',
                      'at the minimum; actually above it', 'at the minimum-ish'):
            bad_cases['inexact or contradicted label ' + label] = [
                'region 0: evidence 2; minimum 2; ' + label, good[1]]
        for suffix in ('0', ' trailing text', '\n', '\x00'):
            bad_cases['trailing material ' + repr(suffix)] = [good[0], good[1] + suffix]
        for bad_field in ('region 00: evidence 2', 'region 0: evidence 02',
                          'region 0: evidence -2', 'region 0: evidence 2.0'):
            bad_cases['invalid region/evidence field ' + bad_field] = [
                bad_field + '; minimum 2; at the minimum', good[1]]
        for name, bad in bad_cases.items():
            with self.subTest(rendering=name), self.assertRaises(ValueError):
                validate_display(body, bad)

    def test_selection_accounting(self):
        inputs = {'old.py': 'python2-error', 'jsx.js': 'jsx-in-js'}
        good = [{'path': 'old.py', 'disposition': 'lexical-error'},
                {'path': 'jsx.js', 'disposition': 'deferred-to-stage-2'}]
        validate_selection(inputs, good)
        for bad in [good[:1], good[1:], good + good[:1],
                    [good[0], {'path': 'jsx.js', 'disposition': 'lexical-error'}]]:
            with self.subTest(selection=bad), self.assertRaises(ValueError):
                validate_selection(inputs, bad)

    def test_report_identity_uses_body_not_wrapper(self):
        doc = json.loads((r.HERE / 'fixtures/report-link.json').read_text())
        link = doc['object']
        path = ROOT / link['report']['path']
        report = json.loads(path.read_text())
        original_read = Path.read_text
        raw = json.dumps(report, indent=4).encode()
        wrapper_hash = hashlib.sha256(raw).hexdigest()
        self.assertNotEqual(wrapper_hash, link['report']['bodySha256'])
        def read(p, *args, **kwargs):
            return raw.decode() if p == path else original_read(p, *args, **kwargs)
        with patch.object(Path, 'read_text', read):
            out = set()
            r.check_link(link, doc['fixture'], out)
            self.assertFalse(out, out)
            bad = copy.deepcopy(link)
            bad['report']['bodySha256'] = wrapper_hash
            out = set()
            r.check_link(bad, doc['fixture'], out)
            self.assertIn('report-digest', out)

    def test_production_placeholder_refusal(self):
        event = dict(real=False, time=123)
        self.assertEqual(r._final(event, False, 123), ('placeholder', None))
        self.assertEqual(r._final(event, True, 123), ('placeholder-assumed-valid', 123))
        # The production result cannot upgrade this refusal to counted time.
        bad = ('valid', 123)
        self.assertNotEqual(r._final(event, False, 123), bad)


if __name__ == '__main__':
    unittest.main(verbosity=2)
