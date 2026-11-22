"""Build the draft extraction vectors from hand-written token streams.

Usage: python3 -I harness/build_vectors.py [OUTPUT_DIR]   (default: the vector directory)

The token streams, error codes and offsets below are written by hand from the
contract; this script only serialises them and computes k-grams, hashes and
winnowing. check_vectors.py re-verifies everything independently and
crosscheck.py compares the streams with go/scanner, proc-macro2 and rustc.
"""
import base64, hashlib, json, sys
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
K, W = 5, 4
CONTRACT = "traceweave-token-winnow-draft-1"
DOMAIN = b"traceweave/token-kgram/draft-1"
PROFILES = {"go": "go-tokens", "rust": "rust2024-tokens"}
PVER = "draft-1"
LIT = {"go": {"int", "float", "imag", "rune", "string"},
       "rust": {"int", "float", "char", "byte", "string", "rawstring", "bytestring", "rawbytestring", "cstring", "rawcstring"}}

def config_bytes(lang, limit=1048576):
    c = {"contract": CONTRACT, "profile": PROFILES[lang], "profileVersion": PVER, "channels": ["exact", "normalized"],
         "k": K, "window": W, "hash": "sha256-first8-u64be", "maxInputBytes": limit}
    return (json.dumps(c, separators=(",", ":"), ensure_ascii=False) + "\n").encode()

def lp(b): return len(b).to_bytes(4, "big") + b

def kgram_hash(lang, channel, toks):
    data = lp(DOMAIN) + lp(PROFILES[lang].encode()) + lp(PVER.encode()) + lp(channel.encode()) + K.to_bytes(4, "big")
    for c, v in toks: data += lp(c.encode()) + lp(v.encode())
    return hashlib.sha256(data).digest()[:8].hex()

def normalize(lang, cls, text):
    if cls == "ident" or cls in LIT[lang]: return ""
    if cls == "lifetime" and text not in ("'static", "'_"): return ""
    return text

def winnow(h):
    m = len(h)
    if m == 0: return [], False
    if m < W:
        best = max(i for i in range(m) if h[i] == min(h)); return [best], True
    sel = []
    for s in range(m - W + 1):
        win = h[s:s + W]; mn = min(win)
        sel.append(s + max(i for i in range(W) if win[i] == mn))
    return sel, False

def build(lang, vid, desc, src, toks=None, err=None, tags=()):
    v = {"id": vid, "tags": list(tags), "description": desc, "inputBase64": base64.b64encode(src).decode()}
    try: v["inputText"] = src.decode("utf-8")
    except UnicodeDecodeError: v["inputText"] = None; v["inputDisplay"] = src.decode("utf-8", "backslashreplace")
    if err:
        v["result"] = {"status": "error", "error": {"code": err[0], "offset": err[1]}}
        return v
    tokens, pos = [], 0
    for t in toks:
        cls, text = t[0], t[1]
        if len(t) > 2 and t[2] == "AUTO":
            end = tokens[-1]["span"][1]
            tokens.append({"class": "punct", "text": ";", "span": [end, end], "inserted": True}); continue
        b = text.encode()
        i = t[2] if len(t) > 2 and isinstance(t[2], int) else src.index(b, pos)  # explicit start where search would mislocate
        assert src[i:i + len(b)] == b and i >= pos, (vid, text)
        tokens.append({"class": cls, "text": text, "span": [i, i + len(b)]}); pos = i + len(b)
    res = {"status": "ok" if len(tokens) >= K else "insufficient-tokens", "tokenCount": len(tokens), "tokens": tokens, "channels": {}}
    for ch in ("exact", "normalized"):
        stream = [(t["class"], t["text"] if ch == "exact" else normalize(lang, t["class"], t["text"])) for t in tokens]
        kg = []
        for i in range(len(tokens) - K + 1):
            kg.append({"position": i, "hash": kgram_hash(lang, ch, stream[i:i + K]),
                       "span": [tokens[i]["span"][0], tokens[i + K - 1]["span"][1]]})
        sel, partial = winnow([int(x["hash"], 16) for x in kg])
        fps = [{"position": p, "hash": kg[p]["hash"], "span": kg[p]["span"]} for p in sorted(set(sel))]
        chd = {}
        if ch == "normalized": chd["values"] = [s[1] for s in stream]
        chd.update({"kgrams": kg, "windowSelections": sel, "partialWindow": partial, "fingerprints": fps})
        res["channels"][ch] = chd
    v["result"] = res
    return v

def fmt(o, ind=0):
    c = json.dumps(o, ensure_ascii=False, separators=(", ", ": "))
    if len(c) + ind <= 110 or not isinstance(o, (dict, list)) or not o:
        return c
    pad = " " * (ind + 2)
    if isinstance(o, dict):
        items = [pad + json.dumps(k, ensure_ascii=False) + ": " + fmt(v, ind + 2) for k, v in o.items()]
        return "{\n" + ",\n".join(items) + "\n" + " " * ind + "}"
    return "[\n" + ",\n".join(pad + fmt(v, ind + 2) for v in o) + "\n" + " " * ind + "]"

def dump(obj, path):
    path.write_text(fmt(obj) + "\n", encoding="utf-8")

A = "AUTO"
I, P, KW = "ident", "punct", "keyword"
go = []
g = lambda *a, **k: go.append(build("go", *a, **k))
g("go-empty", "Empty input: zero tokens, no k-grams.", b"", [], tags=["empty"])
g("go-short", "Four tokens (including the semicolon inserted at the final newline) is fewer than k=5.", b"x := 1\n",
  [(I, "x"), (P, ":="), ("int", "1"), (P, ";", A)], tags=["short"])
