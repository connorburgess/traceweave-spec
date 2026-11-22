"""Runner for protocol e-img-m-1 (research/drafts/image-mark-protocol.md).

  python -I run_mark.py smoke --out out/smoke-1 [--require-network-denied] [--schemes tm,ps,dw]
  python -I run_mark.py full --frozen-commit <40-hex> --require-network-denied --out out/full-1
  python -I run_mark.py compare out/full-1 out/full-2

`smoke` uses only the smoke seeds (3,000,000-3,000,002 marked, 3,000,102-3,000,104 hosts), never
enforces the identity checks, and is never a result. `full` refuses to start (exit 2) unless the
protocol digest, the code identity, the environment, the inputs and the network probe all hold.
Exit status: 0 completed; 2 refused; 3 aborted at the time limit; 4 a validity condition failed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from twmark import attacks, env, payload  # noqa: E402

SEEDS = {
    "full": {"marked": range(2_000_000, 2_000_100), "host_offset": 102},
    "smoke": {"marked": range(3_000_000, 3_000_003), "host_offset": 102},
}
SCHEME_ORDER = ("tm", "ps", "dw")
CANDIDATES = ("tm", "ps")  # dw is the negative control: no pass line
ABORT_SECONDS = {"full": 4 * 3600, "smoke": 3600}
CLEAN_PASS = 95  # P1, out of 100 (protocol §6)

POSITIVE = ("clean",) + attacks.EDITS + attacks.REMOVALS
QUERY_KEYS = {"id", "scheme", "condition", "kind", "source", "host", "key", "sha256", "byteLength", "decode",
              "rawBits", "agreeTrue", "agreeMaxOther", "agreeMaxOtherEntry", "accepted", "outcome", "entry",
              "bch", "psnrVsMarked"}
KINDS = {"positive", "forgery", "overwrite-original", "overwrite-new", "wrong-key", "unmarked-cover", "unmarked-host"}
OUTCOMES = {"match", "no-match", "ambiguous", "abstain-undecodable", "abstain-unsupported-mode", "abstain-too-small"}
ENTRY_KEYS = {"id", "scheme", "seed", "width", "height", "coverPixelSha256", "markedPixelSha256", "markedSha256",
              "markedByteLength", "payload", "data", "quality", "belowFloor", "payloadRoundTrip"}
PSNR_FLOOR = 38.0


class AbortRun(Exception):
    pass


def entry_id(seed: int) -> str:
    return f"m{seed}"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --------------------------------------------------------------------------- search and records


def search(raw: np.ndarray, matrix: np.ndarray, ids: list[str], k: int, true_id: str | None) -> dict:
    agree = (matrix == raw[None, :]).sum(axis=1).astype(int)
    accepted = [[ids[i], int(agree[i])] for i in np.flatnonzero(agree >= k)]
    out: dict = {"accepted": accepted}
    if not accepted:
        out["outcome"] = "no-match"
    elif len(accepted) == 1:
        out["outcome"] = "match"
        out["entry"] = accepted[0][0]
    else:
        out["outcome"] = "ambiguous"
    if true_id is not None:
        t = ids.index(true_id)
        out["agreeTrue"] = int(agree[t])
        others = np.delete(agree, t)
        o = int(np.argmax(others)) if others.size else None
        out["agreeMaxOther"] = int(others[o]) if o is not None else None
        out["agreeMaxOtherEntry"] = (ids[o if o < t else o + 1]) if o is not None else None
    else:
        o = int(np.argmax(agree))
        out["agreeMaxOther"] = int(agree[o])
        out["agreeMaxOtherEntry"] = ids[o]
    return out


def validate_query(q: dict, k: int, n: int) -> list[str]:
    e = []
    extra = set(q) - QUERY_KEYS
    if extra:
        e.append(f"{q.get('id')}: unknown fields {sorted(extra)}")
    for f in ("id", "scheme", "condition", "kind", "key", "sha256", "byteLength", "decode", "outcome"):
        if f not in q:
            e.append(f"{q.get('id')}: missing {f}")
    if q.get("kind") not in KINDS:
        e.append(f"{q.get('id')}: kind {q.get('kind')}")
    if q.get("outcome") not in OUTCOMES:
        e.append(f"{q.get('id')}: outcome {q.get('outcome')}")
    if q.get("outcome", "").startswith("abstain"):
        return e
    raw = q.get("rawBits", "")
    if len(raw) * 4 != n:
        e.append(f"{q.get('id')}: rawBits length")
    acc = q.get("accepted")
    if not isinstance(acc, list) or any(m < k or m > n for _, m in acc):
        e.append(f"{q.get('id')}: accepted list")
    elif (q["outcome"] == "match") != (len(acc) == 1) or (q["outcome"] == "no-match") != (len(acc) == 0):
        e.append(f"{q.get('id')}: outcome inconsistent with accepted")
    for f in ("agreeTrue", "agreeMaxOther"):
        if f in q and q[f] is not None and not (0 <= q[f] <= n):
            e.append(f"{q.get('id')}: {f} out of range")
    return e


def validate_entry(r: dict, n: int) -> list[str]:
    e = []
    if set(r) - ENTRY_KEYS:
        e.append(f"{r.get('id')}: unknown fields {sorted(set(r) - ENTRY_KEYS)}")
    for f in ("id", "scheme", "seed", "markedSha256", "payload", "quality", "payloadRoundTrip"):
        if f not in r:
            e.append(f"{r.get('id')}: missing {f}")
    if len(r.get("payload", "")) * 4 != n:
        e.append(f"{r.get('id')}: payload length")
    return e


# --------------------------------------------------------------------------- one scheme


def run_scheme(name: str, mode: str, images: dict, deadline: float, log) -> tuple[list, list, dict, float]:
    from twimg import generator
    from twmark import schemes

    t0 = time.time()
    s = schemes.SCHEMES[name]()
    n = s.n
    k = payload.k_for(n)
    plan = SEEDS[mode]
    seeds = list(plan["marked"])
    ids = [entry_id(x) for x in seeds]
    A = np.stack([s.payload("A", i) for i in ids])
    B = np.stack([s.payload("B", i) for i in ids])
    tm_bch = getattr(s, "bch", None)
    remover = s if name == "tm" else _shared_remover()
    entries, queries = [], []
    marked_cache: dict = {}

    def check_time():
        if time.time() > deadline:
            raise AbortRun()

    # 1. Embed.
    for seed, eid in zip(seeds, ids):
        check_time()
        cover = images[seed]
        marked = s.embed(cover, "A", eid)
        mb = attacks.png(marked)
        marked = attacks.decode(mb)  # the published artifact is the PNG; use its decoded pixels
        marked_cache[eid] = (marked, mb)
        q = attacks.quality(cover, marked)
        rt = True
        if tm_bch is not None:
            for key in ("A", "B"):
                ok, data, ver = tm_bch(s.payload(key, eid))
                rt = rt and ok and ver == 1 and data == "".join(map(str, s.data(key, eid)))
        rec = {
            "id": eid, "scheme": name, "seed": seed, "width": int(cover.shape[1]), "height": int(cover.shape[0]),
            "coverPixelSha256": images["px"][seed], "markedPixelSha256": generator.pixel_sha256(marked),
            "markedSha256": sha(mb), "markedByteLength": len(mb), "payload": payload.bits_hex(A[ids.index(eid)]),
            "quality": q, "belowFloor": (q["psnr"] is not None and q["psnr"] < PSNR_FLOOR), "payloadRoundTrip": rt,
        }
        if tm_bch is not None:
            rec["data"] = "".join(map(str, s.data("A", eid)))
        entries.append(rec)
    log(f"  {name}: embedded {len(ids)} in {time.time() - t0:.1f}s")

    def query(qid, condition, kind, data: bytes, key, true_id, source, host=None, ref=None) -> np.ndarray | None:
        check_time()
        rec: dict = {"id": qid, "scheme": name, "condition": condition, "kind": kind, "source": source, "host": host,
                     "key": key, "sha256": sha(data), "byteLength": len(data)}
        try:
            rgb = attacks.decode(data)
            if getattr(s, "min_pixels", 0) and rgb.shape[0] * rgb.shape[1] < s.min_pixels:
                raise attacks.Abstain("too-small")
        except attacks.Abstain as a:
            rec["decode"] = {"status": "abstain", "code": a.code}
            rec["outcome"] = "abstain-" + a.code
            queries.append(rec)
            return None
        rec["decode"] = {"status": "ok", "width": int(rgb.shape[1]), "height": int(rgb.shape[0])}
        raw = s.raw_bits(rgb)
        rec["rawBits"] = payload.bits_hex(raw)
        rec.update(search(raw, A if key == "A" else B, ids, k, true_id))
        if tm_bch is not None:
            ok, data_bits, ver = tm_bch(raw)
            rec["bch"] = {"valid": ok, "version": ver,
                          "dataEqualsTrue": (ok and true_id is not None and data_bits == "".join(map(str, s.data(key, true_id))))}
        if ref is not None:
            rec["psnrVsMarked"] = attacks.psnr(ref, rgb)
        queries.append(rec)
        return raw

    # 2. Positives, removal, forgery, overwrite, wrong key.
    for seed, eid in zip(seeds, ids):
        marked, mb = marked_cache[eid]
        cover = images[seed]
        host_seed = seed + plan["host_offset"]
        raw_clean = query(f"{name}:{eid}:clean", "clean", "positive", mb, "A", eid, eid, ref=marked)
        for e in attacks.EDITS:
            query(f"{name}:{eid}:{e}", e, "positive", attacks.edit(e, marked), "A", eid, eid, ref=marked)
        rm = attacks.png(remover.remove(marked))
        query(f"{name}:{eid}:remark", "remark", "positive", rm, "A", eid, eid, ref=marked)
        query(f"{name}:{eid}:regen", "regen", "positive", attacks.regen(marked), "A", eid, eid, ref=marked)
        query(f"{name}:{eid}:jpeg10", "jpeg10", "positive", attacks.jpeg(marked, 10), "A", eid, eid, ref=marked)
        query(f"{name}:{eid}:noisejpeg", "noisejpeg", "positive", attacks.noise_jpeg(marked, seed), "A", eid, eid, ref=marked)
        query(f"{name}:{eid}:rotate5", "rotate5", "positive", attacks.rotate5(marked), "A", eid, eid, ref=marked)
        forged = attacks.png(attacks.transplant(marked, cover, images[host_seed]))
        query(f"{name}:{eid}:transplant", "transplant", "forgery", forged, "A", eid, eid, host=f"h{host_seed}")
        over = attacks.png(s.embed(marked, "B", eid))
        query(f"{name}:{eid}:overwrite:A", "overwrite", "overwrite-original", over, "A", eid, eid, ref=marked)
        query(f"{name}:{eid}:overwrite:B", "overwrite", "overwrite-new", over, "B", eid, eid, ref=marked)
        if raw_clean is not None:  # wrong key: the clean decode searched against key B payloads
            rec = dict(next(q for q in queries if q["id"] == f"{name}:{eid}:clean"))
            rec.update({"id": f"{name}:{eid}:wrongkey", "condition": "wrongkey", "kind": "wrong-key", "key": "B"})
            for f in ("entry", "agreeTrue", "agreeMaxOther", "agreeMaxOtherEntry", "bch", "psnrVsMarked"):
                rec.pop(f, None)
            rec.update(search(raw_clean, B, ids, k, None))
            if tm_bch is not None:
                ok, _, ver = tm_bch(raw_clean)
                rec["bch"] = {"valid": ok, "version": ver, "dataEqualsTrue": False}
            queries.append(rec)
    # 3. Unmarked: the covers of the marked images, and the hosts (never marked).
    for seed, eid in zip(seeds, ids):
        query(f"{name}:{eid}:cover", "cover", "unmarked-cover", images["coverPng"][seed], "A", None, eid)
    for seed in seeds:
        hs = seed + plan["host_offset"]
        query(f"{name}:h{hs}:host", "host", "unmarked-host", images["coverPng"][hs], "A", None, f"h{hs}")
    log(f"  {name}: {len(queries)} queries in {time.time() - t0:.1f}s")
    return entries, queries, {"n": n, "k": k, "tail": str(payload.tail(n, k)), "tailFloat": float(payload.tail(n, k)),
                              "entries": len(ids)}, round(time.time() - t0, 1)


_REMOVER = None


def _shared_remover():
    """The TrustMark-Q ReMark remover, used as a removal attack on ps and dw marks too."""
    global _REMOVER
    if _REMOVER is None:
        from twmark import schemes

        _REMOVER = schemes.TrustMarkQ(load_remover=True)
    return _REMOVER


# --------------------------------------------------------------------------- metrics


def metrics(name: str, entries: list, queries: list, info: dict) -> dict:
    by = {}
    for q in queries:
        by.setdefault(q["condition"] + ("" if q["kind"] != "overwrite-new" else ":new"), []).append(q)

    def count(qs, pred):
        return sum(1 for q in qs if pred(q))

    conds = {}
    for c, qs in sorted(by.items()):
        d = len(qs)
        row = {"denominator": d,
               "abstained": count(qs, lambda q: q["outcome"].startswith("abstain")),
               "anyAccepted": count(qs, lambda q: bool(q.get("accepted"))),
               "acceptedComparisons": sum(len(q.get("accepted") or []) for q in qs)}
        if qs[0]["kind"] in ("positive", "forgery", "overwrite-original", "overwrite-new"):
            row["acceptedAsTrue"] = count(qs, lambda q: any(e == q["source"] for e, _ in q.get("accepted") or []))
            row["correctMatch"] = count(qs, lambda q: q["outcome"] == "match" and q.get("entry") == q["source"])
            row["wrongEntryAccepted"] = count(qs, lambda q: any(e != q["source"] for e, _ in q.get("accepted") or []))
            row["agreeTrueHistogram"] = _hist(q.get("agreeTrue") for q in qs)
        row["agreeMaxOtherHistogram"] = _hist(q.get("agreeMaxOther") for q in qs)
        if name == "tm":
            row["bchValid"] = count(qs, lambda q: (q.get("bch") or {}).get("valid") is True)
            row["bchDataEqualsTrue"] = count(qs, lambda q: (q.get("bch") or {}).get("dataEqualsTrue") is True)
        if qs[0]["kind"] in ("unmarked-cover", "unmarked-host"):
            row["distinctRawStrings"] = len({q.get("rawBits") for q in qs if q.get("rawBits")})
        conds[c] = row
    psnrs = [e["quality"]["psnr"] for e in entries if e["quality"]["psnr"] is not None]
    quality = {"entries": len(entries), "identicalToCover": sum(e["quality"]["identical"] for e in entries),
               "belowFloor": sum(e["belowFloor"] for e in entries), "floor": PSNR_FLOOR,
               "psnrMin": min(psnrs) if psnrs else None, "psnrMedian": float(np.median(psnrs)) if psnrs else None,
               "psnrMax": max(psnrs) if psnrs else None}
    return {"scheme": name, "decision": info, "quality": quality, "conditions": conds, "passLine": "see verdict"}


def _hist(values) -> dict:
    h: dict = {}
    for v in values:
        if v is not None:
            h[str(v)] = h.get(str(v), 0) + 1
    return dict(sorted(h.items(), key=lambda t: int(t[0])))


def verdict(name: str, m: dict, n_entries: int) -> dict:
    c = m["conditions"]
    if name not in CANDIDATES:
        return {"passLine": "none (negative control)"}
    p1 = c["clean"]["correctMatch"]
    p2 = c["cover"]["acceptedComparisons"] + c["host"]["acceptedComparisons"]
    p3 = c["wrongkey"]["acceptedComparisons"]
    p4 = c["clean"]["wrongEntryAccepted"]
    need = CLEAN_PASS if n_entries == 100 else n_entries  # smoke: every clean query
    out = {"P1cleanCorrect": {"count": p1, "of": c["clean"]["denominator"], "passAtLeast": need, "pass": p1 >= need},
           "P2unmarkedAccepted": {"count": p2, "comparisons": (c["cover"]["denominator"] + c["host"]["denominator"]) * n_entries, "passAtMost": 0, "pass": p2 == 0},
           "P3wrongKeyAccepted": {"count": p3, "comparisons": c["wrongkey"]["denominator"] * n_entries, "passAtMost": 0, "pass": p3 == 0},
           "P4cleanWrongEntryAccepted": {"count": p4, "comparisons": c["clean"]["denominator"] * (n_entries - 1), "passAtMost": 0, "pass": p4 == 0}}
    out["met"] = all(v["pass"] for v in out.values() if isinstance(v, dict))
    return out


# --------------------------------------------------------------------------- run


def run(mode: str, out_dir: str, schemes_sel: list[str], require_denied: bool, frozen: str | None) -> int:
    start = time.time()
    deadline = start + ABORT_SECONDS[mode]
    os.makedirs(out_dir, exist_ok=True)
    lines = []

    def log(msg):
        lines.append(msg)
        print(msg, flush=True)

    summary: dict = {"protocolVersion": env.PROTOCOL_VERSION, "mode": mode, "isResult": mode == "full",
                     "notice": None if mode == "full" else "SMOKE RUN: never a result (protocol §11)"}
    recorded, computed = env.protocol_digest()
    summary["protocolDigest"] = {"recorded": recorded, "computed": computed}
    ident = env.code_identity(frozen)
    summary["codeIdentity"] = ident
    envc = env.check_environment()
    summary["environment"] = envc
    denied, probe = env.network_denied()
    summary["networkProbe"] = {"denied": denied, "detail": probe}
    import fetch_sources

    manifest = json.load(open(os.path.join(HERE, "sources.json")))
    src_err = [e for s in manifest["sources"] for e in fetch_sources.verify(s)]
    summary["sources"] = {"files": sum(len(s["files"]) for s in manifest["sources"]), "errors": src_err}
    try:
        for wid in env.weight_manifest():
            env.weight_path(wid)
        werr = []
    except env.WeightError as e:
        werr = [str(e)]
    summary["weights"] = {"sha256": env.weights_record(), "dir": "$TRACEWEAVE_EVAL_DIR/models", "errors": werr}
    summary["generatorGoldens"] = env.generator_goldens()
    inputs_ok = not src_err and not werr and not envc["deviations"] and summary["generatorGoldens"]["matched"] == 3
    refuse = []
    if mode == "full":
        if recorded is None or recorded != computed:
            refuse.append("protocol digest")
        if not ident["ok"]:
            refuse.append("code identity")
    if require_denied and not denied:
        refuse.append("network probe not denied")
    if not inputs_ok:
        refuse.append("inputs (sources, weights, environment or generator goldens)")
    summary["refused"] = refuse
    if refuse:
        json.dump(summary, open(os.path.join(out_dir, "summary.json"), "w"), indent=1, sort_keys=True)
        log("REFUSED: " + "; ".join(refuse))
        return 2

    from twimg import generator

    plan = SEEDS[mode]
    seeds = list(plan["marked"]) + [x + plan["host_offset"] for x in plan["marked"]]
    images: dict = {"px": {}, "coverPng": {}}
    for seed in seeds:
        rgb = generator.generate(seed)
        images[seed] = rgb
        images["px"][seed] = generator.pixel_sha256(rgb)
        images["coverPng"][seed] = attacks.png(rgb)
    log(f"generated {len(seeds)} images in {time.time() - start:.1f}s")

    all_entries, all_queries, per, timing = [], [], {}, {}
    try:
        for name in [x for x in SCHEME_ORDER if x in schemes_sel]:
            e, q, info, secs = run_scheme(name, mode, images, deadline, log)
            timing[name] = secs
            all_entries += e
            all_queries += q
            per[name] = (e, q, info)
    except AbortRun:
        summary.update({"status": "aborted-time-limit", "elapsedSeconds": round(time.time() - start, 1)})
        json.dump(summary, open(os.path.join(out_dir, "summary.json"), "w"), indent=1, sort_keys=True)
        log("ABORTED at the time limit; no counts are reported")
        return 3

    errors = []
    for name, (e, q, info) in per.items():
        errors += [x for r in e for x in validate_entry(r, info["n"])]
        errors += [x for r in q for x in validate_query(r, info["k"], info["n"])]
    ent_b = b"".join(env.canonical_bytes(r) + b"\n" for r in all_entries)
    qry_b = b"".join(env.canonical_bytes(r) + b"\n" for r in all_queries)
    open(os.path.join(out_dir, "entries.jsonl"), "wb").write(ent_b)
    open(os.path.join(out_dir, "queries.jsonl"), "wb").write(qry_b)
    n_entries = len(plan["marked"])
    results = {}
    for name, (e, q, info) in per.items():
        m = metrics(name, e, q, info)
        m["verdict"] = verdict(name, m, n_entries)
        m["payloadRoundTrip"] = {"ok": sum(r["payloadRoundTrip"] for r in e), "of": len(e)}
        results[name] = m
    summary["results"] = results
    summary["recordValidation"] = {"errors": errors}
    summary["resultsSha256"] = sha(sha(ent_b).encode() + sha(qry_b).encode())
    summary["statusAfterRun"] = env.git_status().splitlines()
    summary["elapsedSeconds"] = round(time.time() - start, 1)
    summary["schemeSeconds"] = timing  # timing stays outside `results` and resultsSha256
    summary["peakRssMiB"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20, 1)
    summary["crossHost"] = "not-tested"
    import torch

    summary["imports"] = env.imported_from_third_party()
    summary["torch"] = {"version": torch.__version__, "threads": torch.get_num_threads(), "device": "cpu",
                        "deterministicAlgorithms": torch.are_deterministic_algorithms_enabled()}
    validity = {
        "W1inputs": inputs_ok,
        "W2offline": denied if (mode == "full" or require_denied) else None,
        "W3determinism": "decided by `compare` on two runs",
        "W4records": not errors,
        "W5payloadRoundTrip": all(r["payloadRoundTrip"] for r in all_entries),
        "W6identity": ident["ok"] if mode == "full" else None,
    }
    summary["validity"] = validity
    summary["status"] = "completed"
    json.dump(summary, open(os.path.join(out_dir, "summary.json"), "w"), indent=1, sort_keys=True)
    log(f"done in {summary['elapsedSeconds']}s; resultsSha256 {summary['resultsSha256']}; record errors {len(errors)}")
    bad = [k for k, v in validity.items() if v is False]
    if bad:
        log("VALIDITY FAILED: " + ", ".join(bad))
        return 4
    return 0


def compare(a: str, b: str) -> int:
    same = True
    for f in ("entries.jsonl", "queries.jsonl"):
        x, y = open(os.path.join(a, f), "rb").read(), open(os.path.join(b, f), "rb").read()
        print(f, "identical" if x == y else "DIFFERENT", sha(x)[:16], sha(y)[:16])
        same = same and x == y
    sa, sb = (json.load(open(os.path.join(d, "summary.json"))) for d in (a, b))
    eq = sa.get("resultsSha256") == sb.get("resultsSha256") and sa.get("results") == sb.get("results")
    print("resultsSha256 and results", "equal" if eq else "DIFFERENT")
    return 0 if (same and eq) else 1


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for m in ("smoke", "full"):
        p = sub.add_parser(m)
        p.add_argument("--out", required=True)
        p.add_argument("--require-network-denied", action="store_true")
        p.add_argument("--schemes", default=",".join(SCHEME_ORDER))
        if m == "full":
            p.add_argument("--frozen-commit", required=True)
    c = sub.add_parser("compare")
    c.add_argument("a")
    c.add_argument("b")
    a = ap.parse_args(argv)
    if a.cmd == "compare":
        return compare(a.a, a.b)
    sel = a.schemes.split(",")
    if a.cmd == "full" and sorted(sel) != sorted(SCHEME_ORDER):
        print("full mode runs all three schemes")
        return 2
    return run(a.cmd, a.out, sel, a.require_network_denied, getattr(a, "frozen_commit", None))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
