#!/usr/bin/env python3
"""v1 conservative lexical census; no Rust parsing, expansion, type or build checks."""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import re

RULE_VERSION = 'rust-census-v1'
CARRIER = Path(__file__).resolve().parents[1] / 'rust-carrier' / 'experiment.py'
spec = importlib.util.spec_from_file_location('reviewed_carrier', CARRIER)
carrier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(carrier)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, relative):
    """Static corpus path guard: reject unsafe inventory and any symlink component."""
    if not relative or '\\' in relative or any(p in ('', '.', '..') for p in relative.split('/')) or Path(relative).is_absolute():
        raise ValueError('unsafe inventory path')
    base = root.absolute()
    if '..' in base.parts:
        raise ValueError('unsafe root path')
    current = Path(base.anchor)
    for component in (*base.parts[1:], *Path(relative).parts):
        current /= component
        if current.is_symlink():
            raise ValueError('symlink component not traversed')
    return current


def lex(text):
    """Return nontrivia tokens with original UTF-8 byte spans; fail closed on strings/comments."""
    tokens, i, offsets = [], 0, [0]
    for c in text:
        offsets.append(offsets[-1] + len(c.encode('utf-8')))
    while i < len(text):
        start = i
        if text[i].isspace():
            i += 1
            continue
        if text.startswith('//', i):
            end = text.find('\n', i)
            i = len(text) if end < 0 else end+1
            continue
        if text.startswith('/*', i):
            i, depth = i+2, 1
            while depth and i < len(text):
                if text.startswith('/*', i):
                    i, depth = i+2, depth+1
                elif text.startswith('*/', i):
                    i, depth = i+2, depth-1
                else:
                    i += 1
            if depth:
                raise ValueError('unterminated block comment')
            continue
        raw = re.match(r'(?:br|cr|r)(#{0,255})"', text[i:])
        if raw:
            ending = '"'+raw[1]
            end = text.find(ending, i+raw.end())
            if end < 0:
                raise ValueError('unterminated raw string')
            i = end+len(ending)
            tokens.append(('literal_opaque', '', offsets[start], offsets[i]))
            continue
        quoted = re.match(r'(?:b|c)?"', text[i:])
        if quoted:
            i += quoted.end()
            while i < len(text):
                if text[i] == '\\':
                    i += 2
                elif text[i] == '"':
                    i += 1
                    break
                else:
                    i += 1
            else:
                raise ValueError('unterminated string')
            tokens.append(('literal_opaque', '', offsets[start], offsets[i]))
            continue
        # Complete char/byte-char tokens; otherwise apostrophe is a lifetime/label token.
        char = re.match(r"b?'(?:\\(?:u\{[0-9A-Fa-f_]+\}|x[0-9A-Fa-f]{2}|[^\n])|[^'\\\n])'", text[i:])
        if char:
            i += char.end()
            tokens.append(('literal_opaque', '', offsets[start], offsets[i]))
            continue
        ident = re.match(r'(?:r#)?(?:[^\W\d]|_)[\w]*', text[i:], re.UNICODE)
        if ident:
            i += ident.end()
            tokens.append(('identifier', ident[0], offsets[start], offsets[i]))
            continue
        number = re.match(r'[0-9][A-Za-z0-9_]*(?:\.[0-9][A-Za-z0-9_]*)?', text[i:])
        if number:
            i += number.end()
            tokens.append(('number', number[0], offsets[start], offsets[i]))
            continue
        i += 1
        tokens.append(('punctuation', text[start:i], offsets[start], offsets[i]))
    return tokens


def canonical_u32(token):
    if not re.fullmatch(r'[0-9][0-9_]*u32', token):
        return None
    digits = token[:-3].replace('_', '')
    if not re.fullmatch(r'0|[1-9][0-9]*', digits):
        return None
    value = int(digits)
    if value > 2**32-1:
        return None
    allowed = [carrier.token(value, 0)] + ([carrier.token(value, 1)] if value >= 10 else [])
    return value if token in allowed else None


