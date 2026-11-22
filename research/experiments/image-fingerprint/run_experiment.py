"""E-IMG-F harness: PDQ and ISCC Image-Code on seeded synthetic images.

Implements research/drafts/image-experiment-protocol.md. Modes:

  smoke   20 images from a seed range disjoint from the experiment; NOT A RESULT.
  full    the frozen protocol: 2,000 images, 6,000 + 3,000 edited queries. Refuses to start
          unless the protocol digest, the environment pin and the vector checks all hold.
  compare DIR_A DIR_B   two-run determinism check (resultsSha256 and catalogue digests).

Nothing is read from the network or from disk other than this directory's code and the
vector files. Images are generated in memory and never written; only hashes are recorded.
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import resource
import socket
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "vendor", "threatexchange_pdq"))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from pdqhashing.hasher.pdq_hasher import PDQHasher  # noqa: E402
from pdqhashing.utils.matrix import MatrixUtil  # noqa: E402
from twimg import generator, transforms  # noqa: E402
from twimg.decode import Abstain, decode  # noqa: E402
from twimg.iscc_img import iscc_from_rgb  # noqa: E402
from twimg.pdq_np import DIHEDRAL_NAMES, luma_from_rgb, pdq_from_luma  # noqa: E402
from twimg.profile import (  # noqa: E402
    EXTRACTION_CONFIG,
    canonical,
    MATCHING_CONFIG,
    check_environment,
    environment,
    extraction_config_sha256,
    matching_config_sha256,
)

PROTOCOL = os.path.join(HERE, "..", "..", "drafts", "image-experiment-protocol.md")
PROTOCOL_VERSION = "e-img-f-1"
ABORT_SECONDS = 4 * 3600
PDQ_T = MATCHING_CONFIG["pdq"]["threshold"]
PDQ_QUALITY_FLOOR = EXTRACTION_CONFIG["pdq"]["qualityFloor"]
EXTRACTORS = ("pdq", "iscc")

# Seed plan (protocol §3). Each split is a contiguous seed range.
SPLITS = {
    "full": {
        "selection": {"catalogue": range(0, 250), "negatives": range(250, 500)},
        "evaluation": {"catalogue": range(500, 1000), "negatives": range(1000, 2000)},
        "vendorQueryEntries": 50,
    },
    "smoke": {
        "selection": {"catalogue": range(1_000_000, 1_000_004), "negatives": range(1_000_004, 1_000_008)},
        "evaluation": {"catalogue": range(1_000_008, 1_000_012), "negatives": range(1_000_012, 1_000_020)},
        "vendorQueryEntries": 2,
    },
}


class AbortRun(Exception):
    pass


# --------------------------------------------------------------------------- helpers


def protocol_digest(path: str = PROTOCOL) -> tuple[str | None, str]:
    """(recorded, computed). The recorded digest is the 64-hex value on the line
    'Protocol digest (SHA-256, self-excluding): `...`'; it is computed over the file with that
    value replaced by 64 zeros."""
    if not os.path.exists(path):
        return None, None
    with open(path, "rb") as fh:
        text = fh.read()
    m = re.search(rb"Protocol digest \(SHA-256, self-excluding\): `([0-9a-f]{64})`", text)
    recorded = m.group(1).decode() if m else None
    zeroed = re.sub(
        rb"(Protocol digest \(SHA-256, self-excluding\): `)[0-9a-f]{64}(`)",
        rb"\g<1>" + b"0" * 64 + rb"\g<2>",
        text,
    )
    return recorded, hashlib.sha256(zeroed).hexdigest()


def network_denied() -> tuple[bool, str]:
    """True if the OS refuses both a local bind and an outbound connect (sandbox-exec deny
    network*). Contacts no remote service: an allowed connect is closed at once."""
    notes = []
    denied_bind = denied_connect = False
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 0))
        notes.append("bind allowed")
    except OSError as e:
        denied_bind = e.errno in (errno.EPERM, errno.EACCES)
        notes.append(f"bind refused errno {e.errno}")
    finally:
        s.close()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect(("1.1.1.1", 443))
        notes.append("connect allowed")
    except OSError as e:
        denied_connect = e.errno in (errno.EPERM, errno.EACCES)
        notes.append(f"connect refused errno {e.errno}")
    finally:
        s.close()
    return denied_bind and denied_connect, "; ".join(notes)


def hex_to_bytes_matrix(hexes: list[str]) -> np.ndarray:
    return np.frombuffer(b"".join(bytes.fromhex(h) for h in hexes), dtype=np.uint8).reshape(len(hexes), -1)


def canonical_bytes(obj) -> bytes:
    """Catalogue-contract canonical JSON: sorted keys, no whitespace, no trailing newline."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


