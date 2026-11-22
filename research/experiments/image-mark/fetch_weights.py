"""Fetch and verify the model files listed in weights.json.

Usage:
  python fetch_weights.py [--only ID ...]     download missing files, then verify every listed file
  python fetch_weights.py --verify            verify only; never touches the network
  python fetch_weights.py --pin               as the first form, and write each computed SHA-256 into
                                              weights.json where it is still null (first fetch only)

Files go under $TRACEWEAVE_EVAL_DIR/models (default ~/traceweave-eval/models). The script refuses a
target directory that lies inside any git work tree, so model files can never be committed by
accident. Each download goes to a ".part" file with curl (system TLS) and is moved into place only
after three checks pass: the byte size, the publisher's own digest (an MD5, or an S3 multipart ETag
recomputed from 8 MiB parts) and, once pinned, the SHA-256 in weights.json. A file that fails any
check is deleted and the script exits 1. Hosts contacted: only the URLs in weights.json.

Exit status: 0 all listed files verified; 1 a check failed; 2 refused location or bad usage;
3 a file verified against size and publisher digest but its SHA-256 is not pinned yet (run --pin).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "weights.json")


def models_dir() -> str:
    base = os.environ.get("TRACEWEAVE_EVAL_DIR") or os.path.join(os.path.expanduser("~"), "traceweave-eval")
    return os.path.realpath(os.path.join(base, "models"))


def inside_work_tree(path: str) -> str | None:
    """Return the work-tree root if `path` (or its nearest existing ancestor) is inside one."""
    probe = path
    while not os.path.isdir(probe):
        parent = os.path.dirname(probe)
        if parent == probe:
            return None
        probe = parent
    r = subprocess.run(["git", "-C", probe, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    # Also refuse anything under this repository even if git cannot see it (e.g. a nested .git).
    here_top = subprocess.run(["git", "-C", HERE, "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    if here_top and os.path.commonpath([os.path.realpath(here_top), path]) == os.path.realpath(here_top):
        return here_top
    return None


def digests(path: str, part_size: int | None) -> tuple[str, str, str | None]:
    """(sha256, md5, s3 multipart etag or None)."""
    sha, md5 = hashlib.sha256(), hashlib.md5()
    parts: list[bytes] = []
    with open(path, "rb") as fh:
        while True:
            block = fh.read(part_size or (1 << 22))
            if not block:
                break
            sha.update(block)
            md5.update(block)
            if part_size:
                parts.append(hashlib.md5(block).digest())
    etag = f"{hashlib.md5(b''.join(parts)).hexdigest()}-{len(parts)}" if part_size else None
    return sha.hexdigest(), md5.hexdigest(), etag


def check(entry: dict, path: str) -> tuple[bool, str, str]:
    """(ok, computed sha256, message)."""
    if not os.path.isfile(path):
        return False, "", "missing"
    size = os.path.getsize(path)
    if size != entry["size"]:
        return False, "", f"size {size} != {entry['size']}"
    pc = entry["publisherCheck"]
    sha, md5, etag = digests(path, pc.get("partSize"))
    got = md5 if pc["kind"] == "md5" else etag
    if got != pc["value"]:
        return False, sha, f"{pc['kind']} {got} != {pc['value']}"
    if entry["sha256"] is not None and sha != entry["sha256"]:
        return False, sha, f"sha256 {sha} != pinned {entry['sha256']}"
    return True, sha, "ok" if entry["sha256"] else "unpinned"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--pin", action="store_true")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args(argv)
    if a.verify and a.pin:
        print("--verify and --pin are exclusive")
        return 2
    root = models_dir()
    tree = inside_work_tree(root)
    if tree:
        print(f"REFUSED: {root} is inside the git work tree {tree}; set TRACEWEAVE_EVAL_DIR elsewhere")
        return 2
    manifest = json.load(open(MANIFEST))
    entries = [e for e in manifest["files"] if not a.only or e["id"] in a.only]
    bad = unpinned = 0
    for e in entries:
        dest = os.path.join(root, e["path"])
        ok, sha, msg = check(e, dest)
        if not ok and not a.verify:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            part = dest + ".part"
            print(f"fetching {e['id']} ({e['size']:,} bytes) from {e['url']}", flush=True)
            subprocess.check_call(["curl", "-sSfL", "--retry", "2", "-o", part, e["url"]])
            ok, sha, msg = check(e, part)
            if ok:
                os.replace(part, dest)
            else:
                os.remove(part)
        if not ok:
            print(f"FAIL {e['id']}: {msg}")
            bad += 1
            continue
        if e["sha256"] is None:
            if a.pin:
                e["sha256"] = sha
                msg = "pinned now"
            else:
                unpinned += 1
        print(f"{msg:>10} {e['id']} sha256={sha}")
    if a.pin:
        with open(MANIFEST, "w") as fh:
            json.dump(manifest, fh, indent=2)
            fh.write("\n")
    print(f"{len(entries) - bad - unpinned}/{len(entries)} files verified under {root}")
    return 1 if bad else (3 if unpinned else 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
