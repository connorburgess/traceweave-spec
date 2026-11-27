"""Check measured fixture accounting, identities, outcomes and controls offline."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(data): return hashlib.sha256(data).hexdigest()
def read(p): return json.loads(p.read_bytes())
def require(ok, message):
    if not ok: raise ValueError(message)

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
    require(len(run['commands']) == 160 and all(c['exit'] == 0 for c in run['commands']), 'successful command accounting')
    for v in run['cli'].values():
        require(v['version']['stamp'] == 'stamped' and
                v['version']['implementation']['commit'] == recipe['implementationCommit'] and
                v['version']['specCommit'] == recipe['implementationSpecPin'], 'CLI pin')
        require(len(v['sha256']) == 64, 'binary digest')
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
    require(all(c['exit']==0 for c in replay['commands']) and len(replay['commands'])==160,'replay commands')
    for label,v in replay['cli'].items():
        require(v['version']==baseline['cli'][label]['version'],'replay stamped identity')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay',type=Path)
    args=parser.parse_args()
    if args.replay:verify_replay(args.replay)
    print('PASS: 6 demos,',check(),'misses across both modes; 2 independent controls; identities and outcomes checked')
