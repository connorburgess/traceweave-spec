"""IMGF.2 evidence: PDQ and ISCC Image-Code against published reference outputs.

Offline (needs vectors/pdq-data/ from fetch_pdq_vectors.py). Writes vectors/check-results.json
and prints counts. Exit status 0 means the checks ran; the counts, not the exit status, are the
evidence, because exact agreement with the published PDQ outputs is not expected for every
decode path (see extraction-profile-image.md §7).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "vendor", "threatexchange_pdq"))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import iscc_core  # noqa: E402
from pdqhashing.hasher.pdq_hasher import PDQHasher  # noqa: E402
from pdqhashing.utils.matrix import MatrixUtil  # noqa: E402
from twimg.decode import decode  # noqa: E402
from twimg.pdq_np import DIHEDRAL_NAMES, hamming_hex, luma_from_rgb, pdq_from_luma  # noqa: E402
from twimg.profile import check_environment, environment  # noqa: E402

DATA = os.path.join(HERE, "vectors", "pdq-data")
VENDOR = PDQHasher()


def vendor_hash(rgb: np.ndarray):
    img = Image.fromarray(rgb, "RGB")
    r, c = rgb.shape[:2]
    x = VENDOR.dihedralFromBufferedImage(
        img,
        MatrixUtil.allocateMatrixAsRowMajorArray(r, c),
        MatrixUtil.allocateMatrixAsRowMajorArray(r, c),
        MatrixUtil.allocateMatrix(64, 64),
        MatrixUtil.allocateMatrix(16, 64),
        MatrixUtil.allocateMatrix(16, 16),
        MatrixUtil.allocateMatrix(16, 16),
        0xFF,
    )
    names = ["hash", "hashRotate90", "hashRotate180", "hashRotate270", "hashFlipX", "hashFlipY", "hashFlipPlus1", "hashFlipMinus1"]
    return {n: str(getattr(x, a)) for n, a in zip(DIHEDRAL_NAMES, names)}, x.quality


def path_profile(path: str):
    rgb, _ = decode(open(path, "rb").read())
    return pdq_from_luma(luma_from_rgb(rgb), dihedral=True)


def path_vendor_python(path: str):
    """The vendor Python tool's path: PDQHasher.fromFile (Pillow open, thumbnail(512,512), RGB)."""
    hq = VENDOR.fromFile(path)
    return str(hq.getHash()), hq.getQuality()


