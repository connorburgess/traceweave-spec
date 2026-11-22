#!/usr/bin/env python3
"""Synthetic raw-state experiment. Whole-input grammar, no general Rust parser."""
import argparse
import hashlib
import itertools
import json
import math
import platform
import re
import subprocess
import tempfile
import time
from pathlib import Path

HEADER = re.compile(r'\s*fn specimen\(\)\s*->\s*\[u32;\s*([0-4])\]\s*\{(.*)\}\s*', re.S)
LET = re.compile(r'\s*let ([a-d]): u32 = ([0-9][0-9_]*u32);')
TAIL = re.compile(r'\s*\[([a-d,\s]*)\]\s*')
BOUNDARY = {'edition': '2021', 'build_script': False, 'source_observers': False,
            'proc_macros': False, 'cfg_features': False, 'generated_or_vendor': False}


def parse(source, boundary):
    if boundary != BOUNDARY:
        raise ValueError('unsupported build/source boundary')
    match = HEADER.fullmatch(source)
    if not match:
        raise ValueError('outside whole-input function grammar')
    count, body = int(match[1]), match[2]
    bindings, end = [], 0
    while (item := LET.match(body, end)):
        name, token = item[1], item[2]
        digits = token[:-3].replace('_', '')
        if not re.fullmatch(r'0|[1-9][0-9]*', digits) or int(digits) > 2**32-1:
            raise ValueError('noncanonical or out-of-range numeric value')
        bindings.append((name, int(digits), token))
        end = item.end()
    tail = TAIL.fullmatch(body[end:])
    if not tail:
        raise ValueError('outside binding/array grammar')
    array_text = tail[1].strip()
    if array_text and not re.fullmatch(r'[a-d](?:\s*,\s*[a-d])*\s*,?', array_text):
        raise ValueError('malformed array separators')
    names = [b[0] for b in bindings]
    returned = [x.strip() for x in tail[1].split(',') if x.strip()]
    if len(bindings) != count or len(set(names)) != count or sorted(returned) != sorted(names) or len(returned) != count:
        raise ValueError('length, shadowing or return-set mismatch')
    return bindings, returned


def render(bindings, returned):
    # Deliberately compact so the formatter test performs an actual whitespace rewrite.
    return ('fn specimen() -> [u32; %d] { ' % len(bindings)
            + ''.join('let %s: u32 = %s; ' % (n, t) for n, _, t in bindings)
            + '[' + ', '.join(returned) + '] }\n')


def token(value, bit):
    digits = str(value)
    return (digits if bit == 0 else digits[:-1] + '_' + digits[-1]) + 'u32'


def inspect(source, family, boundary=BOUNDARY):
    if family not in ('order', 'spelling'):
        raise ValueError('unknown carrier family')
    bindings, returned = parse(source, boundary)
    for _, value, spelling in bindings:
        allowed = [token(value, 0)] + ([token(value, 1)] if value >= 10 else [])
        if spelling not in allowed:
            raise ValueError('unexpected spelling')
    sites = [n for n, v, _ in sorted(bindings) if v >= 10]
    states = math.factorial(len(bindings)) if family == 'order' else 2**len(sites)
    return bindings, returned, sites, states


def embed(source, family, state, boundary=BOUNDARY):
    try:
        bindings, returned, sites, states = inspect(source, family, boundary)
        if states < 2:
            raise ValueError('zero capacity')
        if not 0 <= state < states:
            raise ValueError('state out of range')
        if family == 'order':
            bindings = list(list(itertools.permutations(sorted(bindings)))[state])
        else:
            bits = dict(zip(sites, ((state >> i) & 1 for i in range(len(sites)))))
            bindings = [(n, v, token(v, bits[n]) if n in bits else t) for n, v, t in bindings]
        output = render(bindings, returned)
        return output, 'already_matching' if output == source else 'changed', None
    except ValueError as error:
        return source, 'refused', str(error)


def extract(reference, candidate, family):
    try:
        rb, rr, sites, states = inspect(reference, family)
        cb, cr, cs, _ = inspect(candidate, family)
        if states < 2:
            raise ValueError('zero capacity')
        if sorted((n, v) for n, v, _ in rb) != sorted((n, v) for n, v, _ in cb) or rr != cr or sites != cs:
            raise ValueError('reference mismatch')
        if family == 'order':
            order = tuple(n for n, _, _ in cb)
            state = list(itertools.permutations(sorted(n for n, _, _ in rb))).index(order)
        else:
            by_name = {n: (v, t) for n, v, t in cb}
            state = sum((by_name[n][1] == token(by_name[n][0], 1)) << i for i, n in enumerate(sites))
        return state, None
    except ValueError as error:
        return None, str(error)


