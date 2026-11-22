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
LIMIT = ("no-limit", None, "maxInputBytes is a contract parameter; toolchains have no size limit")
EXPECT = {
    "go-err-bom": {"go/scanner": ("accepts", None, "OD-1: go/scanner skips a leading BOM; the contract rejects it")},
    "go-err-malformed-number": {"go/scanner": ("offset", 7, "OD-13: contract reports the token start")},
    "go-err-invalid-escape": {"go/scanner": ("offset", 7, "OD-13: contract reports the token start")},
    "go-err-hex-float-no-exponent": {"go/scanner": ("offset", 10, "OD-13: contract reports the token start")},
    "go-limit-over": {"go/scanner": LIMIT},
    "go-limit-precedence": {"go/scanner": ("offset", 6, "size check precedes UTF-8 check; go/scanner reports the 0xFF byte")},
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
            lit = json.loads(p[3]) if "\\x" not in p[3] else p[3]
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


def contract_rust_view(raw, data):
    """proc-macro2 tokens in contract terms. Declared adjustments: a "'" Punct immediately followed by an
    Ident becomes a lifetime; tokens whose source bytes differ from their text were synthesized from doc
    comments and are dropped (the contract drops doc comments, OD-5); ident/keyword class from the
    contract keyword list. Literal classes are not compared (proc-macro2 does not expose them)."""
    out, i = [], 0
    while i < len(raw):
        kind, text, s, e = raw[i]
        if kind == "P" and text == "'" and i + 1 < len(raw) and raw[i + 1][0] == "I" and raw[i + 1][2] == e:
            out.append(("lifetime", "'" + raw[i + 1][1], s, raw[i + 1][3]))
            i += 2
            continue
        i += 1
        if data[s:e] != text.encode("utf-8"):
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
    path = build_dir / "rustc-input.rs"
    if data.startswith((b"#!", b"\xef\xbb\xbf")):
        body = data
    else:
        body = b"macro_rules! m { ($($t:tt)*) => {} }\nm! {\n" + data + b"\n}\n"
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
                if toks == contract_go_view(res["tokens"]) and not errs:
                    count("go accepted agree")
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
                if err is None and contract_rust_view(raw, data) == mine:
                    count("rust accepted proc-macro2 agree")
                else:
                    count("rust accepted proc-macro2 DIFF")
                    problems.append(f"{v['id']} [proc-macro2]: {contract_rust_view(raw, data)} vs {mine} err={err}")
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