ENTRY_KEYS = {"id", "seed", "pixelSha256", "sha256", "byteLength", "decode", "pdq", "iscc"}
DECODE_OK_KEYS = {"status", "format", "sourceMode", "width", "height", "exifOrientation", "iccPresent"}


def validate_catalogue(b: bytes) -> list[str]:
    """C6: canonical bytes, profile binding, sorted unique ids, closed field sets."""
    errs = []
    cat = json.loads(b)
    if canonical_bytes(cat) != b:
        errs.append("not canonical")
    if cat.get("catalogueVersion") != "traceweave-image-catalogue-draft-1":
        errs.append("catalogueVersion")
    cfg = cat.get("extractionConfig")
    if hashlib.sha256(canonical(cfg)).hexdigest() != cat["profile"]["configSha256"] or cat["profile"]["configSha256"] != extraction_config_sha256():
        errs.append("extraction config binding")
    if cat.get("matchingConfigSha256") != matching_config_sha256():
        errs.append("matching config binding")
    ids = [a["id"] for a in cat["artifacts"]]
    if ids != sorted(set(ids)):
        errs.append("ids not strictly increasing")
    if len({a["sha256"] for a in cat["artifacts"]}) != len(ids):
        errs.append("duplicate artifact bytes")
    for a in cat["artifacts"]:
        if set(a) != ENTRY_KEYS:
            errs.append(f"{a.get('id')}: entry keys")
        d = a["decode"]
        if d["status"] == "ok" and set(d) != DECODE_OK_KEYS:
            errs.append(f"{a['id']}: decode keys")
        if d["status"] != "ok" and set(d) != {"status", "code"}:
            errs.append(f"{a['id']}: decode abstain keys")
        for x, n in (("pdq", 64), ("iscc", 16)):
            e = a[x]
            if e["status"] == "ok":
                if not re.fullmatch(f"[0-9a-f]{{{n}}}", e.get("hash", "")):
                    errs.append(f"{a['id']}: {x} hash")
                if set(e) - {"status", "hash", "quality"}:
                    errs.append(f"{a['id']}: {x} keys")
            elif set(e) - {"status", "code", "quality"}:
                errs.append(f"{a['id']}: {x} abstain keys")
    return errs


VENDOR = PDQHasher()


def vendor_pdq(rgb: np.ndarray) -> tuple[dict, int]:
    r, c = rgb.shape[:2]
    x = VENDOR.dihedralFromBufferedImage(
        Image.fromarray(rgb, "RGB"),
        MatrixUtil.allocateMatrixAsRowMajorArray(r, c),
        MatrixUtil.allocateMatrixAsRowMajorArray(r, c),
        MatrixUtil.allocateMatrix(64, 64),
        MatrixUtil.allocateMatrix(16, 64),
        MatrixUtil.allocateMatrix(16, 16),
        MatrixUtil.allocateMatrix(16, 16),
        0xFF,
    )
    attrs = ["hash", "hashRotate90", "hashRotate180", "hashRotate270", "hashFlipX", "hashFlipY", "hashFlipPlus1", "hashFlipMinus1"]
    return {n: str(getattr(x, a)) for n, a in zip(DIHEDRAL_NAMES, attrs)}, x.quality


# --------------------------------------------------------------------------- extraction


