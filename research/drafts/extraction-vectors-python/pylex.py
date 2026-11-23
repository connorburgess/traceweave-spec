"""Reference lexer for the draft py-tokens profile (draft-1).

Written from the profile text (research/drafts/extraction-profile-python.md
§3-§7) for the checker. It is NOT how the vectors were made: their token
streams are hand-written in harness/vector_sources.py and only hashed by
harness/build_vectors.py. check_vectors.py compares the two derivations, and
also checks the recorded streams against rules that do not use this module.

Every rule choice that a plausible wrong implementation could make differently
is a method of Lexer, so check_vectors.py can substitute a wrong variant and
require that some shipped vector rejects it.

Standard library only. Identifier classes come from the shared pinned table
(test-vectors/extraction/unicode-17.0.0-tables.json, read only).

lex(text) works on a Python str (code points) and returns
  ("ok", [(class, start, end), ...])   or   ("error", code, offset)
with offsets in code points; the checker converts them to UTF-8 byte offsets.
The shared pre-lexing checks (size, UTF-8, BOM, NUL) are the checker's job.
"""
import bisect
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TABLES_FILE = ROOT / "test-vectors" / "extraction" / "unicode-17.0.0-tables.json"
TABLES_SHA256 = "9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f"

PROFILES = ("py-tokens",)

# §5.2: the 35 keywords of the Python 3.14 reference ("Keywords"); soft keywords are not here.
KEYWORDS = frozenset(
    "False None True and as assert async await break class continue def del elif else except finally for "
    "from global if import in is lambda nonlocal not or pass raise return try while with yield".split())
SOFT_KEYWORDS = frozenset("match case type _".split())
assert len(KEYWORDS) == 35

# §5.6: the reference "Operators and delimiters" grammar, longest match.
PUNCTUATORS = sorted(
    "+= -= *= **= /= //= %= &= |= ^= <<= >>= @= := & | ^ ~ << >> <= >= < > == != ( ) [ ] { } "
    ", : ! ; = -> + - ** * // / % ... . @".split(), key=len, reverse=True)
assert len(PUNCTUATORS) == 48

LAYOUT_CLASSES = ("newline", "indent", "dedent")
CLASSES = ("keyword", "ident", "punct", "int", "float", "imag", "string", "bytes",
           "fstring-start", "fstring-middle", "fstring-end", "tstring-start", "tstring-middle", "tstring-end",
           ) + LAYOUT_CLASSES
LITERAL_CLASSES = frozenset(["int", "float", "imag", "string", "bytes", "fstring-start", "fstring-middle",
                             "fstring-end", "tstring-start", "tstring-middle", "tstring-end"])
ERROR_CODES = ("invalid-utf8", "bom", "nul", "input-too-large", "illegal-character", "unterminated-literal",
               "malformed-literal", "unbalanced-delimiter", "inconsistent-indentation", "unmatched-dedent")

# §5.4: a numeric literal may be directly followed by an ASCII name character only where CPython
# 3.14 verify_end_of_number gives a SyntaxWarning instead of an error: one of the whole words
# and/else/for/not/or (the next character is not a name character, ASCII or non-ASCII), or the
# two letters if/in/is whatever follows them.
NUMBER_FOLLOW_WORDS = ("and", "else", "for", "not", "or")
NUMBER_FOLLOW_PREFIXES = ("if", "in", "is")

# §5.3: valid prefix letter sets (case-insensitive, each letter at most once).
VALID_PREFIXES = {frozenset(x) for x in ("b", "r", "u", "f", "t", "br", "fr", "tr")}
PREFIX_LETTERS = frozenset("brfut")

