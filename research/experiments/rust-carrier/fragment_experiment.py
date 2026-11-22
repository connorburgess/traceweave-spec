#!/usr/bin/env python3
"""Closed synthetic hosts, reference-assisted raw symbols; never executes input."""
import argparse
import hashlib
import json
import platform
import re
import tempfile
import time
from pathlib import Path

import experiment as carrier

BANNER = '// café\n'  # The sole permitted non-ASCII/comment prefix, to test byte offsets.
SPACE = re.compile(r'[ \t\r\n]*')
MODULE = re.compile(r'mod ([a-z][a-z0-9_]*)[ \t\r\n]*\{')
FUNCTION = re.compile(r'fn specimen\(\)[ \t\r\n]*->[ \t\r\n]*\[u32;[ \t\r\n]*([0-4])\][ \t\r\n]*\{([^{}]*)\}')
UNRELATED = re.compile(r'fn host_value\(\) -> u32 \{ 999u32 \}')
DIRECT = re.compile(r'[ \t\r\n]*\[([^\[\]]*)\][ \t\r\n]*')
LITERAL_LET = re.compile(r'let ([a-d]): u32 = ([0-9][0-9_]*u32);')
CONTEXTS = frozenset(('copied', 'fragment', 'left', 'right', 'moved', 'origin', 'partial', 'other'))
ORACLE = [12, 23, 34, 45]  # External task oracle, never calculated from donor/candidate text.


def byte_span(source, start, end):
    return [len(source[:start].encode('utf-8')), len(source[:end].encode('utf-8'))]


def host_nodes(source, boundary=carrier.BOUNDARY):
    """Validate the entire closed host; do not search inside arbitrary Rust text."""
    if boundary != carrier.BOUNDARY:
        raise ValueError('unsupported build/source boundary')
    pos = len(BANNER) if source.startswith(BANNER) else 0
    if not source[pos:].isascii():
        raise ValueError('unsupported non-ASCII host text')
    nodes, modules, unrelated_seen = [], set(), False
    while True:
        pos = SPACE.match(source, pos).end()
        if pos == len(source):
            return nodes
        scalar = UNRELATED.match(source, pos)
        if scalar:
            if unrelated_seen:
                raise ValueError('duplicate unrelated item')
            unrelated_seen, pos = True, scalar.end()
            continue
        module = MODULE.match(source, pos)
        if not module or module[1] not in CONTEXTS or module[1] in modules:
            raise ValueError('unsupported or duplicate host module')
        modules.add(module[1])
        start = SPACE.match(source, module.end()).end()
        function = FUNCTION.match(source, start)
        if not function:
            raise ValueError('unsupported or incomplete host function')
        text = function[0]
        try:
            bindings, returned = carrier.parse(text, carrier.BOUNDARY)
            values = {n: v for n, v, _ in bindings}
            expected = [values[n] for n in returned]
            kind = 'carrier'
        except ValueError:
            # One independent same-task control: a direct array of suffixed literals.
            direct = DIRECT.fullmatch(function[2])
            items = direct[1].strip() if direct else ''
            decimal = r'(?:0|[1-9][0-9]*)u32'
            if not direct or (items and not re.fullmatch(decimal+r'(?:[ \t\r\n]*,[ \t\r\n]*'+decimal+r')*[ \t\r\n]*,?', items)):
                raise ValueError('unsupported host function body') from None
            expected = [int(x.strip()[:-3]) for x in items.rstrip(',').split(',')] if items else []
            if len(expected) != int(function[1]) or any(v > 2**32-1 for v in expected):
                raise ValueError('invalid direct-return fixture')
            kind = 'direct_return'
        end = SPACE.match(source, function.end()).end()
        if source[end:end+1] != '}':
            raise ValueError('unsupported trailing module content')
        nodes.append({'context': module[1], 'start': start, 'end': function.end(),
                      'source': text, 'kind': kind, 'expected_values': expected})
        pos = end + 1


