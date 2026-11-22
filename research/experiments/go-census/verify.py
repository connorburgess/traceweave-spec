"""Independent read-only inventories; local audit coordinates, no source publication."""
import hashlib
import json
from pathlib import Path
import re
import tarfile

BASE = Path('.local/go-census')
OUT = Path('research/experiments/go-census')
manifest = json.loads((OUT / 'manifest.json').read_text())
assert hashlib.sha256((OUT / 'main.go').read_bytes()).hexdigest() == manifest['scannerSHA256']
checks = []
audit = []
for repo in manifest['repositories']:
    name = repo['id']
    root = BASE / 'sources' / name
    raw = json.loads((BASE / f'{name}-details.json').read_text())
    summary = json.loads((OUT / f'{name}-summary.json').read_text())
    assert raw['ScannerSHA256'] == summary['ScannerSHA256'] == manifest['scannerSHA256']
    files = {f['Path']: f for f in raw['Files']}
    paths = {str(p.relative_to(root)): p for p in root.rglob('*.go')
             if p.is_file() and not p.is_symlink()}
    assert paths.keys() == files.keys()
    archive_path = BASE / 'archives' / f"{name}-{repo['commit']}.tar.gz"
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == repo['archiveSHA256']
    with tarfile.open(archive_path, 'r:gz') as archive:
        archive_go = {'/'.join(m.name.split('/')[1:]): m.size for m in archive
                      if m.isfile() and m.name.endswith('.go')}
        for member in archive:
            if member.isfile() and member.name.endswith('.go'):
                path = '/'.join(member.name.split('/')[1:])
                assert hashlib.sha256(archive.extractfile(member).read()).hexdigest() == files[path]['SHA256']
    assert archive_go == {p: f['Bytes'] for p, f in files.items()}
    for p, f in files.items():
        assert hashlib.sha256(paths[p].read_bytes()).hexdigest() == f['SHA256']
    generated = [p for p in paths if re.search(rb'^// Code generated .* DO NOT EDIT\.$', paths[p].read_bytes(), re.M)]
    class_inventory = {}
    for cls in sorted({f['Class'] for f in files.values()}):
        selected = [(paths[p], f) for p, f in files.items() if f['Class'] == cls]
        regex_count = sum(len(re.findall(rb'^func\s+', p.read_bytes(), re.M)) for p, f in selected)
        ast_count = sum(len(f['Functions']) for p, f in selected)
        # Two apparent declarations in hey's vendored generator are inside its
        # testHeader raw string, manually checked. Never execute that generator.
        explained = 2 if name == 'hey' and cls == 'dependency' else 0
        assert regex_count - ast_count == explained
        class_inventory[cls] = {'files': len(selected), 'regexFunctionLines': regex_count,
                                'ASTDeclarations': ast_count, 'explainedRawStringLines': explained}
    choices = []
    reasons = sorted({fn['ShapeReason'] for f in files.values() if f['Class'] == 'primary' for fn in f['Functions']})
    for reason in reasons:
        options = [(f, fn) for f in files.values() if f['Class'] == 'primary'
                   for fn in f['Functions'] if fn['ShapeReason'] == reason]
        for f, fn in options[:2]:
            choices.append({'category': reason, 'path': f['Path'], 'span': fn['Span'],
                            'sha256': f['SHA256'], 'function': fn['Name']})
    for f in files.values():
        if f['Class'] != 'primary':
            continue
        for r in f['Runs']:
            data = paths[f['Path']].read_bytes()
            span = r['Span']
            assert len(data[:span['Start']].decode()) <= span['Start']
            # Audited candidates are singleton decimal literal bindings only.
            assert r['Length'] == 1
            assert re.fullmatch(rb'[a-z][a-z0-9]* := (0|[1-9][0-9]*)', data[span['Start']:span['End']])
            choices.append({'category': 'potential_singleton', 'path': f['Path'],
                            'span': span, 'sha256': f['SHA256'],
                            'prefixBytes': span['Start'],
                            'prefixCodepoints': len(data[:span['Start']].decode())})
    audit.append({'repository': name, 'selection': 'First two per observed primary shape-refusal category, all primary potential runs',
                  'samples': choices, 'exactAcceptedSamples': 0})
    checks.append({'repository': name, 'files': len(paths), 'bytes': sum(p.stat().st_size for p in paths.values()),
                   'fileDigestChecks': len(paths), 'archiveEntrySizeChecks': len(paths),
                   'classInventory': class_inventory, 'generatedHeaderFiles': len(generated),
                   'generatedDependencyFiles': sum(files[p]['Class'] == 'dependency' for p in generated),
                   'auditedPrimaryRefusals': sum(x['category'] != 'potential_singleton' for x in choices),
                   'auditedPrimaryPotentials': sum(x['category'] == 'potential_singleton' for x in choices)})
(BASE / 'audit-samples.json').write_text(json.dumps(audit, indent=2) + '\n')
(OUT / 'verification.json').write_text(json.dumps(checks, indent=2) + '\n')
print(json.dumps(checks, indent=2))