_DIG = r"[0-9](?:_?[0-9])*"
_EXP = r"[eE][+-]?" + _DIG
_FLOAT = rf"(?:{_DIG}\.(?:{_DIG})?(?:{_EXP})?|\.{_DIG}(?:{_EXP})?|{_DIG}{_EXP})"
NUMBER_FORMS = [
    ("int", re.compile(r"[1-9](?:_?[0-9])*")),
    ("int", re.compile(r"0(?:_?0)*")),
    ("int", re.compile(r"0[bB](?:_?[01])+")),
    ("int", re.compile(r"0[oO](?:_?[0-7])+")),
    ("int", re.compile(r"0[xX](?:_?[0-9a-fA-F])+")),
    ("float", re.compile(_FLOAT)),
    ("imag", re.compile(rf"(?:{_FLOAT}|{_DIG})[jJ]")),
]


class Tables:
    def __init__(self, path=TABLES_FILE):
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != TABLES_SHA256:
            raise SystemExit(f"{path}: SHA-256 differs from the pinned value")
        data = json.loads(raw)
        assert data["unicodeVersion"] == "17.0.0"
        self.sets = {}
        for name in ("xid_start", "xid_continue"):
            r = data["properties"][name]
            self.sets[name] = ([a for a, _ in r], [b for _, b in r])

    def has(self, name, cp):
        starts, ends = self.sets[name]
        i = bisect.bisect_right(starts, cp) - 1
        return i >= 0 and cp <= ends[i]


T = Tables()


class LexError(Exception):
    def __init__(self, code, offset):
        super().__init__(f"{code}@{offset}")
        self.code, self.offset = code, offset


def number_class_and_length(s, i):
    """Longest match of the reference NUMBER grammar at i: (class, length) or (None, 0)."""
    best = (None, 0)
    for cls, rx in NUMBER_FORMS:
        m = rx.match(s, i)
        if m and m.end() - i > best[1]:
            best = (cls, m.end() - i)
    return best