g("go-exact-k", "Exactly k=5 tokens: one k-gram, partial window selects it.", b"return x + 1\n",
  [(KW, "return"), (I, "x"), (P, "+"), ("int", "1"), (P, ";", A)], tags=["exact-k"])
g("go-unicode", "Unicode letters in identifiers, multi-byte string and rune literals; spans are UTF-8 byte offsets.",
  "päivä := \"héllo, 世界\" + 名前 + string('☃')\n".encode(),
  [(I, "päivä"), (P, ":="), ("string", "\"héllo, 世界\""), (P, "+"), (I, "名前"), (P, "+"), (I, "string"), (P, "("), ("rune", "'☃'"), (P, ")"), (P, ";", A)],
  tags=["unicode"])
g("go-literals", "Numeric literal forms, raw string spanning a newline (no insertion inside it), interpreted string escapes.",
  b"a := []int{0x1F, 1_000, 0o17, 0755}\nb := 1.5e3 + .5 + 0x1p-2 + 2i\nc := `raw\nline` + \"\\t\\\"q\\\"\"\n",
  [(I, "a"), (P, ":="), (P, "["), (P, "]"), (I, "int"), (P, "{"), ("int", "0x1F"), (P, ","), ("int", "1_000"), (P, ","), ("int", "0o17"), (P, ","), ("int", "0755"), (P, "}"), (P, ";", A),
   (I, "b"), (P, ":="), ("float", "1.5e3"), (P, "+"), ("float", ".5"), (P, "+"), ("float", "0x1p-2"), (P, "+"), ("imag", "2i"), (P, ";", A),
   (I, "c"), (P, ":="), ("string", "`raw\nline`"), (P, "+"), ("string", "\"\\t\\\"q\\\"\""), (P, ";", A)], tags=["literals"])
g("go-semicolon-comments", "No insertion after ',' at line end; a general comment containing a newline and a final line comment each act as a newline.",
  b"x := f(a,\n\tb) /* c\n */ y := 2 // end",
  [(I, "x"), (P, ":="), (I, "f"), (P, "("), (I, "a"), (P, ","), (I, "b"), (P, ")"), (P, ";", A), (I, "y"), (P, ":="), ("int", "2"), (P, ";", A)],
  tags=["semicolon-insertion", "comments"])
g("go-repeated", "Ten identical tokens: all k-grams identical, every window ties, rightmost minimum wins; duplicate hashes at distinct positions are all retained.",
  b"+ + + + + + + + + +", [(P, "+")] * 10, tags=["repeated", "equal-minimum"])
g("go-equal-minimum", "Period-3 token sequence: every window of 4 contains a repeated k-gram, so ties on the minimum are guaranteed.",
  b"x++\nx++\nx++\nx++\n", [(I, "x"), (P, "++"), (P, ";", A)] * 4, tags=["repeated", "equal-minimum"])
FMT = [(KW, "func"), (I, "add"), (P, "("), (I, "a"), (P, ","), (I, "b"), (I, "int"), (P, ")"), (I, "int"), (P, "{"), (KW, "return"), (I, "a"), (P, "+"), (I, "b"), (P, ";", A), (P, "}"), (P, ";", A)]
g("go-format-a", "Reference for the comment/whitespace pair.", b"func add(a, b int) int {\n\treturn a + b\n}\n", FMT, tags=["trivia-pair"])
g("go-format-b", "Same tokens as go-format-a with different comments and whitespace and no final newline; fingerprint hashes must be identical.",
  b"// add sums.\nfunc add(a,b int)int{ // sum\n  return a+b /* plain */\n}", FMT, tags=["trivia-pair", "comments"])
REN = lambda f, x, y: [(KW, "func"), (I, f), (P, "("), (I, x), (P, ","), (I, y), (I, "int"), (P, ")"), (I, "int"), (P, "{"), (KW, "return"), (I, x), (P, "+"), (I, y), (P, "}"), (P, ";", A)]
g("go-rename-a", "Reference for the rename pair.", b"func add(a, b int) int { return a + b }\n", REN("add", "a", "b"), tags=["rename-pair"])
g("go-rename-b", "Identifiers renamed: exact hashes differ, normalized hashes equal go-rename-a.", b"func sum(x, y int) int { return x + y }\n", REN("sum", "x", "y"), tags=["rename-pair"])
g("go-err-invalid-utf8", "Byte 0xFF inside a string literal: invalid UTF-8, rejected before lexing.", b"x := \"a\xffb\"\n", err=("invalid-utf8", 7), tags=["malformed"])
g("go-err-bom", "Leading UTF-8 byte order mark: rejected (stricter than go/scanner, which skips it).", b"\xef\xbb\xbfpackage p\n", err=("bom", 0), tags=["malformed"])
g("go-err-nul", "NUL character: rejected.", b"x := 1\x00\n", err=("nul", 6), tags=["malformed"])
g("go-err-unterminated-string", "Newline before the closing quote of an interpreted string.", b"s := \"abc\nt := 1\n", err=("unterminated-literal", 5), tags=["malformed"])
g("go-err-unterminated-comment", "General comment never closed.", b"x := 1 /* never closed", err=("unterminated-comment", 7), tags=["malformed"])
g("go-err-illegal-character", "'#' does not begin any Go token.", b"a := b # c\n", err=("illegal-character", 7), tags=["malformed"])
g("go-err-malformed-number", "Hex prefix without digits.", b"x := 0x\n", err=("malformed-literal", 5), tags=["malformed"])
g("go-err-invalid-escape", "Unknown escape \\q in an interpreted string; offset is the literal start.", b"s := \"\\q\"\n", err=("malformed-literal", 5), tags=["malformed"])

