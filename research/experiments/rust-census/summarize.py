#!/usr/bin/env python3
"""Publish counts/provenance only; retain source, token offsets and raw audits locally."""
import argparse
import json
from pathlib import Path
import re

import scanner


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    output = {'rule_version': scanner.RULE_VERSION, 'repositories': []}
    local_audits = []
    for repo in manifest['repositories']:
        root = scanner.safe_path(args.local_root, repo['local_id'])
        inventory_data = scanner.safe_path(root, 'inventory.json').read_bytes()
        inventory = json.loads(inventory_data)
        scan_data = scanner.safe_path(root, 'scan.json').read_bytes()
        scan = json.loads(scan_data)
        if scan['scanner_sha256'] != scanner.sha(Path(scanner.__file__).read_bytes()):
            raise SystemExit('scan/scanner digest mismatch')
        independent_files = sorted(p for p in (root/'source').rglob('*.rs') if p.is_file())
        paths = [str(p.relative_to(root/'source')) for p in independent_files]
        assert paths == sorted(x['path'] for x in inventory['rust_files'] if x['downloaded'])
        line_inventory = {}
        unicode_audit = None
        for record in scan['records']:
            if not record['downloaded']:
                continue
            data = scanner.safe_path(root/'source', record['path']).read_bytes()
            text = data.decode('utf-8')
            # Independent raw line heuristic, NOT a function parser or lexical reference.
            line_inventory[record['path']] = sum(bool(re.match(r'\s*(?:(?:pub(?:\([^)]*\))?|unsafe|async|const)\s+)*fn\s+', line)) for line in text.splitlines())
            for begin, end in record.get('local_offsets', {}).get('fn', []):
                assert data[begin:end] == b'fn'
                if unicode_audit is None and record['path'].startswith('src/') and len(data[:begin].decode()) != begin:
                    unicode_audit = {'path': record['path'], 'file_sha256': scanner.sha(data),
                                     'span_bytes': [begin, end], 'character_index': len(data[:begin].decode()),
                                     'checked_slice_is_fn': True}
        assert unicode_audit is not None
        local_audits.append({'repository': repo['repository'], 'unicode': unicode_audit,
                             'independent_line_heuristic_by_file': line_inventory})
        files = [{k: v for k, v in record.items() if k != 'local_offsets'} for record in scan['records']]
        output['repositories'].append({
            'repository': repo['repository'], 'commit': repo['commit'],
            'acquired_utc': inventory['acquired_utc'], 'inventory_sha256': scanner.sha(inventory_data),
            'scan_sha256': scanner.sha(scan_data), 'api_tree_sha256': scanner.sha(scanner.safe_path(root, 'api-tree.json').read_bytes()),
            'scanner_sha256': scan['scanner_sha256'], 'carrier_sha256': scan['carrier_sha256'],
            'cargo_license': inventory['cargo_license'], 'cargo_edition': inventory['cargo_edition'],
            'cargo_sha256': inventory['cargo_sha256'], 'licenses': inventory['licenses'],
            'build_rs_present': inventory['build_rs_present'], 'submodules': inventory['submodules'],
            'nested_license_paths': inventory['nested_license_paths'],
            'independent_files_count': len(paths), 'independent_bytes': sum(p.stat().st_size for p in independent_files),
            'independent_file_inventory_matches': True, 'independent_fn_like_line_total': sum(line_inventory.values()),
            'unicode_byte_offset_audit_passed': True,
            'groups': scan['groups'], 'failure_reasons': scan['failure_reasons'],
            'grammar_refusal_reasons': scan['grammar_refusal_reasons'], 'files': files})
    scanner.safe_path(args.local_root, 'audit-offsets.json').write_text(json.dumps(local_audits, indent=2, sort_keys=True)+'\n')
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True)+'\n')
    print('Wrote aggregate counts/provenance; no source excerpts or token offsets published.')


if __name__ == '__main__':
    main()
