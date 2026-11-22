"""Fetch the upstream source files listed in sources.json into third_party/<name>/.

Online step, run once, outside the network-denied sandbox (host: codeload.github.com). For each
source it downloads the archive of the pinned commit to a temporary file, extracts **only** the
listed paths (no other member is written; absolute paths and ".." are refused), and checks each
file's byte size, SHA-256 and git blob id against sources.json. The archive bytes themselves are not
pinned, because GitHub does not guarantee stable archive bytes; the per-file checks are what count.

  python fetch_sources.py            fetch if needed, then verify
  python fetch_sources.py --verify   verify only; never touches the network

Exit status 0 when every listed file is present and matches; 1 otherwise (mismatching files are
deleted). third_party/ is git-ignored.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "third_party")


def blob_ids(data: bytes) -> tuple[str, str]:
    return hashlib.sha256(data).hexdigest(), hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def verify(src: dict) -> list[str]:
    errors = []
    for f in src["files"]:
        p = os.path.join(OUT, src["name"], f["path"])
        if not os.path.isfile(p):
            errors.append(f"missing {src['name']}/{f['path']}")
            continue
        data = open(p, "rb").read()
        sha, blob = blob_ids(data)
        if len(data) != f["size"] or sha != f["sha256"] or blob != f["gitBlob"]:
            errors.append(f"mismatch {src['name']}/{f['path']}")
            os.remove(p)
    return errors


def fetch(src: dict) -> None:
    wanted = {f["path"] for f in src["files"]}
    with tempfile.TemporaryDirectory() as tmp:
        arc = os.path.join(tmp, "src.tar.gz")
        subprocess.check_call(["curl", "-sSfL", "-o", arc, src["archive"]])
        with tarfile.open(arc) as t:
            for m in t.getmembers():
                if not m.isfile() or "/" not in m.name:
                    continue
                rel = m.name.split("/", 1)[1]
                if rel not in wanted:
                    continue
                if os.path.isabs(rel) or ".." in rel.split("/"):
                    raise SystemExit(f"refused archive member {m.name!r}")
                dest = os.path.join(OUT, src["name"], rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as fh:
                    fh.write(t.extractfile(m).read())


def main(argv: list[str]) -> int:
    manifest = json.load(open(os.path.join(HERE, "sources.json")))
    errors: list[str] = []
    n = 0
    for src in manifest["sources"]:
        n += len(src["files"])
        if "--verify" not in argv and verify(src):
            fetch(src)
        errors += verify(src)
    for e in errors:
        print(e)
    print(f"{n - len(errors)}/{n} source files verified under third_party/")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
