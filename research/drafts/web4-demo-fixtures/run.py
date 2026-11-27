#!/usr/bin/env python3
"""Bounded native fixture reproduction; no WEB.6 timing/budget or browser run."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent

def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_bytes())

def run(rust, go, out):
    recipe = read(HERE / 'recipes.json')
    out.mkdir(parents=True, exist_ok=False)
    result = {'scope': 'WEB.4 native synthetic preparation only', 'host': platform.platform(),
              'python': platform.python_version(), 'cli': {}, 'commands': [], 'cases': []}
    for label, binary in [('rust', rust), ('go', go)]:
        version = json.loads(subprocess.check_output([str(binary), '--version-json']))
        assert version['stamp'] == 'stamped', version
        assert version['implementation']['commit'] == recipe['implementationCommit'], version
        assert version['specCommit'] == recipe['implementationSpecPin'], version
        result['cli'][label] = {'sha256': sha(binary.read_bytes()), 'version': version}
    with tempfile.TemporaryDirectory(prefix='tw-web4-') as temp:
        work = Path(temp)
        def call(label, args, input_bytes=None):
            binary = rust if label == 'rust' else go
            if label == 'go' and args[0] == 'validate':
                kind, path = args[1:]
                args = ['validate', '-' + kind, path]
                if kind == 'record':
                    args += ['-config', HERE / recipe['extractionConfig']]
            elif label == 'go' and args[0] == 'build-catalogue':
                args = ['build-catalogue', '-config', args[2], '-out', '-', args[4]]
            elif label == 'go' and args[0] == 'compare':
                args = ['compare', '-comparison-config', args[2], '-reference', args[4],
                        '-candidate', args[6], '-body-only', '-out', '-']
            env = {k: v for k, v in os.environ.items() if not k.startswith(('TRACEWEAVE_TEST_', 'TW_TEST_'))}
            env['TRACEWEAVE_PRIVATE_DIR'] = str(work / 'private')
            p = subprocess.run([str(binary), *map(str, args)], capture_output=True, env=env, input=input_bytes)
            portable = [str(a).replace(str(work), '${WORK}').replace(str(HERE), '${PACKAGE}') for a in args]
            result['commands'].append({'cli': label, 'argv': portable, 'exit': p.returncode,
                                       'stdoutSha256': sha(p.stdout), 'stderrSha256': sha(p.stderr), 'stdinSha256': sha(input_bytes) if input_bytes is not None else None})
            assert p.returncode == 0, (portable, p.returncode, p.stderr.decode(errors='replace'))
            return p.stdout
        for case in recipe['cases']:
            outputs = {}
            for label in ['rust', 'go']:
                case_dir = out / case['id'] / label
                case_dir.mkdir(parents=True)
                for side in ['sample', 'transformed']:
                    source = HERE / case[side]
                    assert sha(source.read_bytes()) == case[side + 'Sha256']
                    local = work / (side + '.go')
                    local.write_bytes(source.read_bytes())
                    args = ['extract', '--config', HERE / recipe['extractionConfig']]
                    if label == 'rust':
                        args += ['--input', local]
                    record = call(label, args, local.read_bytes() if label == 'go' else None)
                    (case_dir / (side + '.record.json')).write_bytes(record)
                    rec = work / (side + '.record.json'); rec.write_bytes(record)
                    call(label, ['validate', 'record', rec])
                    catalogue = call(label, ['build-catalogue', '--config', HERE / recipe['extractionConfig'],
                                            '--source', side + '.go=' + str(local), '--out', '-'])
                    (case_dir / (side + '.catalogue.json')).write_bytes(catalogue)
                    cat = work / (side + '.catalogue.json'); cat.write_bytes(catalogue)
                    call(label, ['validate', 'catalogue', cat])
                body = call(label, ['compare', '--config', HERE / recipe['comparisonConfig'],
                                    '--reference', work / 'sample.catalogue.json',
                                    '--candidate', work / 'transformed.catalogue.json', '--body-only', '--out', '-'])
                (case_dir / 'body.json').write_bytes(body)
                bpath = work / 'body.json'; bpath.write_bytes(body)
                call(label, ['validate', 'body', bpath])
                outputs[label] = {p.name: sha(p.read_bytes()) for p in sorted(case_dir.iterdir())}
            assert outputs['rust'] == outputs['go'], case['id'] + ': native divergence'
            result['cases'].append({'id': case['id'], 'artifacts': outputs})
    (out / 'run.json').write_text(json.dumps(result, indent=2) + '\n')
    return result

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rust', type=Path, required=True)
    p.add_argument('--go', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = run(a.rust.resolve(), a.go.resolve(), a.out.resolve())
    print('PASS:', len(result['cases']), 'case pairs, native artifact bytes agree; no performance measurement')
