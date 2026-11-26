"""Check hand-written TS.2 selection decisions and supplemental stage-1 pairs.

This is a fixture adapter, not a product selector or JSX detector. The frozen
profile supplies the rules; expected decisions are committed independently.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_vectors as extraction  # noqa: E402


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_sources(doc):
    root = HERE.parents[1]
    required = {'profiles/typescript.md'} | {
        'test-vectors/extraction-typescript/' + n for n in
        ('ts.json', 'limits-ts.json', 'config-ts.json', 'config-ts-limit16.json')}
    require(set(doc['sourceSha256']) == required, 'incomplete source identity map')
    for name, digest in doc['sourceSha256'].items():
        require(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest,
                'source identity mismatch: ' + name)


def content(vector):
    parts = []
    for part in vector['inputParts']:
        if isinstance(part, str):
            parts.append(part)
        else:
            require(set(part) == {'text', 'repeat'} and isinstance(part['text'], str)
                    and type(part['repeat']) is int and 0 <= part['repeat'] <= 8192,
                    'invalid input part')
            parts.append(part['text'] * part['repeat'])
    return ''.join(parts).encode('utf-8')


def decision(name, data, jsx_known, variant=None):
    """Mirror only §2's stated predicates; avoid undefined overlapping decisions."""
    declaration = name.endswith(('.d.ts', '.d.mts', '.d.cts')) or bool(
        re.fullmatch(r'.*\.d\..*\.ts', name))
    if variant in ('no-d-mts', 'no-d-cts') and name.endswith('.d.' + variant[5:]):
        declaration = False
    if variant == 'no-declaration':
        declaration = False
    if variant == 'broad-declaration':
        declaration = '.d' in name
    if variant == 'no-declaration-pattern':
        declaration = name.endswith(('.d.ts', '.d.mts', '.d.cts'))
    window = data[:2048]
    if variant == 'window2047':
        window = data[:2047]
    if variant == 'window2049':
        window = data[:2049]
    if variant == 'character-window':
        window = data.decode('utf-8')[:2048].encode('utf-8')
    if variant == 'all-file-marker':
        window = data
    markers = (b'@generated', b'DO NOT EDIT')
    if variant == 'no-at-generated':
        markers = (b'DO NOT EDIT',)
    if variant == 'no-do-not-edit':
        markers = (b'@generated',)
    generated = any(marker in window for marker in markers)
    if variant == 'no-generated':
        generated = False
    if variant == 'casefold-marker':
        generated = any(marker.lower() in window.lower() for marker in markers)
    if variant == 'partial-marker':
        generated = b'@generate' in window or b'DO NOT EDI' in window
    suffix = name.endswith(('.min.js', '.min.mjs', '.min.cjs'))
    if variant == 'no-minified-suffix':
        suffix = False
    if variant == 'broad-minified-suffix':
        suffix = '.min' in name
    separators = r'\r\n|[\r\n\u2028\u2029]'
    if variant == 'lf-only':
        separators = r'\n'
    if variant == 'no-lf':
        separators = r'[\r\u2028\u2029]'
    if variant == 'no-ls':
        separators = r'\r\n|[\r\n\u2029]'
    if variant == 'no-ps':
        separators = r'\r\n|[\r\n\u2028]'
    lines = re.split(separators, data.decode('utf-8'))
    lengths = [len(line.encode('utf-8')) for line in lines]
    if variant == 'character-lines':
        lengths = list(map(len, lines))
    long_line = any(n > 4096 for n in lengths)
    if variant == 'inclusive-line':
        long_line = any(n >= 4096 for n in lengths)
    if variant == 'no-line-limit':
        long_line = False
    excluded = declaration or generated or suffix or long_line
    deferred = name.endswith(('.tsx', '.jsx')) or jsx_known
    if variant == 'no-defer':
        deferred = False
    # The fixtures do not invent precedence between excluded and deferred files.
    require(not (excluded and deferred), 'overlapping rules need a specification decision')
    return 'exclude' if excluded else 'defer' if deferred else 'extract'


REQUIRED = {'declaration.d.ts', 'declaration.d.mts', 'declaration.d.cts',
            'declaration.d.css.ts', 'generated-end2048', 'generated-end2049',
            'do-not-edit-end2048', 'do-not-edit-end2049', 'generated-unicode-boundary',
            'line4096', 'line4097', 'utf8-line4097', 'split-cr', 'split-ls', 'split-ps',
            'minified.min.js', 'minified.min.mjs', 'minified.min.cjs',
            'defer.tsx', 'defer.jsx', 'self-closing-jsx'}


