#!/usr/bin/env python3
"""Cross-check the text profile's classes, fold and tokens against library code.

Usage:
  python3 -I harness/crosscheck_text.py NormalizationTest.txt [--build-dir DIR]

Builds two oracles offline (GOPROXY=off, cargo --offline) into DIR (default
$TMPDIR/text-xcheck) and compares them with check_text_vectors.py's own
implementation, which reads only text-tables-17.0.0.json:

  Go   go1.27 unicode (17.0.0) and golang.org/x/text v0.39.0 norm and cases
       (17.0.0 tables under the go1.27 build tag): character classes for every
       scalar value; the fold for every scalar value, for every
       NormalizationTest.txt string and for every vector token; the plain
       token rule on every plain-profile vector.
  Rust pulldown-cmark 0.13.5 (CommonMark): text content of each Markdown
       vector, reported only to show where the profile's masks differ from a
       CommonMark parse (not an agreement check).
       unicode-normalization 0.1.25 (17.0.0): NFC and NFD for every scalar
       value and every NormalizationTest.txt string. unicode-segmentation
       1.13.3 (17.0.0): UAX #29 words, reported only to show where the
       profile's token rule differs from UAX #29 (not an agreement check).

Python's unicodedata (16.0.0 here) and caseless 0.2.2 (16.0.0) are not used:
their Unicode version does not match the profile.
"""
import base64
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
spec = importlib.util.spec_from_file_location("ctv", ROOT / "check_text_vectors.py")
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


def build(dest):
    dest.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, GOFLAGS="-mod=mod", GOPROXY="off", GOSUMDB="off",
               GOCACHE=str(dest / "gocache"))
    subprocess.run(["cp", "-R", str(HERE / "go"), str(HERE / "rust"), str(dest)], check=True)
    subprocess.run(["go", "build", "-o", "textxcheck", "."], cwd=dest / "go", env=env, check=True)
    subprocess.run(["cargo", "build", "--offline", "--release", "--locked", "-q"], cwd=dest / "rust", check=True)
    return dest / "go" / "textxcheck", dest / "rust" / "target" / "release" / "text-xcheck"


def ask(binary, mode, strings):
    payload = "".join(f"{mode} {s.encode('utf-8').hex()}\n" for s in strings)
    out = subprocess.run([str(binary)], input=payload.encode(), capture_output=True, check=True).stdout.decode()
    lines = out.split("\n")[:-1]
    assert len(lines) == len(strings)
    return lines


def CHEROKEE(c):
    return 0x13F8 <= c <= 0x13FD or 0xAB70 <= c <= 0xABBF


def unhex(h):
    return bytes.fromhex(h).decode("utf-8")


def scalars():
    return [chr(c) for c in range(0x110000) if not 0xD800 <= c <= 0xDFFF]


def string_fold(T, s):
    """The profile's fold before the separator filter: NFC(map NFKC_CF over NFD)."""
    mapped = []
    for c in C.nfd(T, [ord(x) for x in s]):
        mapped.extend(T.nfkc_cf(c))
    return C.s_of(C.nfc(T, mapped))


def report(name, n, bad, examples):
    status = "agree" if not bad else "DIFFER"
    print(f"{name}: {n - len(bad)}/{n} {status}")
    for e in bad[:examples]:
        print("   ", e)