def extract(data: bytes) -> tuple[dict, np.ndarray | None]:
    """Profile extraction of one input. Returns the record fragment for both extractors."""
    rec: dict = {"sha256": hashlib.sha256(data).hexdigest(), "byteLength": len(data)}
    try:
        rgb, info = decode(data)
    except Abstain as a:
        rec["decode"] = {"status": "abstain", "code": a.code}
        for x in EXTRACTORS:
            rec[x] = {"status": "abstain", "code": a.code}
        return rec, None
    rec["decode"] = {"status": "ok", **info}
    hashes, quality = pdq_from_luma(luma_from_rgb(rgb), dihedral=True)
    if quality < PDQ_QUALITY_FLOOR:
        rec["pdq"] = {"status": "abstain", "code": "low-quality", "quality": quality}
    else:
        rec["pdq"] = {"status": "ok", "quality": quality, "hashes": hashes}
    rec["iscc"] = {"status": "ok", "hashes": iscc_from_rgb(rgb, dihedral=True)}
    return rec, rgb


# --------------------------------------------------------------------------- matching


def nearest(query_hashes: dict, cat_ids: list[str], cat_matrix: np.ndarray) -> np.ndarray:
    """Distances from one query (8 dihedral variants) to every enrolled entry: min over variants."""
    q = hex_to_bytes_matrix([query_hashes[n] for n in DIHEDRAL_NAMES])  # 8 x B
    x = np.bitwise_xor(q[:, None, :], cat_matrix[None, :, :])  # 8 x E x B
    return np.bitwise_count(x).sum(axis=2, dtype=np.int64).min(axis=0)  # E


def decide(dist: np.ndarray, cat_ids: list[str], threshold: int, true_id: str | None) -> dict:
    out: dict = {}
    within = np.nonzero(dist <= threshold)[0] if threshold >= 0 else np.array([], dtype=np.int64)
    matched = sorted((int(dist[i]), cat_ids[i]) for i in within)
    if not matched:
        out["outcome"] = "no-match"
    else:
        best = matched[0][0]
        tops = [i for d, i in matched if d == best]
        if len(tops) > 1:
            out["outcome"] = "abstain-ambiguous"
        else:
            out["outcome"] = "match"
            out["entry"] = tops[0]
        out["distance"] = best
    out["withinThreshold"] = [[i, d] for d, i in matched][:20]
    out["withinThresholdCount"] = len(matched)
    if true_id is not None:
        idx = {c: k for k, c in enumerate(cat_ids)}
        if true_id in idx:
            out["trueDistance"] = int(dist[idx[true_id]])
            wrong = np.delete(dist, idx[true_id])
            wrong_ids = [c for c in cat_ids if c != true_id]
        else:
            wrong, wrong_ids = dist, cat_ids
        out["wrongWithinThreshold"] = sum(1 for d, i in matched if i != true_id)
        if len(wrong):
            k = int(np.argmin(wrong))
            out["nearestWrong"] = [wrong_ids[k], int(wrong[k])]
    else:
        if len(dist):
            k = int(np.argmin(dist))
            out["nearest"] = [cat_ids[k], int(dist[k])]
    return out


# --------------------------------------------------------------------------- run


