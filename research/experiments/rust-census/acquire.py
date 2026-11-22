#!/usr/bin/env python3
"""Fetch pinned licensed source bytes only. No upstream code/commands are executed."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib
import urllib.parse
import urllib.request

import scanner


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'traceweave-source-only-census-v1'})
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read()


def acquire(manifest_path, freeze_path, local_root):
    manifest = json.loads(manifest_path.read_text())
    freeze = json.loads(freeze_path.read_text())
    if scanner.sha(Path(scanner.__file__).read_bytes()) != freeze['scanner_sha256'] or scanner.sha(scanner.CARRIER.read_bytes()) != freeze['carrier_sha256']:
        raise SystemExit('scanner is not frozen revision')
    # Require the corpus to remain beneath the existing ignored .local directory.
    workspace = Path(__file__).resolve().parents[3]
    local_root = local_root.absolute()
    if not local_root.is_relative_to(workspace/'.local'):
        raise SystemExit('acquisition root must be beneath ignored workspace .local')
    probe = scanner.safe_path(local_root, 'ignore-probe.rs')
    subprocess.run(['git', 'check-ignore', '-v', str(probe)], cwd=workspace, check=True)
    for repo in manifest['repositories']:
        commit, name = repo['commit'], repo['repository']
        base = scanner.safe_path(local_root, repo['local_id'])
        base.mkdir(parents=True, exist_ok=True)
        raw = f'https://raw.githubusercontent.com/{name}/{commit}/'
        license_records = []
        # Verify known license bytes before any Rust sources are downloaded.
        for license_file in repo['licenses']:
            data = fetch(raw+license_file['path'])
            if scanner.sha(data) != license_file['sha256']:
                raise SystemExit('upstream license digest mismatch')
            dest = scanner.safe_path(base, 'metadata/'+license_file['path'])
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            license_records.append(license_file)
        cargo = fetch(raw+'Cargo.toml')
        metadata = tomllib.loads(cargo.decode('utf-8'))
        if metadata['package'].get('license') != repo['cargo_license']:
            raise SystemExit('unexpected Cargo license; review before acquisition')
        scanner.safe_path(base, 'metadata/Cargo.toml').write_bytes(cargo)
        tree_data = fetch(f'https://api.github.com/repos/{name}/git/trees/{commit}?recursive=1')
        tree = json.loads(tree_data)
        if tree.get('truncated'):
            raise SystemExit('truncated Git tree')
        scanner.safe_path(base, 'api-tree.json').write_bytes(tree_data)
        files = []
        for item in tree['tree']:
            if not item['path'].endswith('.rs'):
                continue
            classification = scanner.classify(item['path'])
            record = {'path': item['path'], 'size': item.get('size', 0), 'mode': item['mode'],
                      'git_blob_sha1': item['sha'], 'downloaded': False}
            # Validate every inventory path even if excluded or a symlink.
            destination = scanner.safe_path(base, 'source/'+item['path'])
            if item['type'] == 'blob' and item['mode'] != '120000' and not classification.startswith('excluded_'):
                data = fetch(raw+urllib.parse.quote(item['path']))
                blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
                if blob != item['sha'] or len(data) != item['size']:
                    raise SystemExit('Git tree/source byte mismatch')
                destination.parent.mkdir(parents=True, exist_ok=True)
                scanner.safe_path(base, 'source/'+item['path']).write_bytes(data)
                record.update(downloaded=True, sha256=scanner.sha(data))
            files.append(record)
        inventory = {'repository': name, 'commit': commit, 'tree_sha': tree['sha'],
                     'acquired_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     'licenses': license_records, 'cargo_sha256': scanner.sha(cargo),
                     'cargo_license': metadata['package']['license'],
                     'cargo_edition': metadata['package'].get('edition', '2015 default'),
                     'nested_license_paths': [x['path'] for x in tree['tree'] if '/' in x['path'] and 'LICENSE' in x['path'].upper()],
                     'build_rs_present': any(x['path']=='build.rs' for x in tree['tree']),
                     'submodules': [x['path'] for x in tree['tree'] if x['mode']=='160000'],
                     'rust_files': files}
        scanner.safe_path(base, 'inventory.json').write_text(json.dumps(inventory, indent=2, sort_keys=True)+'\n')
        print(name, commit, 'Rust paths:', len(files), 'downloaded:', sum(x['downloaded'] for x in files))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--local-root', type=Path, required=True)
    args = parser.parse_args()
    acquire(args.manifest, args.freeze, args.local_root)