g("go-unicode-boundary", "Identifier boundary code points accepted by Go: U+2E2F VERTICAL TILDE is Lm (a letter), U+0660 is Nd (a digit, allowed after the first character), '_' alone is an identifier.",
  "aⸯ := x٠ + _\n".encode(), [(I, "aⸯ"), (P, ":="), (I, "x٠"), (P, "+"), (I, "_"), (P, ";", A)], tags=["unicode", "unicode-boundary"])
g("go-err-u2160", "U+2160 ROMAN NUMERAL ONE is Nl, not a Go letter: illegal character (Rust accepts it).", "xⅠ := 1\n".encode(), err=("illegal-character", 1), tags=["malformed", "unicode-boundary"])
g("go-err-u00b7", "U+00B7 MIDDLE DOT is Po: illegal in Go identifiers (Rust XID_Continue accepts it).", "x·y := 1\n".encode(), err=("illegal-character", 1), tags=["malformed", "unicode-boundary"])
g("go-err-u0345", "U+0345 COMBINING YPOGEGRAMMENI is Mn: illegal in Go (Rust XID_Continue accepts it).", "x\u0345 := 1\n".encode(), err=("illegal-character", 1), tags=["malformed", "unicode-boundary"])
g("go-err-u200d", "U+200D ZERO WIDTH JOINER is Cf: illegal in Go.", "x\u200d := 1\n".encode(), err=("illegal-character", 1), tags=["malformed", "unicode-boundary"])
g("go-err-nd-start", "U+0660 (Nd) cannot start an identifier and does not start a number.", "٠x := 1\n".encode(), err=("illegal-character", 0), tags=["malformed", "unicode-boundary"])
g("go-err-mid-bom", "U+FEFF after offset 0 is rejected by the forbidden-code-point scan.", "x := 1\n\ufeff".encode(), err=("bom", 7), tags=["malformed"])
g("go-err-hex-float-no-exponent", "Hex mantissa with '.' but no 'p' exponent matches no literal production.", b"f := 0x1.8\n", err=("malformed-literal", 5), tags=["malformed", "literals"])
g("go-raw-string-cr", "CR inside a raw string is kept in the exact token text (OD-9); go/scanner strips it from its literal value.",
  b"s := `a\r\nb` + t\n", [(I, "s"), (P, ":="), ("string", "`a\r\nb`"), (P, "+"), (I, "t"), (P, ";", A)], tags=["literals"])

# ---- contract questions from the two-implementation cross-check (revision draft-1, 2026-11-22) ----
g("go-q9-unassigned", "Q9: U+0378 is unassigned (not in go_letter): illegal character. The assigned table is informative only.", "\u0378".encode(), err=("illegal-character", 0), tags=["malformed", "question", "unicode-boundary"])
g("go-q11-imag-binary-digit", "Q11: '0b2i' matches no production (0b2 is not int_lit or decimal_digits): malformed. go/scanner accepts; cmd/compile rejects.", b"0b2i", err=("malformed-literal", 0), tags=["malformed", "question", "literals"])
g("go-q11-imag-octal-digit", "Q11: '0o9i' likewise malformed.", b"0o9i", err=("malformed-literal", 0), tags=["malformed", "question", "literals"])
g("go-q12-line-directive", "Q12: '/*line :*/' is an ordinary general comment (section 4.6): zero tokens. go/scanner rejects it as an invalid line directive.", b"/*line :*/", [], tags=["question", "comments"])
g("go-escapes-vt-raw", "Interpreted string with \\x escape and a raw string containing U+000B (exercises the cross-check harness quoting fix).",
  b"s := \"\\x41\" + `a\x0bb`\n", [(I, "s"), (P, ":="), ("string", "\"\\x41\""), (P, "+"), ("string", "`a\x0bb`"), (P, ";", A)], tags=["literals"])

rs = []
r = lambda *a, **k: rs.append(build("rust", *a, **k))
r("rust-empty", "Empty input: zero tokens, no k-grams.", b"", [], tags=["empty"])
r("rust-short", "Four tokens is fewer than k=5.", b"let x = 1", [(KW, "let"), (I, "x"), (P, "="), ("int", "1")], tags=["short"])
r("rust-exact-k", "Exactly k=5 tokens: one k-gram, partial window selects it.", b"let x = 1;", [(KW, "let"), (I, "x"), (P, "="), ("int", "1"), (P, ";")], tags=["exact-k"])
r("rust-unicode", "NFC Unicode identifiers, multi-byte string and char literals; spans are UTF-8 byte offsets.",
  "let größe: &str = \"naïve ☃ 世界\";\nlet λ = 'é';\n".encode(),
  [(KW, "let"), (I, "größe"), (P, ":"), (P, "&"), (I, "str"), (P, "="), ("string", "\"naïve ☃ 世界\""), (P, ";"),
   (KW, "let"), (I, "λ"), (P, "="), ("char", "'é'"), (P, ";")], tags=["unicode"])