def main() -> int:
    ref = json.load(open(os.path.join(HERE, "vectors", "pdq-reference.json")))
    out: dict = {"environment": environment(), "environmentDeviations": check_environment()}

    # 1. Input integrity.
    present = 0
    for f in ref["files"]:
        p = os.path.join(DATA, f["path"])
        if os.path.exists(p) and hashlib.sha256(open(p, "rb").read()).hexdigest() == f["sha256"]:
            present += 1
    out["inputFiles"] = {"verified": present, "listed": len(ref["files"])}
    if present != len(ref["files"]):
        print("vector files missing or altered; run fetch_pdq_vectors.py first")
        return 2

    # 2. Hash core: NumPy port vs vendored pure Python on identical decoded pixels
    #    (profile decode; 8 dihedral hashes and quality must all be equal).
    agree = 0
    for f in ref["files"]:
        rgb, _ = decode(open(os.path.join(DATA, f["path"]), "rb").read())
        nh, nq = pdq_from_luma(luma_from_rgb(rgb), dihedral=True)
        vh, vq = vendor_hash(rgb)
        agree += nh == vh and nq == vq
    out["pdqCorePortVsVendor"] = {"equal": agree, "total": len(ref["files"]), "compared": "8 dihedral hashes + quality, full-resolution profile decode"}

    # 3. Published outputs, per reference set and per decode path.
    sets_out = []
    for s in ref["referenceSets"]:
        for pathname, fn in (("profile-full-resolution", None), ("vendor-python-thumbnail512", path_vendor_python)):
            rows = []
            for v in s["vectors"]:
                p = os.path.join(DATA, v["path"])
                if not os.path.exists(p):
                    rows.append({"path": v["path"], "status": "input-missing-at-commit"})
                    continue
                if fn is None:
                    hs, q = path_profile(p)
                    h = hs["orig"]
                else:
                    h, q = fn(p)
                row = {"path": v["path"], "distance": hamming_hex(h, v["hash"]), "computed": h, "quality": q}
                if "quality" in v:
                    row["qualityEqual"] = q == v["quality"]
                rows.append(row)
            ok = [r for r in rows if "distance" in r]
            res = {
                "set": s["id"],
                "decodePath": pathname,
                "comparable": len(ok),
                "listed": len(rows),
                "exactEqual": sum(r["distance"] == 0 for r in ok),
                "maxDistance": max(r["distance"] for r in ok),
                "distances": [r["distance"] for r in ok],
                "within10": sum(r["distance"] <= 10 for r in ok),
                "within16": sum(r["distance"] <= 16 for r in ok),
                "rows": rows,
            }
            if any("qualityEqual" in r for r in ok):
                res["qualityEqual"] = sum(bool(r.get("qualityEqual")) for r in ok)
            sets_out.append(res)
        if s.get("dihedral"):
            p = os.path.join(DATA, s["dihedral"][0]["path"])
            hs, _ = path_profile(p)
            names = {"orig": "orig", "rot90": "rot90", "rot180": "rot180", "rot270": "rot270", "flipx": "flipx", "flipy": "flipy", "flipp": "flipp", "flipm": "flipm"}
            ds = [hamming_hex(hs[names[d["xform"]]], d["hash"]) for d in s["dihedral"]]
            sets_out.append({"set": s["id"] + "-dihedral-of-" + s["dihedral"][0]["path"], "decodePath": "profile-full-resolution", "comparable": len(ds), "exactEqual": sum(d == 0 for d in ds), "distances": ds, "maxDistance": max(ds)})
    out["pdqPublished"] = sets_out

    # 4. ISCC Image-Code v0: iscc-core conformance vectors (data.json), compiled and pure-Python DCT.
    data = json.load(open(os.path.join(os.path.dirname(iscc_core.__file__), "data.json")))
    vecs = data["gen_image_code_v0"]
    spec = importlib.util.spec_from_file_location("iscc_dct_pure", os.path.join(os.path.dirname(iscc_core.__file__), "dct.py"))
    pure = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pure)
    compiled_ok = pure_ok = 0
    rows = []
    for name, v in vecs.items():
        px, bits = v["inputs"]
        want = v["outputs"]["iscc"]
        got_c = iscc_core.gen_image_code_v0(px, bits)["iscc"]
        orig = iscc_core.alg_dct
        try:
            iscc_core.alg_dct = pure.alg_dct
            got_p = iscc_core.gen_image_code_v0(px, bits)["iscc"]
        finally:
            iscc_core.alg_dct = orig
        compiled_ok += got_c == want
        pure_ok += got_p == want
        rows.append({"name": name, "bits": bits, "expected": want, "compiledDct": got_c, "pureDct": got_p})
    out["isccConformance"] = {
        "source": "iscc_core/data.json gen_image_code_v0 (shipped in the pinned iscc-core 1.5.0 wheel)",
        "compiledDctEqual": compiled_ok,
        "pureDctEqual": pure_ok,
        "total": len(vecs),
        "alg_dct_module": getattr(iscc_core.alg_dct, "__module__", "?"),
        "rows": rows,
    }

    path = os.path.join(HERE, "vectors", "check-results.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"vector files verified: {present}/{len(ref['files'])}")
    print(f"PDQ core, NumPy port vs vendored: {agree}/{len(ref['files'])}")
    for r in sets_out:
        extra = f", quality equal {r['qualityEqual']}/{r['comparable']}" if "qualityEqual" in r else ""
        print(f"PDQ {r['set']} [{r['decodePath']}]: exact {r['exactEqual']}/{r['comparable']}, max distance {r['maxDistance']}{extra}")
    c = out["isccConformance"]
    print(f"ISCC image v0 conformance: compiled {c['compiledDctEqual']}/{c['total']}, pure {c['pureDctEqual']}/{c['total']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