def main(argv):
    if not argv:
        sys.exit(__doc__)
    ntest = Path(argv[0])
    dest = Path(argv[argv.index("--build-dir") + 1]) if "--build-dir" in argv else Path(os.environ.get("TMPDIR", "/tmp")) / "text-xcheck"
    T = C.Tables(ROOT / C.TABLES_FILE)
    go, rust = build(dest)
    print(subprocess.run([str(go), "versions"], capture_output=True, text=True, check=True).stdout.strip())
    print(subprocess.run([str(rust), "versions"], capture_output=True, text=True, check=True).stdout.strip())
    raw = ntest.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == C.NORMALIZATION_TEST_SHA256, "NormalizationTest.txt digest"
    ns = []
    for line in raw.decode().splitlines():
        body = line.split("#", 1)[0].strip()
        if body and not body.startswith("@"):
            ns.extend("".join(chr(int(x, 16)) for x in f.split()) for f in body.split(";")[:5])
    ns = sorted(set(ns))
    sc = scalars()

    # 1. classes
    gcls = subprocess.run([str(go), "classes"], capture_output=True, text=True, check=True).stdout.strip()
    bad = [f"U+{c:04X}: Go {gcls[c]} table {T.char_class(c)}" for c in range(0x110000)
           if not 0xD800 <= c <= 0xDFFF and gcls[c] != T.char_class(c)]
    report("classes W/C/I/S, every scalar value (Go unicode)", len(sc), bad, 10)

    # 2. fold of every scalar value, and token fold of every word/ideographic one
    gf = ask(go, "fold", sc)
    bad = [ord(s) for s, h in zip(sc, gf) if unhex(h) != string_fold(T, s)]
    cherokee = [c for c in bad if CHEROKEE(c)]
    report("fold, every scalar value (Go x/text NFKC+cases.Fold+DI loop, then NFC)", len(sc),
           [f"U+{c:04X}" for c in bad], 0)
    print(f"    attributed: {len(cherokee)} Cherokee small letters (U+13F8-13FD, U+AB70-ABBF): UCD NFKC_CF maps them to "
          f"capitals, x/text cases.Fold leaves them; unexplained: {len(bad) - len(cherokee)} "
          + " ".join(f"U+{c:04X}" for c in bad if not CHEROKEE(c))[:400])
    wc = [s for s in sc if T.char_class(ord(s)) in ("W", "C")]
    gtf = ask(go, "tokenfold", wc)
    bad = [ord(s) for s, h in zip(wc, gtf) if unhex(h) != C.s_of(C.fold(T, [ord(s)]))]
    report("token fold (with separator filter), every W/C scalar value", len(wc), [f"U+{c:04X}" for c in bad], 0)
    print(f"    attributed to Cherokee: {sum(map(CHEROKEE, bad))}; unexplained: {len(bad) - sum(map(CHEROKEE, bad))}")

    # 3. fold of NormalizationTest.txt strings
    gf = ask(go, "fold", ns)
    bad = [f"{[hex(ord(x)) for x in s]}: Go {[hex(ord(x)) for x in unhex(h)]} profile {[hex(ord(x)) for x in string_fold(T, s)]}"
           for s, h in zip(ns, gf) if unhex(h) != string_fold(T, s)]
    report("fold, NormalizationTest.txt strings", len(ns), bad, 10)

    # 4. vectors: token folds and the plain token rule
    vectors = []
    for name in C.VECTOR_FILES:
        vectors += json.loads((ROOT / name).read_text())["vectors"]
    toks = [t for v in vectors if v["result"]["status"] != "error" for t in v["result"]["tokens"]]
    gtf = ask(go, "tokenfold", [t["text"] for t in toks])
    bad = [f"{t['text']!r}: Go {unhex(h)!r} vector {t['folded']!r}" for t, h in zip(toks, gtf) if unhex(h) != t["folded"]]
    report("token fold, every vector token (Go)", len(toks), bad, 10)
    print(f"    of which Cherokee small letters: {sum(any(CHEROKEE(ord(x)) for x in t['text']) for t, h in zip(toks, gtf) if unhex(h) != t['folded'])}")
    plain = [v for v in vectors if v["result"]["status"] != "error" and v["config"] != "config-text-markdown.json"]
    inputs = [base64.b64decode(v["inputBase64"]).decode() for v in plain]
    gt = ask(go, "tokens", inputs)
    bad = []
    for v, line in zip(plain, gt):
        got = [] if not line else [(int(p.split(":")[0].split("-")[0]), int(p.split(":")[0].split("-")[1]), unhex(p.split(":")[1]))
                                    for p in line.split(",")]
        want = [(t["span"][0], t["span"][1], t["folded"]) for t in v["result"]["tokens"]]
        if got != want:
            bad.append(v["id"] + (" (Cherokee)" if any(CHEROKEE(ord(x)) for x in inputs[plain.index(v)]) else ""))
    report("plain token rule + fold, every plain-profile vector (Go)", len(plain), bad, 20)

    # 5. Rust NFC/NFD
    for form, fn in (("nfc", C.nfc), ("nfd", C.nfd)):
        r = ask(rust, form, sc + ns)
        bad = [f"{[hex(ord(x)) for x in s]}" for s, h in zip(sc + ns, r) if unhex(h) != C.s_of(fn(T, [ord(x) for x in s]))]
        report(f"{form.upper()}, every scalar value + NormalizationTest.txt strings (Rust unicode-normalization)", len(sc) + len(ns), bad, 10)

    # 6. CommonMark 0.31.2 text content (pulldown-cmark), informative
    md = [v for v in vectors if v["result"]["status"] != "error" and v["config"] == "config-text-markdown.json"]
    rendered = ask(rust, "mdtext", [base64.b64decode(v["inputBase64"]).decode() for v in md])
    same, diff = 0, []
    for v, h in zip(md, rendered):
        text = [ord(x) for x in unhex(h)]
        cm = [C.s_of(C.fold(T, text[a:b + 1])) for a, b in C.tokenize(T, text, [])]
        if cm == [t["folded"] for t in v["result"]["tokens"]]:
            same += 1
        else:
            diff.append(v["id"])
    print(f"Markdown masks vs CommonMark text content, folded token sequences (informative): {same}/{len(md)} equal; differ: {', '.join(diff)}")

    # 7. UAX #29, informative
    words = ask(rust, "words", inputs)
    same, diff = 0, []
    for v, line in zip(plain, words):
        uax = [tuple(map(int, p.split("-"))) for p in line.split(",")] if line else []
        ours = [tuple(t["span"]) for t in v["result"]["tokens"]]
        if uax == ours:
            same += 1
        else:
            diff.append(v["id"])
    print(f"UAX #29 word spans equal to profile token spans (informative, not required): {same}/{len(plain)} plain vectors; differ: {', '.join(diff)}")


if __name__ == "__main__":
    main(sys.argv[1:])