r("rust-literals", "Integer/float forms with suffixes, '2.' float, tuple-index float, raw/byte/raw-byte/C strings.",
  b"let v = [0xFF_u8, 1_000, 0o17, 0b1010, 1.5e3, 2., 3f32];\nlet s = r#\"raw \"q\"\"#; let b = b'\\n'; let bs = br\"\\d\"; let c = c\"hi\";\nlet t = p.0.1;\n",
  [(KW, "let"), (I, "v"), (P, "="), (P, "["), ("int", "0xFF_u8"), (P, ","), ("int", "1_000"), (P, ","), ("int", "0o17"), (P, ","), ("int", "0b1010"), (P, ","),
   ("float", "1.5e3"), (P, ","), ("float", "2."), (P, ","), ("int", "3f32"), (P, "]"), (P, ";"),
   (KW, "let"), (I, "s"), (P, "="), ("rawstring", "r#\"raw \"q\"\"#"), (P, ";"), (KW, "let"), (I, "b"), (P, "="), ("byte", "b'\\n'"), (P, ";"),
   (KW, "let"), (I, "bs"), (P, "="), ("rawbytestring", "br\"\\d\""), (P, ";"), (KW, "let"), (I, "c"), (P, "="), ("cstring", "c\"hi\""), (P, ";"),
   (KW, "let"), (I, "t"), (P, "="), (I, "p"), (P, "."), ("float", "0.1"), (P, ";")], tags=["literals"])
r("rust-lifetimes-chars", "Lifetimes versus char literals, 'static kept under normalization, raw identifier, single-character punctuation for '->'.",
  b"fn r#match<'a>(x: &'a str, y: &'static str) -> char { 'a' }",
  [(KW, "fn"), (I, "r#match"), (P, "<"), ("lifetime", "'a"), (P, ">"), (P, "("), (I, "x"), (P, ":"), (P, "&"), ("lifetime", "'a"), (I, "str"), (P, ","),
   (I, "y"), (P, ":"), (P, "&"), ("lifetime", "'static"), (I, "str"), (P, ")"), (P, "-"), (P, ">"), (I, "char"), (P, "{"), ("char", "'a'"), (P, "}")],
  tags=["lifetimes", "chars"])
r("rust-shebang", "A first line starting '#!' not followed by '[' is a shebang and is skipped.",
  b"#!/usr/bin/env run-cargo-script\nfn main() {}\n", [(KW, "fn"), (I, "main"), (P, "("), (P, ")"), (P, "{"), (P, "}")], tags=["shebang"])
r("rust-inner-attribute", "'#!' followed by '[' is an inner attribute, not a shebang.",
  b"#![allow(dead_code)]\nfn main() {}\n",
  [(P, "#"), (P, "!"), (P, "["), (I, "allow"), (P, "("), (I, "dead_code"), (P, ")"), (P, "]"), (KW, "fn"), (I, "main"), (P, "("), (P, ")"), (P, "{"), (P, "}")], tags=["shebang"])
r("rust-doc-comment", "Doc comments are dropped like other comments (rustc treats them as doc attributes).",
  b"/// Adds.\n//! inner\n/** block doc */\nfn add() {}\n", [(KW, "fn"), (I, "add"), (P, "("), (P, ")"), (P, "{"), (P, "}")], tags=["comments"])
r("rust-repeated", "Ten identical tokens: all k-grams identical, every window ties, rightmost minimum wins.",
  b"+ + + + + + + + + +", [(P, "+")] * 10, tags=["repeated", "equal-minimum"])
r("rust-equal-minimum", "Period-3 token sequence: every window of 4 contains a repeated k-gram, so ties on the minimum are guaranteed.",
  b"{x} {x} {x} {x}", [(P, "{"), (I, "x"), (P, "}")] * 4, tags=["repeated", "equal-minimum"])
FR = [(KW, "fn"), (I, "add"), (P, "("), (I, "a"), (P, ":"), (I, "i32"), (P, ","), (I, "b"), (P, ":"), (I, "i32"), (P, ")"), (P, "-"), (P, ">"), (I, "i32"), (P, "{"), (I, "a"), (P, "+"), (I, "b"), (P, "}")]
r("rust-format-a", "Reference for the comment/whitespace pair.", b"fn add(a: i32, b: i32) -> i32 {\n    a + b\n}\n", FR, tags=["trivia-pair"])
r("rust-format-b", "Same tokens as rust-format-a with line and nested block comments and different whitespace; fingerprint hashes must be identical.",
  b"// line comment\r\nfn add(a:i32,b:i32)->i32{/* outer /* nested */ still comment */a+b // tail\r\n}", FR, tags=["trivia-pair", "comments"])
