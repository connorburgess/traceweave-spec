"""Static retained-evidence consistency only; never import/run numerical records."""
from pathlib import Path
import argparse
import copy
import csv
import hashlib
import io
import json

P = Path(__file__).resolve().parent
NAMES = ['black', 'constant127', 'low-contrast', 'asymmetric', 'wide', 'tall']
VARIANTS = ['orig', 'rot90', 'rot180', 'rot270', 'flipx', 'flipy', 'flipp', 'flipm']
sha = lambda data: hashlib.sha256(data).hexdigest()

def accounting(d, ind, ledger, decisions, baseline):
    assert [c['id'] for c in d['cases']] == NAMES
    assert [c['id'] for c in baseline['cases']] == NAMES
    assert [c['id'] for c in ind['cases']] == NAMES
    assert d['baseline'] == ledger['baseline']
    assert d['baseline']['inputs'] == 6 and d['baseline']['variantComparisons'] == 48
    assert d['baseline']['cppHashesExact'] == ind['baselineHashesExact'] == 32
    assert d['baseline']['cppQualityExact'] == ind['baselineQualitiesExact'] == 6
    assert ind['hashesAndMappingsChecked'] == ledger['diagnosticCppReconstructed'] == 48
    assert ind['changedBitDecisionsChecked'] == ledger['affectedDecisions'] == 1606
    assert ind['coefficientsReconstructed'] == ledger['matrixEntriesReconstructed'] == 1024
    assert ind['TandBBitwiseChecks'] == ledger['TandBStageChecks'] == 12
    assert sum(c['cppHashExactCount'] for c in baseline['cases']) == 32
    assert sum(c['cppQualityExact'] for c in baseline['cases']) == 6
    expected = []
    for c, trace, ir in zip(baseline['cases'], d['cases'], ind['cases']):
        expected.append({k:c[k] for k in ['id','width','height','inputSha256','inputBytes','cppHashExactCount','cppQualityExact']} | {'affectedDecisions':ir['differentBits']})
        assert trace['instrumentationUnchanged'] is True
        assert [v['name'] for v in trace['variants']] == VARIANTS
        rows = decisions[c['id']]
        pairs = [(r['variant'], int(r['bitIndex'])) for r in rows]
        assert len(pairs) == len(set(pairs)) == ir['differentBits']
        assert ir['differentBits'] == {'constant127':1118, 'low-contrast':488}.get(c['id'], 0)
        for v in trace['variants']:
            xor = int(c['cpp']['hashes'][v['name']],16) ^ int(c['port']['hashes'][v['name']],16)
            indices = [i for i in range(256) if xor & (1 << i)]
            assert indices == v['indices'] and len(indices) == v['differentBits']
            assert {i for variant,i in pairs if variant == v['name']} == set(indices)
        for r in rows:
            i=int(r['bitIndex']); assert 0 <= i < 256
            assert int(r['row']) == i//16 and int(r['col']) == i%16
            # Verify stored scalar decisions, not DCT/coefficient computation.
            assert int(r['cppBit']) == int(float(r['cppCoefficient']) > float(r['cppMedian']))
            assert int(r['pythonBit']) == int(float(r['pythonCoefficient']) > float(r['pythonMedian']))
            assert r['cppBit'] != r['pythonBit']
    assert ledger['cases'] == expected
    assert sum(len(rows) for rows in decisions.values()) == 1606


