"""Reference lexer for the draft ts-tokens / tsx-tokens profiles (draft-2).

Written from the profile text (profiles/typescript.md §3-§6) for the
checker. It is NOT how the vectors were made: their token streams are
hand-written in harness/vector_sources.py and only hashed by
harness/build_vectors.py. check_vectors.py compares the two derivations.

Standard library only. Unicode data comes from the shared pinned table
(../extraction/unicode-17.0.0-tables.json, read only) plus the two
explicit deltas below, which harness/derive_deltas.py re-derives from the
digest-pinned UCD 17.0.0 DerivedCoreProperties.txt.
"""
import bisect
import hashlib
import json
from pathlib import Path

TABLES_FILE = Path(__file__).resolve().parent.parent / "extraction" / "unicode-17.0.0-tables.json"
TABLES_SHA256 = "9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f"

# ID_Start minus XID_Start, and ID_Continue minus XID_Continue, Unicode 17.0.0 (profile §3.2).
ID_START_EXTRA = frozenset([0x037A, 0x0E33, 0x0EB3, 0x309B, 0x309C, 0xFC5E, 0xFC5F, 0xFC60, 0xFC61,
                            0xFC62, 0xFC63, 0xFDFA, 0xFDFB, 0xFE70, 0xFE72, 0xFE74, 0xFE76, 0xFE78,
                            0xFE7A, 0xFE7C, 0xFE7E, 0xFF9E, 0xFF9F])
ID_CONTINUE_EXTRA = frozenset([0x037A, 0x309B, 0x309C, 0xFC5E, 0xFC5F, 0xFC60, 0xFC61, 0xFC62, 0xFC63,
                               0xFDFA, 0xFDFB, 0xFE70, 0xFE72, 0xFE74, 0xFE76, 0xFE78, 0xFE7A, 0xFE7C,
                               0xFE7E])
# General_Category Zs, Unicode 17.0.0 (profile §3.1).
ZS = frozenset([0x0020, 0x00A0, 0x1680] + list(range(0x2000, 0x200B)) + [0x202F, 0x205F, 0x3000])
WHITESPACE = frozenset(chr(c) for c in ZS | {0x0009, 0x000B, 0x000C, 0xFEFF})
LINE_TERMINATORS = frozenset("\n\r  ")
TRIVIA_CHARS = WHITESPACE | LINE_TERMINATORS

# §4.1: ECMAScript ReservedWord (38) plus the 8 strict-mode reserved words.
RESERVED_WORDS = frozenset(
    "await break case catch class const continue debugger default delete do else enum export extends "
    "false finally for function if import in instanceof new null return super switch this throw true "
    "try typeof var void while with yield".split())
STRICT_RESERVED = frozenset("implements interface let package private protected public static".split())
KEYWORDS = RESERVED_WORDS | STRICT_RESERVED
assert len(RESERVED_WORDS) == 38 and len(KEYWORDS) == 46
EXPR_END_KEYWORDS = frozenset("this super null true false".split())
HEADER_KEYWORDS = frozenset("if while for with".split())

# §4.4 punctuators (normal mode), longest match. '/' and '/=' only in division position;
# '{' '}' '(' ')' '[' ']' are handled with the delimiter stack.
PUNCTUATORS = sorted(
    "{ } ( ) [ ] . ... ; , < > <= >= == != === !== + - * % ** ++ -- << >> >>> & | ^ ! ~ && || ?? ? ?. : "
    "= += -= *= %= **= <<= >>= >>>= &= |= ^= &&= ||= ??= => / /= @".split(),
    key=len, reverse=True)

CLASSES = ("keyword", "ident", "privatename", "punct", "number", "bigint", "string", "template",
           "template-head", "template-middle", "template-tail", "regex", "jsx-text", "jsx-string")
LITERAL_CLASSES = frozenset(CLASSES[4:]) | {"privatename"}
ERROR_CODES = ("invalid-utf8", "bom", "nul", "input-too-large", "illegal-character", "unterminated-comment",
               "unterminated-literal", "malformed-literal", "malformed-identifier", "unbalanced-delimiter")