def align(reference, candidate, family, expected_context=None, boundary=carrier.BOUNDARY):
    """One query, one reference, all matching anchors; no execution or file reads."""
    result = {'status': 'abstain', 'reason': None, 'state': None, 'symbols': [],
              'function_span_bytes': None, 'context': None, 'matching_anchors': 0,
              'candidate_sha256': hashlib.sha256(candidate.encode('utf-8')).hexdigest()}
    try:
        rb, rr, _, states = carrier.inspect(reference, family)
        if states < 2:
            raise ValueError('zero reference capacity')
        key = sorted((n, v) for n, v, _ in rb), rr
        nodes = host_nodes(candidate, boundary)
        matches = []
        for node in nodes:
            if node['kind'] != 'carrier':
                continue
            cb, cr, _, _ = carrier.inspect(node['source'], family)
            if (sorted((n, v) for n, v, _ in cb), cr) == key:
                matches.append(node)
        result['matching_anchors'] = len(matches)
        if not matches:
            result['reason'] = 'no_complete_reference_anchor'
            return result
        if len(matches) != 1:
            result['reason'] = 'ambiguous_reference_anchors'
            return result
        node = matches[0]
        if expected_context is not None and node['context'] != expected_context:
            result['reason'] = 'context_mismatch'
            return result
        state, error = carrier.extract(reference, node['source'], family)
        if error:
            raise ValueError(error)
        literals = list(LITERAL_LET.finditer(node['source']))
        symbols = []
        if family == 'order':
            begin = node['start'] + literals[0].start()
            end = node['start'] + literals[-1].end()
            symbols.append({'unit': 'permutation_rank', 'raw': state,
                            'span_bytes': byte_span(candidate, begin, end)})
        else:
            for literal in sorted(literals, key=lambda m: m[1]):
                value = int(literal[2][:-3].replace('_', ''))
                if value < 10:
                    continue
                begin, end = node['start'] + literal.start(2), node['start'] + literal.end(2)
                symbols.append({'unit': 'spelling_bit', 'name': literal[1],
                                'raw': int(literal[2] == carrier.token(value, 1)),
                                'span_bytes': byte_span(candidate, begin, end)})
        result.update(status='raw_state', state=state, symbols=symbols,
                      function_span_bytes=byte_span(candidate, node['start'], node['end']),
                      context=node['context'])
        return result
    except ValueError as error:
        result['reason'] = str(error)
        return result


def host(functions):
    return BANNER + 'fn host_value() -> u32 { 999u32 }\n' + ''.join(
        f'mod {context} {{\n{text.rstrip()}\n}}\n' for context, text in functions)


def independent_source(family, donor=None, changed_values=False):
    """Construct from fixed independent values; transfer only ordering or separator bits."""
    values = {'a': 13, 'b': 24, 'c': 35, 'd': 46} if changed_values else {'a': 12, 'b': 23, 'c': 34, 'd': 45}
    names, bits = list(values), {n: 0 for n in values}
    if donor is not None:
        bindings, _ = carrier.parse(donor, carrier.BOUNDARY)
        if family == 'order':
            names = [n for n, _, _ in bindings]
        else:
            bits = {n: int('_' in t) for n, _, t in bindings}
    # Deliberately construct fresh text instead of copying the donor function.
    declarations = '\n'.join(f'let {n}: u32 = {carrier.token(values[n], bits[n])};' for n in names)
    return 'fn specimen() -> [u32; 4] {\n'+declarations+'\n[a,b,c,d]\n}\n'


def make_cases():
    reference = carrier.fixture(4)
    cases = []
    for family, states in [('order', [0, 1, 23]), ('spelling', [0, 1, 15])]:
        for state in states:
            donor, embedding_status, error = carrier.embed(reference, family, state)
            assert error is None
            donor_bindings, donor_returned = carrier.parse(donor, carrier.BOUNDARY)
            partial = carrier.render([b for b in donor_bindings if b[0] != 'd'],
                                     [n for n in donor_returned if n != 'd'])
            alternate, _, _ = carrier.embed(reference, family, 1 if state == 0 else 0)
            direct = 'fn specimen() -> [u32; 4] { [12u32,23u32,34u32,45u32] }\n'
            items = [
                ('whole_copy', host([('copied', donor)]), None, state, None),
                ('incomplete_run', host([('fragment', partial)]), None, None, 'no_complete_reference_anchor'),
                ('cut_excerpt', donor[donor.index('let '):donor.rindex('[')], None, None, 'unsupported or duplicate host module'),
                ('duplicate_anchor', host([('left', donor), ('right', donor)]), None, None, 'ambiguous_reference_anchors'),
                ('conflicting_duplicate', host([('left', donor), ('right', alternate)]), None, None, 'ambiguous_reference_anchors'),
                ('changed_context_open', host([('moved', donor)]), None, state, None),
                ('changed_context_strict', host([('moved', donor)]), 'origin', None, 'context_mismatch'),
                ('independent_same_task', host([('origin', independent_source(family))]), 'origin', 0, None),
                ('independent_direct_return', host([('origin', direct)]), None, None, 'no_complete_reference_anchor'),
                ('signal_only_transfer', host([('origin', independent_source(family, donor))]), 'origin', state, None),
                ('signal_transfer_changed_values', host([('origin', independent_source(family, donor, changed_values=True))]), 'origin', None, 'no_complete_reference_anchor'),
                ('unexpected_spelling', host([('origin', donor.replace('12u32', '1__2u32').replace('1_2u32', '1__2u32'))]), None, None, 'unexpected spelling'),
            ]
            for category, candidate, context, expected, reason in items:
                # Explicit fixture oracle by construction; never infer expected behavior
                # from the transformed donor or from parsed candidate return values.
                contexts = {
                    'whole_copy': ['copied'], 'incomplete_run': ['fragment'],
                    'cut_excerpt': [], 'duplicate_anchor': ['left', 'right'],
                    'conflicting_duplicate': ['left', 'right'],
                    'changed_context_open': ['moved'], 'changed_context_strict': ['moved'],
                    'independent_same_task': ['origin'], 'independent_direct_return': ['origin'],
                    'signal_only_transfer': ['origin'], 'signal_transfer_changed_values': ['origin'],
                    'unexpected_spelling': ['origin'],
                }[category]
                expected_values = ([12, 23, 34] if category == 'incomplete_run' else
                                   [13, 24, 35, 46] if category == 'signal_transfer_changed_values' else ORACLE)
                cases.append({'family': family, 'donor_state': state, 'embedding_status': embedding_status,
                              'category': category, 'candidate': candidate, 'expected_context': context,
                              'expected_state': expected, 'expected_reason': reason,
                              'expected_values_by_context': {name: list(expected_values) for name in contexts}})
    return reference, cases


