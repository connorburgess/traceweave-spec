"""Bounded synthetic conformance; no fetch, decode, trim, hash-core or study runner."""
import argparse
import ast
import hashlib
import json
import platform
import sys
import zipfile
from pathlib import Path

import arithmetic
import oracle
from build_fixtures import flat

HERE = Path(__file__).resolve().parent
WHEEL_SHA = 'd9b0a2bee3f3e03e9f29057aedb807dbf1e1d96ee1b9d0f422d9db6c8583271d'


def pillow_target(wheel):
    import PIL
    from PIL import Image, _imaging
    if PIL.__version__ != '13.0.0':
        raise ValueError('target must be Pillow 13.0.0')
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != WHEEL_SHA:
        raise ValueError('wheel does not match pinned macOS arm64 CPython 3.14 artifact')
    # Validate the actual loaded Python wrapper and compiled imaging target, not just metadata.
    with zipfile.ZipFile(wheel) as z:
        for path in [Path(Image.__file__), Path(_imaging.__file__)]:
            entry = 'PIL/'+path.name
            if path.read_bytes() != z.read(entry):
                raise ValueError('loaded Pillow target differs from pinned wheel: '+path.name)
    return Image


def mismatch(a, b):
    return sum(x != y for x,y in zip(a,b)) + abs(len(a)-len(b))


def intermediate_mismatch(matrix, expected):
    values = [v for row in matrix for v in row]
    return sum(type(x) is not int or x != y for x,y in zip(values,expected)) + abs(len(values)-len(expected))