def inspect(self_test=False):
    m=json.loads((P/'retention-manifest.json').read_text())
    assert m['originalAuthorPackage']['reportSha256'] == '2816c35b4ce7ace508170bb6f55a515fe4df60cec7a20d0d3603f66e30ebac95'
    assert m['originalAuthorPackage']['manifestSha256'] == '5b2db7762a4e7949b9ebb70fb1d40397bfff25a85a8af968ba7ea31541976b8e'
    assert m['originalAuthorPackage']['files'] == 413 and m['originalAuthorPackage']['manifestEntries'] == 412
    actual={str(p.relative_to(P)) for p in P.rglob('*') if p.is_file() and p.name != 'retention-manifest.json'}
    assert set(m['packageFiles']) == actual
    for name,i in m['packageFiles'].items():
        b=(P/name).read_bytes(); assert sha(b)==i['sha256'] and len(b)==i['bytes']
    retained=[]
    for r in m['records']:
        if r['retainedPath'] is None:
            assert r['retainedSha256'] is None and r['retainedBytes'] is None
            continue
        name=r['retainedPath']; assert name not in retained; retained.append(name)
        assert name == '../../experiments/pdq-cpp-feasibility/comparison.json' or (P/name).resolve().is_relative_to(P)
        b=(P/name).read_bytes(); assert sha(b)==r['retainedSha256'] and len(b)==r['retainedBytes']
        if r['adaptation'].startswith('none;'):
            assert sha(b)==r['originalSha256'] and len(b)==r['originalBytes']
    for r in m['derivedRecords']:
        b=(P/r['retainedPath']).read_bytes(); assert sha(b)==r['retainedSha256'] and len(b)==r['retainedBytes']
    baseline_path=P/'../../experiments/pdq-cpp-feasibility/comparison.json'
    baseline=json.loads(baseline_path.read_text());d=json.loads((P/'results/diagnosis.json').read_text());ind=json.loads((P/'results/independent-results.json').read_text());ledger=json.loads((P/'summary-ledger.json').read_text())
    assert ledger['sourceComparisonSha256']==sha(baseline_path.read_bytes())
    assert ledger['sourceDiagnosisSha256']==sha((P/'results/diagnosis.json').read_bytes())
    assert ledger['sourceIndependentResultsSha256']==sha((P/'results/independent-results.json').read_bytes())
    decisions={n:list(csv.DictReader(io.StringIO((P/'decisions'/f'{n}.csv').read_text()))) for n in NAMES}
    accounting(d,ind,ledger,decisions,baseline)
    checks=json.loads((P/'results/bitwise-checks.json').read_text())
    assert checks['softwareFloat32StageBytesIdentical']==[f'{n}/{s}' for n in NAMES for s in ['T','B']]
    assert [c['id'] for c in json.loads((P/'results/mixed-probes.json').read_text())]==NAMES
    focused=json.loads((P/'results/pdq-d1-addendum-evidence.json').read_text())
    assert focused['reportSha256']==m['originalAuthorPackage']['reportSha256']
    assert focused['packageManifestSha256']==m['originalAuthorPackage']['manifestSha256']
    assert focused['unchangedExistingFiles']==409 and focused['manifestEntriesVerified']==412
    assert focused['packageFiles']==413 and focused['numericReruns']==0
    report=(P/'reports/author-report.md').read_text()
    assert '| flipx | +B if i odd, else −B (top/bottom) |' in report
    assert '| flipy | +B if j odd, else −B (left/right) |' in report
    rejected=[]
    if self_test:
        for name,change in [
            ('missing decision',lambda x:x[3]['constant127'].pop()),
            ('duplicate decision',lambda x:x[3]['constant127'].__setitem__(1,copy.deepcopy(x[3]['constant127'][0]))),
            ('input identity drift',lambda x:x[2]['cases'][0].update(inputSha256='0'*64)),
            ('baseline relabelled parity',lambda x:x[0]['baseline'].update(cppHashesExact=48)),
            ('wrong variant association',lambda x:x[3]['constant127'][0].update(variant='flipy')),
        ]:
            x=copy.deepcopy([d,ind,ledger,decisions,baseline]);change(x)
            try:accounting(*x)
            except (AssertionError,KeyError):rejected.append(name)
            else:raise AssertionError('retention corruption accepted: '+name)
    return {'staticOnly':True,'packageFilesVerified':len(actual),'originalAuthorFiles':413,'baselineHashMatches':32,'baselineVariants':48,'qualityMatches':6,'diagnosticReconstructionsRecorded':48,'affectedDecisions':1606,'retentionCorruptionsRejected':rejected,'causalExperimentRerun':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--self-test',action='store_true');args=ap.parse_args()
    print(json.dumps(inspect(args.self_test),indent=2))