RR = lambda f, x, y: [(KW, "fn"), (I, f), (P, "("), (I, x), (P, ":"), (I, "i32"), (P, ","), (I, y), (P, ":"), (I, "i32"), (P, ")"), (P, "-"), (P, ">"), (I, "i32"), (P, "{"), (I, x), (P, "+"), (I, y), (P, "}")]
r("rust-rename-a", "Reference for the rename pair.", b"fn add(a: i32, b: i32) -> i32 { a + b }", RR("add", "a", "b"), tags=["rename-pair"])
r("rust-rename-b", "Identifiers renamed: exact hashes differ, normalized hashes equal rust-rename-a.", b"fn sum(x: i32, y: i32) -> i32 { x + y }", RR("sum", "x", "y"), tags=["rename-pair"])
r("rust-err-invalid-utf8", "Byte 0xFF inside a string literal: invalid UTF-8.", b"let s = \"a\xffb\";", err=("invalid-utf8", 10), tags=["malformed"])
r("rust-err-bom", "Leading byte order mark: rejected (stricter than the Reference, which removes it).", b"\xef\xbb\xbffn main() {}\n", err=("bom", 0), tags=["malformed"])
r("rust-err-nul", "NUL inside a string literal: rejected (stricter than the Reference).", b"let s = \"a\x00\";", err=("nul", 10), tags=["malformed"])
r("rust-err-isolated-cr", "CR not followed by LF: rejected (stricter than the Reference, which treats it as whitespace here).", b"let a = 1;\rlet b = 2;", err=("isolated-cr", 10), tags=["malformed"])
r("rust-err-unterminated-nested-comment", "Nested block comment: the inner '*/' closes only the inner level.", b"fn f() {} /* outer /* inner */ still open", err=("unterminated-comment", 10), tags=["malformed", "comments"])
r("rust-err-unterminated-string", "String literal never closed.", b"let s = \"abc;\n", err=("unterminated-literal", 8), tags=["malformed"])
r("rust-err-unbalanced", "Closing '}' while '(' is open.", b"fn f() { (1 }", err=("unbalanced-delimiter", 12), tags=["malformed"])
r("rust-err-char-two-codepoints", "'ab' is neither a char literal nor a lifetime.", b"let c = 'ab';", err=("malformed-literal", 8), tags=["malformed", "lifetimes"])
r("rust-err-reserved-prefix", "Identifier immediately followed by '\"' is a reserved prefix in edition 2021+.", b"let s = f\"x\";", err=("reserved-token", 8), tags=["malformed"])
r("rust-err-non-nfc-identifier", "Identifier 'e' + U+0301 is valid XID but not NFC: rejected rather than normalized.", "let e\u0301 = 1;".encode(), err=("non-nfc-identifier", 4), tags=["malformed", "unicode"])

r("rust-unicode-boundary", "XID boundary code points accepted by Rust: U+2160 (XID_Start), U+00B7 and U+0345 (XID_Continue); all NFC.",
  "let xⅠ = x·y + x\u0345;".encode(), [(KW, "let"), (I, "xⅠ"), (P, "="), (I, "x·y"), (P, "+"), (I, "x\u0345"), (P, ";")], tags=["unicode", "unicode-boundary"])
r("rust-err-u2e2f", "U+2E2F VERTICAL TILDE is Pattern_Syntax, not XID: illegal character after the identifier 'a' (Go accepts it as Lm).", "let aⸯ = 1;".encode(), err=("illegal-character", 5), tags=["malformed", "unicode-boundary"])
r("rust-err-u200d", "U+200D is XID_Continue in Unicode 17.0 but forbidden in identifiers by [ident.zero-width-chars].", "let x\u200d = 1;".encode(), err=("malformed-identifier", 4), tags=["malformed", "unicode-boundary"])
r("rust-err-non-nfc-suffix", "Literal suffix 'u8' + 'e' + U+0301 is not NFC; offset is the literal start.", "let n = 1_u8e\u0301;".encode(), err=("non-nfc-identifier", 8), tags=["malformed", "unicode-boundary"])
r("rust-err-non-nfc-raw-ident", "Raw identifier r#e + U+0301 is not NFC; offset is the token start (the 'r').", "let r#e\u0301 = 1;".encode(), err=("non-nfc-identifier", 4), tags=["malformed", "unicode-boundary"])
r("rust-err-non-nfc-before-quote", "Non-NFC identifier immediately followed by '\"': the NFC check precedes the reserved-prefix check.", "let s = e\u0301\"x\";".encode(), err=("non-nfc-identifier", 8), tags=["malformed", "unicode-boundary"])
r("rust-err-string-underscore-suffix", "'_' after a string with no XID_Continue after it: the Reference SUFFIX cut makes this an error, not a string plus '_'.", b"let s = \"x\"_;", err=("malformed-literal", 8), tags=["malformed", "literals"])
r("rust-err-char-underscore-suffix", "Same suffix cut after a char literal.", b"let c = 'a'_;", err=("malformed-literal", 8), tags=["malformed", "literals"])
r("rust-literal-suffixes", "Suffixes are part of literal tokens: '_' followed by XID_Continue is a valid suffix; 0x1f32 is a hex int; 1e3f32 a float.",
  b"m!(\"x\"_a 'c'sfx 1_u8 0x1f32 1e3f32 b\"y\"_z);",
  [(I, "m"), (P, "!"), (P, "("), ("string", "\"x\"_a"), ("char", "'c'sfx"), ("int", "1_u8"), ("int", "0x1f32"), ("float", "1e3f32"), ("bytestring", "b\"y\"_z"), (P, ")"), (P, ";")], tags=["literals"])
r("rust-raw-lifetime", "Raw lifetimes (edition 2021+) are single lifetime tokens; normalized to empty like other lifetimes.",
  b"fn f<'r#fn>(x: &'r#fn u8) {}",
  [(KW, "fn"), (I, "f"), (P, "<"), ("lifetime", "'r#fn"), (P, ">"), (P, "("), (I, "x"), (P, ":"), (P, "&"), ("lifetime", "'r#fn"), (I, "u8"), (P, ")"), (P, "{"), (P, "}")], tags=["lifetimes"])
r("rust-err-reserved-raw-lifetime", "'r#_ is RESERVED_RAW_LIFETIME.", b"fn f<'r#_>() {}", err=("reserved-token", 5), tags=["malformed", "lifetimes"])
r("rust-err-pounds", "'##' is RESERVED_POUNDS in edition 2024.", b"a ## b", err=("reserved-token", 2), tags=["malformed"])
r("rust-cstring-escapes", "C string with byte, Unicode and ASCII escapes.", b"let c = c\"a\\x41\\u{e9}\\n\";",
  [(KW, "let"), (I, "c"), (P, "="), ("cstring", "c\"a\\x41\\u{e9}\\n\""), (P, ";")], tags=["literals"])
