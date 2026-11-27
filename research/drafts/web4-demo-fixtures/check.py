"""Check measured fixture accounting, identities, outcomes and controls offline."""
import argparse
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(data): return hashlib.sha256(data).hexdigest()
def read(p): return json.loads(p.read_bytes())
def require(ok, message):
    if not ok: raise ValueError(message)

# Exact measured binaries reviewed at d2dd3df. This validates recorded metadata;
# static metadata is not proof that a process actually executed those bytes.
CLI_IDENTITIES = {
    'rust': ('traceweave', '0.0.1', '5d22a4d37d6403c595f8ccab04172a496ca74368a52d5ee89a3b7e1b918308a3'),
    'go': ('traceweave-go', '0.2.0-dev', '0219f19b4222ff71733d3709a57116aae0756f2fd0bba0d6f1e9251e025052b1'),
}


def check_cli_metadata(cli, recipe):
    require(recipe['implementationCommit'] == 'dcaa0d42e9de63d23aa113d9306134de9b28942c' and
            recipe['implementationSpecPin'] == '9cf78eec72d89c4a5383dc0ebf0fa98a4693d191', 'reviewed source pins')
    require(isinstance(cli, dict) and set(cli) == set(CLI_IDENTITIES), 'CLI identity coverage')
    for label, (name, version, digest) in CLI_IDENTITIES.items():
        entry = cli[label]
        require(isinstance(entry, dict) and set(entry) == {'version', 'sha256'}, 'CLI metadata fields')
        require(entry['sha256'] == digest, 'measured binary identity')
        require(entry['version'] == {
            'implementation': {'commit': recipe['implementationCommit'], 'name': name, 'version': version},
            'specCommit': recipe['implementationSpecPin'], 'stamp': 'stamped'}, 'CLI stamped identity')


def command_plan(recipe, run):
    """Derive ordered operations from cases, configs, inputs and artifact hashes.

    Slots are case / native CLI / operation. Repeated argv across cases is valid;
    each slot still binds its own expected stdin and generated artifact stdout.
    """
    cfg = '${PACKAGE}/' + recipe['extractionConfig']
    cmp_cfg = '${PACKAGE}/' + recipe['comparisonConfig']
    plan = []
    for case, measured in zip(recipe['cases'], run['cases']):
        for label in ('rust', 'go'):
            artifacts = measured['artifacts'][label]
            def add(argv, artifact=None, stdin=None):
                plan.append((case['id'], label, argv, artifacts[artifact] if artifact else None, stdin))
            for side in ('sample', 'transformed'):
                source = '${WORK}/' + side + '.go'
                record = '${WORK}/' + side + '.record.json'
                catalogue = '${WORK}/' + side + '.catalogue.json'
                if label == 'rust':
                    add(['extract', '--config', cfg, '--input', source], side+'.record.json')
                    add(['validate', 'record', record])
                    add(['build-catalogue', '--config', cfg, '--source', side+'.go='+source,
                         '--out', '-'], side+'.catalogue.json')
                    add(['validate', 'catalogue', catalogue])
                else:
                    add(['extract', '--config', cfg], side+'.record.json', case[side+'Sha256'])
                    add(['validate', '-record', record, '-config', cfg])
                    add(['build-catalogue', '-config', cfg, '-out', '-', side+'.go='+source],
                        side+'.catalogue.json')
                    add(['validate', '-catalogue', catalogue])
            if label == 'rust':
                add(['compare', '--config', cmp_cfg, '--reference', '${WORK}/sample.catalogue.json',
                     '--candidate', '${WORK}/transformed.catalogue.json', '--body-only', '--out', '-'], 'body.json')
                add(['validate', 'body', '${WORK}/body.json'])
            else:
                add(['compare', '-comparison-config', cmp_cfg, '-reference', '${WORK}/sample.catalogue.json',
                     '-candidate', '${WORK}/transformed.catalogue.json', '-body-only', '-out', '-'], 'body.json')
                add(['validate', '-body', '${WORK}/body.json'])
    return plan


def check_commands(run, recipe):
    plan = command_plan(recipe, run)
    commands = run.get('commands')
    require(isinstance(commands, list) and len(plan) == 160 and len(commands) == len(plan), 'command count coverage')
    fields = {'cli', 'argv', 'exit', 'stdoutSha256', 'stderrSha256', 'stdinSha256'}
    for index, (actual, (case, label, argv, output, stdin)) in enumerate(zip(commands, plan)):
        where = f'command {index} ({case}/{label})'
        require(isinstance(actual, dict) and set(actual) == fields, where + ': metadata fields')
        require(actual['cli'] == label and actual['argv'] == argv, where + ': identity coverage')
        require(type(actual['exit']) is int and actual['exit'] == 0, where + ': success')
        require(actual['stdinSha256'] == stdin, where + ': input binding')
        for field in ('stdoutSha256', 'stderrSha256'):
            require(isinstance(actual[field], str) and re.fullmatch('[0-9a-f]{64}', actual[field]),
                    where + ': output digest shape')
        if output is not None:
            require(actual['stdoutSha256'] == output, where + ': artifact output binding')


