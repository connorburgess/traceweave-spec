"""Fetch the exact files pinned in requirements-build.txt and requirements.txt into wheelhouse/.

Online step, run once. For each `name==version --hash=sha256:H` it asks PyPI's JSON API for
that release, picks the file whose published SHA-256 is H, downloads it with curl (system TLS)
and re-checks the hash. Exit status 1 if any pinned file is missing or mismatched.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "wheelhouse")


def pins(path):
    text = open(path).read().replace("\\\n", " ")
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        m = re.match(r"([A-Za-z0-9_.-]+)==(\S+)\s+--hash=sha256:([0-9a-f]{64})", line)
        if m:
            yield m.groups()


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    bad = 0
    n = 0
    for req in ("requirements-build.txt", "requirements.txt"):
        for name, version, want in pins(os.path.join(HERE, req)):
            n += 1
            meta = json.loads(subprocess.check_output(["curl", "-sSf", f"https://pypi.org/pypi/{name}/{version}/json"]))
            files = [f for f in meta["urls"] if f["digests"]["sha256"] == want]
            if not files:
                print("NOT FOUND", name, version, want)
                bad += 1
                continue
            dest = os.path.join(OUT, files[0]["filename"])
            if not os.path.exists(dest):
                subprocess.check_call(["curl", "-sSfL", "-o", dest, files[0]["url"]])
            if hashlib.sha256(open(dest, "rb").read()).hexdigest() != want:
                print("MISMATCH", dest)
                os.remove(dest)
                bad += 1
    print(f"{n - bad}/{n} pinned files present and verified in wheelhouse/")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
