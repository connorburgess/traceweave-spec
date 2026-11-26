# Portable filesystem adaptation of retained compare.py; not executed during evidence packaging.
from pathlib import Path
import json,hashlib,sys,struct,subprocess,importlib.util,platform,socket,errno,argparse
package=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='Bounded six-input comparison; requires OS network denial and provisioned dependencies')
parser.add_argument('--reference',type=Path,required=True)
parser.add_argument('--binary',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args(); reference=args.reference.resolve(); binary=args.binary.resolve(); h=args.out.resolve()
h.mkdir(parents=True,exist_ok=False)
# This program must be invoked inside OS network denial; fail before package/core runs otherwise.
sock=socket.socket()
try:
 sock.bind(('127.0.0.1',0))
 raise SystemExit('network denial probe unexpectedly allowed bind')
except OSError as e:
 if e.errno!=errno.EPERM:raise
 probe={'operation':'loopback bind','errno':e.errno,'error':str(e)}
finally:sock.close()
for f in json.loads((package/'python-source.json').read_text())['files']:
 assert hashlib.sha256((reference/f['path']).read_bytes()).hexdigest()==f['sha256']
sys.path.insert(0,str(reference/'vendor/threatexchange_pdq'))
import numpy as np
import PIL
assert np.__version__=='2.5.5' and PIL.__version__=='13.0.0'
spec=importlib.util.spec_from_file_location('pinned_pdq',reference/'twimg/pdq_np.py');port=importlib.util.module_from_spec(spec);spec.loader.exec_module(port)
from pdqhashing.hasher.pdq_hasher import PDQHasher
from pdqhashing.utils.matrix import MatrixUtil as M
vendor=PDQHasher()
attrs=['hash','hashRotate90','hashRotate180','hashRotate270','hashFlipX','hashFlipY','hashFlipPlus1','hashFlipMinus1']
manifest=json.loads((package/'declared-inputs.json').read_text());(h/'inputs').mkdir(exist_ok=True)
rows=[]
for c in manifest['cases']:
 width,height=c['width'],c['height'];values=[]
 for y in range(height):
  for x in range(width):
   if c['id']=='black':v=0
   elif c['id']=='constant127':v=127
   elif c['id']=='low-contrast':v=126+(17*x+31*y+7*x*y)%4
   else:v=(17*x+31*y+7*x*y)%256
   values.append(v)
 raw=b'TWLUMA1\0'+struct.pack('<II',width,height)+struct.pack('<'+'f'*len(values),*values)
 path=h/'inputs'/(c['id']+'.luma');path.write_bytes(raw)
 a=np.frombuffer(raw,offset=16,dtype='<f4').reshape(height,width).astype(np.float64)
 assert all(float(a.reshape(-1)[i])==v for i,v in enumerate(values))
 ph,pq=port.pdq_from_luma(a.copy(),dihedral=True)
 vhq=vendor.pdqHash256esFromFloatLuma(a.reshape(-1).tolist(),M.allocateMatrixAsRowMajorArray(height,width),height,width,M.allocateMatrix(64,64),M.allocateMatrix(16,64),M.allocateMatrix(16,16),M.allocateMatrix(16,16),0xff)
 vh={name:str(getattr(vhq,attr)) for name,attr in zip(port.DIHEDRAL_NAMES,attrs)}
 p=subprocess.run([str(binary),str(path)],capture_output=True,text=True)
 (h/(c['id']+'-cpp.stdout')).write_text(p.stdout);(h/(c['id']+'-cpp.stderr')).write_text(p.stderr)
 if p.returncode:raise RuntimeError(c['id']+': C++ returned '+str(p.returncode))
 cpp=json.loads(p.stdout)
 distances={name:(int(ph[name],16)^int(cpp['hashes'][name],16)).bit_count() for name in port.DIHEDRAL_NAMES}
 rows.append({'id':c['id'],'width':width,'height':height,'inputSha256':hashlib.sha256(raw).hexdigest(),'inputBytes':len(raw),'port':{'hashes':ph,'quality':pq},'pythonVendor':{'hashes':vh,'quality':vhq.quality},'cpp':cpp,'pythonExact':ph==vh and pq==vhq.quality,'cppHashExactCount':sum(d==0 for d in distances.values()),'cppHammingByVariant':distances,'cppQualityExact':pq==cpp['quality'],'belowProfileQualityFloor':pq<=49})
result={'scope':manifest['scope'],'networkDenialProbe':probe,'environment':{'python':platform.python_version(),'numpy':np.__version__,'pillow':PIL.__version__,'os':platform.platform(),'machine':platform.machine()},'cases':rows,'summary':{'inputs':len(rows),'variantComparisons':8*len(rows),'cppHashesExact':sum(r['cppHashExactCount'] for r in rows),'cppQualityExact':sum(r['cppQualityExact'] for r in rows),'pythonPortVendorExact':sum(r['pythonExact'] for r in rows),'completeCppExactInputs':sum(r['cppHashExactCount']==8 and r['cppQualityExact'] for r in rows)}}
(h/'comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
for r in rows:print(r['id'],'quality',r['port']['quality'],r['cpp']['quality'],'exact hashes',r['cppHashExactCount'],'distances',r['cppHammingByVariant'])
# Completion of feasibility is distinct from equality: report every mismatch, never replace bytes.