r("rust-err-cstring-nul-escape", "C strings forbid the \\0 escape.", b"let c = c\"\\0\";", err=("malformed-literal", 8), tags=["malformed", "literals"])
r("rust-err-raw-too-many-hashes", "A raw string with 256 '#' exceeds the 255 limit.", b"r" + b"#" * 256 + b"\"x\"" + b"#" * 256, err=("malformed-literal", 0), tags=["malformed", "literals"])
r("rust-err-cr-in-literal", "Isolated CR inside a string literal: rejected by the forbidden-code-point scan.", b"let s = \"a\rb\";", err=("isolated-cr", 10), tags=["malformed"])
r("rust-err-mid-bom", "U+FEFF inside a string literal (not at offset 0) is rejected.", "let s = \"\ufeff\";".encode(), err=("bom", 9), tags=["malformed"])
r("rust-shebang-unterminated-comment", "Shebang look-ahead: an unterminated block comment counts as comment, so '#!' starts a shebang (matches rustc).",
  b"#!/*x\nfn main() {}", [(KW, "fn"), (I, "main"), (P, "("), (P, ")"), (P, "{"), (P, "}")], tags=["shebang"])

# ---- contract questions from the two-implementation cross-check (revision draft-1, 2026-11-22) ----
r("rust-q1-raw-extra-hash", "Q1: a raw string ends at the first '\"' followed by n '#'; the extra '#' is punctuation.", b"r#\"a\"##",
  [("rawstring", "r#\"a\"#"), (P, "#")], tags=["question", "literals"])
r("rust-q1-raw-extra-pounds", "Q1: after the raw string, '##' is RESERVED_POUNDS.", b"r#\"a\"###", err=("reserved-token", 6), tags=["malformed", "question", "literals"])
r("rust-q2-open-then-unterminated", "Q2: errors in scan order; the unterminated string comes before the end-of-input delimiter check.", b"( \"abc", err=("unterminated-literal", 2), tags=["malformed", "question"])
r("rust-q2-open-then-illegal", "Q2: scan order: illegal character before the unclosed '('.", "( €".encode(), err=("illegal-character", 2), tags=["malformed", "question"])
r("rust-q2-unclosed-innermost", "Q2: two unclosed openers at end of input: the innermost '[' is reported.", b"( [ x", err=("unbalanced-delimiter", 2), tags=["malformed", "question"])
r("rust-q3-byte-unclosed", "Q3: char and byte literals have no unterminated state: b'a at end of input is malformed.", b"b'a", err=("malformed-literal", 0), tags=["malformed", "question", "literals"])
r("rust-q4-cstring-xff", "Q4: C strings accept \\x escapes 01-FF.", b"c\"\\xff\"", [("cstring", "c\"\\xff\"")], tags=["question", "literals"])
r("rust-q4-cstring-x00", "Q4: \\x00 in a C string is malformed.", b"c\"\\x00\"", err=("malformed-literal", 0), tags=["malformed", "question", "literals"])
r("rust-q4-cstring-u-zero", "Q4: any \\u{...} spelling of zero (here \\u{0_0}) is malformed in a C string.", b"c\"\\u{0_0}\"", err=("malformed-literal", 0), tags=["malformed", "question", "literals"])
r("rust-q5-raw-lifetime-hash", "Q5: a raw lifetime followed by '#' is not reserved: lifetime then '#'.", b"'r#a#", [("lifetime", "'r#a"), (P, "#")], tags=["question", "lifetimes"])
r("rust-q6-lifetime-nfc-first", "Q6: lifetime checks run NFC, then zero-width, then the '#' reservation.", "'e\u0301#".encode(), err=("non-nfc-identifier", 0), tags=["malformed", "question", "lifetimes", "unicode-boundary"])
r("rust-q6-lifetime-zwj-before-hash", "Q6: zero-width check precedes the '#' reservation.", "'a\u200d#".encode(), err=("malformed-identifier", 0), tags=["malformed", "question", "lifetimes", "unicode-boundary"])
r("rust-q7-unterminated-escape", "Q7: termination is decided first (escape-aware): '\"\\q' has no closing quote.", b"\"\\q", err=("unterminated-literal", 0), tags=["malformed", "question", "literals"])
r("rust-q7-closed-bad-escape", "Q7: closed literal with an unknown escape is malformed.", b"\"\\q\"", err=("malformed-literal", 0), tags=["malformed", "question", "literals"])
r("rust-q7-raw-byte-unterminated", "Q7: an unterminated raw byte string is unterminated even though its content is not ASCII.", "br\"é".encode(), err=("unterminated-literal", 0), tags=["malformed", "question", "literals"])
r("rust-q8-shebang-outer-line-doc", "Q8: in the shebang look-ahead '///' is a doc comment, i.e. content, so line 1 is a shebang (Reference SHEBANG, rustc).",
  b"#!///x\n[a]", [(P, "["), (I, "a"), (P, "]")], tags=["question", "shebang"])
r("rust-q8-shebang-inner-line-doc", "Q8: '//!' is a doc comment: shebang.", b"#!//!x\n[a]", [(P, "["), (I, "a"), (P, "]")], tags=["question", "shebang"])
r("rust-q8-shebang-outer-block-doc", "Q8: '/** d */' is a doc comment: shebang through end of input (no LF), zero tokens.", b"#!/** d */[a]", [], tags=["question", "shebang"])
r("rust-q8-shebang-inner-block-doc", "Q8: '/*! d */' is a doc comment: shebang, zero tokens.", b"#!/*! d */[a]", [], tags=["question", "shebang"])
r("rust-q8-not-shebang-four-slashes", "Q8: '////x' is an ordinary comment, so the look-ahead reaches '[': not a shebang.", b"#!////x\n[a]",
  [(P, "#"), (P, "!"), (P, "["), (I, "a"), (P, "]")], tags=["question", "shebang"])