def compile_generated_cases(cases):
    """Called only by main with make_cases output. No CLI input-source path exists."""
    parts, expected_checks = [], 0
    for index, case in enumerate(cases):
        if case['category'] == 'cut_excerpt':
            continue  # Deliberately not a complete Rust program.
        source = case['candidate']
        nodes = host_nodes(source)
        oracle = case['expected_values_by_context']
        assert {node['context'] for node in nodes} == set(oracle)
        for node in reversed(nodes):
            assert node['expected_values'] == oracle[node['context']]
            test = f'\n#[test] fn check() {{ assert_eq!(specimen(), {oracle[node["context"]]}); }}\n'
            source = source[:node['end']] + test + source[node['end']:]
        parts.append(f'mod case_{index} {{\n{source}\n}}\n')
        expected_checks += len(nodes)
    compiler = carrier.run(['rustc', '--version', '--verbose']).stdout.strip()
    target = re.search(r'^host: (.*)$', compiler, re.M)[1]
    with tempfile.TemporaryDirectory(prefix='traceweave-rust-fragment-') as directory:
        path = Path(directory)
        source_path = path / 'trusted_matrix.rs'
        source_path.write_text('\n'.join(parts))
        for name, flags in [('debug', ['-C', 'opt-level=0', '-C', 'overflow-checks=yes']),
                            ('release', ['-C', 'opt-level=3', '-C', 'overflow-checks=no'])]:
            executable = path / name
            carrier.run(['rustc', '--edition=2021', '--target', target, '--test', str(source_path), *flags, '-o', str(executable)])
            output = carrier.run([str(executable)]).stdout
            assert f'{expected_checks} passed; 0 failed' in output
    return {'compiler': compiler, 'target': target, 'generated_hosts_compiled': len(parts),
            'checks_per_profile': expected_checks, 'profiles': ['debug', 'release']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    reference, cases = make_cases()
    records, totals = [], {}
    for case in cases:
        candidate = case['candidate']
        result = align(reference, candidate, case['family'], case['expected_context'])
        assert result == align(reference, candidate, case['family'], case['expected_context'])
        assert (result['state'], result['reason']) == (case['expected_state'], case['expected_reason'])
        if result['status'] == 'raw_state':
            start, end = result['function_span_bytes']
            fragment = candidate.encode('utf-8')[start:end].decode('utf-8')
            assert carrier.extract(reference, fragment, case['family'])[0] == result['state']
            assert start != candidate.index('fn specimen')  # UTF-8 prefix is two bytes, not one.
            for symbol in result['symbols']:
                begin, finish = symbol['span_bytes']
                assert start <= begin < finish <= end
                assert candidate.encode('utf-8')[begin:finish].decode('utf-8')
        group = totals.setdefault(case['family'], {'queries': 0, 'raw_states': 0, 'abstentions': 0,
                                                   'localized_symbols': 0, 'expected_results': 0})
        group['queries'] += 1
        group['raw_states' if result['status'] == 'raw_state' else 'abstentions'] += 1
        group['localized_symbols'] += len(result['symbols'])
        group['expected_results'] += 1
        records.append({**case, 'result': result})
    report = {'boundary': carrier.BOUNDARY, 'reference_source': reference,
              'python': platform.python_version(),
              'reference_sha256': hashlib.sha256(reference.encode()).hexdigest(),
              'totals': totals, 'records': records,
              'compilation': compile_generated_cases(cases), 'identity_metrics': 'unavailable',
              'wall_seconds': round(time.perf_counter()-started, 6)}
    if args.output:
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('records', 'reference_source')}, indent=2))


if __name__ == '__main__':
    main()
