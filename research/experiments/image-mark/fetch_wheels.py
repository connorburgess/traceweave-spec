"""Fetch the exact files pinned in requirements.txt into wheelhouse/.

Online step, run once, outside the network-denied sandbox. For each
`name==version --hash=sha256:H` it asks PyPI's JSON API for that release, picks the file whose
published SHA-256 is H, downloads it with curl (system TLS) to a temporary name, re-checks the
SHA-256 and only then moves it into place. Hosts contacted: pypi.org, files.pythonhosted.org.
Exit status 1 if any pinned file is missing or mismatched; a mismatched file is deleted.
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
        m = re.match(r"([A-Za-z0-9_.-]+)==(\S+)\s+--hash=sha256:([0-9a-f]{64})$", line)
        if m:
            yield m.groups()
        elif line:
            raise SystemExit(f"unparsed requirement line: {line!r}")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    bad = n = 0
    for name, version, want in pins(os.path.join(HERE, "requirements.txt")):
        n += 1
        meta = json.loads(subprocess.check_output(["curl", "-sSf", f"https://pypi.org/pypi/{name}/{version}/json"]))
        files = [f for f in meta["urls"] if f["digests"]["sha256"] == want]
        if not files:
            print("NOT FOUND", name, version, want)
            bad += 1
            continue
        dest = os.path.join(OUT, files[0]["filename"])
        if not (os.path.exists(dest) and sha256(dest) == want):
            part = dest + ".part"
            subprocess.check_call(["curl", "-sSfL", "-o", part, files[0]["url"]])
            if sha256(part) != want:
                print("MISMATCH", files[0]["filename"])
                os.remove(part)
                bad += 1
                continue
            os.replace(part, dest)
    print(f"{n - bad}/{n} pinned files present and verified in wheelhouse/")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
