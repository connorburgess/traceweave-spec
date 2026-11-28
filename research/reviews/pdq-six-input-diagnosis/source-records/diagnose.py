from pathlib import Path
import os,sys,json,hashlib,subprocess,importlib.util,socket,errno,csv,math
r=Path(__file__).resolve().parent
s=socket.socket()
try:s.bind(('127.0.0.1',0));raise RuntimeError('network allowed')
except OSError as e:assert e.errno==errno.EPERM
finally:s.close()
import numpy as np
assert np.__version__=='2.5.5'
spec=importlib.util.spec_from_file_location('port',r/'baseline-run-root/python-reference/twimg/pdq_np.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
baseline=json.loads((r/'baseline-artifact/comparison.json').read_text())
def save(d,n,a):np.asarray(a,dtype='<f8').tofile(d/(n+'.f64'))
def read(d,n,shape):return np.fromfile(d/(n+'.f32'),dtype='<f4').reshape(shape)
def stats(a,b):
 delta=np.abs(a.astype(np.float64)-b.astype(np.float64));ii=np.flatnonzero(delta)
 return {'different':len(ii),'maxAbs':float(delta.max()),'firstFlatIndex':int(ii[0]) if len(ii) else None,'firstValues':[float(a.flat[ii[0]]),float(b.flat[ii[0]])] if len(ii) else None}
def dct(a,d,dtype):
 a=a.astype(dtype);d=d.astype(dtype);t=np.zeros((16,64),dtype=dtype)
 for k in range(64):t=t+d[:,k:k+1]*a[k:k+1,:]
 b=np.zeros((16,16),dtype=dtype)
 for k in range(64):b=b+t[:,k:k+1]*d[:,k][None,:]
 return t,b
def hashes(b):return {n:p._bits_to_hex(p._dihedral(b,n)) for n in p.DIHEDRAL_NAMES}
results=[];commands=[]
for case in baseline['cases']:
 name=case['id'];d=r/'traces'/name;d.mkdir(parents=True,exist_ok=True)
 inp=r/'baseline-artifact/inputs'/(name+'.luma');assert hashlib.sha256(inp.read_bytes()).hexdigest()==case['inputSha256']
 cmd=[str(r/'pdq-instrumented'),str(inp)];commands.append({'argv':cmd,'env':{'PDQ_TRACE':str(d)}})
 run=subprocess.run(cmd,env={**os.environ,'PDQ_TRACE':str(d)},capture_output=True,text=True)
 (d/'stdout.json').write_text(run.stdout);(d/'stderr.txt').write_text(run.stderr)
 assert run.returncode==0 and json.loads(run.stdout)==case['cpp'],'STOP: instrumentation changed baseline'
 a=np.frombuffer(inp.read_bytes(),offset=16,dtype='<f4').reshape(case['height'],case['width']).astype(np.float64)
 stage={};buf=a
 for i in range(2):
  buf=p._box_1d(buf,p._window(case['width']));save(d,'py-rows-'+str(i),buf);stage['rows-'+str(i)]=stats(read(d,'rows-'+str(i),buf.shape),buf)
  buf=p._box_1d(buf.T.copy(),p._window(case['height'])).T.copy();save(d,'py-cols-'+str(i),buf);stage['cols-'+str(i)]=stats(read(d,'cols-'+str(i),buf.shape),buf)
 a=p._decimate(buf);save(d,'py-A',a);stage['A']=stats(read(d,'A',(64,64)),a)
 cd=read(d,'D',(16,64));ct=read(d,'T',(16,64));cb=read(d,'B-0',(16,16));pt,pb=dct(a,p.DCT,np.float64)
 assert np.array_equal(pb,p._dct16(a)) and hashes(pb)==case['port']['hashes']
 save(d,'py-D',p.DCT);save(d,'py-T',pt);save(d,'py-B',pb)
 stage.update({'D':stats(cd,p.DCT),'T':stats(ct,pt),'B':stats(cb,pb)})
 # Only predeclared substitutions: identical inputs, k order, no threshold changes.
 probe={}
 for label,dd,dt in [('cpp-D-f32',cd,np.float32),('rounded-python-D-f32',p.DCT.astype(np.float32),np.float32),('cpp-D-f64',cd,np.float64),('python-D-f64',p.DCT,np.float64)]:
  t,b=dct(a,dd,dt);save(d,label+'-T',t);save(d,label+'-B',b);hs=hashes(b)
  probe[label]={'TvsCpp':stats(t,ct),'BvsCpp':stats(b,cb),'cppExactVariants':sum(hs[n]==case['cpp']['hashes'][n] for n in hs),'pythonExactVariants':sum(hs[n]==case['port']['hashes'][n] for n in hs),'hashes':hs}
 assert probe['cpp-D-f32']['TvsCpp']['different']==0 and probe['cpp-D-f32']['BvsCpp']['different']==0,'STOP: software arithmetic not reproducing observed C++'
 variants=[]
 with (d/'affected-bits.csv').open('w') as f:
  writer=csv.writer(f);writer.writerow(['variant','bitIndex','row','col','cppCoefficient','cppMedian','cppMargin','pythonCoefficient','pythonMedian','pythonMargin','cppBit','pythonBit'])
  for v,n in enumerate(p.DIHEDRAL_NAMES):
   c=read(d,'B-'+str(v),(16,16));m=float(read(d,'median-'+str(v),(1,))[0]);b=p._dihedral(pb,n);pm=p._torben(b)
   assert np.array_equal(c,p._dihedral(cb,n));assert m==float(np.sort(c.reshape(-1))[127]);assert p._bits_to_hex(c)==case['cpp']['hashes'][n];assert pm==float(np.sort(b.reshape(-1))[127])
   bits=c>m;pybits=b>pm;idx=np.flatnonzero(bits!=pybits)
   for k in idx:
    i,j=divmod(int(k),16);writer.writerow([n,k,i,j,repr(float(c[i,j])),repr(m),repr(float(c[i,j])-m),repr(float(b[i,j])),repr(pm),repr(float(b[i,j])-pm),int(bits[i,j]),int(pybits[i,j])])
   variants.append({'name':n,'cppMedian':m,'pythonMedian':pm,'cppTies':int((c==m).sum()),'pythonTies':int((b==pm).sum()),'cppMaxAbs':float(np.abs(c).max()),'pythonMaxAbs':float(np.abs(b).max()),'differentBits':len(idx),'indices':idx.tolist(),'cppChangedMarginMaxAbs':float(np.abs(c.astype(float)-m).reshape(-1)[idx].max()) if len(idx) else None,'pythonChangedMarginMaxAbs':float(np.abs(b-pm).reshape(-1)[idx].max()) if len(idx) else None})
 results.append({'id':name,'instrumentationUnchanged':True,'stages':stage,'probes':probe,'variants':variants})
# Isolate scale-rounding vs final coefficient rounding; no new input.
pred=np.array([[float(np.float32(math.sqrt(2/64)))*math.cos((math.pi/2/64)*(i+1)*(2*j+1)) for j in range(64)] for i in range(16)],dtype=np.float32)
co={'cppVsRoundedPython':stats(cd,p.DCT.astype(np.float32)),'cppVsFloatScaleConstruction':stats(cd,pred),'scaleDouble':math.sqrt(2/64),'scaleFloat':float(np.float32(math.sqrt(2/64)))}
(r/'commands-run.json').write_text(json.dumps(commands,indent=2)+'\n');(r/'diagnosis.json').write_text(json.dumps({'networkDenial':'bind EPERM before import/core','baseline':baseline['summary'],'coefficientConstruction':co,'cases':results},indent=2)+'\n')
for c in results:print(c['id'],{k:v['different'] for k,v in c['stages'].items()}, {k:(v['cppExactVariants'],v['pythonExactVariants']) for k,v in c['probes'].items()})
print(co)