r("rust-q8-not-shebang-empty-block", "Q8: '/**/' is an ordinary comment: not a shebang.", b"#!/**/[a]", [(P, "#"), (P, "!"), (P, "["), (I, "a"), (P, "]")], tags=["question", "shebang"])
r("rust-q8-not-shebang-three-stars", "Q8: '/***/' is an ordinary comment: not a shebang.", b"#!/***/[a]", [(P, "#"), (P, "!"), (P, "["), (I, "a"), (P, "]")], tags=["question", "shebang"])
r("rust-q8b-shebang-lookahead-nel", "Q8b: U+0085 is white space in the look-ahead: '[' follows, not a shebang.", "#!\u0085[a]".encode(), [(P, "#"), (P, "!"), (P, "["), (I, "a"), (P, "]")], tags=["question", "shebang"])
r("rust-q8b-bare-shebang", "Q8b: a bare '#!' is a shebang: zero tokens.", b"#!", [], tags=["question", "shebang"])
r("rust-q9-unassigned", "Q9: U+0378 is not XID_Continue: illegal character after 'x'. The assigned table is informative only.", "x\u0378".encode(), err=("illegal-character", 1), tags=["malformed", "question", "unicode-boundary"])
r("rust-q11-shebang-first-line-only", "Q11: the shebang covers line 1 only, even when a block comment opened on it closes later.", b"#!/*\n*/ fn",
  [(P, "*", 5), (P, "/", 6), (KW, "fn", 8)], tags=["question", "shebang"])
for vid, src, toks in [
    ("rust-s1-string-digit", b"\"x\"0", [("string", "\"x\""), ("int", "0")]),
    ("rust-s1-char-digit", b"'a'0", [("char", "'a'"), ("int", "0")]),
    ("rust-s1-bytestring-digit", b"b\"x\"0", [("bytestring", "b\"x\""), ("int", "0")]),
    ("rust-s1-rawstring-digit", b"r\"x\"0", [("rawstring", "r\"x\""), ("int", "0")]),
    ("rust-s1-cstring-digit", b"c\"x\"0", [("cstring", "c\"x\""), ("int", "0")]),
    ("rust-s1-byte-digit", b"b'a'0", [("byte", "b'a'"), ("int", "0")]),
    ("rust-s1-string-digit-expr", b"\"x\"1 + y", [("string", "\"x\""), ("int", "1"), (P, "+"), (I, "y")]),
]:
    r(vid, "S1/Q11: a digit cannot start a SUFFIX, so a literal directly followed by a digit is two tokens (rustc accepts).", src, toks, tags=["question", "literals"])
r("rust-shebang-unresolved-body", "Shebang then a body that lexes but would fail name resolution (exercises the cross-check: only the remainder is macro-wrapped).",
  b"#!/usr/bin/env x\nfn f() { y }", [(KW, "fn"), (I, "f"), (P, "("), (P, ")"), (P, "{"), (I, "y"), (P, "}")], tags=["shebang"])
r("rust-doc-comment-bracket", "A doc comment containing ']' is dropped (exercises the cross-check filter for proc-macro2's synthesized doc tokens).",
  b"/// a]\nfn f() {}", [(KW, "fn"), (I, "f"), (P, "("), (P, ")"), (P, "{"), (P, "}")], tags=["comments"])

lim = {"go": [], "rust": []}
lim["go"].append(build("go", "go-limit-exact", "Input of exactly maxInputBytes=16 bytes is accepted.", b"xy := 1 + 2 + 3\n",
  [(I, "xy"), (P, ":="), ("int", "1"), (P, "+"), ("int", "2"), (P, "+"), ("int", "3"), (P, ";", A)], tags=["limits"]))
lim["go"].append(build("go", "go-limit-over", "17 bytes with maxInputBytes=16.", b"xyz := 1 + 2 + 3\n", err=("input-too-large", 0), tags=["limits", "malformed"]))
lim["go"].append(build("go", "go-limit-precedence", "18 bytes that are also invalid UTF-8: the size check runs first.", b"x := \"\xff\" + 1 + 23\n", err=("input-too-large", 0), tags=["limits", "malformed"]))
lim["rust"].append(build("rust", "rust-limit-exact", "Input of exactly maxInputBytes=16 bytes is accepted.", b"let abc = 1 + 2;",
  [(KW, "let"), (I, "abc"), (P, "="), ("int", "1"), (P, "+"), ("int", "2"), (P, ";")], tags=["limits"]))
lim["rust"].append(build("rust", "rust-limit-over", "17 bytes with maxInputBytes=16.", b"let abcd = 1 + 2;", err=("input-too-large", 0), tags=["limits", "malformed"]))
lim["rust"].append(build("rust", "rust-limit-precedence", "17 bytes that also contain NUL: the size check runs first.", b"let a = \"\x00\" + 12;", err=("input-too-large", 0), tags=["limits", "malformed"]))
for lang, vecs in lim.items():
    cb = config_bytes(lang, 16)
    (OUT / f"config-{lang}-limit16.json").write_bytes(cb)
    dump({"contract": CONTRACT, "profile": PROFILES[lang], "profileVersion": PVER, "configFile": f"config-{lang}-limit16.json",
          "configSha256": hashlib.sha256(cb).hexdigest(), "k": K, "window": W, "requiredCoverage": False,
          "vectors": vecs}, OUT / f"limits-{lang}.json")
    print("limits", lang, len(vecs))