def check(wheel=None):
    fixture = json.loads((HERE/'fixtures.json').read_text())
    if fixture['fixtureVersion'] != 'image-normalization-draft3-fixtures-1':
        raise ValueError('fixture version')
    # Guard frozen inheritance and canonical config identity before target execution.
    frozen = json.loads((HERE/'frozen-pins.json').read_text())
    root = HERE.parents[2]
    for name, digest in frozen['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise ValueError('inherited frozen bytes changed: '+name)
    config_raw = (HERE/'extraction-config.json').read_bytes()
    config = json.loads(config_raw)
    canonical = (json.dumps(config,sort_keys=True,separators=(',',':'))+'\n').encode()
    if config_raw != canonical or hashlib.sha256(config_raw).hexdigest() != '38b2dc7c534cc93e321160a9bba1f885e0106f8212760559d0c744f4ddb8654d':
        raise ValueError('draft-3 configuration identity')
    tree = ast.parse((root/'research/experiments/image-fingerprint/twimg/profile.py').read_text())
    inherited = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                     and any(isinstance(t,ast.Name) and t.id=='EXTRACTION_CONFIG' for t in n.targets))
    inherited['profileVersion']='draft-3'
    inherited['iscc']['normalization']='traceweave-iscc-normalization-draft-1'
    if config != inherited:
        raise ValueError('configuration changes exceed the two proposed fields')
    Image = pillow_target(wheel) if wheel else None
    report = dict(scope='bounded-synthetic-post-trim-grey-resize-only',
                  python=platform.python_version(),platform=platform.system()+' '+platform.machine(),
                  pillowWheelSha256=WHEEL_SHA if Image else None,
                  fixtureSha256=hashlib.sha256((HERE/'fixtures.json').read_bytes()).hexdigest(),
                  configSha256=hashlib.sha256(config_raw).hexdigest(),
                  sourceSha256={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                                for name in ['arithmetic.py','oracle.py','check.py','build_fixtures.py']},
                  cases=[],failures=[])
    sizes = sorted({n for c in fixture['cases'] for n in (c['width'],c['height']) if n!=32})
    tables = {str(n): arithmetic.coefficients(n) for n in sizes}
    digest = hashlib.sha256(json.dumps(tables,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if digest != fixture['coefficientSha256']:
        report['failures'].append('ordinary coefficient tables differ from oracle fixture')
    for n in sizes:
        if arithmetic.coefficients(n) != oracle.weights(n):
            report['failures'].append('coefficient oracle mismatch '+str(n))
    witnesses = {'wrong-order':[], 'final-only':[], 'grey-ties-even':[]}
    for c in fixture['cases']:
        w,h = c['width'],c['height']
        raw=bytes.fromhex(c['rgbHex'])
        if len(raw)!=3*w*h:
            raise ValueError('RGB length '+c['id'])
        rgb = [[tuple(raw[3*(y*w+x):3*(y*w+x)+3]) for x in range(w)] for y in range(h)]
        g = arithmetic.grey(rgb)
        expected_g = bytes.fromhex(c['greyHex'])
        expected = bytes.fromhex(c['outputHex'])
        expected_first = bytes.fromhex(c['firstHex'])
        result,first,order = arithmetic.resize(g)
        mathematical, math_first, math_order = oracle.resize(oracle.grey(rgb))
        row=dict(id=c['id'],width=w,height=h,order=order,
                 ordinaryDifferentBytes=mismatch(flat(result),expected),
                 oracleDifferentBytes=mismatch(flat(mathematical),expected),
                 firstDifferentBytes=intermediate_mismatch(first,expected_first))
        if (len(expected)!=1024 or flat(g)!=expected_g or flat(oracle.grey(rgb))!=expected_g
                or flat(math_first)!=expected_first or order!=c['order'] or math_order!=order
                or any(row[k] for k in ['ordinaryDifferentBytes','oracleDifferentBytes','firstDifferentBytes'])):
            report['failures'].append(c['id']+': fixture/arithmetic mismatch')
        for mutation in ('wrong-order','final-only'):
            mutated,_,_ = arithmetic.resize(g, mutation)
            different = mismatch(flat(mutated),expected)
            row[mutation+'DifferentBytes']=different
            if different:
                witnesses[mutation].append(c['id'])
        # Independent anchor: 19595*1+38470*53+7471*185 = 3440640
        # = 52*65536+32768. Half-up is 53, whereas ties-even is 52.
        even = []
        for pixels in rgb:
            line = []
            for red, green, blue in pixels:
                q, rem = divmod(19595*red+38470*green+7471*blue,65536)
                line.append(q + (rem > 32768 or (rem == 32768 and q % 2 == 1)))
            even.append(line)
        row['grey-ties-evenDifferentBytes']=mismatch(flat(even),expected_g)
        if row['grey-ties-evenDifferentBytes']:
            witnesses['grey-ties-even'].append(c['id'])
        if c['id']=='grey-half-tie' and (raw!=bytes([1,53,185])*1024 or expected_g!=bytes([53])*1024):
            report['failures'].append('exact grey half-tie anchor differs from independent derivation')
        if Image:
            im = Image.frombytes('RGB',(w,h),raw).convert('L')
            got = im.resize((32,32),Image.Resampling.BICUBIC,reducing_gap=None).tobytes()
            first_size=(32,h) if order=='xy' else (w,32)
            pf=im.resize(first_size,Image.Resampling.BICUBIC,reducing_gap=None).tobytes()
            row.update(pillowGreyDifferentBytes=mismatch(im.tobytes(),expected_g),
                       pillowFirstDifferentBytes=mismatch(pf,expected_first),
                       pillowDifferentBytes=mismatch(got,expected),pillowOutputHex=got.hex())
            if any(row[k] for k in ['pillowGreyDifferentBytes','pillowFirstDifferentBytes','pillowDifferentBytes']):
                row.update(pillowGreyHex=im.tobytes().hex(),pillowFirstHex=pf.hex())
                report['failures'].append(c['id']+': pinned Pillow mismatch (retained)')
        report['cases'].append(row)
    if not any(c['id']=='grey-half-tie' for c in fixture['cases']):
        report['failures'].append('missing exact grey half-tie fixture')
    report['mutationWitnesses']=witnesses
    for mutation, ids in witnesses.items():
        if not ids:
            report['failures'].append('no fixture detects '+mutation)
    # Tiny exact-arithmetic anchors independent of full fixture output generation.
    if oracle.b64(oracle.F(1)+oracle.F(1,2**53))!=1:
        report['failures'].append('binary64 tie-even anchor')
    if oracle.b64(oracle.F(1)+oracle.F(3,2**53))!=oracle.F(1)+oracle.F(1,2**51):
        report['failures'].append('binary64 odd tie anchor')
    if arithmetic.grey([[(255,0,0),(0,255,0),(0,0,255)]]) != [[76,150,29]]:
        report['failures'].append('grey primary anchors')
    report['ok']=not report['failures']
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pillow-wheel',type=Path,help='existing hash-pinned wheel; never installed/fetched')
    p.add_argument('--report',type=Path,help='write JSON including every mismatching target byte')
    args=p.parse_args()
    report=check(args.pillow_wheel)
    if args.report:
        args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
    print('cases:',len(report['cases']))
    sys.exit(0 if report['ok'] else 1)
