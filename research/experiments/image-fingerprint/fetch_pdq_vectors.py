"""Fetch the ThreatExchange PDQ conformance images named in vectors/pdq-reference.json.

Online step, run once before the offline checks. Uses curl (system TLS) and pins every file
by the git blob SHA-1 of the pinned commit and by SHA-256. Images go to vectors/pdq-data/
(git-ignored). Exit status 1 on any mismatch; a mismatching file is deleted.
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    ref = json.load(open(os.path.join(HERE, "vectors", "pdq-reference.json")))
    commit = ref["source"]["commit"]
    out = os.path.join(HERE, "vectors", "pdq-data")
    bad = 0
    for f in ref["files"]:
        dest = os.path.join(out, f["path"])
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if not os.path.exists(dest):
            url = f"https://raw.githubusercontent.com/meta/ThreatExchange/{commit}/pdq/data/{f['path']}"
            subprocess.check_call(["curl", "-sSfL", "-o", dest, url])
        b = open(dest, "rb").read()
        blob = hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()
        sha = hashlib.sha256(b).hexdigest()
        if blob != f["gitBlobSha1"] or sha != f["sha256"]:
            print("MISMATCH", f["path"], blob, sha)
            os.remove(dest)
            bad += 1
    print(f"{len(ref['files']) - bad}/{len(ref['files'])} vector files verified")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