def check_selection(doc, variant=None):
    ids = set()
    for v in doc['vectors']:
        require(v['id'] not in ids, 'duplicate selection id')
        ids.add(v['id'])
        require(v['derivation'] == 'hand' and v['rationale'], 'missing hand judgment')
        require(type(v['jsxKnown']) is bool and '/' not in v['name'],
                'only basenames and explicit JSX knowledge are supported')
        got = decision(v['name'], content(v), v['jsxKnown'], variant)
        require(got == v['expected'], f"{v['id']}: {got} != {v['expected']}")
    require(REQUIRED <= ids, 'missing required selection boundary case')
    return len(ids)


VARIANTS = ('no-declaration', 'no-d-mts', 'no-d-cts', 'broad-declaration', 'no-declaration-pattern',
            'window2047', 'window2049', 'character-window', 'all-file-marker', 'no-generated', 'no-at-generated', 'no-do-not-edit',
            'casefold-marker', 'partial-marker', 'no-minified-suffix',
            'broad-minified-suffix', 'lf-only', 'no-lf', 'no-ls', 'no-ps',
            'character-lines', 'inclusive-line', 'no-line-limit', 'no-defer')


def check_pairs(doc):
    original, cfg = extraction.load('ts.json')
    limits, _ = extraction.load('limits-ts.json')
    require((doc['profile'], doc['profileVersion'], doc['configSha256']) ==
            ('ts-tokens', 'draft-2', original['configSha256']), 'pair config mismatch')
    errors = {v['id']: v for d in (original, limits) for v in d['vectors']
              if v['result']['status'] == 'error'}
    supplemental = doc['rejections']
    require(len({v['id'] for v in supplemental}) == len(supplemental), 'duplicate rejection id')
    require(not set(errors).intersection(v['id'] for v in supplemental), 'rejection id collision')
    require(all(v['result']['status'] == 'error' for v in supplemental), 'partner is not error')
    extraction.run_file({'vectors': supplemental}, cfg)
    errors.update((v['id'], v) for v in supplemental)
    positives = {v['id']: v for d in (original, limits) for v in d['vectors']
                 if v['result']['status'] != 'error'}
    overrides = doc['pairingOverrides']
    require(set(overrides) == {'ts-html-comment', 'ts-type-assertion'}, 'missing or extra pairing override')
    require(set(overrides.values()) == {v['id'] for v in supplemental}, 'unused or missing rejection')
    for vid, v in positives.items():
        partner = overrides.get(vid, v['pairedRejection'])
        require(partner in errors, f'{vid}: no stage-1 rejection partner')
    # Pin the deliberate malformed suffix, so unrelated errors cannot masquerade
    # as evidence repairing these two specific pairing gaps.
    for vid, suffix, code in [('ts-html-comment', '/*', 'unterminated-comment'),
                              ('ts-type-assertion', ')', 'unbalanced-delimiter')]:
        base = positives[vid]['inputText']
        v = errors[overrides[vid]]
        require(v['inputText'] == base + suffix and
                v['result']['error'] == {'code': code, 'offset': len(base.encode())},
                vid + ': incorrect deliberate rejection partner')
    return len(positives), len(supplemental)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, default=HERE / 'selection-decisions.json')
    parser.add_argument('--pairs', type=Path, default=HERE / 'stage1-rejection-pairs.json')
    args = parser.parse_args()
    selection = json.loads(args.selection.read_text())
    pairs = json.loads(args.pairs.read_text())
    check_sources(selection)
    check_sources(pairs)
    n = check_selection(selection)
    for variant in VARIANTS:
        try:
            check_selection(selection, variant)
        except ValueError:
            continue
        raise ValueError('wrong selector accepted: ' + variant)
    npos, nerr = check_pairs(pairs)
    print(f'PASS TS.2: {n} hand selection decisions; {len(VARIANTS)}/{len(VARIANTS)} wrong selectors rejected; '
          f'{npos}/{npos} stage-1 positives paired; {nerr} supplemental rejection inputs')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, extraction.CheckError) as e:
        print('FAIL TS.2:', e)
        sys.exit(1)
