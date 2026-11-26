#!/usr/bin/env python3
"""Optional targeted M5 process probes against caller-supplied native binaries.

No builds, downloads or corpus access. Example after building a pinned archive:
  python tools/check_native_m5.py --go <go-binary> --rust <rust-binary>
This is not a complete implementation conformance run or the M5.3 demo.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def need(condition, name):
    if not condition:
        raise ValueError(name)


def probe(binary, lane):
    with tempfile.TemporaryDirectory(prefix='tw-m5-process-') as temporary:
        work = Path(temporary)
        home = work / 'home'; home.mkdir()
        src = work / 'source.go'; src.write_text('package p\nfunc add(a, b int) int { return a + b }\n')
        config = ROOT / 'test-vectors/extraction/config-go.json'
        env = dict(os.environ, HOME=str(home), XDG_DATA_HOME='', TRACEWEAVE_PRIVATE_DIR='', TRACEWEAVE_TEST_FAULT='')
        def run(args):
            return subprocess.run([str(binary), *map(str, args)], cwd=work, env=env, capture_output=True, timeout=30)
        def build(out, record=None):
            if lane == 'go':
                return run(['build-catalogue', '-config', config, '-out', out,
                            *(['-records'] if record else []), 'a.go=' + str(record or src)])
            return run(['build-catalogue', '--config', config, '--out', out,
                        '--record' if record else '--source', 'a.go=' + str(record or src)])
        # usage refusal must not silently fall back to a default command/config.
        p = run(['compare', '-m5-unknown-option' if lane == 'go' else '--m5-unknown-option'])
        need(p.returncode == 2, 'unknown-options')
        # Unknown-key and source-text canaries must not leak in raw process output.
        records = json.loads((ROOT / 'test-vectors/matching/records.json').read_text())
        text = next(x['expectedRecordText'] for x in records['records'] if x['id'] == 'rec-go-ok')
        rec = work / 'bad-record.json'; rec.write_text(text.replace('{', '{"zzCanaryKey7":1,', 1))
        args = ['validate', '-record', rec, '-config', config] if lane == 'go' else ['validate', 'record', rec]
        p = run(args)
        need(p.returncode == 1 and b'zzCanary' not in p.stdout + p.stderr, 'diagnostic-key-canary')
        p = build(work / 'bad-catalogue.json', rec)
        need(p.returncode == 1 and b'zzCanary' not in p.stdout + p.stderr and not (work / 'bad-catalogue.json').exists(), 'diagnostic-build-canary')
        src.write_text('s := "zzCanaryText8')
        args = ['extract', '-config', config, src] if lane == 'go' else ['extract', '--config', config, '--input', src]
        p = run(args)
        need(p.returncode == 0 and b'zzCanary' not in p.stdout + p.stderr and json.loads(p.stdout)['result']['status'] == 'error', 'diagnostic-source-canary')
        src.write_text('package p\nfunc add(a, b int) int { return a + b }\n')
        # Working-tree refusal must happen before writing the private destination.
        tree = work / 'checkout'; tree.mkdir(); (tree / '.git').mkdir()
        destination = tree / 'new' / 'catalogue.json'
        p = build(destination)
        need(p.returncode == 2 and not destination.parent.exists(), 'private-path-refusal')
        # Cleanup has both a required deletion and a required non-deletion.
        out = work / 'catalogue.json'
        stale = work / '.catalogue.json.tw-tmp-OLD1'; stale.write_text('partial')
        other = work / '.other.json.tw-tmp-KEEP1'; other.write_text('keep')
        p = build(out)
        need(p.returncode == 0 and out.is_file() and not stale.exists() and other.read_text() == 'keep', 'temporary-cleanup')
    return 6


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--go', type=Path, required=True)
    parser.add_argument('--rust', type=Path, required=True)
    args = parser.parse_args()
    for lane in ('go', 'rust'):
        try:
            count = probe(getattr(args, lane).resolve(), lane)
        except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
            raise SystemExit(f'FAIL native M5 {lane}: {exc}')
        print(f'PASS native M5 {lane}: {count}/{count} targeted negative process cases')