class Lexer:
    # ------------------------------------------------------------ policy (rule choices)
    def tab_stop(self, col):
        """§4.4: a tab advances to the next multiple of 8."""
        return (col // 8 + 1) * 8

    def formfeed_in_indent(self, col, alt):
        """§4.4: a form feed in leading white space resets both counts to zero."""
        return 0, 0

    def line_terminator_len(self, i):
        """§4.1: LF, CR LF and a lone CR each end a physical line."""
        s = self.s
        if i >= self.n:
            return 0
        if s[i] == "\n":
            return 1
        if s[i] == "\r":
            return 2 if i + 1 < self.n and s[i + 1] == "\n" else 1
        return 0

    def blank_line_starts(self, j):
        """§4.3: a line holding only white space and possibly a comment is blank."""
        return j >= self.n or self.s[j] == "#" or self.line_terminator_len(j) > 0

    def joins_implicitly(self):
        """§4.2: an open bracket or replacement field suppresses NEWLINE and indentation."""
        return bool(self.stack)

    def recognizes_ftstrings(self):
        return True

    def keyword_set(self):
        return KEYWORDS

    def backslash_escapes_in_raw(self):
        """§5.3: in raw and non-raw strings alike, '\\' takes the next character into the literal."""
        return True

    def continuation_indent(self, cont, col, alt):
        """§4.4: the white space up to the first backslash determines the indentation."""
        return cont if cont is not None else (col, alt)

    def spec_brace_escapes(self):
        """§6.4: no '{{' / '}}' escapes inside a format spec."""
        return False

    def number_follow_ok(self, s, k, i):
        """§5.4: what may follow a numeric literal."""
        if k == i + 1 and s[i] == "0" and k < self.n and s[k] in "bBoOxX":
            return False  # a radix prefix with no digit of its base
        c = s[k] if k < self.n else ""
        if not (c.isascii() and (c.isalnum() or c == "_")):
            return True
        if any(s.startswith(w, k) for w in NUMBER_FOLLOW_PREFIXES):
            return True
        for w in NUMBER_FOLLOW_WORDS:
            if s.startswith(w, k):
                e = k + len(w)
                return e >= self.n or not (ord(s[e]) >= 128 or s[e].isascii() and (s[e].isalnum() or s[e] == "_"))
        return False

    def number_at(self, s, i):
        return number_class_and_length(s, i)

    def check_tab_consistency(self):
        return True

    def dedents_at_eof(self):
        return True

    def layout_position(self, line_start, first):
        """§4.5: INDENT and DEDENT are zero-width at the first byte of the line's first token."""
        return first

    def newline_position(self, terminator, last_end):
        """§4.5: NEWLINE is zero-width at the first byte of the line terminator."""
        return terminator

    def name_start(self, c):
        o = ord(c)
        if o < 128:
            return c.isalpha() or c == "_"
        return T.has("xid_start", o)

    def name_continue(self, c):
        o = ord(c)
        if o < 128:
            return c.isalnum() or c == "_"
        return T.has("xid_continue", o)

    def prefix_kind(self, word):
        """§5.3: None if `word` is not a prefix; 'bad' if incompatible; else the lowercase letter set."""
        low = word.lower()
        if not word.isascii() or not low or any(ch not in PREFIX_LETTERS for ch in low) \
                or len(set(low)) != len(low):
            return None
        return frozenset(low) if frozenset(low) in VALID_PREFIXES else "bad"

    def named_escape_applies(self, raw):
        """§6.3: '\\N{' starts a named escape in non-raw f/t-strings only."""
        return not raw

    def colon_starts_spec_first(self):
        """§6.2: at the field's own level ':' starts the format spec before longest match (':=')."""
        return True

    def whitespace(self, c):
        return c in " \t\f"

    def dedent_checks_alt(self):
        """§4.4: after popping, the tab-size-1 width must equal the new top's too."""
        return True

    def spec_closing_quote_is_error(self):
        """§6.2: the enclosing f-string's closing delimiter inside a format spec is an error."""
        return True

    def brace_in_named_escape_opens_field(self):
        """§6.3: inside '\\N{...}', '{' still opens a field (and ends the named escape)."""
        return True

    def eof_in_field_offset(self, field):
        """§6.4: end of input with a field innermost is reported at the f/t-string start."""
        return field["fstr"]["start"]

    # ------------------------------------------------------------ machinery
    def __init__(self, text):
        self.s = text
        self.n = len(text)
        self.toks = []
        self.ind = [(0, 0)]
        self.stack = []
        self.line_has_tokens = False
        self.last_end = 0

    def emit(self, cls, a, b):
        self.toks.append((cls, a, b))
        if cls != "newline":
            self.line_has_tokens = True
        if cls not in LAYOUT_CLASSES:
            self.last_end = b

    def run(self):
        s, n = self.s, self.n
        i = 0
        at_bol = True
        while True:
            top = self.stack[-1] if self.stack else None
            if top is not None and (top["kind"] == "fstr" or (top["kind"] == "field" and top["spec"])):
                i = self.scan_ft_text(i)
                continue
            if at_bol and not self.joins_implicitly():
                i = self.line_start(i)
                at_bol = False
            if i >= n:
                break
            c = s[i]
            if self.whitespace(c):
                i += 1
                continue
            if c == "#":
                while i < n and not self.line_terminator_len(i):
                    i += 1
                continue
            lt = self.line_terminator_len(i)
            if lt:
                if not self.joins_implicitly():
                    if self.line_has_tokens:
                        self.emit("newline", *[self.newline_position(i, self.last_end)] * 2)
                        self.line_has_tokens = False
                    at_bol = True
                i += lt
                continue
            if c == "\\":
                i = self.continuation(i)
                continue
            if self.name_start(c):
                i = self.name_or_prefixed(i)
                continue
            if c.isascii() and c.isdigit() or (c == "." and i + 1 < n and s[i + 1].isascii() and s[i + 1].isdigit()):
                i = self.number(i)
                continue
            if c in "'\"":
                i = self.string(i, i, frozenset())
                continue
            i = self.operator(i)
        # end of input
        if self.stack:
            top = self.stack[-1]
            if top["kind"] in ("field", "fstr"):
                raise LexError("unterminated-literal",
                               self.eof_in_field_offset(top) if top["kind"] == "field" else top["start"])
            raise LexError("unbalanced-delimiter", top["pos"])
        if self.line_has_tokens:
            self.emit("newline", n, n)
        if self.dedents_at_eof():
            while len(self.ind) > 1:
                self.ind.pop()
                self.emit("dedent", n, n)
        return self.toks

    def continuation(self, i):
        """§4.2: '\\' must be followed by a line terminator that is not the end of input."""
        lt = self.line_terminator_len(i + 1)
        if lt == 0 or i + 1 + lt >= self.n:
            raise LexError("illegal-character", i)
        return i + 1 + lt

    def line_start(self, i):
        """§4.4: measure indentation at the start of a logical line and emit INDENT/DEDENT."""
        s, n = self.s, self.n
        col = alt = 0
        cont = None
        j = i
        while j < n:
            c = s[j]
            if c == " ":
                col, alt = col + 1, alt + 1
            elif c == "\t":
                col, alt = self.tab_stop(col), alt + 1
            elif c == "\f":
                col, alt = self.formfeed_in_indent(col, alt)
            elif c == "\\":
                if cont is None:
                    cont = (col, alt)
                j = self.continuation(j)
                continue
            else:
                break
            j += 1
        if self.blank_line_starts(j):
            return j
        col, alt = self.continuation_indent(cont, col, alt)
        pos = self.layout_position(i, j)
        top_col, top_alt = self.ind[-1]
        tabs = self.check_tab_consistency()
        if col == top_col:
            if tabs and alt != top_alt:
                raise LexError("inconsistent-indentation", j)
        elif col > top_col:
            if tabs and alt <= top_alt:
                raise LexError("inconsistent-indentation", j)
            self.ind.append((col, alt))
            self.emit("indent", pos, pos)
        else:
            pops = 0
            while len(self.ind) > 1 and col < self.ind[-1][0]:
                self.ind.pop()
                pops += 1
            if col != self.ind[-1][0]:
                raise LexError("unmatched-dedent", j)
            if tabs and self.dedent_checks_alt() and alt != self.ind[-1][1]:
                raise LexError("inconsistent-indentation", j)
            for _ in range(pops):
                self.emit("dedent", pos, pos)
        return j

    def name_or_prefixed(self, i):
        s, n = self.s, self.n
        j = i + 1
        while j < n and self.name_continue(s[j]):
            j += 1
        word = s[i:j]
        if j < n and s[j] in "'\"":
            kind = self.prefix_kind(word)
            if kind == "bad":
                raise LexError("malformed-literal", i)
            if kind is not None:
                return self.string(i, j, kind)
        self.emit("keyword" if word in self.keyword_set() else "ident", i, j)
        return j

    def number(self, i):
        cls, length = self.number_at(self.s, i)
        k = i + length
        if not self.number_follow_ok(self.s, k, i):
            raise LexError("malformed-literal", i)
        self.emit(cls, i, k)
        return k

    def string(self, p, q, prefix):
        """A string or bytes literal, or the start of an f/t-string. p: prefix start, q: the quote."""
        s, n = self.s, self.n
        quote = s[q]
        triple = s.startswith(quote * 3, q)
        body = q + (3 if triple else 1)
        if ("f" in prefix or "t" in prefix) and self.recognizes_ftstrings():
            kind = "tstring" if "t" in prefix else "fstring"
            self.emit(kind + "-start", p, body)
            self.stack.append({"kind": "fstr", "start": p, "quote": quote, "triple": triple,
                               "raw": "r" in prefix, "cls": kind, "pos": p})
            return body
        raw = "r" in prefix
        j = body
        while True:
            if j >= n:
                raise LexError("unterminated-literal", p)
            c = s[j]
            if c == "\\" and (not raw or self.backslash_escapes_in_raw()):
                j += 1
                if j < n:
                    j += self.line_terminator_len(j) or 1
                continue
            if not triple and self.line_terminator_len(j):
                raise LexError("unterminated-literal", p)
            if c == quote and (not triple or s.startswith(quote * 3, j)):
                end = j + (3 if triple else 1)
                break
            j += 1
        self.emit("bytes" if "b" in prefix else "string", p, end)
        return end

    def scan_ft_text(self, i):
        """Literal part (top is the f/t-string) or format spec (top is a field in spec mode)."""
        s, n = self.s, self.n
        top = self.stack[-1]
        fs = top if top["kind"] == "fstr" else top["fstr"]
        spec = top["kind"] == "field"
        cls = fs["cls"]
        closing = fs["quote"] * (3 if fs["triple"] else 1)
        start = j = i
        named = False

        def flush(end):
            if end > start:
                self.emit(cls + "-middle", start, end)

        while True:
            if j >= n:
                raise LexError("unterminated-literal", fs["start"])
            c = s[j]
            if not fs["triple"] and self.line_terminator_len(j):
                raise LexError("unterminated-literal", fs["start"])
            if s.startswith(closing, j):
                if spec and self.spec_closing_quote_is_error():
                    raise LexError("unterminated-literal", fs["start"])
                flush(j)
                self.emit(cls + "-end", j, j + len(closing))
                while self.stack.pop() is not fs:  # only a wrong variant reaches this with fields open
                    pass
                return j + len(closing)
            if c == "\\":
                k = j + 1
                if k >= n:
                    j = k
                    continue
                lt = self.line_terminator_len(k)
                if lt:
                    j = k + lt
                    continue
                if s[k] in "{}":
                    j = k
                    continue
                if s[k] == "N" and self.named_escape_applies(fs["raw"]) and k + 1 < n and s[k + 1] == "{":
                    named = True
                    j = k + 2
                    continue
                j = k + 1
                continue
            if c == "{" and named and not self.brace_in_named_escape_opens_field():
                j += 1
                continue
            if c == "{":
                if s.startswith("{{", j) and (not spec or self.spec_brace_escapes()):
                    j += 2
                    continue
                flush(j)
                self.emit("punct", j, j + 1)
                self.stack.append({"kind": "field", "pos": j, "fstr": fs, "spec": False})
                return j + 1
            if c == "}":
                if named:
                    named = False
                    j += 1
                    continue
                if spec and not (self.spec_brace_escapes() and s.startswith("}}", j)):
                    flush(j)
                    self.emit("punct", j, j + 1)
                    self.stack.pop()
                    return j + 1
                if s.startswith("}}", j):
                    j += 2
                    continue
                raise LexError("malformed-literal", fs["start"])
            j += 1

    def operator(self, i):
        s = self.s
        c = s[i]
        top = self.stack[-1] if self.stack else None
        in_field = top is not None and top["kind"] == "field"
        if in_field and c == ":" and self.colon_starts_spec_first():
            self.emit("punct", i, i + 1)
            top["spec"] = True
            return i + 1
        if c in "([{":
            self.emit("punct", i, i + 1)
            self.stack.append({"kind": c, "pos": i})
            return i + 1
        if c in ")]}":
            if in_field and c == "}":
                self.emit("punct", i, i + 1)
                self.stack.pop()
                return i + 1
            want = {")": "(", "]": "[", "}": "{"}[c]
            if top is None or top["kind"] != want:
                raise LexError("unbalanced-delimiter", i)
            self.stack.pop()
            self.emit("punct", i, i + 1)
            return i + 1
        for p in PUNCTUATORS:
            if s.startswith(p, i):
                self.emit("punct", i, i + len(p))
                if in_field and p == ":":
                    top["spec"] = True
                return i + len(p)
        raise LexError("illegal-character", i)


def lex(text, profile="py-tokens", lexer=Lexer):
    assert profile in PROFILES
    lx = lexer(text)
    try:
        return ("ok", lx.run())
    except LexError as e:
        return ("error", e.code, e.offset)
