"""Inspect the curated public evidence; never execute PDQ or fetch any source.

The raw upstream commit is deliberately absent. Commit-to-root binding is a
reported historical private verification, NOT a proof recomputed by this tool.
Optional source/reference arguments read already provisioned bytes only.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
PIN = '9f627fb1d6d2a4a26c9b5ee1d6ca5e5ccc8e06a2'
TREE = 'dbd86e307c396ab13c3d261126732be72163295e'
RAW_SHA256 = '7882c170759184eddf668891bb1311f65f7a214e00816b9a78e1e787eaf48079'
TREE_SHA256 = '74f080287b5ffc4a19ab277b729ccf04890e21107b3ff332c23474cb892d10d4'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def obj(kind, data):
    return hashlib.sha1(kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text())


def inspect(source=None, reference=None):
    manifest = load('public-package-sha256.json')
    require(manifest['packageVersion'] == 'pdq-curated-public-evidence-1', 'manifest version')
    files = manifest['files']
    require(isinstance(files, dict) and files, 'empty manifest')
    require('upstream-commit.txt' not in files and 'package-sha256.json' not in files,
            'private-package file in public manifest')
    require(all(p.is_file() and not p.is_symlink() for p in ROOT.iterdir()), 'public directory entry type')
    actual = {p.name for p in ROOT.iterdir()}
    require(actual == set(files) | {'public-package-sha256.json'}, 'public file inventory')
    for name, digest in files.items():
        require(Path(name).name == name and name not in ('.', '..'), 'manifest path')
        path = ROOT / name
        require(not path.is_symlink() and path.is_file(), 'manifest file type')
        require(sha(path.read_bytes()) == digest, 'package hash: ' + name)

    # These are consistency checks of a HISTORICAL REPORT, not commit hashing.
    verification = load('original-provenance-verification.json')
    require(verification['pin'] == verification['rawCommitGitSha1'] == PIN, 'reported pin')
    require(verification['rawCommitBytes'] == 1135 and verification['rawCommitSha256'] == RAW_SHA256,
            'reported private object identity')
    require(verification['treeHeader'] == verification['reconstructedRootTree'] == TREE,
            'reported root tree')
    proof = load('source-tree-proof.json')
    require(proof['root'] == TREE, 'declared root')
    trees = {t['path']: t for t in proof['trees']}
    require(len(trees) == len(proof['trees']) == 6 and trees['']['oid'] == TREE, 'tree inventory')
    for path, tree in trees.items():
        entries = sorted(tree['entries'], key=lambda e: (e['name'] + ('/' if e['mode'] == '040000' else '')).encode())
        require(len({e['name'] for e in entries}) == len(entries), 'duplicate tree entry')
        body = b''.join(e['mode'].lstrip('0').encode() + b' ' + e['name'].encode() + b'\0' + bytes.fromhex(e['oid']) for e in entries)
        require(obj('tree', body) == tree['oid'], 'tree object: ' + path)
        if not path:
            require(sha(body) == TREE_SHA256 == verification['rootTreeRawSha256'], 'root bytes')
        else:
            parent, _, name = path.rpartition('/')
            require(next(e['oid'] for e in trees[parent]['entries'] if e['name'] == name) == tree['oid'], 'tree chain')
    acquired = load('acquisition.json')['files']
    require(len(acquired) == 17, 'source subset count')
    for f in acquired:
        parent, _, name = f['path'].rpartition('/')
        require(next(e['oid'] for e in trees[parent]['entries'] if e['name'] == name) == f['gitBlobSha1'], 'leaf membership')
        if source is not None:
            data = (source / f['path']).read_bytes()
            require(len(data) == f['bytes'] and sha(data) == f['sha256'] and obj('blob', data) == f['gitBlobSha1'], 'provisioned source')
    if reference is not None:
        for f in load('python-source.json')['files']:
            require(sha((reference / f['path']).read_bytes()) == f['sha256'], 'provisioned reference')

    rows = load('comparison.json')['cases']
    names = ['orig', 'rot90', 'rot180', 'rot270', 'flipx', 'flipy', 'flipp', 'flipm']
    require(len(rows) == 6 and len({r['id'] for r in rows}) == 6, 'comparison input inventory')
    exact = quality = python_exact = complete = 0
    ids = load('original-artifact-identities.json')
    declared = {c['id']: c for c in load('declared-inputs.json')['cases']}
    require(set(declared) == {r['id'] for r in rows}, 'declared input inventory')
    for row in rows:
        require((row['width'], row['height']) == (declared[row['id']]['width'], declared[row['id']]['height']), 'declared input dimensions')
        for target in ['port', 'pythonVendor', 'cpp']:
            hashes = row[target]['hashes']
            require(set(hashes) == set(names) and all(re.fullmatch('[0-9a-f]{64}', h) for h in hashes.values()), 'hash inventory')
        distances = {n: (int(row['port']['hashes'][n], 16) ^ int(row['cpp']['hashes'][n], 16)).bit_count() for n in names}
        count = sum(d == 0 for d in distances.values())
        q = row['port']['quality'] == row['cpp']['quality']
        py = row['port'] == row['pythonVendor']
        require(distances == row['cppHammingByVariant'] and count == row['cppHashExactCount'], 'hash accounting')
        require(q == row['cppQualityExact'] and py == row['pythonExact'], 'quality accounting')
        require(row['inputSha256'] == ids['comparison/inputs/' + row['id'] + '.luma']['sha256'], 'reported input identity')
        require(row['inputBytes'] == 16 + 4 * row['width'] * row['height'], 'reported input size')
        exact += count
        quality += q
        python_exact += py
        complete += count == 8 and q
    for name, quality_value in [('constant127', 0), ('low-contrast', 11)]:
        row = next(r for r in rows if r['id'] == name)
        require(row['cppHashExactCount'] == 0 and row['port']['quality'] == row['cpp']['quality'] == quality_value, 'retained low-quality mismatch')
    expected = {'inputs': 6, 'variantComparisons': 48, 'cppHashesExact': 32,
                'cppQualityExact': 6, 'pythonPortVendorExact': 6, 'completeCppExactInputs': 4}
    require(load('comparison.json')['summary'] == expected and (exact, quality, python_exact, complete) == (32, 6, 6, 4), 'summary accounting')
    return {'publicFiles': len(files), 'trees': len(trees), 'sourceLeaves': len(acquired),
            'hashesExact': exact, 'hashesCompared': 48, 'qualityExact': quality,
            'commitToRootBinding': 'historically privately verified; not recomputed from public package',
            'pdqExecuted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--reference', type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.source, args.reference)
    except (ValueError, KeyError, TypeError, OSError, StopIteration) as exc:
        raise SystemExit('FAIL public evidence inspection: ' + str(exc)) from exc
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