def canonicalize(source, family):
    bindings, returned = parse(source, BOUNDARY)
    if family == 'order':
        bindings.sort()
    else:
        bindings = [(n, v, token(v, 0)) for n, v, _ in bindings]
    return render(bindings, returned)


def fixture(n, single_digit=False):
    bindings = [(chr(97+i), i+1 if single_digit else 12+11*i, '') for i in range(n)]
    return render([(n, v, token(v, 0)) for n, v, _ in bindings], [n for n, _, _ in bindings])


def run(command, **kwargs):
    return subprocess.run(command, check=True, capture_output=True, text=True, timeout=60, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    compiler = run(['rustc', '--version', '--verbose']).stdout.strip()
    formatter = run(['rustfmt', '--version']).stdout.strip()
    target = re.search(r'^host: (.*)$', compiler, re.M)[1]
    report = {'toolchain': compiler, 'formatter': formatter, 'python': platform.python_version(),
              'boundary': BOUNDARY, 'target': target, 'families': {}, 'identity_metrics': 'unavailable'}
    # Entire source is parsed, so extra items, comments and macro bodies cannot hide observers.
    base = fixture(2)
    refusals = {
        'Drop_item': 'struct Guard; impl Drop for Guard { fn drop(&mut self) {} }\n'+base,
        'borrow': base.replace('12u32', '&12u32'),
        'dependent_initializer': base.replace('23u32', 'a'),
        'shadowing': base.replace('let b:', 'let a:'),
        'call': base.replace('12u32', 'effect()'),
        'macro_definition': 'macro_rules! observe { ($t:tt) => { stringify!($t) } }\n'+base,
        'macro_invocation': base.replace('12u32', 'observe!(12u32)'),
        'attribute_macro': '#[observer]\n'+base,
        'cfg': '#[cfg(feature="x")]\n'+base,
        'unsafe': base.replace('fn specimen', 'unsafe fn specimen'),
        'trait_operator': base.replace('12u32', 'left + right'),
        'lifetime': base.replace('specimen()', "specimen<'a>()"),
        'visibility': base.replace('fn specimen', 'pub fn specimen'),
        'unexpected_spelling': base.replace('12u32', '1__2u32'),
        'malformed': base.replace('[a, b]', '[a,, b]'),
        'malformed_leading_comma': base.replace('[a, b]', '[,a,b]'),
        'malformed_missing_comma': base.replace('[a, b]', '[ab]'),
    }
    artifacts = []
    with tempfile.TemporaryDirectory(prefix='traceweave-rust-') as temporary:
        root = Path(temporary)
        for family in ('order', 'spelling'):
            counts = dict(requests=0, completed=0, changed=0, already_matching=0, refused=0,
                          clean_recovered=0, deterministic=0, formatted_recovered=0,
                          format_idempotent=0, format_changed=0, attack_valid=0, attack_transformed=0,
                          attack_already_canonical=0, attack_state_preserved=0,
                          attack_nonzero_collapsed=0, attack_extraction_erasures=0)
            cases, capacity = [], []
            for n in range(5):
                source = fixture(n)
                _, _, sites, states = inspect(source, family)
                capacity.append({'bindings': n, 'sites': len(sites), 'raw_states': states,
                                 'fixed_binary_bits': states.bit_length()-1})
                for state in range(states):
                    counts['requests'] += 1
                    marked, status, reason = embed(source, family, state)
                    counts[status] += 1
                    assert (marked, status, reason) == embed(source, family, state)
                    counts['deterministic'] += 1
                    if status == 'refused':
                        assert marked == source and reason == 'zero capacity'
                        cases.append({'n': n, 'state': state, 'status': status, 'reason': reason})
                        continue
                    counts['completed'] += 1
                    assert extract(source, marked, family) == (state, None)
                    counts['clean_recovered'] += 1
                    path = root / 'candidate.rs'
                    path.write_text(marked)
                    run(['rustfmt', '--edition', '2021', '--config', 'style_edition=2021', str(path)])
                    formatted = path.read_text()
                    counts['format_changed'] += formatted != marked
                    assert extract(source, formatted, family) == (state, None)
                    counts['formatted_recovered'] += 1
                    run(['rustfmt', '--edition', '2021', '--config', 'style_edition=2021', str(path)])
                    assert path.read_text() == formatted
                    counts['format_idempotent'] += 1
                    attacked = canonicalize(marked, family)
                    recovered, error = extract(source, attacked, family)
                    assert error is None and recovered == 0
                    counts['attack_transformed' if attacked != marked else 'attack_already_canonical'] += 1
                    counts['attack_nonzero_collapsed' if state else 'attack_state_preserved'] += 1
                    expected = [12+11*i for i in range(n)]
                    for stage, text in [('marked', marked), ('formatted', formatted), ('canonicalized', attacked)]:
                        artifacts.append((text, expected, family, n, state, stage))
                    cases.append({'n': n, 'state': state, 'status': status,
                                  'original_sha256': hashlib.sha256(source.encode()).hexdigest(),
                                  'marked_sha256': hashlib.sha256(marked.encode()).hexdigest(),
                                  'attack_sha256': hashlib.sha256(attacked.encode()).hexdigest()})
            refused_details = []
            boundary_cases = [(k, base, BOUNDARY | {k: True}) for k in
                              ('build_script', 'source_observers', 'proc_macros', 'cfg_features', 'generated_or_vendor')]
            for name, source, boundary in [(k, v, BOUNDARY) for k, v in refusals.items()] + boundary_cases:
                output, status, reason = embed(source, family, 0, boundary)
                assert status == 'refused' and output.encode() == source.encode()
                refused_details.append({'fixture': name, 'reason': reason, 'unchanged_bytes': True})
            for name, requested_family, requested_state in [
                ('negative_state', family, -1),
                ('out_of_range_state', family, inspect(base, family)[3]),
                ('unknown_family', 'unknown', 0),
            ]:
                output, status, reason = embed(base, requested_family, requested_state)
                assert status == 'refused' and output.encode() == base.encode()
                refused_details.append({'fixture': name, 'reason': reason, 'unchanged_bytes': True})
            # An eligible single-digit function has zero spelling sites.
            if family == 'spelling':
                source = fixture(1, single_digit=True)
                assert embed(source, family, 0) == (source, 'refused', 'zero capacity')
                refused_details.append({'fixture': 'single_digit_zero_capacity', 'reason': 'zero capacity', 'unchanged_bytes': True})
            # Noncanonical spelling must erase, even if its value is unchanged.
            unexpected = base.replace('12u32', '1__2u32')
            assert extract(base, unexpected, family) == (None, 'unexpected spelling')
            mismatch = base.replace('12u32', '13u32')
            assert extract(base, mismatch, family) == (None, 'reference mismatch')
            counts['controls_extraction_erasures'] = 2
            report['families'][family] = {'counts': counts, 'capacity': capacity,
                                         'states': cases, 'refusal_controls': refused_details}
        # Every transformed source is compiled and its returned array checked, including attacks.
        suite = []
        for i, (text, expected, family, n, state, stage) in enumerate(artifacts):
            suite.append(text.replace('specimen', f'case_{i}'))
            suite.append(f'#[test] fn check_{i}() {{ assert_eq!(case_{i}(), {expected}); }}\n')
        test_source = root / 'matrix.rs'
        test_source.write_text('\n'.join(suite))
        report['compiled_checks_per_profile'] = len(artifacts)
        for profile, flags in [('debug', ['-C', 'opt-level=0', '-C', 'overflow-checks=yes']),
                               ('release', ['-C', 'opt-level=3', '-C', 'overflow-checks=no'])]:
            executable = root / profile
            run(['rustc', '--edition=2021', '--target', target, '--test', str(test_source), *flags, '-o', str(executable)])
            result = run([str(executable)])
            assert f'{len(artifacts)} passed; 0 failed' in result.stdout
        for family in report['families'].values():
            family['counts']['attack_valid'] = family['counts']['completed']
    report['wall_seconds_including_tools'] = round(time.perf_counter()-started, 6)
    output = json.dumps(report, indent=2, sort_keys=True)+'\n'
    if args.output:
        args.output.write_text(output)
    print(json.dumps({k: v for k, v in report.items() if k != 'families'}, indent=2))
    for family, data in report['families'].items():
        print(family, json.dumps(data['counts'], sort_keys=True), 'refusal_controls=', len(data['refusal_controls']))


if __name__ == '__main__':
    main()
