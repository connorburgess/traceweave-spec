from pathlib import Path
import json,runpy,sys,socket,errno
# Reuse definitions without rerunning diagnose core calls.
r=Path(__file__).resolve().parent
scope={'__file__':str(r/'diagnose.py')};exec((r/'diagnose.py').read_text().split('results=[];commands=[]')[0],scope)
np=scope['np'];p=scope['p'];stats=scope['stats'];hashes=scope['hashes'];save=scope['save'];read=scope['read']
def mixed(a,d,mode):
 def mat(left,right):
  out=np.zeros((left.shape[0],right.shape[1]),dtype=np.float64 if mode=='wide-sum' else np.float32)
  for k in range(64):
   prod=left[:,k:k+1].astype(np.float32)*right[k:k+1,:].astype(np.float32) if mode=='wide-sum' else left[:,k:k+1].astype(np.float64)*right[k:k+1,:].astype(np.float64)
   out=(out+prod).astype(out.dtype)
  return out.astype(np.float32)
 t=mat(d,a);return t,mat(t,d.T)
rows=[]
for case in scope['baseline']['cases']:
 d=r/'traces'/case['id'];a=read(d,'A',(64,64));dd=read(d,'D',(16,64));ct=read(d,'T',(16,64));cb=read(d,'B-0',(16,16));out={'id':case['id']}
 for mode in ['wide-sum','wide-product']:
  t,b=mixed(a,dd,mode);save(d,mode+'-T',t);save(d,mode+'-B',b);hs=hashes(b)
  out[mode]={'TvsCpp':stats(t,ct),'BvsCpp':stats(b,cb),'cppExactVariants':sum(hs[n]==case['cpp']['hashes'][n] for n in hs),'pythonExactVariants':sum(hs[n]==case['port']['hashes'][n] for n in hs),'hashes':hs}
 rows.append(out)
(r/'mixed-probes.json').write_text(json.dumps(rows,indent=2)+'\n')
for row in rows:print(row['id'],{k:(v['cppExactVariants'],v['pythonExactVariants'],v['BvsCpp']['different']) for k,v in row.items() if k!='id'})
