#!/usr/bin/env python3
"""Compare the draft extraction vectors with real toolchains, offline.

Builds two small oracles into a scratch directory and compares them with
every vector:

* go/ (go/scanner from the local Go toolchain, standard library only);
* rust/ (proc-macro2 1.0.107 fallback lexer with unicode-ident 1.0.24, built
  with `cargo --offline --locked` from the local cargo cache);
* rustc --edition 2024, for lexical acceptance only.

It also compares the pinned Unicode tables with Go's unicode package and with
unicode-ident. Every known divergence is listed in EXPECT with its reason.
Any other difference, or an expected divergence that no longer occurs, makes
the run fail.

Usage:
  python3 -I research/drafts/extraction-vectors/harness/crosscheck.py [--build-dir DIR]

Requirements: go 1.27.x, cargo/rustc 1.97.x, and proc-macro2 1.0.107 plus
unicode-ident 1.0.24 already present in the local cargo registry cache.
Nothing is downloaded or installed; DIR defaults to a new temporary directory.
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
VECTORS = HARNESS.parent
spec = importlib.util.spec_from_file_location("check_vectors", VECTORS / "check_vectors.py")
cv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cv)

GO_FILES = ["go.json", "limits-go.json"]
RUST_FILES = ["rust.json", "limits-rust.json"]
GO_CLASS = {"INT": "int", "FLOAT": "float", "IMAG": "imag", "CHAR": "rune", "STRING": "string", "IDENT": "ident"}

# Known, deliberate divergences: vector id -> {tool: (kind, detail, reason)}.
# kind "accepts": the tool accepts input the contract rejects.
# kind "offset": the tool rejects at a different offset (detail = tool offset).
# kind "no-limit": the contract's maxInputBytes check has no toolchain counterpart.
# kind "rejects": the tool rejects (at detail offset) an input the contract accepts; tokens must still agree.
LIMIT = ("no-limit", None, "maxInputBytes is a contract parameter; toolchains have no size limit")
EXPECT = {
    "go-err-bom": {"go/scanner": ("accepts", None, "OD-1: go/scanner skips a leading BOM; the contract rejects it")},
    "go-err-malformed-number": {"go/scanner": ("offset", 7, "OD-13: contract reports the token start")},
    "go-err-invalid-escape": {"go/scanner": ("offset", 7, "OD-13: contract reports the token start")},
    "go-err-hex-float-no-exponent": {"go/scanner": ("offset", 10, "OD-13: contract reports the token start")},
    "go-limit-over": {"go/scanner": LIMIT},
    "go-limit-precedence": {"go/scanner": ("offset", 6, "size check precedes UTF-8 check; go/scanner reports the 0xFF byte")},
    "go-q11-imag-binary-digit": {"go/scanner": ("accepts", None, "Q11: go/scanner and gofmt accept 0b2i; cmd/compile rejects it (malformed constant); the contract follows the literal productions")},
    "go-q11-imag-octal-digit": {"go/scanner": ("accepts", None, "Q11: as 0b2i")},
    "go-q12-line-directive": {"go/scanner": ("rejects", 8, "Q12: go/scanner interprets /*line ...*/ directives; the contract treats every comment as a comment (section 4.6)")},
    "rust-q1-raw-extra-pounds": {"proc-macro2": ("accepts", None, "proc-macro2 does not implement edition 2024 reserved pounds; rustc rejects")},
    "rust-err-bom": {"proc-macro2": ("accepts", None, "OD-1"), "rustc": ("accepts", None, "OD-1: Reference removes a leading BOM")},
    "rust-err-nul": {"proc-macro2": ("accepts", None, "OD-2"), "rustc": ("accepts", None, "OD-2: Reference allows NUL in literals")},
    "rust-err-isolated-cr": {"proc-macro2": ("accepts", None, "OD-2"), "rustc": ("accepts", None, "OD-2: isolated CR is whitespace in the Reference")},
    "rust-err-cr-in-literal": {"proc-macro2": ("offset", 8, "proc-macro2 reports the literal start; the contract's forbidden-code-point scan reports the CR itself")},
    "rust-err-mid-bom": {"proc-macro2": ("accepts", None, "contract rejects U+FEFF anywhere"),
                         "rustc": ("accepts", None, "U+FEFF inside a string literal is valid Rust")},
    "rust-err-non-nfc-identifier": {"proc-macro2": ("accepts", None, "OD-3"), "rustc": ("accepts", None, "OD-3: rustc NFC-normalizes")},
    "rust-err-non-nfc-suffix": {"proc-macro2": ("accepts", None, "OD-3"), "rustc": ("accepts", None, "OD-3: rustc NFC-normalizes")},
    "rust-err-non-nfc-raw-ident": {"proc-macro2": ("accepts", None, "OD-3"), "rustc": ("accepts", None, "OD-3: rustc NFC-normalizes")},
    "rust-err-non-nfc-before-quote": {"proc-macro2": ("accepts", None, "OD-3 plus proc-macro2 has no reserved prefixes")},
    "rust-err-reserved-prefix": {"proc-macro2": ("accepts", None, "proc-macro2 does not implement edition 2021 reserved prefixes")},
    "rust-err-pounds": {"proc-macro2": ("accepts", None, "proc-macro2 does not implement edition 2024 reserved pounds")},
    "rust-err-u200d": {"proc-macro2": ("accepts", None, "proc-macro2 accepts ZWJ as XID_Continue"),
                       "rustc": ("accepts", None, "rustc 1.97.1 accepts ZWJ with only an uncommon_codepoints warning, contrary to Reference [ident.zero-width-chars]; the contract follows the Reference")},
    "rust-err-string-underscore-suffix": {"proc-macro2": ("accepts", None, "proc-macro2 lexes \"x\"_ as one literal; rustc rejects (F2)")},
    "rust-err-char-underscore-suffix": {"proc-macro2": ("accepts", None, "proc-macro2 lexes 'a'_ as one literal; rustc rejects (F2)")},
    "rust-limit-over": {"proc-macro2": LIMIT, "rustc": LIMIT},
    "rust-limit-precedence": {"proc-macro2": LIMIT, "rustc": LIMIT},
}


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, check=False, **kw)


def build(build_dir: Path):
    env = dict(os.environ, GOTOOLCHAIN="local", GOFLAGS="-mod=mod", GOWORK="off",
               GOCACHE=str(build_dir / "gocache"), CARGO_TARGET_DIR=str(build_dir / "cargo-target"))
    go_bin = build_dir / "crosscheck-go"
    r = run(["go", "build", "-o", str(go_bin), "."], cwd=HARNESS / "go", env=env)
    if r.returncode:
        sys.exit("go build failed:\n" + r.stderr.decode())
    r = run(["cargo", "build", "--offline", "--locked", "--quiet", "--manifest-path", str(HARNESS / "rust" / "Cargo.toml")], env=env)
    if r.returncode:
        sys.exit("cargo build failed (needs proc-macro2 1.0.107 and unicode-ident 1.0.24 in the local cargo cache):\n" + r.stderr.decode())
    versions = {
        "go": run(["go", "version"], env=env).stdout.decode().strip(),
        "rustc": run(["rustc", "--version"]).stdout.decode().strip(),
    }
    return go_bin, build_dir / "cargo-target" / "debug" / "crosscheck-rust", versions


def check_tables(go_bin, rust_bin):
    pinned = json.loads((VECTORS / cv.TABLES_FILE).read_text())
    problems = []
    go = json.loads(run([str(go_bin), "tables"]).stdout)
    rs = json.loads(run([str(rust_bin), "tables"]).stdout)
    for name, data in (("go unicode", go), ("unicode-ident", rs)):
        if data["unicodeVersion"] != "17.0.0":
            problems.append(f"{name} reports Unicode {data['unicodeVersion']}")
    for prop, data in (("go_letter", go), ("go_digit", go), ("xid_start", rs), ("xid_continue", rs)):
        if [list(r) for r in data[prop]] != pinned["properties"][prop]:
            problems.append(f"{prop} differs from the pinned table")
    return problems


def go_tokens(go_bin, data):
    out = run([str(go_bin)], input=data).stdout.decode("utf-8", "replace")
    toks, errs = [], []
    for line in out.splitlines():
        p = line.split("\t")
        if p[0] == "T":
            off, tok = int(p[1]), p[2]
            lit = base64.b64decode(p[3]).decode("utf-8", "surrogateescape")  # harness emits base64: no quoting to undo
            if tok in GO_CLASS:
                toks.append((GO_CLASS[tok], lit, off, False))
            elif tok in cv.GO_KEYWORDS:
                toks.append(("keyword", lit, off, False))
            elif tok == ";":
                toks.append(("punct", ";", None if lit == "\n" else off, lit == "\n"))
            else:
                toks.append(("punct", tok, off, False))
        elif p[0] == "ERR":
            errs.append(int(p[1]))
    return toks, errs


def contract_go_view(tokens):
    """Contract tokens in go/scanner's terms. Declared adjustments: inserted ';' compared by kind and
    order only (offsets differ by design); raw-string CR removed (go/scanner strips CR from raw literals)."""
    out = []
    for t in tokens:
        if t.get("inserted"):
            out.append(("punct", ";", None, True))
            continue
        text = t["text"]
        if t["class"] == "string" and text.startswith("`"):
            text = text.replace("\r", "")
        out.append((t["class"], text, t["span"][0], False))
    return out


def rust_tokens(rust_bin, data):
    out = run([str(rust_bin)], input=data).stdout.decode("utf-8")
    raw, err = [], None
    for line in out.splitlines():
        p = line.split("\t")
        if p[0] == "ERR":
            err = p[1]
        elif p[0] in ("I", "P", "D", "L"):
            text = bytes.fromhex(p[1]).decode("utf-8") if p[0] == "L" else p[1]
            raw.append((p[0], text, int(p[2]), int(p[3])))
    return raw, err


def doc_comment_intervals(data, tokens):
    """Byte intervals of doc comments in the trivia between the contract's tokens (accepted vectors only)."""
    text = data.decode("utf-8")
    b2c, acc = {}, 0
    for ci, ch in enumerate(text):
        b2c[acc] = ci
        acc += len(ch.encode("utf-8"))
    b2c[acc] = len(text)
    c2b = {c: b for b, c in b2c.items()}
    real = [t for t in tokens if not t.get("inserted")]
    bounds = [0] + [b2c[x] for t in real for x in t["span"]] + [len(text)]
    out = []
    for gs, ge in zip(bounds[::2], bounds[1::2]):
        i = gs
        if gs == 0:
            sb = cv.rust_shebang_end(text)
            i = sb if sb is not None else 0
        while i < ge:
            if text.startswith("//", i):
                nl = text.find("\n", i)
                end = len(text) if nl < 0 else nl
            elif text.startswith("/*", i):
                end = cv.skip_block(text, i, True) or len(text)
            else:
                i += 1
                continue
            if cv.rust_doc_comment_at(text, i):
                out.append((c2b[i], c2b[end]))
            i = end
    return out


