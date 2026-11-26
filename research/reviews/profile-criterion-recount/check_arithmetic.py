import base64, hashlib, json
from pathlib import Path
from collections import Counter
REV = "24bb4b8483dc86966cb7c8277130bb816b0c6b3f"
ROOT = Path(__file__).resolve().parents[3]
IDENTITIES = {f["path"]: f["sha256"] for f in json.loads(
    Path(__file__).with_name("evidence-manifest.json").read_text())["files"]}
def raw(p):
    b = (ROOT / p).read_bytes()
    assert hashlib.sha256(b).hexdigest() == IDENTITIES[p], p + ": snapshot mismatch"
    return b
def doc(p): return json.loads(raw(p))
def lp(b): return len(b).to_bytes(4,"big")+b
out={"revision":REV,"files":{}}
for family,names in [("extraction-typescript",["ts.json","limits-ts.json"]),("extraction-text",["text-plain.json","limits-text.json"])]:
 prefix="test-vectors/"+family+"/"
 allv=[v for name in names for v in doc(prefix+name)["vectors"]]
 ids={v["id"]:v for v in allv}
 paired=set(x["vector"] for x in doc(prefix+"rejections.json")["rejections"]) if family=="extraction-text" else set()
 for name in names:
  d=doc(prefix+name); counts=Counter(); cross=[]
  for v in d["vectors"]:
   counts["vectors"]+=1; assert v["derivation"]=="hand"
   r=v["result"]
   if r["status"]=="error": counts["errors"]+=1; continue
   counts["positive"]+=1
   if family=="extraction-typescript":
    target=ids.get(v.get("pairedRejection"))
    if target is None: cross.append([v["id"],v.get("pairedRejection")])
    else: assert target["result"]["status"]=="error"; counts["stage1_rejected_input_pairs"]+=1
   else: assert v["id"] in paired; counts["mutated_result_pairs"]+=1
   cfg=doc(prefix+(d["configFile"] if family=="extraction-typescript" else v["config"]))
   k,w=cfg["k"],cfg["window"]; ts=r["tokens"]; data=base64.b64decode(v["inputBase64"])
   for t in ts:
    a,b=t["span"]; assert data[a:b].decode()==t["text"]; counts["token_spans"]+=1
   for ch,block in r["channels"].items():
    kept=[ts[i] for i in block.get("tokenIndices",range(len(ts)))]
    values=block.get("values",[t["text"] for t in kept])
    assert len(values)==len(kept)
    hs=[]
    for i in range(max(0,len(kept)-k+1)):
     domain=b"traceweave/token-kgram/draft-1" if family=="extraction-typescript" else b"traceweave/text-kgram/draft-1"
     m=lp(domain)+lp(cfg["profile"].encode())+lp(cfg["profileVersion"].encode())+lp(ch.encode())+k.to_bytes(4,"big")
     for t,value in zip(kept[i:i+k],values[i:i+k]): m+=lp(t["class"].encode())+lp(value.encode())
     h=hashlib.sha256(m).digest()[:8].hex(); hs.append(h)
     assert block["kgrams"][i]=={"position":i,"hash":h,"span":[kept[i]["span"][0],kept[i+k-1]["span"][1]]}, (name,v["id"],ch,i,block["kgrams"][i],h)
     counts["kgrams"]+=1
    assert len(block["kgrams"])==len(hs)
    windows=[(0,len(hs))] if 0<len(hs)<w else [(i,i+w) for i in range(max(0,len(hs)-w+1))]
    picks=[max(range(a,b), key=lambda j:(-int(hs[j],16),j)) for a,b in windows]
    assert picks==block["windowSelections"]
    assert block["partialWindow"]==(0<len(hs)<w)
    assert block["fingerprints"]==[block["kgrams"][j] for j in sorted(set(picks))]
    counts["fingerprints"]+=len(block["fingerprints"])
  out["files"][prefix+name]={**dict(counts),"cross_scope_pairs":cross}
print(json.dumps(out,indent=2))
