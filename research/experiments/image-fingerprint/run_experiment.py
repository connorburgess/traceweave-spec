"""E-IMG-F harness: PDQ and ISCC Image-Code on seeded synthetic images.

Implements research/drafts/image-experiment-protocol.md. Modes:

  smoke   20 images from a seed range disjoint from the experiment; NOT A RESULT.
  full    the frozen contract check: 200 images (100 enrolled, 100 never enrolled) and
          1,200 edited queries. Refuses to start unless the protocol digest, the environment
          pin, the vector checks and the network probe all hold.
  compare DIR_A DIR_B   two-run determinism check (byte comparison of the record files).

Match and false-match counts are reported without any pass line. The run is judged only on
the validity conditions V1-V5 (protocol section 6).

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
import subprocess
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
PROTOCOL_VERSION = "e-img-f-2"
ABORT_SECONDS = 4 * 3600
PDQ_T = MATCHING_CONFIG["pdq"]["threshold"]
ISCC_T = MATCHING_CONFIG["iscc"]["threshold"]
PDQ_QUALITY_FLOOR = EXTRACTION_CONFIG["pdq"]["qualityFloor"]
EXTRACTORS = ("pdq", "iscc")

# Seed plan (protocol §3). Contiguous seed ranges.
SPLITS = {
    "full": {"catalogue": range(0, 100), "negatives": range(100, 200)},
    "smoke": {"catalogue": range(1_000_000, 1_000_010), "negatives": range(1_000_010, 1_000_020)},
}
SPLIT_LABEL = "contract"


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
    """True if the OS sandbox refuses both a local bind and a loopback connect.

    Refused by design: nothing listens on 127.0.0.1 port 1, so with the network allowed the
    connect fails with ECONNREFUSED; under sandbox-exec deny network* it fails with EPERM. No
    packet ever leaves the host, whether or not the network is denied."""
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
        s.connect(("127.0.0.1", 1))
        notes.append("loopback connect accepted")
    except OSError as e:
        denied_connect = e.errno in (errno.EPERM, errno.EACCES)
        notes.append(f"loopback connect refused errno {e.errno} ({errno.errorcode.get(e.errno, '?')})")
    finally:
        s.close()
    return denied_bind and denied_connect, "; ".join(notes)


FROZEN_PATHS = (
    "research/experiments/image-fingerprint",
    "research/drafts/image-experiment-protocol.md",
    "research/drafts/extraction-profile-image.md",
)


def _git(*args: str) -> tuple[int, str]:
    r = subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def git_status() -> str:
    """Porcelain status of the whole work tree, untracked files included (ignored files excluded)."""
    return _git("status", "--porcelain", "--untracked-files=all")[1]


def code_identity(frozen_commit: str | None) -> dict:
    """The identity checks of protocol §8, logged verbatim into summary.json."""
    rc_head, head = _git("rev-parse", "HEAD")
    status = git_status()
    out: dict = {
        "frozenCommit": frozen_commit,
        "head": head if rc_head == 0 else None,
        "statusPorcelain": status.splitlines(),
        "protocolVersionInFile": None,
    }
    with open(PROTOCOL, "rb") as fh:
        m = re.search(rb"Protocol version: `([a-z0-9-]+)`", fh.read())
    out["protocolVersionInFile"] = m.group(1).decode() if m else None
    if frozen_commit:
        rc_diff, diff = _git("diff", "--exit-code", "--stat", frozen_commit, "--", *FROZEN_PATHS)
        rc_anc, _ = _git("merge-base", "--is-ancestor", frozen_commit, "HEAD")
        out["diffAgainstFrozen"] = {"exitCode": rc_diff, "stat": diff.splitlines()}
        out["frozenIsAncestorOfHead"] = rc_anc == 0
    out["ok"] = bool(
        frozen_commit
        and out["head"] == frozen_commit
        and status == ""
        and out["diffAgainstFrozen"]["exitCode"] == 0
        and out["frozenIsAncestorOfHead"]
        and out["protocolVersionInFile"] == PROTOCOL_VERSION
    )
    return out


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
    out["withinThreshold"] = [[i, d] for d, i in matched]
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


# --------------------------------------------------------------------------- query records

OUTCOMES = {"match", "no-match", "abstain-ambiguous"} | {"abstain-" + c for c in (
    "input-too-large", "undecodable", "unsupported-format", "unsupported-bit-depth", "multi-frame", "too-many-pixels",
    "unsupported-mode", "too-small", "low-quality")}
QUERY_KEYS = {"id", "split", "kind", "source", "transform", "sha256", "byteLength", "decode", "pdq", "iscc"}
EXTRACTOR_OK_KEYS = {"status", "quality", "hashes", "outcome", "entry", "distance", "withinThreshold",
                     "withinThresholdCount", "trueDistance", "wrongWithinThreshold", "nearestWrong", "nearest"}
BITS = {"pdq": 256, "iscc": 64}


def validate_query(q: dict, entry_ids: set) -> list[str]:
    """V5: a query line has the closed field set of protocol §10 and internally consistent values."""
    e = []
    qid = q.get("id", "?")
    keys = set(q)
    want = QUERY_KEYS | ({"pixelSha256"} if q.get("kind") == "negative" else set())
    if keys != want:
        e.append(f"{qid}: keys")
    if q.get("kind") == "positive" and (q.get("source") not in entry_ids or q.get("transform") not in transforms.TRANSFORMS):
        e.append(f"{qid}: source or transform")
    if q.get("kind") == "negative" and (q.get("source") is not None or q.get("transform") is not None):
        e.append(f"{qid}: negative fields")
    if not re.fullmatch(r"[0-9a-f]{64}", q.get("sha256", "")):
        e.append(f"{qid}: sha256")
    for x in EXTRACTORS:
        r = q.get(x, {})
        if r.get("outcome") not in OUTCOMES:
            e.append(f"{qid}: {x} outcome")
            continue
        if r["status"] == "ok":
            if set(r) - EXTRACTOR_OK_KEYS:
                e.append(f"{qid}: {x} keys")
            if set(r.get("hashes", {})) != set(DIHEDRAL_NAMES) or any(
                not re.fullmatch(f"[0-9a-f]{{{BITS[x] // 4}}}", h) for h in r["hashes"].values()
            ):
                e.append(f"{qid}: {x} hashes")
            for d in [r.get("distance"), r.get("trueDistance")] + [w[1] for w in r.get("withinThreshold", [])]:
                if d is not None and not (isinstance(d, int) and 0 <= d <= BITS[x]):
                    e.append(f"{qid}: {x} distance range")
            if (r["outcome"] == "match") != ("entry" in r) or (r["outcome"] == "match" and r["entry"] not in entry_ids):
                e.append(f"{qid}: {x} match entry")
            if r["withinThresholdCount"] != len(r["withinThreshold"]) or (r["outcome"] == "no-match") != (r["withinThresholdCount"] == 0):
                e.append(f"{qid}: {x} within-threshold count")
        else:
            if set(r) - {"status", "code", "quality", "outcome"} or r["outcome"] != "abstain-" + r["code"]:
                e.append(f"{qid}: {x} abstain fields")
    return e


# --------------------------------------------------------------------------- run


def run(mode: str, out_dir: str, require_network_denied: bool, vendor_check: bool, frozen_commit: str | None = None) -> int:
    t0 = time.time()
    plan = SPLITS[mode]
    os.makedirs(out_dir, exist_ok=True)
    meta: dict = {
        "protocolVersion": PROTOCOL_VERSION,
        "mode": mode,
        "label": "SMOKE RUN - NOT A RESULT" if mode == "smoke" else "MEASURED RUN (contract check; counts have no pass line)",
        "extractionConfigSha256": extraction_config_sha256(),
        "matchingConfigSha256": matching_config_sha256(),
        "generator": generator.GENERATOR_ID,
        "environment": environment(),
        "crossHost": "not-tested: one host (macOS arm64). Audit source X1 (arXiv:2610.04151v1, author-run preprint) reports PDQ and ISCC bit-identical across x86 and arm64 on 200 PNG files; that is not our measurement",
    }
    rec_digest, comp_digest = protocol_digest()
    meta["protocolDigest"] = {"recorded": rec_digest, "computed": comp_digest}
    env_dev = check_environment()
    meta["environmentDeviations"] = env_dev
    denied, note = network_denied()
    meta["networkDenied"] = {"denied": denied, "probe": note}
    meta["codeIdentity"] = code_identity(frozen_commit)

    if mode == "full":
        problems = []
        ci = meta["codeIdentity"]
        if not ci["ok"]:
            problems.append("code identity: HEAD must equal --frozen-commit, the work tree must be clean, "
                            "the frozen paths must not differ, and the protocol version must be " + PROTOCOL_VERSION)
        if rec_digest is None or rec_digest != comp_digest:
            problems.append("protocol digest missing or mismatched")
        if env_dev:
            problems.append("environment deviates from pin: " + "; ".join(env_dev))
        if require_network_denied and not denied:
            problems.append("network not denied: " + note)
        if not require_network_denied:
            problems.append("a measured run requires --require-network-denied")
        if not vendor_check:
            problems.append("the vendor cross-check cannot be disabled in a measured run")
        if problems:
            print("REFUSING full run:\n  " + "\n  ".join(problems))
            return 2
        # Fresh reference-vector check on this host (V1); it rewrites the tracked
        # vectors/check-results.json, so the work tree must still be clean afterwards.
        import check_vectors

        fresh = check_vectors.run_checks(verbose=False)
        meta["vectorChecks"] = vector_verdict(fresh) if fresh is not None else None
        meta["statusAfterVectorCheck"] = git_status().splitlines()
        if fresh is None or meta["statusAfterVectorCheck"]:
            print("REFUSING full run: fresh vector check missing inputs or changed the work tree")
            return 2
    else:
        vec = os.path.join(HERE, "vectors", "check-results.json")
        meta["vectorChecks"] = None
        if os.path.exists(vec):
            with open(vec) as fh:
                meta["vectorChecks"] = vector_verdict(json.load(fh))
        meta["vectorChecksSource"] = "stored file (smoke mode only)"
        if require_network_denied and not denied:
            print("network not denied: " + note)
            return 2

    vendor_mismatch: list = []
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

    try:
        # Enrollment.
        entries = []
        for seed in plan["catalogue"]:
            check_time()
            rgb0 = generator.generate(seed)
            rec, rgb = extract(transforms.encode_original(rgb0))
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
            "split": SPLIT_LABEL,
            "artifacts": entries,
        }
        cbytes = canonical_bytes(catalogue)
        with open(os.path.join(out_dir, "catalogue.json"), "wb") as fh:
            fh.write(cbytes)
        cat_errors = validate_catalogue(cbytes)

        enrolled = {}
        for x in EXTRACTORS:
            ok = [e for e in entries if e[x]["status"] == "ok"]
            enrolled[x] = ([e["id"] for e in ok], hex_to_bytes_matrix([e[x]["hash"] for e in ok]) if ok else np.zeros((0, BITS[x] // 8), np.uint8))

        # Queries: the 12 edits of every catalogue original (regenerated, not held in memory),
        # then the never-enrolled negatives.
        queries = []
        for e in entries:
            rgb0 = generator.generate(e["seed"])
            for tname in transforms.TRANSFORMS:
                check_time()
                rec, rgb = extract(transforms.apply(tname, rgb0))
                qid = f"{e['id']}.{tname}"
                vendor_compare(qid, rgb, rec)
                queries.append({"id": qid, "split": SPLIT_LABEL, "kind": "positive", "source": e["id"], "transform": tname, **rec})
        for seed in plan["negatives"]:
            check_time()
            rgb0 = generator.generate(seed)
            rec, rgb = extract(transforms.encode_original(rgb0))
            qid = f"s{seed:07d}.neg"
            vendor_compare(qid, rgb, rec)
            queries.append({"id": qid, "split": SPLIT_LABEL, "kind": "negative", "source": None, "transform": None, "pixelSha256": generator.pixel_sha256(rgb0), **rec})

        thresholds = {"pdq": PDQ_T, "iscc": ISCC_T}
        for q in queries:
            for x in EXTRACTORS:
                if q[x]["status"] != "ok":
                    q[x]["outcome"] = "abstain-" + q[x]["code"]
                    continue
                ids, mat = enrolled[x]
                dist = nearest(q[x]["hashes"], ids, mat) if len(ids) else np.zeros(0, np.int64)
                q[x].update(decide(dist, ids, thresholds[x], q["source"] if q["kind"] == "positive" else None))
    except AbortRun:
        meta["status"] = "aborted-time-limit"
        meta["elapsedSeconds"] = round(time.time() - t0, 1)
        with open(os.path.join(out_dir, "summary.json"), "w") as fh:
            fh.write(json.dumps(meta, indent=1, sort_keys=True) + "\n")
        print("ABORTED at time limit; nothing here is a result")
        return 3

    queries.sort(key=lambda q: q["id"])
    entry_ids = {e["id"] for e in entries}
    query_errors = [err for q in queries for err in validate_query(q, entry_ids)]
    qbytes = b"".join(canonical_bytes(q) + b"\n" for q in queries)
    with open(os.path.join(out_dir, "queries.jsonl"), "wb") as fh:
        fh.write(qbytes)
    det = {"catalogueSha256": hashlib.sha256(cbytes).hexdigest(), "queriesSha256": hashlib.sha256(qbytes).hexdigest()}
    results_sha = hashlib.sha256(canonical_bytes(det)).hexdigest()

    elapsed = time.time() - t0
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # bytes on macOS
    summary = {
        **meta,
        "status": "completed",
        "thresholds": thresholds,
        "deterministic": det,
        "resultsSha256": results_sha,
        "enrollment": {
            x: {"enrolled": len(enrolled[x][0]), "catalogue": len(entries),
                "abstained": {c: sum(1 for e in entries if e[x]["status"] != "ok" and e[x]["code"] == c) for c in sorted({e[x]["code"] for e in entries if e[x]["status"] != "ok"})}}
            for x in EXTRACTORS
        },
        "recordValidation": {"catalogueErrors": cat_errors, "queryErrors": query_errors, "queryErrorCount": len(query_errors), "queriesChecked": len(queries)},
        "vendorCrossCheck": {"compared": vendor_compared, "mismatches": len(vendor_mismatch), "mismatchIds": vendor_mismatch},
        "elapsedSeconds": round(elapsed, 1),
        "peakRssBytes": int(peak),
        "counts": {"catalogue": len(entries), "queries": len(queries)},
    }
    summary["statusAfterRun"] = git_status().splitlines()
    if mode == "full":
        summary["metrics"] = compute_metrics(queries, thresholds)
        summary["passLine"] = "none: match and false-match counts are reported, not judged (protocol §6)"
        summary["validity"] = validity(summary)
    else:
        # A smoke run records only that the pipeline completed; its match figures are withheld
        # from the summary so they cannot be read as results (they remain in queries.jsonl).
        summary["metricsWithheld"] = True
    with open(os.path.join(out_dir, "summary.json"), "w") as fh:
        fh.write(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print(f"{summary['label']}: {len(queries)} queries, {elapsed:.1f} s, peak RSS {peak / 2**20:.0f} MiB")
    print(f"resultsSha256 {results_sha}")
    print(f"vendor cross-check {vendor_compared - len(vendor_mismatch)}/{vendor_compared} equal; record errors: catalogue {len(cat_errors)}, queries {len(query_errors)}")
    return 0


# --------------------------------------------------------------------------- metrics and validity


def _hist(values) -> dict:
    h: dict = {}
    for v in values:
        h[v] = h.get(v, 0) + 1
    return {str(k): h[k] for k in sorted(h)}


def compute_metrics(queries: list, thresholds: dict) -> dict:
    """Counts with denominators (protocol §6). No pass line is applied to any of them."""
    m: dict = {}
    for x in EXTRACTORS:
        per: dict = {}
        for tname in transforms.TRANSFORMS:
            sub = [q for q in queries if q["kind"] == "positive" and q["transform"] == tname]
            o = [q[x]["outcome"] for q in sub]
            per[tname] = {
                "n": len(sub),
                "correctMatch": sum(1 for q in sub if q[x]["outcome"] == "match" and q[x]["entry"] == q["source"]),
                "wrongTopMatch": sum(1 for q in sub if q[x]["outcome"] == "match" and q[x]["entry"] != q["source"]),
                "anyWrongWithinThreshold": sum(1 for q in sub if q[x].get("wrongWithinThreshold", 0) > 0),
                "ambiguous": o.count("abstain-ambiguous"),
                "noMatch": o.count("no-match"),
                "abstain": {c: o.count(c) for c in sorted(set(o)) if c.startswith("abstain-") and c != "abstain-ambiguous"},
                "trueDistanceHistogram": _hist(q[x]["trueDistance"] for q in sub if "trueDistance" in q[x]),
            }
        negs = [q for q in queries if q["kind"] == "negative"]
        o = [q[x]["outcome"] for q in negs]
        m[x] = {
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
                "nearestDistanceHistogram": _hist(q[x]["nearest"][1] for q in negs if "nearest" in q[x]),
            },
            "positivesNearestWrongHistogram": _hist(q[x]["nearestWrong"][1] for q in queries if q["kind"] == "positive" and "nearestWrong" in q[x]),
        }
    return m


def vector_verdict(v: dict) -> dict:
    """V1 from vectors/check-results.json (protocol §6 defines 'reference-vector mismatch')."""
    sets = {(r["set"], r["decodePath"]): r for r in v["pdqPublished"]}
    core = v["pdqCorePortVsVendor"]
    cpp = sets[("cpp-regtest", "profile-full-resolution")]
    ut = sets[("python-unittest", "profile-full-resolution")]
    readme = sets[("python-readme", "profile-full-resolution")]
    ic = v["isccConformance"]
    checks = {
        "pdqCorePortEqualsVendored": [core["equal"], core["total"]],
        "pdqCppWithin10": [cpp["within10"], cpp["comparable"]],
        "pdqCppQualityEqual": [cpp["qualityEqual"], cpp["comparable"]],
        "pdqPythonUnittestWithin16": [ut["within16"], ut["comparable"]],
        "pdqPythonReadmeWithin16": [readme["within16"], readme["comparable"]],
        "isccConformanceEqual": [ic["compiledDctEqual"], ic["total"]],
        "inputFilesVerified": [v["inputFiles"]["verified"], v["inputFiles"]["listed"]],
    }
    return {"checks": checks, "pass": all(a == b for a, b in checks.values())}


def validity(summary: dict) -> dict:
    """V1, V2, V4, V5 and the start conditions as observed in one run (V3 needs compare)."""
    vc = summary.get("vectorChecks") or {}
    rv = summary["recordValidation"]
    return {
        "V1-reference-vectors": bool(vc.get("pass")),
        "V2-run-to-run": "decided by compare (two runs)",
        "V3-cross-host": "not-tested",
        "V4-vendor-cross-check": summary["vendorCrossCheck"]["mismatches"] == 0 and summary["vendorCrossCheck"]["compared"] == summary["counts"]["catalogue"] + summary["counts"]["queries"],
        "V5-records-fit": not rv["catalogueErrors"] and rv["queryErrorCount"] == 0,
        "start-environment-and-digest": not summary["environmentDeviations"] and summary["protocolDigest"]["recorded"] == summary["protocolDigest"]["computed"],
        "start-network-denied": summary["networkDenied"]["denied"],
        "start-code-identity": summary["codeIdentity"]["ok"],
        "work-tree-clean-after-vector-check-and-run": not summary.get("statusAfterVectorCheck") and not summary["statusAfterRun"],
    }


def compare(a: str, b: str) -> int:
    sa = json.load(open(os.path.join(a, "summary.json")))
    sb = json.load(open(os.path.join(b, "summary.json")))
    same = sa["resultsSha256"] == sb["resultsSha256"]
    files_same = all(
        open(os.path.join(a, f), "rb").read() == open(os.path.join(b, f), "rb").read()
        for f in ("catalogue.json", "queries.jsonl")
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
    ap.add_argument("--frozen-commit", default=None, help="full mode: the 40-hex protocol commit; HEAD must equal it")
    a = ap.parse_args()
    if a.mode == "compare":
        return compare(*a.dirs)
    out = a.out or os.path.join(HERE, "out", a.mode)
    return run(a.mode, out, a.require_network_denied, not a.no_vendor_check, a.frozen_commit)


if __name__ == "__main__":
    sys.exit(main())