def contract_rust_view(raw, data, docs):
    """proc-macro2 tokens in contract terms. Declared adjustments: a "'" Punct immediately followed by an
    Ident becomes a lifetime; tokens whose span starts inside a doc comment were synthesized by proc-macro2
    (#[doc = ...]) and are dropped (the contract drops doc comments, OD-5); ident/keyword class from the
    contract keyword list. Literal classes are not compared (proc-macro2 does not expose them)."""
    out, i = [], 0
    while i < len(raw):
        kind, text, s, e = raw[i]
        if kind == "P" and text == "'" and i + 1 < len(raw) and raw[i + 1][0] == "I" and raw[i + 1][2] == e:
            out.append(("lifetime", "'" + raw[i + 1][1], s, raw[i + 1][3]))
            i += 2
            continue
        i += 1
        if any(a <= s < b for a, b in docs):
            continue
        if kind == "I":
            cls = "keyword" if not text.startswith("r#") and text in cv.RUST_KEYWORDS else "ident"
        elif kind in ("P", "D"):
            cls = "punct"
        else:
            cls = "literal"
        out.append((cls, text, s, e))
    return out


def rustc_accepts(data, build_dir: Path):
    """Lexical acceptance. A leading BOM and a shebang line (as the contract decides it) must stay at file
    start; everything after them is wrapped in a token-swallowing macro, so name resolution never runs."""
    path = build_dir / "rustc-input.rs"
    prefix = b"\xef\xbb\xbf" if data.startswith(b"\xef\xbb\xbf") else b""
    rest = data[len(prefix):]
    try:
        sb = cv.rust_shebang_end(rest.decode("utf-8"))
    except UnicodeDecodeError:
        sb = None
    if sb is not None:
        cut = len(rest.decode("utf-8")[:sb].encode("utf-8"))
        prefix, rest = prefix + rest[:cut], rest[cut:]
    if prefix and not prefix.endswith(b"\n") and rest == b"":
        body = prefix + b"\n"
    else:
        body = prefix + (b"" if prefix.endswith(b"\n") or not prefix else b"\n")
        body += b"macro_rules! m { ($($t:tt)*) => {} }\nm! {\n" + rest + b"\n}\n"
    path.write_bytes(body)
    r = run(["rustc", "--edition", "2024", "--crate-type", "lib", "--emit=metadata", "-A", "warnings",
             "-o", str(build_dir / "rustc-output.rmeta"), str(path)])
    return r.returncode == 0