def run(mode: str, out_dir: str, require_network_denied: bool, vendor_check: bool) -> int:
    t0 = time.time()
    plan = SPLITS[mode]
    os.makedirs(out_dir, exist_ok=True)
    meta: dict = {
        "protocolVersion": PROTOCOL_VERSION,
        "mode": mode,
        "label": "SMOKE RUN - NOT A RESULT" if mode == "smoke" else "MEASURED RUN",
        "extractionConfigSha256": extraction_config_sha256(),
        "matchingConfigSha256": matching_config_sha256(),
        "generator": generator.GENERATOR_ID,
        "environment": environment(),
    }
    rec_digest, comp_digest = protocol_digest()
    meta["protocolDigest"] = {"recorded": rec_digest, "computed": comp_digest}
    env_dev = check_environment()
    meta["environmentDeviations"] = env_dev
    denied, note = network_denied()
    meta["networkDenied"] = {"denied": denied, "probe": note}

    if mode == "full":
        problems = []
        if rec_digest is None or rec_digest != comp_digest:
            problems.append("protocol digest missing or mismatched")
        if env_dev:
            problems.append("environment deviates from pin: " + "; ".join(env_dev))
        if require_network_denied and not denied:
            problems.append("network not denied: " + note)
        vec = os.path.join(HERE, "vectors", "check-results.json")
        if not os.path.exists(vec):
            problems.append("vectors/check-results.json missing; run check_vectors.py")
        else:
            v = json.load(open(vec))
            core = v["pdqCorePortVsVendor"]
            ic = v["isccConformance"]
            if core["equal"] != core["total"] or ic["compiledDctEqual"] != ic["total"]:
                problems.append("vector conformance failed")
            meta["vectorChecks"] = {"pdqCore": core, "iscc": {k: ic[k] for k in ("compiledDctEqual", "pureDctEqual", "total")}}
        if problems:
            print("REFUSING full run:\n  " + "\n  ".join(problems))
            return 2
    elif require_network_denied and not denied:
        print("network not denied: " + note)
        return 2

    peak_check = []
    vendor_mismatch = []
    vendor_compared = 0

    def check_time():
        if time.time() - t0 > ABORT_SECONDS:
            raise AbortRun()

    def vendor_compare(qid, rgb, rec):
        nonlocal vendor_compared
        if not vendor_check or rgb is None:
            return
        vh, vq = vendor_pdq(rgb)
        nh = rec["pdq"].get("hashes")
        nq = rec["pdq"].get("quality")
        vendor_compared += 1
        if nq != vq or (nh is not None and nh != vh) or (nh is None and vq >= PDQ_QUALITY_FLOOR):
            vendor_mismatch.append(qid)

    results: dict = {"catalogues": {}, "queries": [], "selectionRule": None}
    split_state: dict = {}
    try:
        for split in ("selection", "evaluation"):
            cat_seeds = list(plan[split]["catalogue"])
            neg_seeds = list(plan[split]["negatives"])
            # Enrollment.
            entries = []
            for seed in cat_seeds:
                check_time()
                rgb0 = generator.generate(seed)
                data = transforms.encode_original(rgb0)
                rec, rgb = extract(data)
                eid = f"s{seed:07d}"
                vendor_compare(eid, rgb, rec)
                entry = {"id": eid, "seed": seed, "pixelSha256": generator.pixel_sha256(rgb0), **rec}
                for x in EXTRACTORS:
                    if rec[x]["status"] == "ok":
                        entry[x] = {"status": "ok", "hash": rec[x]["hashes"]["orig"], **({"quality": rec[x]["quality"]} if "quality" in rec[x] else {})}
                entries.append(entry)
            entries.sort(key=lambda e: e["id"])
            catalogue = {
                "catalogueVersion": "traceweave-image-catalogue-draft-1",
                "profile": {"configSha256": extraction_config_sha256(), "id": EXTRACTION_CONFIG["profile"], "version": EXTRACTION_CONFIG["profileVersion"]},
                "extractionConfig": EXTRACTION_CONFIG,
                "matchingConfigSha256": matching_config_sha256(),
                "split": split,
                "artifacts": entries,
            }
            cbytes = canonical_bytes(catalogue)
            with open(os.path.join(out_dir, f"catalogue-{split}.json"), "wb") as fh:
                fh.write(cbytes)
            results["catalogues"][split] = {"sha256": hashlib.sha256(cbytes).hexdigest(), "entries": len(entries)}
            results.setdefault("catalogueValidation", {})[split] = validate_catalogue(cbytes)

            enrolled = {}
            for x in EXTRACTORS:
                ok = [e for e in entries if e[x]["status"] == "ok"]
                ids = [e["id"] for e in ok]
                enrolled[x] = (ids, hex_to_bytes_matrix([e[x]["hash"] for e in ok]) if ok else np.zeros((0, 32 if x == "pdq" else 8), np.uint8))

            # Queries: 12 edits of every catalogue original, then the never-enrolled negatives.
            queries = []
            # Originals are regenerated here rather than held in memory (about 1.6 GB for 500).
            cat_ids = sorted(e["id"] for e in entries)
            seed_of = {e["id"]: e["seed"] for e in entries}
            vendor_entries = set(cat_ids[: plan["vendorQueryEntries"]]) if split == "evaluation" else set()
            for eid in cat_ids:
                rgb0 = generator.generate(seed_of[eid])
                for tname in transforms.TRANSFORMS:
                    check_time()
                    data = transforms.apply(tname, rgb0)
                    rec, rgb = extract(data)
                    qid = f"{eid}.{tname}"
                    if eid in vendor_entries:
                        vendor_compare(qid, rgb, rec)
                    queries.append({"id": qid, "split": split, "kind": "positive", "source": eid, "transform": tname, **rec})
            for seed in neg_seeds:
                check_time()
                rgb0 = generator.generate(seed)
                rec, rgb = extract(transforms.encode_original(rgb0))
                qid = f"s{seed:07d}.neg"
                vendor_compare(qid, rgb, rec)
                queries.append({"id": qid, "split": split, "kind": "negative", "source": None, "transform": None, "pixelSha256": generator.pixel_sha256(rgb0), **rec})

            # Distances for every query and extractor.
            for q in queries:
                for x in EXTRACTORS:
                    if q[x]["status"] != "ok":
                        continue
                    ids, mat = enrolled[x]
                    q[x]["_dist"] = nearest(q[x]["hashes"], ids, mat) if len(ids) else np.zeros(0, np.int64)

            # Thresholds. The ISCC threshold is fixed from the selection split only, before any
            # evaluation query is scored (selection-rule-1, protocol §5).
            if split == "selection":
                rule = {}
                for x in EXTRACTORS:
                    ids = enrolled[x][0]
                    dmins = []
                    for q in queries:
                        if q[x]["status"] != "ok" or not len(ids):
                            continue
                        d = q[x]["_dist"]
                        if q["kind"] == "negative":
                            dmins.append(int(d.min()))
                        else:
                            mask = np.array([i != q["source"] for i in ids])
                            if mask.any():
                                dmins.append(int(d[mask].min()))
                    rule[x] = {"nullComparisonsMinDistance": min(dmins) if dmins else None, "nullQueries": len(dmins)}
                d_min = rule["iscc"]["nullComparisonsMinDistance"]
                iscc_t = (d_min - 1) if d_min is not None else -1
                rule["iscc"]["threshold"] = iscc_t
                rule["pdq"]["threshold"] = PDQ_T
                rule["rule"] = "selection-rule-1: T_iscc = (minimum over selection null comparisons of the min-over-dihedral Hamming distance) - 1"
                results["selectionRule"] = rule
                with open(os.path.join(out_dir, "selection-threshold.json"), "w") as fh:
                    fh.write(json.dumps(rule, indent=1, sort_keys=True) + "\n")
                split_state["thresholds"] = {"pdq": PDQ_T, "iscc": iscc_t}

            th = split_state["thresholds"]
            for q in queries:
                for x in EXTRACTORS:
                    if q[x]["status"] != "ok":
                        q[x]["outcome"] = "abstain-" + q[x]["code"]
                        continue
                    ids = enrolled[x][0]
                    true_id = q["source"] if q["kind"] == "positive" else None
                    q[x].update(decide(q[x].pop("_dist"), ids, th[x], true_id))
            results["queries"].extend(queries)
            results.setdefault("enrollment", {})[split] = {
                x: {"enrolled": len(enrolled[x][0]), "catalogue": len(entries), "abstained": {c: sum(1 for e in entries if e[x]["status"] != "ok" and e[x]["code"] == c) for c in sorted({e[x]["code"] for e in entries if e[x]["status"] != "ok"})}}
                for x in EXTRACTORS
            }
    except AbortRun:
        meta["status"] = "aborted-time-limit"
        meta["elapsedSeconds"] = round(time.time() - t0, 1)
        open(os.path.join(out_dir, "summary.json"), "w").write(json.dumps(meta, indent=1, sort_keys=True) + "\n")
        print("ABORTED at time limit; nothing here is a result")
        return 3

    # Records (deterministic part) and digest.
    results["queries"].sort(key=lambda q: (q["split"], q["id"]))
    qbytes = b"".join(canonical_bytes(q) + b"\n" for q in results["queries"])
    open(os.path.join(out_dir, "queries.jsonl"), "wb").write(qbytes)
    det = {
        "catalogues": results["catalogues"],
        "queriesSha256": hashlib.sha256(qbytes).hexdigest(),
        "selectionRule": results["selectionRule"],
    }
    results_sha = hashlib.sha256(canonical_bytes(det)).hexdigest()

    metrics = compute_metrics(results, split_state["thresholds"])
    elapsed = time.time() - t0
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # bytes on macOS
    summary = {
        **meta,
        "status": "completed",
        "thresholds": split_state["thresholds"],
        "deterministic": det,
        "resultsSha256": results_sha,
        "enrollment": results["enrollment"],
        "catalogueValidation": results["catalogueValidation"],
        "vendorCrossCheck": {"compared": vendor_compared, "mismatches": len(vendor_mismatch), "mismatchIds": vendor_mismatch[:50]},
        "elapsedSeconds": round(elapsed, 1),
        "peakRssBytes": int(peak),
        "counts": {"queries": len(results["queries"])},
    }
    if mode == "full":
        summary["metrics"] = metrics
        summary["criteria"] = criteria(metrics, vendor_mismatch)
        summary["validity"] = validity(summary)
    else:
        # A smoke run records only that the pipeline completed; its match figures are withheld
        # from the summary so they cannot be read as results (they remain in queries.jsonl).
        summary["metricsWithheld"] = True
    open(os.path.join(out_dir, "summary.json"), "w").write(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print(f"{summary['label']}: {len(results['queries'])} queries, {elapsed:.1f} s, peak RSS {peak / 2**20:.0f} MiB")
    print(f"resultsSha256 {results_sha}")
    print(f"vendor cross-check {vendor_compared - len(vendor_mismatch)}/{vendor_compared} equal")
    return 0


# --------------------------------------------------------------------------- metrics


def compute_metrics(results: dict, thresholds: dict) -> dict:
    m: dict = {}
    for split in ("selection", "evaluation"):
        qs = [q for q in results["queries"] if q["split"] == split]
        m[split] = {}
        for x in EXTRACTORS:
            per: dict = {}
            for tname in transforms.TRANSFORMS:
                sub = [q for q in qs if q["kind"] == "positive" and q["transform"] == tname]
                o = [q[x]["outcome"] for q in sub]
                hist: dict = {}
                for q in sub:
                    if "trueDistance" in q[x]:
                        hist[q[x]["trueDistance"]] = hist.get(q[x]["trueDistance"], 0) + 1
                per[tname] = {
                    "n": len(sub),
                    "correctMatch": sum(1 for q in sub if q[x]["outcome"] == "match" and q[x]["entry"] == q["source"]),
                    "wrongTopMatch": sum(1 for q in sub if q[x]["outcome"] == "match" and q[x]["entry"] != q["source"]),
                    "anyWrongWithinThreshold": sum(1 for q in sub if q[x].get("wrongWithinThreshold", 0) > 0),
                    "ambiguous": o.count("abstain-ambiguous"),
                    "noMatch": o.count("no-match"),
                    "abstain": {c: o.count(c) for c in sorted(set(o)) if c.startswith("abstain-") and c != "abstain-ambiguous"},
                    "trueDistanceHistogram": {str(k): hist[k] for k in sorted(hist)},
                }
            negs = [q for q in qs if q["kind"] == "negative"]
            o = [q[x]["outcome"] for q in negs]
            nh: dict = {}
            for q in negs:
                if "nearest" in q[x]:
                    d = q[x]["nearest"][1]
                    nh[d] = nh.get(d, 0) + 1
            wrong_hist: dict = {}
            for q in qs:
                if q["kind"] == "positive" and "nearestWrong" in q[x]:
                    d = q[x]["nearestWrong"][1]
                    wrong_hist[d] = wrong_hist.get(d, 0) + 1
            m[split][x] = {
                "threshold": thresholds[x],
                "positives": per,
                "positivesTotal": {
                    "n": sum(v["n"] for v in per.values()),
                    "anyWrongWithinThreshold": sum(v["anyWrongWithinThreshold"] for v in per.values()),
                    "wrongTopMatch": sum(v["wrongTopMatch"] for v in per.values()),
                },
                "negatives": {
                    "n": len(negs),
                    "anyWithinThreshold": sum(1 for q in negs if q[x].get("withinThresholdCount", 0) > 0),
                    "outcomes": {c: o.count(c) for c in sorted(set(o))},
                    "nearestDistanceHistogram": {str(k): nh[k] for k in sorted(nh)},
                },
                "positivesNearestWrongHistogram": {str(k): wrong_hist[k] for k in sorted(wrong_hist)},
            }
    return m


def criteria(metrics: dict, vendor_mismatch: list) -> dict:
    """Protocol §6 failure criteria on the evaluation split, per extractor."""
    out = {}
    for x in EXTRACTORS:
        e = metrics["evaluation"][x]
        p = e["positives"]
        f1 = e["negatives"]["anyWithinThreshold"] >= 1
        f2 = e["positivesTotal"]["anyWrongWithinThreshold"] > 5
        f3 = any(p[t]["correctMatch"] * 100 < 95 * p[t]["n"] for t in ("jpeg75", "png"))
        out[x] = {
            "F1-negative-within-threshold": f1,
            "F2-more-than-5-wrong-entry-queries": f2,
            "F3-recall-below-95-jpeg75-or-png": f3,
            "fails": f1 or f2 or f3,
        }
    out["C2-vendor-cross-check-mismatch"] = bool(vendor_mismatch)
    return out


def validity(summary: dict) -> dict:
    """C1, C2, C4, C5, C6 as observed in one run (C3 needs two runs: compare)."""
    vc = summary.get("vectorChecks", {})
    return {
        "C1-vectors": bool(vc) and vc["pdqCore"]["equal"] == vc["pdqCore"]["total"] and vc["iscc"]["compiledDctEqual"] == vc["iscc"]["total"],
        "C2-vendor-cross-check": summary["vendorCrossCheck"]["mismatches"] == 0 and summary["vendorCrossCheck"]["compared"] > 0,
        "C4-environment-and-digest": not summary["environmentDeviations"] and summary["protocolDigest"]["recorded"] == summary["protocolDigest"]["computed"],
        "C5-network-denied": summary["networkDenied"]["denied"],
        "C6-catalogues": all(not v for v in summary["catalogueValidation"].values()),
    }


def compare(a: str, b: str) -> int:
    sa = json.load(open(os.path.join(a, "summary.json")))
    sb = json.load(open(os.path.join(b, "summary.json")))
    same = sa["resultsSha256"] == sb["resultsSha256"]
    files_same = all(
        open(os.path.join(a, f), "rb").read() == open(os.path.join(b, f), "rb").read()
        for f in ("catalogue-selection.json", "catalogue-evaluation.json", "queries.jsonl", "selection-threshold.json")
    )
    print(f"resultsSha256 equal: {same}; record files byte-identical: {files_same}")
    return 0 if same and files_same else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["smoke", "full", "compare"])
    ap.add_argument("dirs", nargs="*")
    ap.add_argument("--out", default=None)
    ap.add_argument("--require-network-denied", action="store_true")
    ap.add_argument("--no-vendor-check", action="store_true")
    a = ap.parse_args()
    if a.mode == "compare":
        return compare(*a.dirs)
    out = a.out or os.path.join(HERE, "out", a.mode)
    return run(a.mode, out, a.require_network_denied, not a.no_vendor_check)


if __name__ == "__main__":
    sys.exit(main())