base = config_bytes("go").decode()
def neg(i, reason, text):
    return {"id": i, "reason": reason, "configBase64": base64.b64encode(text.encode() if isinstance(text, str) else text).decode()}
negs = [
  neg("cfg-whitespace", "insignificant whitespace added", base.replace(",", ", ", 1)),
  neg("cfg-key-order", "keys reordered", base.replace('"k":5,"window":4', '"window":4,"k":5')),
  neg("cfg-unknown-key", "unknown key", base.replace('"maxInputBytes"', '"extra":"x","maxInputBytes"')),
  neg("cfg-duplicate-key", "duplicate key", base.replace('"k":5,', '"k":5,"k":5,')),
  neg("cfg-missing-key", "required key missing", base.replace('"maxInputBytes":1048576', '').replace(',}', '}')),
  neg("cfg-no-final-lf", "missing trailing LF", base.rstrip("\n")),
  neg("cfg-crlf", "CRLF line ending", base.rstrip("\n") + "\r\n"),
  neg("cfg-channels-order", "channels reordered", base.replace('["exact","normalized"]', '["normalized","exact"]')),
  neg("cfg-channels-subset", "channel subset", base.replace('["exact","normalized"]', '["exact"]')),
  neg("cfg-unknown-profile", "unknown profile", base.replace('"go-tokens"', '"go-tokens-x"')),
  neg("cfg-unknown-profile-version", "unknown profile version", base.replace('"draft-1"', '"draft-9"')),
  neg("cfg-unknown-contract", "unknown contract", base.replace(CONTRACT, "traceweave-token-winnow-draft-0")),
  neg("cfg-unknown-hash", "unknown hash", base.replace("sha256-first8-u64be", "sha256-first4-u32be")),
  neg("cfg-k-zero", "k below 1", base.replace('"k":5', '"k":0')),
  neg("cfg-k-above-bound", "k above 16", base.replace('"k":5', '"k":17')),
  neg("cfg-window-above-bound", "window above 128", base.replace('"window":4', '"window":129')),
  neg("cfg-max-above-bound", "maxInputBytes above 8388608", base.replace('1048576', '8388609')),
  neg("cfg-k-too-large", "k above 2^32-1", base.replace('"k":5', '"k":4294967296')),
  neg("cfg-window-zero", "window below 1", base.replace('"window":4', '"window":0')),
  neg("cfg-max-zero", "maxInputBytes below 1", base.replace('1048576', '0')),
  neg("cfg-max-too-large", "maxInputBytes above 2^32-1", base.replace('1048576', '4294967296')),
  neg("cfg-leading-zero", "integer with leading zero", base.replace('"k":5', '"k":05')),
  neg("cfg-float", "non-integer number", base.replace('"k":5', '"k":5.0')),
  neg("cfg-negative", "negative integer", base.replace('"window":4', '"window":-4')),
  neg("cfg-string-number", "number as string", base.replace('"k":5', '"k":"5"')),
  neg("cfg-escape", "string escape in a value", base.replace('"go-tokens"', '"go\\u002dtokens"')),
  neg("cfg-not-json", "not JSON", "contract=traceweave\n"),
  neg("cfg-invalid-utf8", "invalid UTF-8", base.encode().replace(b"go-tokens", b"go-tok\xffns")),
]
for n in negs:
    n["expectedResult"] = {"status": "error", "error": {"code": "unsupported-config", "offset": None}}
pos = [{"id": i, "reason": r, "configBase64": base64.b64encode(t.encode()).decode()} for i, r, t in [
  ("cfg-bounds-min", "k, window and maxInputBytes at their lower bound 1", base.replace('"k":5', '"k":1').replace('"window":4', '"window":1').replace('1048576', '1')),
  ("cfg-bounds-max", "k, window and maxInputBytes at their upper bounds 16, 128, 8388608", base.replace('"k":5', '"k":16').replace('"window":4', '"window":128').replace('1048576', '8388608')),
  ("cfg-rust-bounds-max", "Rust profile at the upper bounds", config_bytes("rust").decode().replace('"k":5', '"k":16').replace('"window":4', '"window":128').replace('1048576', '8388608')),
]]
dump({"contract": CONTRACT, "description": "negatives: configuration byte strings that MUST be rejected as unsupported-config (offset null); each is the shipped Go configuration with one change. boundaryPositives: configurations at the section 10 bounds that MUST be accepted.", "negatives": negs, "boundaryPositives": pos}, OUT / "config-negative.json")
print("negatives", len(negs), "positives", len(pos))

for lang, vecs in (("go", go), ("rust", rs)):
    cb = config_bytes(lang)
    (OUT / f"config-{lang}.json").write_bytes(cb)
    dump({"contract": CONTRACT, "profile": PROFILES[lang], "profileVersion": PVER, "configFile": f"config-{lang}.json",
          "configSha256": hashlib.sha256(cb).hexdigest(), "k": K, "window": W, "requiredCoverage": True,
          "lexingCheck": "Token streams are hand-derived; check_vectors.py re-verifies lexical invariants and harness/crosscheck.py compares them with go/scanner, proc-macro2 and rustc.",
          "vectors": vecs}, OUT / f"{lang}.json")
    print(lang, len(vecs))