def outcome(vid, tool, got_kind, got_detail, problems, notes):
    """Compare an error-vector outcome with expectations."""
    exp = EXPECT.get(vid, {}).get(tool)
    if exp is None:
        if got_kind != "agree":
            problems.append(f"{vid} [{tool}]: unexpected {got_kind} {got_detail}")
        return "agree" if got_kind == "agree" else "UNEXPECTED"
    kind, detail, reason = exp
    if kind == "no-limit":
        notes.append(f"{vid} [{tool}]: {reason}")
        return "expected"
    if (kind, detail) != (got_kind, got_detail if kind == "offset" else None):
        problems.append(f"{vid} [{tool}]: expected {kind} {detail}, got {got_kind} {got_detail}")
        return "UNEXPECTED"
    notes.append(f"{vid} [{tool}]: {kind}{'' if detail is None else ' ' + str(detail)} ({reason})")
    return "expected"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-dir", type=Path)
    args = ap.parse_args()
    build_dir = args.build_dir or Path(tempfile.mkdtemp(prefix="traceweave-crosscheck-"))
    build_dir.mkdir(parents=True, exist_ok=True)
    cv.TABLES = cv.Tables(VECTORS / cv.TABLES_FILE)
    go_bin, rust_bin, versions = build(build_dir)
    problems, notes = [], []
    tally = {}

    def count(key):
        tally[key] = tally.get(key, 0) + 1

    table_problems = check_tables(go_bin, rust_bin)
    problems += table_problems
    print(f"tables: go unicode + unicode-ident 1.0.24 vs pinned 17.0.0 tables: {'MATCH' if not table_problems else table_problems}")
    seen = set()
    for name in GO_FILES:
        for v in json.loads((VECTORS / name).read_text())["vectors"]:
            seen.add(v["id"])
            data = base64.b64decode(v["inputBase64"])
            toks, errs = go_tokens(go_bin, data)
            res = v["result"]
            if res["status"] == "error":
                if not errs:
                    got = ("accepts", None)
                elif errs[0] == res["error"]["offset"]:
                    got = ("agree", None)
                else:
                    got = ("offset", errs[0])
                count(f"go error {outcome(v['id'], 'go/scanner', *got, problems, notes)}")
            else:
                exp = EXPECT.get(v["id"], {}).get("go/scanner")
                if toks == contract_go_view(res["tokens"]) and not errs:
                    count("go accepted agree")
                elif exp and exp[0] == "rejects" and toks == contract_go_view(res["tokens"]) and errs[:1] == [exp[1]]:
                    count("go accepted expected")
                    notes.append(f"{v['id']} [go/scanner]: rejects at {exp[1]} ({exp[2]})")
                else:
                    count("go accepted DIFF")
                    problems.append(f"{v['id']} [go/scanner]: token mismatch {toks} vs {contract_go_view(res['tokens'])} errs={errs}")
    for name in RUST_FILES:
        for v in json.loads((VECTORS / name).read_text())["vectors"]:
            seen.add(v["id"])
            data = base64.b64decode(v["inputBase64"])
            res = v["result"]
            probe = data
            sb = cv.rust_shebang_end(data.decode("utf-8", "replace")) if data.startswith(b"#!") else None
            if sb is not None:  # declared adjustment: proc-macro2 does not strip shebangs; blank it, keep offsets
                cut = len(data.decode("utf-8")[:sb].encode("utf-8"))
                probe = bytes(b if b == 0x0A else 0x20 for b in data[:cut]) + data[cut:]
            raw, err = rust_tokens(rust_bin, probe)
            accepted = rustc_accepts(data, build_dir)
            if res["status"] == "error":
                if err is None:
                    got = ("accepts", None)
                elif err.startswith("invalid-utf8"):
                    got = ("agree", None) if int(err.split()[1]) == res["error"]["offset"] else ("offset", int(err.split()[1]))
                elif int(err) == res["error"]["offset"]:
                    got = ("agree", None)
                else:
                    got = ("offset", int(err))
                count(f"rust error proc-macro2 {outcome(v['id'], 'proc-macro2', *got, problems, notes)}")
                count(f"rust error rustc {outcome(v['id'], 'rustc', 'agree' if not accepted else 'accepts', None, problems, notes)}")
            else:
                mine = [("literal" if t["class"] in ("int", "float", "char", "byte", "string", "rawstring", "bytestring",
                                                     "rawbytestring", "cstring", "rawcstring") else t["class"],
                         t["text"], t["span"][0], t["span"][1]) for t in res["tokens"]]
                view = contract_rust_view(raw, data, doc_comment_intervals(data, res["tokens"]))
                if err is None and view == mine:
                    count("rust accepted proc-macro2 agree")
                else:
                    count("rust accepted proc-macro2 DIFF")
                    problems.append(f"{v['id']} [proc-macro2]: {view} vs {mine} err={err}")
                if accepted:
                    count("rust accepted rustc accepts")
                else:
                    count("rust accepted rustc REJECTS")
                    problems.append(f"{v['id']} [rustc]: rejects an input the contract accepts")
    stale = sorted(set(EXPECT) - seen)
    problems += [f"EXPECT entry for unknown vector {s}" for s in stale]
    print(f"toolchains: {versions['go']}; {versions['rustc']}; proc-macro2 1.0.107 + unicode-ident 1.0.24 (Cargo.lock)")
    for key in sorted(tally):
        print(f"  {key}: {tally[key]}")
    print("expected divergences:")
    for n in notes:
        print(f"  {n}")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(f"  {p}")
        return 1
    print("PASS: no unexpected divergence")
    return 0


if __name__ == "__main__":
    sys.exit(main())