def check(root=HERE):
    recipe, expected, run = (read(root / n) for n in ['recipes.json', 'expected.json', 'evidence/run.json'])
    ids = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'C-identical', 'C-unrelated']
    require([c['id'] for c in recipe['cases']] == ids, 'case accounting')
    require([c['id'] for c in expected['cases']] == ids, 'expectation accounting')
    require([c['id'] for c in run['cases']] == ids, 'run accounting')
    cfg = read(root / recipe['comparisonConfig'])
    require(cfg == {'comparison': 'traceweave-seed-merge-draft-2', 'modes': ['exact','normalized'],
                    'minRegionDistinctHashes': 2, 'mergeGap': 4, 'maxSeedsPerMode': 100000,
                    'maxRegionsPerMode': 1000, 'suppressionCatalogueSha256': 'none'}, 'fixed comparison config')
    for kind, path in [('extraction',recipe['extractionConfig']),('comparison',recipe['comparisonConfig'])]:
        require(sha((root / path).read_bytes()) == expected[kind+'ConfigSha256'], 'config identity')
        pinned = next(v for k,v in recipe['sources'].items() if k.endswith(Path(path).name))
        require(pinned['sha256'] == expected[kind+'ConfigSha256'], 'config source pin')
    check_cli_metadata(run.get('cli'), recipe)
    check_commands(run, recipe)
    negative = 0
    for case, want, measured in zip(recipe['cases'], expected['cases'], run['cases']):
        for side in ['sample','transformed']:
            data = (root / case[side]).read_bytes()
            require(sha(data) == case[side+'Sha256'], 'input identity')
        require(case['kind'] == ('demonstration' if case['id'].startswith('D') else 'control'), 'case kind')
        artifacts={'sample.record.json','transformed.record.json','sample.catalogue.json','transformed.catalogue.json','body.json'}
        require(set(measured['artifacts'])=={'rust','go'} and all(set(v)==artifacts for v in measured['artifacts'].values()), 'artifact accounting')
        for name,digest in measured['artifacts']['rust'].items():
            a=(root/'evidence'/case['id']/'rust'/name).read_bytes()
            b=(root/'evidence'/case['id']/'go'/name).read_bytes()
            require(sha(a)==digest==measured['artifacts']['go'][name] and a==b,'native artifact identity')
        data=(root/'evidence'/case['id']/'rust/body.json').read_bytes();body=json.loads(data)
        require(sha(data)==want['bodyFileSha256'],'body file identity')
        canonical=json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
        require(sha(canonical)==want['bodySha256'] and canonical==data,'canonical body identity')
        require(body['status']=='compared' and len(body['pairs'])==1,'pair computed')
        require(body['inputs']['comparisonConfigSha256']==expected['comparisonConfigSha256'],'bound comparison')
        pair=body['pairs'][0];modes=pair['modes']
        require(pair['reference']['sha256']==case['sampleSha256'] and pair['candidate']['sha256']==case['transformedSha256'], 'subject binding')
        for side in ['sample','transformed']:
            record=read(root/'evidence'/case['id']/'rust'/(side+'.record.json'))
            require(record['inputSha256']==case[side+'Sha256'] and record['configSha256']==expected['extractionConfigSha256'], 'record binding')
        require(set(modes)=={'exact','normalized'},'mode accounting')
        for mode,v in modes.items():
            require({k:v[k] for k in ['outcome','containment','regionCounts']}==want['modes'][mode],'observed expectation')
            for region in v['regions']:
                for side,field in [('sample','referenceSpan'),('transformed','candidateSpan')]:
                    a,b=region[field];require(0<=a<=b<=len((root/case[side]).read_bytes()),'region byte span')
        if case['kind']=='demonstration':
            require(case['id'].startswith('D'),'demo accounting')
            # A miss must hold across BOTH displayed modes. An exact-mode miss
            # alongside a normalized match (D2) does not inflate the numerator.
            if all(v['outcome']['class']=='no-match' or v['outcome']['code']=='below-minimum-evidence'
                   for v in modes.values()): negative+=1
        if case['id']=='C-identical':
            require(case['sampleSha256']==case['transformedSha256'],'identity inputs')
            for v in modes.values():
                require(v['outcome']['class']=='match','identity match')
                for fraction in v['containment'].values():
                    require(fraction['numerator']==fraction['denominator']>0,'full fingerprint containment')
        if case['id']=='C-unrelated':
            require(all(v['outcome']['class']=='no-match' for v in modes.values()),'unrelated control')
    # Reconstruct derived transformations from the retained sample token stream,
    # without a new lexer or generator and without changing the input bytes.
    def source(id,side):return (root/'inputs'/id/(side+'.go')).read_bytes()
    tokens=read(root/'evidence/D4/rust/sample.record.json')['result']['tokens']
    evasion=[]
    for i,t in enumerate(tokens):
        evasion.append(t['text'])
        if (i+1)%4==0:evasion.extend(['break',';'])
    require(source('D4','transformed')==(' '.join(evasion)+'\n').encode(),'evasion recipe')
    require(source('D6','transformed')==source('D5','transformed')+(' '.join(t['text'] for t in tokens[:5])+'\n').encode(),'fragment recipe')
    before=source('D3','sample');split=before.index(b'func save(')
    require(source('D3','transformed')==before[split:]+before[:split],'reorder recipe')
    require(negative>=3,'half-negative demonstrations')
    return negative

def verify_replay(path):
    baseline=read(HERE/'evidence/run.json'); replay=read(path/'run.json')
    require(replay['cases']==baseline['cases'],'replay artifact manifests')
    for case in replay['cases']:
        for label,artifacts in case['artifacts'].items():
            for name,digest in artifacts.items():
                require(sha((path/case['id']/label/name).read_bytes())==digest,'replay bytes')
    recipe=read(HERE/'recipes.json')
    check_cli_metadata(replay.get('cli'), recipe)
    check_commands(replay, recipe)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay',type=Path)
    args=parser.parse_args()
    if args.replay:verify_replay(args.replay)
    print('PASS: 6 demos,',check(),'misses across both modes; 2 independent controls; identities and outcomes checked')