EXPR_END_CLASSES = frozenset(["ident", "privatename", "number", "bigint", "string", "template", "template-tail",
                              "regex"])
PROFILES = {"ts-tokens": False, "tsx-tokens": True}  # value: JSX recognized


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


def id_start(cp):
    return T.has("xid_start", cp) or cp in ID_START_EXTRA


def id_continue(cp):
    return T.has("xid_continue", cp) or cp in ID_CONTINUE_EXTRA


def ident_start_char(cp):  # IdentifierStartChar
    return cp in (0x24, 0x5F) or id_start(cp)


def ident_part_char(cp):  # IdentifierPartChar (ES2026: UnicodeIDContinue | $; ZWNJ/ZWJ are ID_Continue in 17.0)
    return cp == 0x24 or id_continue(cp)


HEX = frozenset("0123456789abcdefABCDEF")
DEC = frozenset("0123456789")


class LexError(Exception):
    def __init__(self, code, index):
        super().__init__(code)
        self.code, self.index = code, index


class Lexer:
    """The profile's lexer. The small policy methods below are the rule choices the
    review found unpinned; check_vectors.py overrides them to build wrong lexers."""

    def __init__(self, text, jsx):
        self.s, self.n, self.jsx = text, len(text), jsx
        self.toks = []          # (class, start_index, end_index)
        self.stack = []         # dicts with key 'k' in ( [ { ${ jbrace tag elem
        self.expr_end = False
        self.nl_before = False  # a line terminator lies between the previous token and this one

    # ------------------------------------------------------------ policies (§4.9, §5)
    def line_breaks(self):
        """Characters that count as a line terminator before '!', '++', '--' (§3.1, §4.9)."""
        return LINE_TERMINATORS

    def keyword_expr_end(self, word):
        return word in EXPR_END_KEYWORDS

    def closer_expr_end(self, entry, c):
        """exprEnd after a matching ')', ']' or '}' (§4.9)."""
        return not entry.get("header", False) and not entry.get("arrow", False)

    def prefix_like_expr_end(self, p):
        """exprEnd after '!', '++', '--': unchanged unless a line terminator precedes it (§4.9)."""
        return False if self.nl_before else self.expr_end

    def element_end_expr_end(self):
        return True

    def jsx_trim(self, ch):
        return ch in TRIVIA_CHARS

    def attr_element_ok(self, prev):
        return prev == "="

    def string_breaks(self):
        return ("\n", "\r")

    def zero_separator_ok(self):
        return False

    def lookahead_escapes_ok(self):
        return False

    def lookahead_comment_after_extends(self):
        return False  # unterminated comment anywhere in the look-ahead: JSX (§5.2)

    def nonoctal_fraction_separators_ok(self):
        return True

    # ------------------------------------------------------------ helpers
    def at(self, i):
        return self.s[i] if i < self.n else ""

    def emit(self, cls, a, b):
        self.toks.append((cls, a, b))

    def last_text(self):
        if not self.toks:
            return None
        c, a, b = self.toks[-1]
        return self.s[a:b]

    def skip_trivia(self, i, errors=True):
        """Skip white space, line terminators and comments. Returns new index, or -1 for an
        unterminated comment when errors is False."""
        s = self.s
        while i < self.n:
            c = s[i]
            if c in TRIVIA_CHARS:
                i += 1
            elif c == "/" and self.at(i + 1) == "/":
                i += 2
                while i < self.n and s[i] not in LINE_TERMINATORS:
                    i += 1
            elif c == "/" and self.at(i + 1) == "*":
                j = s.find("*/", i + 2)
                if j < 0:
                    if errors:
                        raise LexError("unterminated-comment", i)
                    return -1
                i = j + 2
            else:
                break
        return i

    def u_escape(self, j):
        """At s[j] == '\\'. Returns (code point, end) or None."""
        s = self.s
        if self.at(j + 1) != "u":
            return None
        if self.at(j + 2) == "{":
            k = j + 3
            while k < self.n and s[k] in HEX:
                k += 1
            if k == j + 3 or self.at(k) != "}":
                return None
            v = int(s[j + 3:k], 16)
            if v > 0x10FFFF:
                return None
            return v, k + 1
        h = s[j + 2:j + 6]
        if len(h) == 4 and all(c in HEX for c in h):
            return int(h, 16), j + 6
        return None

    def ident_name(self, i):
        """IdentifierName at i. Returns (end, has_escape) or None if no identifier starts at i.
        Raises malformed-identifier at i for a bad escape."""
        s, j, first, esc = self.s, i, True, False
        while j < self.n:
            c = s[j]
            if c == "\\":
                r = self.u_escape(j)
                if r is None or not (ident_start_char(r[0]) if first else ident_part_char(r[0])):
                    raise LexError("malformed-identifier", i)
                esc, j = True, r[1]
            elif (ident_start_char if first else ident_part_char)(ord(c)):
                j += 1
            else:
                break
            first = False
        return None if j == i else (j, esc)

    def starts_ident(self, i):
        c = self.at(i)
        return c == "\\" or (c != "" and ident_start_char(ord(c)))

    # ------------------------------------------------------------ main loop
    def run(self):
        s = self.s
        i = 0
        if s.startswith("#!"):
            i = 2
            while i < self.n and s[i] not in LINE_TERMINATORS:
                i += 1
        while True:
            top = self.stack[-1]["k"] if self.stack else None
            if top != "elem":
                j = self.skip_trivia(i)
                self.nl_before = any(ch in self.line_breaks() for ch in s[i:j])
                i = j
            if i >= self.n:
                break
            if top == "elem":
                i = self.children(i)
            elif top == "tag":
                i = self.tag(i)
            else:
                i = self.normal(i)
        if self.stack:
            t = self.stack[-1]
            if t["k"] == "${":
                raise LexError("unterminated-literal", t["tok"])
            raise LexError("unbalanced-delimiter", t["at"])
        return self.toks

    # ------------------------------------------------------------ normal mode
    def normal(self, i):
        s, c = self.s, self.s[i]
        prev = self.last_text()
        if c == "\\" and self.at(i + 1) != "u":
            raise LexError("illegal-character", i)
        if self.starts_ident(i):
            r = self.ident_name(i)
            if r is None:
                raise LexError("malformed-identifier", i)
            j, esc = r
            word = s[i:j]
            after_dot = prev in (".", "?.") and self.toks[-1][0] == "punct"
            if not esc and word in KEYWORDS and not after_dot:
                self.emit("keyword", i, j)
                self.expr_end = self.keyword_expr_end(word)
            else:
                self.emit("ident", i, j)
                self.expr_end = True
            return j
        if c in DEC or (c == "." and self.at(i + 1) in DEC and self.at(i + 1) != ""):
            return self.number(i)
        if c in "\"'":
            return self.string(i)
        if c == "`":
            return self.template(i, i + 1, True)
        if c == "#":
            if self.starts_ident(i + 1):
                try:
                    r = self.ident_name(i + 1)
                except LexError:
                    raise LexError("malformed-identifier", i)
                if r is None:
                    raise LexError("malformed-identifier", i)
                self.emit("privatename", i, r[0])
                self.expr_end = True
                return r[0]
            raise LexError("illegal-character", i)
        if c == "/" and not self.expr_end:
            return self.regex(i)
        if c == "<" and self.jsx and not self.expr_end and not self.generic_arrow(i):
            self.emit("punct", i, i + 1)
            self.stack.append({"k": "tag", "at": i, "closing": False, "started": False, "slash": False})
            return i + 1
        if c in "([{":
            hdr = bool(c == "(" and self.toks and self.toks[-1][0] == "keyword" and prev in HEADER_KEYWORDS)
            arrow = bool(c == "{" and self.toks and self.toks[-1][0] == "punct" and prev == "=>")
            self.emit("punct", i, i + 1)
            self.stack.append({"k": c, "at": i, "header": hdr, "arrow": arrow})
            self.expr_end = False
            return i + 1
        if c in ")]}":
            want = {")": "(", "]": "[", "}": "{"}[c]
            t = self.stack[-1] if self.stack else None
            if c == "}" and t is not None and t["k"] == "${":
                self.stack.pop()
                return self.template(i, i + 1, False)
            if c == "}" and t is not None and t["k"] == "jbrace":
                self.stack.pop()
                self.emit("punct", i, i + 1)
                return i + 1
            if t is None or t["k"] != want:
                raise LexError("unbalanced-delimiter", i)
            self.stack.pop()
            self.emit("punct", i, i + 1)
            self.expr_end = self.closer_expr_end(t, c)
            return i + 1
        for p in PUNCTUATORS:
            if s.startswith(p, i):
                if p == "?." and self.at(i + 2) in DEC and self.at(i + 2) != "":
                    continue
                if p in "{}()[]":
                    continue
                self.emit("punct", i, i + len(p))
                if p in ("!", "++", "--"):
                    self.expr_end = self.prefix_like_expr_end(p)
                else:
                    self.expr_end = False
                return i + len(p)
        raise LexError("illegal-character", i)

    def generic_arrow(self, i):
        """§5.2 look-ahead at a JSX-position '<' in tsx-tokens. True: generic arrow, not JSX."""
        def name(j):
            # An escape-free IdentifierName at j, or None. A '\\' where a name is expected,
            # or an escape inside it, makes the '<' JSX (§5.2 rule 1).
            if j < 0 or not self.starts_ident(j):
                return None
            try:
                r = self.ident_name(j)
            except LexError:
                return None
            if r is None or (r[1] and not self.lookahead_escapes_ok()):
                return None
            return r[0]

        j = self.skip_trivia(i + 1, errors=False)
        e = name(j)
        if e is None:
            return False
        w1 = self.s[j:e]
        if w1 == "const":
            j = self.skip_trivia(e, errors=False)
            e = name(j)
            if e is None:
                return False
        elif w1 in RESERVED_WORDS:
            return False
        j = self.skip_trivia(e, errors=False)
        if j < 0:
            return False
        c = self.at(j)
        if c == ",":
            return True
        if c == "=" and self.at(j + 1) not in ("=", ">"):
            return True
        e = name(j)
        if e is not None and self.s[j:e] == "extends":
            k = self.skip_trivia(e, errors=False)
            if k < 0:
                return self.lookahead_comment_after_extends()
            c4 = self.at(k)
            if c4 == "=" and self.at(k + 1) not in ("=", ">"):
                return False
            if c4 == ">":
                return False
            if c4 == "/" and self.at(k + 1) != "=":
                return False
            return True
        return False

    # ------------------------------------------------------------ literals
    def number(self, i):
        s = self.s

        def digits(j, ok, sep=True):
            """Maximal run of digit-or-underscore at j; None if separators are misplaced."""
            k = j
            while k < self.n and (s[k] in ok or (sep and s[k] == "_")):
                k += 1
            run = s[j:k]
            if run and (run[0] == "_" or run[-1] == "_" or "__" in run):
                return None, k
            return run, k

        cls = "number"
        c = s[i]
        if c == "0" and self.at(i + 1) in ("x", "X", "b", "B", "o", "O") and self.at(i + 1) != "":
            radix = {"x": HEX, "b": frozenset("01"), "o": frozenset("01234567")}[s[i + 1].lower()]
            j = i + 2
            while j < self.n and (ident_part_char(ord(s[j]))):
                j += 1
            body = s[i + 2:j]
            if body.endswith("n"):
                body, cls = body[:-1], "bigint"
            if not body or body[0] == "_" or body[-1] == "_" or "__" in body or any(
                    ch not in radix and ch != "_" for ch in body):
                raise LexError("malformed-literal", i)
            end = j
        elif c == "0" and self.at(i + 1) in DEC and self.at(i + 1) != "":
            j = i + 1
            while j < self.n and s[j] in DEC:
                j += 1
            if all(ch in "01234567" for ch in s[i:j]):
                end = j  # LegacyOctalIntegerLiteral: no fraction, exponent or suffix
            else:
                end = self.fraction_exponent(i, j, nonoctal=True)
        elif c == ".":
            run, j = digits(i + 1, DEC)
            if run is None:
                raise LexError("malformed-literal", i)
            end = self.exponent(i, j)
        else:
            if c == "0" and not (self.zero_separator_ok() and self.at(i + 1) == "_"):
                j = i + 1
            else:
                run, j = digits(i, DEC)
                if run is None:
                    raise LexError("malformed-literal", i)
            if self.at(j) == "n":
                end, cls = j + 1, "bigint"
            else:
                end = self.fraction_exponent(i, j)
        nxt = self.at(end)
        if nxt and (nxt == "\\" or nxt in DEC or ident_start_char(ord(nxt))):
            raise LexError("malformed-literal", i)
        self.emit(cls, i, end)
        self.expr_end = True
        return end

    def fraction_exponent(self, i, j, nonoctal=False):
        s = self.s
        sep = not nonoctal or self.nonoctal_fraction_separators_ok()
        if self.at(j) == ".":
            k = j + 1
            while k < self.n and (s[k] in DEC or (sep and s[k] == "_")):
                k += 1
            run = s[j + 1:k]
            if run and (run[0] == "_" or run[-1] == "_" or "__" in run):
                raise LexError("malformed-literal", i)
            j = k
        return self.exponent(i, j, sep)

    def exponent(self, i, j, sep=True):
        s = self.s
        if self.at(j) in ("e", "E") and self.at(j) != "":
            k = j + 1
            if self.at(k) in ("+", "-") and self.at(k) != "":
                k += 1
            m = k
            while m < self.n and (s[m] in DEC or (sep and s[m] == "_")):
                m += 1
            run = s[k:m]
            if not run or run[0] == "_" or run[-1] == "_" or "__" in run:
                raise LexError("malformed-literal", i)
            return m
        return j

    def string(self, i):
        s, q, j = self.s, self.s[i], i + 1
        while True:
            if j >= self.n:
                raise LexError("unterminated-literal", i)
            c = s[j]
            if c == q:
                break
            if c in self.string_breaks():
                raise LexError("unterminated-literal", i)
            if c == "\\":
                if j + 1 >= self.n:
                    raise LexError("unterminated-literal", i)
                j += 3 if s[j + 1] == "\r" and self.at(j + 2) == "\n" else 2
                continue
            j += 1
        end = j + 1
        k = i + 1
        while k < j:  # escape validation (§4.6)
            if s[k] == "\\":
                e = s[k + 1]
                if e == "x":
                    if not (k + 3 < j and s[k + 2] in HEX and s[k + 3] in HEX):
                        raise LexError("malformed-literal", i)
                    k += 4
                    continue
                if e == "u":
                    r = self.u_escape(k)
                    if r is None or r[1] > j:
                        raise LexError("malformed-literal", i)
                    k = r[1]
                    continue
                k += 3 if e == "\r" and s[k + 2] == "\n" else 2
                continue
            k += 1
        self.emit("string", i, end)
        self.expr_end = True
        return end

    def template(self, start, j, from_backtick):
        s = self.s
        while True:
            if j >= self.n:
                raise LexError("unterminated-literal", start)
            c = s[j]
            if c == "\\":
                if j + 1 >= self.n:
                    raise LexError("unterminated-literal", start)
                j += 3 if s[j + 1] == "\r" and self.at(j + 2) == "\n" else 2
                continue
            if c == "`":
                self.emit("template" if from_backtick else "template-tail", start, j + 1)
                self.expr_end = True
                return j + 1
            if c == "$" and self.at(j + 1) == "{":
                self.emit("template-head" if from_backtick else "template-middle", start, j + 2)
                self.stack.append({"k": "${", "at": j, "tok": start})
                self.expr_end = False
                return j + 2
            j += 1

    def regex(self, i):
        s, j, in_class = self.s, i + 1, False
        while True:
            if j >= self.n or s[j] in LINE_TERMINATORS:
                raise LexError("unterminated-literal", i)
            c = s[j]
            if c == "\\":
                if j + 1 >= self.n or s[j + 1] in LINE_TERMINATORS:
                    raise LexError("unterminated-literal", i)
                j += 2
                continue
            if in_class:
                if c == "]":
                    in_class = False
            elif c == "[":
                in_class = True
            elif c == "/":
                break
            j += 1
        j += 1
        while j < self.n and ident_part_char(ord(s[j])):
            j += 1
        self.emit("regex", i, j)
        self.expr_end = True
        return j

    # ------------------------------------------------------------ JSX
    def element_done(self):
        if not self.stack or self.stack[-1]["k"] not in ("elem", "tag"):
            self.expr_end = self.element_end_expr_end()

    def children(self, i):
        s = self.s
        if i >= self.n:
            return i
        c = s[i]
        if c == "{":
            self.emit("punct", i, i + 1)
            self.stack.append({"k": "jbrace", "at": i})
            self.expr_end = False
            return i + 1
        if c == "<":
            self.emit("punct", i, i + 1)
            self.stack.append({"k": "tag", "at": i, "closing": False, "started": False, "slash": False})
            return i + 1
        if c in ">}":
            raise LexError("illegal-character", i)
        j = i
        while j < self.n and s[j] not in "{<>}":
            j += 1
        a, b = i, j
        while a < b and self.jsx_trim(s[a]):
            a += 1
        while b > a and self.jsx_trim(s[b - 1]):
            b -= 1
        if a < b:
            self.emit("jsx-text", a, b)
        return j

    def tag(self, i):
        s = self.s
        i = self.skip_trivia(i)
        if i >= self.n:
            return i
        t = self.stack[-1]
        c = s[i]
        if t["slash"] and c != ">":
            raise LexError("illegal-character", i)
        if c == "/":
            if not t["started"]:
                if len(self.stack) < 2 or self.stack[-2]["k"] != "elem":
                    raise LexError("unbalanced-delimiter", t["at"])
                t["closing"] = True
            elif t["closing"]:
                raise LexError("illegal-character", i)
            else:
                t["slash"] = True
            t["started"] = True
            self.emit("punct", i, i + 1)
            return i + 1
        if c == ">":
            self.emit("punct", i, i + 1)
            self.stack.pop()
            if t["closing"]:
                self.stack.pop()  # the element it closes
                self.element_done()
            elif t["slash"]:
                self.element_done()
            else:
                self.stack.append({"k": "elem", "at": t["at"]})
            return i + 1
        prev = self.last_text()
        t["started"] = True
        if c in ".:":
            self.emit("punct", i, i + 1)
            return i + 1
        if c in "={\"'<" and t["closing"]:
            raise LexError("illegal-character", i)
        if c == "=":
            self.emit("punct", i, i + 1)
            return i + 1
        if c == "{":
            self.emit("punct", i, i + 1)
            self.stack.append({"k": "jbrace", "at": i})
            self.expr_end = False
            return i + 1
        if c in "\"'":
            j = s.find(c, i + 1)
            if j < 0:
                raise LexError("unterminated-literal", i)
            self.emit("jsx-string", i, j + 1)
            return j + 1
        if c == "<":
            if not self.attr_element_ok(prev):
                raise LexError("illegal-character", i)
            self.emit("punct", i, i + 1)
            self.stack.append({"k": "tag", "at": i, "closing": False, "started": False, "slash": False})
            return i + 1
        if ident_start_char(ord(c)):
            j = i + 1
            while j < self.n and (s[j] == "-" or ident_part_char(ord(s[j]))):
                j += 1
            self.emit("ident", i, j)
            return j
        raise LexError("illegal-character", i)


def lex(text, profile, lexer=Lexer):
    """Returns ('ok', [(class, start, end)]) with character indices, or ('error', code, index)."""
    lx = lexer(text, PROFILES[profile])
    try:
        return ("ok", lx.run())
    except LexError as e:
        return ("error", e.code, e.index)