def inspect_file(data):
    text = data.decode('utf-8')
    tokens = lex(text)
    values = [t[1] for t in tokens]
    inline_test_markers = sum(values[i:i+4] in (['#', '[', 'test', ']'], ['cfg', '(', 'test', ')'])
                              for i in range(max(0, len(values)-3)))
    fn = [t for t in tokens if t[:2] == ('identifier', 'fn')]
    numbers = [t for t in tokens if t[0] == 'number']
    spell = [t for t in numbers if (v := canonical_u32(t[1])) is not None and v >= 10]
    lets = []
    for i in range(len(tokens)-6):
        t = tokens[i:i+7]
        if (t[0][1] == 'let' and t[1][0] == 'identifier' and t[2][1] == ':'
                and t[3][1] == 'u32' and t[4][1] == '=' and t[6][1] == ';'
                and t[5][0] == 'number' and canonical_u32(t[5][1]) is not None):
            lets.append({'token_start': i, 'token_end': i+7, 'span_bytes': [t[0][2], t[-1][3]]})
    runs = []
    for item in lets:
        if runs and runs[-1]['token_end'] == item['token_start']:
            runs[-1]['token_end'] = item['token_end']
            runs[-1]['span_bytes'][1] = item['span_bytes'][1]
            runs[-1]['declarations'] += 1
        else:
            runs.append(dict(item, declarations=1))
    runs = [r for r in runs if r['declarations'] >= 2]
    try:
        carrier.inspect(text, 'order')
        shape, refusal = True, None
    except ValueError as error:
        shape, refusal = False, str(error)
    return {'lexical_fn_tokens': len(fn), 'number_tokens': len(numbers),
            'potential_spelling_tokens': len(spell), 'potential_literal_declarations': len(lets),
            'potential_adjacent_runs': len(runs), 'exact_whole_file_grammar_shape': int(shape),
            'exact_eligible': 0, 'exact_boundary': 'not_established', 'grammar_refusal': refusal,
            'markers': {'macro_bang_tokens': values.count('!'), 'unsafe_tokens': values.count('unsafe'),
                        'cfg_tokens': values.count('cfg'), 'attribute_hash_tokens': values.count('#'),
                        'inline_test_marker_tokens': inline_test_markers},
            'local_offsets': {'fn': [[t[2], t[3]] for t in fn],
                              'spelling': [[t[2], t[3]] for t in spell], 'declarations': lets, 'runs': runs}}


def classify(path):
    parts = Path(path).parts
    if any(p in ('vendor', 'generated', 'target', 'third_party') for p in parts):
        return 'excluded_vendor_generated'
    if path.startswith('src/'):
        return 'primary_src_may_contain_inline_tests'
    if parts[0] in ('tests', 'benches', 'examples', 'fuzz'):
        return 'auxiliary_'+parts[0]
    return 'excluded_other_rust'


def scan(root):
    inventory = json.loads(safe_path(root, 'inventory.json').read_text())
    records = []
    for item in inventory['rust_files']:
        record = dict(item, classification=classify(item['path']))
        if item['mode'] == '120000':
            record['failure'] = 'symlink_not_traversed'
        elif not item['downloaded']:
            record['failure'] = 'excluded_not_collected'
        else:
            try:
                path = safe_path(root/'source', item['path'])
                data = path.read_bytes()
                record['sha256'] = sha(data)
                if record['sha256'] != item['sha256']:
                    raise ValueError('download digest mismatch')
                if re.search(rb'@generated|automatically generated|do not edit', b'\n'.join(data.splitlines()[:10]), re.I):
                    record['classification'] = 'excluded_generated_banner_heuristic'
                    record['failure'] = 'excluded_generated_banner'
                else:
                    record.update(inspect_file(data))
            except (OSError, UnicodeError, ValueError) as error:
                record['failure'] = str(error)
        records.append(record)
    groups = {}
    counts = ['lexical_fn_tokens', 'number_tokens', 'potential_spelling_tokens',
              'potential_literal_declarations', 'potential_adjacent_runs',
              'exact_whole_file_grammar_shape', 'exact_eligible']
    for record in records:
        group = groups.setdefault(record['classification'], dict(files=0, bytes=0, inspected=0, failures=0,
                                                                 **{k: 0 for k in counts}))
        group['files'] += 1
        group['bytes'] += record['size']
        group['failures' if 'failure' in record else 'inspected'] += 1
        for key in counts:
            group[key] += record.get(key, 0)
    return {'rule_version': RULE_VERSION, 'scanner_sha256': sha(Path(__file__).read_bytes()),
            'carrier_sha256': sha(CARRIER.read_bytes()), 'groups': groups, 'records': records,
            'failure_reasons': dict(collections.Counter(r['failure'] for r in records if 'failure' in r)),
            'grammar_refusal_reasons': dict(collections.Counter(r['grammar_refusal'] for r in records if r.get('grammar_refusal')))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text())
    if sha(Path(__file__).read_bytes()) != freeze['scanner_sha256'] or sha(CARRIER.read_bytes()) != freeze['carrier_sha256']:
        raise SystemExit('frozen scanner/carrier mismatch; do not silently revise census')
    result = scan(args.root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result['groups'], indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
