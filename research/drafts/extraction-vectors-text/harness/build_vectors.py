#!/usr/bin/env python3
"""Write the text-profile vector, configuration and rejection files.

Usage: python3 -I harness/build_vectors.py   (from extraction-vectors-text/)

Derivation (`derivation: hand`): for every vector the expected token texts,
folded values and skeleton values below were written by hand from the profile
rules and from per-character lookups in the pinned tables (NFKC_Casefold and
confusables rows). This script does NOT segment, fold or skeletonize. It only
(a) locates each hand-written token text in the input, left to right, to get
its byte span, (b) computes k-gram hashes and winnowing, and (c) writes JSON.
check_text_vectors.py recomputes everything from the input bytes and the
pinned tables and must agree.

Standard library only. Output is deterministic.
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent
DOMAIN = b"traceweave/text-kgram/draft-1"
CHANNELS = ["exact", "folded", "skeleton"]


def config_bytes(profile, max_bytes=1048576, k=8, window=8):
    cfg = {"contract": "traceweave-text-winnow-draft-1", "profile": profile, "profileVersion": "draft-1",
           "channels": CHANNELS, "k": k, "window": window, "hash": "sha256-first8-u64be",
           "maxInputBytes": max_bytes}
    return (json.dumps(cfg, separators=(",", ":")) + "\n").encode()


CONFIGS = {
    "config-text-plain.json": config_bytes("text-plain"),
    "config-text-markdown.json": config_bytes("text-markdown"),
    "config-text-plain-limit16.json": config_bytes("text-plain", 16),
}


def lp(b):
    return len(b).to_bytes(4, "big") + b


def kgram_hash(cfg, channel, values):
    msg = lp(DOMAIN) + lp(cfg["profile"].encode()) + lp(cfg["profileVersion"].encode()) + lp(channel.encode())
    msg += cfg["k"].to_bytes(4, "big")
    for v in values:
        msg += lp(b"word") + lp(v.encode())
    return hashlib.sha256(msg).digest()[:8].hex()


def winnow(hs, w):
    if not hs:
        return [], False
    if len(hs) < w:
        return [max(range(len(hs)), key=lambda p: (-int(hs[p], 16), p))], True
    sel = []
    for s in range(len(hs) - w + 1):
        best = s
        for p in range(s, s + w):
            if hs[p] <= hs[best]:
                best = p
        sel.append(best)
    return sel, False


def block(cfg, ch, values, spans):
    k = cfg["k"]
    kg = [{"position": i, "hash": kgram_hash(cfg, ch, values[i:i + k]), "span": [spans[i][0], spans[i + k - 1][1]]}
          for i in range(max(0, len(values) - k + 1))]
    sel, partial = winnow([g["hash"] for g in kg], cfg["window"])
    return {"kgrams": kg, "windowSelections": sel, "partialWindow": partial,
            "fingerprints": [kg[p] for p in sorted(set(sel))]}


def result(cfg, data, exact, folded, skel, masked=None):
    text = data.decode("utf-8")
    toks = []
    pos = 0  # character index
    for i, t in enumerate(exact):
        while True:
            j = text.find(t, pos)
            if j < 0:
                sys.exit(f"token {t!r} not found after {pos}")
            a = len(text[:j].encode())
            if not any(ma < a + len(t.encode()) and a < mb for ma, mb in (masked or [])):
                break
            pos = j + 1  # occurrence lies in a hand-listed masked range
        b = a + len(t.encode())
        toks.append({"text": t, "span": [a, b], "folded": folded[i], "skeleton": skel[i]})
        pos = j + len(t)
    res = {"status": "ok" if len(toks) >= cfg["k"] else "insufficient-tokens"}
    if cfg["profile"] == "text-markdown":
        res["masked"] = masked or []
    res["tokens"] = toks
    spans = [t["span"] for t in toks]
    for ch in CHANNELS:
        vals = [t["text"] if ch == "exact" else t[ch] for t in toks]
        b = block(cfg, ch, vals, spans)
        res[ch] = b if ch == "exact" else {"values": vals, **b}
    return res


def split(s):
    return s.split(" ") if s else []


VECTORS = {"text-plain.json": [], "text-markdown.json": [], "limits-text.json": []}
PAIRS = {"text-plain.json": [], "text-markdown.json": [], "limits-text.json": []}
REJECTIONS = []


def vec(file, vid, classes, desc, data, exact=None, folded=None, skel=None, error=None, masked=None,
        config=None, starts=None):
    if isinstance(data, str):
        data = data.encode("utf-8")
    config = config or ("config-text-markdown.json" if file == "text-markdown.json" else "config-text-plain.json")
    cfg = json.loads(CONFIGS[config])
    if error:
        res = {"status": "error", "error": {"code": error[0], "offset": error[1]}}
    else:
        ex = split(exact) if isinstance(exact, str) else exact
        if folded is None:
            raise SystemExit(f"{vid}: folded must be written by hand")
        fo = split(folded)
        sk = split(skel) if skel is not None else fo
        assert len(ex) == len(fo) == len(sk), (vid, len(ex), len(fo), len(sk))
        res = result(cfg, data, ex, fo, sk, masked)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = None
    v = {"id": vid, "tags": ["class:" + c for c in classes], "description": desc, "derivation": "hand",
         "config": config, "inputBase64": base64.b64encode(data).decode(), "inputText": text}
    if text is None:
        v["inputDisplay"] = "".join(chr(b) if 0x20 <= b < 0x7f and b != 0x5c else f"\\x{b:02x}" for b in data)
    v["result"] = res
    VECTORS[file].append(v)


def rej(vid, layer, desc, mutation):
    REJECTIONS.append({"id": f"rej-{vid}", "vector": vid, "layer": layer, "description": desc, "mutation": mutation})


P, M, L = "text-plain.json", "text-markdown.json", "limits-text.json"

# ------------------------------------------------------------------ plain: empty, short, window edges

vec(P, "plain-empty", ["empty"], "Empty input: zero tokens, insufficient-tokens, no k-grams.", "", "", "")
rej("plain-empty", "status", "Empty input reported as ok", {"op": "status", "status": "ok"})

vec(P, "plain-whitespace-only", ["empty", "reflow"],
    "Only White_Space (SP, TAB, CR, LF, NBSP, IDEOGRAPHIC SPACE): all separators, zero tokens.",
    " \t\r\n\xa0\u3000\n", "", "")
rej("plain-whitespace-only", "segmentation", "NBSP treated as a word character", {"op": "replace-tokens", "tokens": [
    {"text": "\xa0", "span": [4, 6], "folded": " ", "skeleton": " "}]})

vec(P, "plain-punctuation-only", ["empty", "punctuation"],
    "Punctuation and symbols only (General_Category P*, S*): zero tokens.",
    "... \u2014 !? \xbf\xa1 \u201c\u201d \xab \xbb \u2013 -- \u2018\u2019 #*_`~ $ \u20ac +", "", "")
rej("plain-punctuation-only", "segmentation", "Underscore (Pc) treated as a word character",
    {"op": "replace-tokens", "tokens": [{"text": "_", "span": [37, 38], "folded": "_", "skeleton": "_"}]})

vec(P, "plain-short", ["short"], "Five tokens, fewer than k = 8: insufficient-tokens, tokens listed, no k-grams.",
    "The quick brown fox jumps.", "The quick brown fox jumps", "the quick brown fox jumps", "the quick brown fox jurnps")
rej("plain-short", "fold", "Folded channel keeps case", {"op": "set", "token": 0, "field": "folded", "value": "The"})

vec(P, "plain-exact-k", ["below-kw1"], "Exactly k = 8 tokens: one k-gram, partial window.",
    "One two three four five six seven eight.", "One two three four five six seven eight",
    "one two three four five six seven eight")
rej("plain-exact-k", "status", "Exactly k tokens reported as insufficient", {"op": "status", "status": "insufficient-tokens"})

vec(P, "plain-below-kw1", ["below-kw1"], "12 tokens (k <= n < k + w - 1 = 15): m = 5 < w, one partial window.",
    "A small paragraph of twelve plain words stays below the locality bound.",
    "A small paragraph of twelve plain words stays below the locality bound",
    "a small paragraph of twelve plain words stays below the locality bound",
    "a srnall paragraph of twelve plain words stays below the locality bound")
rej("plain-below-kw1", "skeleton", "Skeleton omits the listed confusable m -> rn",
    {"op": "set", "token": 1, "field": "skeleton", "value": "small"})

vec(P, "plain-at-kw1", ["below-kw1"], "Exactly k + w - 1 = 15 tokens: m = 8 = w, one full window, not partial.",
    "Fifteen words make exactly one full window when k is eight and w is eight.",
    "Fifteen words make exactly one full window when k is eight and w is eight",
    "fifteen words make exactly one full window when k is eight and w is eight",
    "fifteen words rnake exactly one full window when k is eight and w is eight")
rej("plain-at-kw1", "segmentation", "Final period kept in the last token",
    {"op": "replace-tokens", "tokens": "AT-KW1-PERIOD"})

# ------------------------------------------------------------------ ties

vec(P, "plain-ties", ["ties"], "Period-3 cycle of 24 tokens: k-gram hashes repeat with period 3, so windows hold equal minima and the rightmost is selected.",
    "red green blue " * 8, " ".join(["red green blue"] * 8), " ".join(["red green blue"] * 8))
rej("plain-ties", "winnow", "Ties broken leftmost", {"op": "leftmost-ties"})

vec(P, "plain-repeated", ["ties"], "20 identical tokens: every k-gram hash is equal; each window selects its last position.",
    "na " * 20, " ".join(["na"] * 20), " ".join(["na"] * 20))
rej("plain-repeated", "winnow", "Ties broken leftmost", {"op": "leftmost-ties"})

# ------------------------------------------------------------------ reflow family

REFLOW_A = ("Shared passages can survive when a writer copies a paragraph\n"
            "into another document and then reflows the lines to fit\n"
            "a narrower column.\n")
RA_EXACT = "Shared passages can survive when a writer copies a paragraph into another document and then reflows the lines to fit a narrower column"
RA_FOLD = "shared passages can survive when a writer copies a paragraph into another document and then reflows the lines to fit a narrower column"
RA_SKEL = "shared passages can survive when a writer copies a paragraph into another docurnent and then reflows the lines to fit a narrower colurnn"

vec(P, "plain-reflow-a", ["reflow"], "Reference paragraph, wrapped at about 60 columns with LF.", REFLOW_A, RA_EXACT, RA_FOLD, RA_SKEL)
rej("plain-reflow-a", "hash", "k omitted from the hashed bytes", {"op": "hash-without-k"})

vec(P, "plain-reflow-b", ["reflow"], "Same words, one long line with doubled spaces, a TAB and trailing spaces: identical hashes in every channel.",
    "Shared passages can survive when a writer copies a  paragraph into another\tdocument and then reflows the lines   to fit a narrower column.  \n",
    RA_EXACT, RA_FOLD, RA_SKEL)
rej("plain-reflow-b", "segmentation", "TAB treated as part of a word",
    {"op": "replace-tokens", "tokens": "REFLOW-B-TAB"})

vec(P, "plain-crlf", ["crlf", "reflow"], "Reference paragraph with CRLF line ends: CR is White_Space, so tokens and hashes equal plain-reflow-a; spans shift.",
    REFLOW_A.replace("\n", "\r\n"), RA_EXACT, RA_FOLD, RA_SKEL)
rej("plain-crlf", "segmentation", "CR kept at the end of the token before each line end",
    {"op": "replace-tokens", "tokens": "CRLF-CR"})

vec(P, "plain-bom", ["bom"], "U+FEFF at offset 0 followed by the reference paragraph: the BOM is Default_Ignorable, never inside a token; spans keep original offsets (first token starts at 3).",
    "\ufeff" + REFLOW_A, RA_EXACT, RA_FOLD, RA_SKEL)
rej("plain-bom", "segmentation", "BOM included in the first token's span and text",
    {"op": "replace-tokens", "tokens": "BOM-IN-TOKEN"})

vec(P, "plain-upper", ["case"], "Reference paragraph in capitals: exact channel differs, folded and skeleton identical to plain-reflow-a.",
    REFLOW_A.upper(), RA_EXACT.upper(), RA_FOLD, RA_SKEL)
rej("plain-upper", "fold", "Folded value keeps capitals (no case folding)",
    {"op": "set", "token": 3, "field": "folded", "value": "SURVIVE"})

ZW = ("Shared pas\u200bsages can survive when a wri\u200cter copies a \u200b paragraph\n"
      "into another docu\u200dment and then re\u2060flows the lines to fit\n"
      "a nar\xadrower column.\n")
vec(P, "plain-zero-width", ["zero-width", "default-ignorable"],
    "ZWSP, ZWNJ, ZWJ, WORD JOINER and SOFT HYPHEN inside words; a ZWSP between spaces. Default_Ignorable code points are transparent inside a token: exact text keeps them, folded deletes them, so folded and skeleton equal plain-reflow-a.",
    ZW,
    ["Shared", "pas\u200bsages", "can", "survive", "when", "a", "wri\u200cter", "copies", "a", "paragraph", "into", "another",
     "docu\u200dment", "and", "then", "re\u2060flows", "the", "lines", "to", "fit", "a", "nar\xadrower", "column"],
    RA_FOLD, RA_SKEL)
rej("plain-zero-width", "segmentation", "ZWSP splits the word (WB-style break at Format characters not applied)",
    {"op": "split", "token": 1, "at": 3, "folded": ["pas", "sages"], "skeleton": ["pas", "sages"]})

vec(P, "plain-zwsp-as-separator", ["zero-width", "limit"],
    "ZWSP used as the only separator between words joins them into one token (a stated limit for scripts that use ZWSP as a word separator).",
    "alpha\u200bbeta gamma delta epsilon zeta eta theta iota",
    ["alpha\u200bbeta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota"],
    "alphabeta gamma delta epsilon zeta eta theta iota", "alphabeta garnrna delta epsilon zeta eta theta iota")
rej("plain-zwsp-as-separator", "segmentation", "ZWSP treated as a separator",
    {"op": "split", "token": 0, "at": 5, "folded": ["alpha", "beta"], "skeleton": ["alpha", "beta"]})

vec(P, "plain-other-ignorable", ["default-ignorable"],
    "Other Default_Ignorable code points: CGJ, VS16, a TAG letter, LRM, MONGOLIAN VOWEL SEPARATOR and U+FEFF inside words; leading and trailing ignorables outside the span; a HANGUL FILLER alone is no token.",
    "\u200bstart co\u034fde emo\ufe0fji ta\U000e0041g left\u200eright mon\u180egol inter\ufeffnational \u3164 end\u2060 \u2060word\n",
    ["start", "co\u034fde", "emo\ufe0fji", "ta\U000e0041g", "left\u200eright", "mon\u180egol", "inter\ufeffnational", "end", "word"],
    "start code emoji tag leftright mongol international end word",
    "start code ernoji tag leftright rnongol international end word")
rej("plain-other-ignorable", "fold", "Variation selector kept in the folded value",
    {"op": "set", "token": 2, "field": "folded", "value": "emo\ufe0fji"})

# ------------------------------------------------------------------ Unicode forms

FR_NFC = "Le caf\xe9 cr\xe8me est tr\xe8s chaud, d\xe9j\xe0 pr\xeat \xe0 c\xf4t\xe9 de la fen\xeatre."
FR_FOLD = "le caf\xe9 cr\xe8me est tr\xe8s chaud d\xe9j\xe0 pr\xeat \xe0 c\xf4t\xe9 de la fen\xeatre"
FR_SKEL = "le cafe\u0301 cre\u0300rne est tre\u0300s chaud de\u0301ja\u0300 pre\u0302t a\u0300 co\u0302te\u0301 de la fene\u0302tre"
vec(P, "plain-nfc", ["nfd", "non-latin"], "French sentence in NFC.", FR_NFC,
    "Le caf\xe9 cr\xe8me est tr\xe8s chaud d\xe9j\xe0 pr\xeat \xe0 c\xf4t\xe9 de la fen\xeatre", FR_FOLD, FR_SKEL)
rej("plain-nfc", "skeleton", "Skeleton not decomposed (NFC prototype output)",
    {"op": "set", "token": 1, "field": "skeleton", "value": "caf\xe9"})

FR_NFD_WORDS = ["Le", "cafe\u0301", "cre\u0300me", "est", "tre\u0300s", "chaud", "de\u0301ja\u0300", "pre\u0302t", "a\u0300",
                "co\u0302te\u0301", "de", "la", "fene\u0302tre"]
vec(P, "plain-nfd", ["nfd"], "The same sentence in NFD: combining marks are word characters, exact text differs, folded (NFC) and skeleton equal plain-nfc.",
    "Le cafe\u0301 cre\u0300me est tre\u0300s chaud, de\u0301ja\u0300 pre\u0302t a\u0300 co\u0302te\u0301 de la fene\u0302tre.",
    FR_NFD_WORDS, FR_FOLD, FR_SKEL)
rej("plain-nfd", "fold", "Folded value left in NFD (no NFC after the mapping)",
    {"op": "set", "token": 1, "field": "folded", "value": "cafe\u0301"})

LIG_FOLD = "the final figure shows flow fields in the first office"
vec(P, "plain-nfkc-ligature", ["nfkc"], "U+FB01, U+FB02 and U+FB03 ligatures expand under NFKC: folded equals the ASCII spelling.",
    "The \ufb01nal \ufb01gure shows \ufb02ow \ufb01elds in the \ufb01rst o\ufb03ce.",
    "The \ufb01nal \ufb01gure shows \ufb02ow \ufb01elds in the \ufb01rst o\ufb03ce", LIG_FOLD,
    "the final figure shows flow fields in the first office")
rej("plain-nfkc-ligature", "fold", "Canonical-only fold (NFC) keeps the ligature",
    {"op": "set", "token": 1, "field": "folded", "value": "\ufb01nal"})

vec(P, "plain-nfkc-ascii", ["nfkc"], "ASCII spelling of plain-nfkc-ligature.",
    "The final figure shows flow fields in the first office.",
    "The final figure shows flow fields in the first office", LIG_FOLD)
rej("plain-nfkc-ascii", "segmentation", "Token dropped", {"op": "drop", "token": 2})

vec(P, "plain-nfkc-compat", ["nfkc", "numbers"],
    "Fullwidth letters, circled digits, superscript, Roman numeral, vulgar fraction and parenthesized digit. The fold drops separators produced by NFKC (U+2044 in 1/2, the parentheses of U+2474).",
    "\uff26\uff35\uff2c\uff2c\uff37\uff29\uff24\uff34\uff28 \uff54\uff45\uff58\uff54 \uff41\uff4e\uff44 \u2460\u2461\u2462 x\xb2 \u216b \xbd \u2474 end",
    "\uff26\uff35\uff2c\uff2c\uff37\uff29\uff24\uff34\uff28 \uff54\uff45\uff58\uff54 \uff41\uff4e\uff44 \u2460\u2461\u2462 x\xb2 \u216b \xbd \u2474 end",
    "fullwidth text and 123 x2 xii 12 1 end",
    "fullwidth text and l23 x2 xii l2 l end")
rej("plain-nfkc-compat", "fold", "Separator from NFKC kept in the folded value (1/2 with FRACTION SLASH)",
    {"op": "set", "token": 6, "field": "folded", "value": "1\u20442"})

vec(P, "plain-casefold-expansion", ["casefold-expansion", "case"],
    "Full case folding expands U+00DF and U+1E9E to ss; capitals and sharp s fold to the same value.",
    "Die Stra\xdfe ist gro\xdf und die STRASSE ist GRO\u1e9e, sagt Wei\xdf.",
    "Die Stra\xdfe ist gro\xdf und die STRASSE ist GRO\u1e9e sagt Wei\xdf",
    "die strasse ist gross und die strasse ist gross sagt weiss")
rej("plain-casefold-expansion", "fold", "Simple case folding keeps U+00DF",
    {"op": "set", "token": 1, "field": "folded", "value": "stra\xdfe"})

# ------------------------------------------------------------------ confusables

CONF_LATIN = "The paper copy of the essay was scanned and posted on the course page for every reader."
CONF_FOLD_L = "the paper copy of the essay was scanned and posted on the course page for every reader"
vec(P, "plain-confusable-latin", ["confusable"], "Latin reference sentence (17 tokens).", CONF_LATIN,
    "The paper copy of the essay was scanned and posted on the course page for every reader", CONF_FOLD_L)
rej("plain-confusable-latin", "segmentation", "Two tokens merged across a space",
    {"op": "replace-tokens", "tokens": "CONF-MERGE"})

CONF_CYR = ("The \u0440\u0430per \u0441opy of the ess\u0430y was sc\u0430nned and p\u043ested on the \u0441ourse p\u0430ge "
            "for every re\u0430der.")
vec(P, "plain-confusable-cyrillic", ["confusable"],
    "Cyrillic \u0430 \u0441 \u043e \u0440 (listed in confusables.txt) substituted in 8 words: folded values differ from the Latin sentence in every k-gram; skeleton values are identical.",
    CONF_CYR,
    "The \u0440\u0430per \u0441opy of the ess\u0430y was sc\u0430nned and p\u043ested on the \u0441ourse p\u0430ge for every re\u0430der",
    "the \u0440\u0430per \u0441opy of the ess\u0430y was sc\u0430nned and p\u043ested on the \u0441ourse p\u0430ge for every re\u0430der",
    CONF_FOLD_L)
rej("plain-confusable-cyrillic", "skeleton", "Skeleton keeps the Cyrillic letters (no confusable mapping)",
    {"op": "set", "token": 1, "field": "skeleton", "value": "\u0440\u0430per"})

# ------------------------------------------------------------------ punctuation, numbers, hyphenation

PUNCT_TOK = "Well it s fine isn t it Yes well known state of the art rules mostly"
PUNCT_SKEL = "well it s fine isn t it yes well known state of the art rules rnostly"
vec(P, "plain-punct-a", ["punctuation"], "Typographic punctuation: curly apostrophes and quotes, em dash, hyphenated compounds, parentheses. Apostrophes and hyphens separate.",
    "Well, it\u2019s \u201cfine\u201d \u2014 isn\u2019t it? Yes: well-known, state-of-the-art rules (mostly).",
    PUNCT_TOK, PUNCT_TOK.lower(), PUNCT_SKEL)
rej("plain-punct-a", "segmentation", "Right single quotation mark kept inside it's (UAX #29 MidNumLet behaviour)",
    {"op": "replace-tokens", "tokens": "PUNCT-APOS"})

vec(P, "plain-punct-b", ["punctuation"], "The same words with ASCII and other punctuation only: identical hashes in every channel to plain-punct-a.",
    "Well; it's \"fine\" -- isn't it! Yes... well known / state of the art rules [mostly]",
    PUNCT_TOK, PUNCT_TOK.lower(), PUNCT_SKEL)
rej("plain-punct-b", "fold", "Folded value keeps capital Y", {"op": "set", "token": 7, "field": "folded", "value": "Yes"})

vec(P, "plain-numbers", ["numbers", "punctuation", "non-latin"],
    "Decimal points, thousands separators and dates split numbers; Arabic-Indic digits are word characters and are not mapped to ASCII by NFKC.",
    "Version 3.14 shipped on 2026-11-22 with 1,000 users, 1.000 in German style, and \u0663\u0664 in Arabic-Indic digits.",
    "Version 3 14 shipped on 2026 11 22 with 1 000 users 1 000 in German style and \u0663\u0664 in Arabic Indic digits",
    "version 3 14 shipped on 2026 11 22 with 1 000 users 1 000 in german style and \u0663\u0664 in arabic indic digits",
    "version 3 l4 shipped on 2O26 ll 22 with l OOO users l OOO in gerrnan style and \u0663\u0664 in arabic indic digits")
rej("plain-numbers", "segmentation", "3.14 kept as one token (UAX #29 MidNum behaviour)",
    {"op": "replace-tokens", "tokens": "NUM-DECIMAL"})

vec(P, "plain-hyphenation-wrap", ["hyphenation", "limit"],
    "A hyphen at a line break splits the word: exam-/ple gives exam, ple (stated limit; a SOFT HYPHEN would be transparent instead).",
    "The exam-\nple shows line-end hyphen-\nation in wrapped text.",
    "The exam ple shows line end hyphen ation in wrapped text",
    "the exam ple shows line end hyphen ation in wrapped text",
    "the exarn ple shows line end hyphen ation in wrapped text")
rej("plain-hyphenation-wrap", "segmentation", "Hyphen plus newline joined into one word",
    {"op": "replace-tokens", "tokens": "HYPHEN-JOIN"})

# ------------------------------------------------------------------ partial copy

SRC = "Winnowing keeps one fingerprint from every window of hashes, so a long enough shared run always leaves a trace."
SRC_EX = "Winnowing keeps one fingerprint from every window of hashes so a long enough shared run always leaves a trace"
vec(P, "plain-partial-source", ["partial-copy"], "Source passage, 19 tokens.", SRC, SRC_EX, SRC_EX.lower(),
    "winnowing keeps one fingerprint frorn every window of hashes so a long enough shared run always leaves a trace")
rej("plain-partial-source", "fold", "Folded value of a token replaced by its exact text",
    {"op": "set", "token": 0, "field": "folded", "value": "Winnowing"})

HOST = ("Our notes begin with unrelated remarks about gardens. ONE FINGERPRINT FROM EVERY WINDOW OF\n"
        "HASHES, SO A LONG ENOUGH SHARED RUN ALWAYS LEAVES A TRACE was quoted, then the notes return to gardens and weather.")
HOST_EX = ("Our notes begin with unrelated remarks about gardens ONE FINGERPRINT FROM EVERY WINDOW OF HASHES SO A LONG ENOUGH "
           "SHARED RUN ALWAYS LEAVES A TRACE was quoted then the notes return to gardens and weather")
vec(P, "plain-partial-host", ["partial-copy", "case", "reflow"],
    "Unrelated host with 17 consecutive source tokens (>= k + w - 1 = 15), capitalized and rewrapped: at least one shared folded and skeleton fingerprint is guaranteed.",
    HOST, HOST_EX, HOST_EX.lower(),
    "our notes begin with unrelated rernarks about gardens one fingerprint frorn every window of hashes so a long enough "
    "shared run always leaves a trace was quoted then the notes return to gardens and weather")
rej("plain-partial-host", "segmentation", "Token span shifted by one byte",
    {"op": "replace-tokens", "tokens": "HOST-SHIFT"})

# ------------------------------------------------------------------ non-Latin scripts

vec(P, "plain-greek", ["non-latin", "casefold-expansion"],
    "Greek with final sigma: full case folding maps \u03c2 and \u03a3 to \u03c3. Skeleton maps several Greek letters to Latin prototypes.",
    "\u039a\u03b1\u03bb\u03b7\u03bc\u03ad\u03c1\u03b1 \u03ba\u03cc\u03c3\u03bc\u03b5\u0387 \u039f\u0394\u039f\u03a3 \u03ba\u03b1\u03b9 \u03bf\u03b4\u03cc\u03c2, \u03a3\u039f\u03a6\u039f\u03a3 \u03ba\u03b1\u03b9 \u03c3\u03bf\u03c6\u03cc\u03c2.",
    "\u039a\u03b1\u03bb\u03b7\u03bc\u03ad\u03c1\u03b1 \u03ba\u03cc\u03c3\u03bc\u03b5 \u039f\u0394\u039f\u03a3 \u03ba\u03b1\u03b9 \u03bf\u03b4\u03cc\u03c2 \u03a3\u039f\u03a6\u039f\u03a3 \u03ba\u03b1\u03b9 \u03c3\u03bf\u03c6\u03cc\u03c2",
    "\u03ba\u03b1\u03bb\u03b7\u03bc\u03ad\u03c1\u03b1 \u03ba\u03cc\u03c3\u03bc\u03b5 \u03bf\u03b4\u03bf\u03c3 \u03ba\u03b1\u03b9 \u03bf\u03b4\u03cc\u03c3 \u03c3\u03bf\u03c6\u03bf\u03c3 \u03ba\u03b1\u03b9 \u03c3\u03bf\u03c6\u03cc\u03c3",
    "\u0138a\u03bbn\u0329\u03bc\ua793\u0301pa \u0138o\u0301o\u03bc\ua793 o\u1e9foo \u0138ai o\u1e9fo\u0301o oo\u0278oo \u0138ai oo\u0278o\u0301o")
rej("plain-greek", "fold", "Final sigma left unfolded", {"op": "set", "token": 4, "field": "folded", "value": "\u03bf\u03b4\u03cc\u03c2"})

vec(P, "plain-rtl-and-indic", ["non-latin", "bidi", "combining"],
    "Cyrillic, Arabic, Hebrew and Devanagari (with virama and vowel signs, General_Category Mn/Mc) words; danda and Arabic comma are separators.",
    "\u041f\u0440\u0438\u0432\u0435\u0442 \u043c\u0438\u0440. \u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645\u060c \u05e9\u05dc\u05d5\u05dd \u05e2\u05d5\u05dc\u05dd. \u0928\u092e\u0938\u094d\u0924\u0947 \u0926\u0941\u0928\u093f\u092f\u093e\u0964",
    "\u041f\u0440\u0438\u0432\u0435\u0442 \u043c\u0438\u0440 \u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645 \u05e9\u05dc\u05d5\u05dd \u05e2\u05d5\u05dc\u05dd \u0928\u092e\u0938\u094d\u0924\u0947 \u0926\u0941\u0928\u093f\u092f\u093e",
    "\u043f\u0440\u0438\u0432\u0435\u0442 \u043c\u0438\u0440 \u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645 \u05e9\u05dc\u05d5\u05dd \u05e2\u05d5\u05dc\u05dd \u0928\u092e\u0938\u094d\u0924\u0947 \u0926\u0941\u0928\u093f\u092f\u093e",
    "\u03c0p\u1d0e\u0299e\u1d1b \u028d\u1d0ep \u0645\u0631\u062d\u0628l \u0628l\u0644\u0639l\u0644\u0645 \u05e9\u05dcl\u05dd \u05e2l\u05dc\u05dd \u0928\u092e\u0938\u094d\u0924\U00011b64 \u0926\u0941\u0928\u09bf\u092f\u093e")
rej("plain-rtl-and-indic", "segmentation", "Virama treated as a separator (marks not word characters)",
    {"op": "split", "token": 6, "at": 3, "folded": ["\u0928\u092e\u0938", "\u094d\u0924\u0947"], "skeleton": ["\u0928\u092e\u0938", "\u094d\u0924\U00011b64"]})

vec(P, "plain-japanese", ["non-latin", "no-spaces"],
    "Japanese without spaces: each Ideographic code point is one token; kana runs between ideographs form one token each.",
    "\u65e5\u672c\u8a9e\u3092\u52c9\u5f37\u3057\u3066\u3044\u307e\u3059\u3002\u6f22\u5b57\u3068\u304b\u306a\u304c\u6df7\u3056\u308b\u6587\u3067\u3059\u3002",
    "\u65e5 \u672c \u8a9e \u3092 \u52c9 \u5f37 \u3057\u3066\u3044\u307e\u3059 \u6f22 \u5b57 \u3068\u304b\u306a\u304c \u6df7 \u3056\u308b \u6587 \u3067\u3059",
    "\u65e5 \u672c \u8a9e \u3092 \u52c9 \u5f37 \u3057\u3066\u3044\u307e\u3059 \u6f22 \u5b57 \u3068\u304b\u306a\u304c \u6df7 \u3056\u308b \u6587 \u3067\u3059",
    "\u65e5 \u672c \u8a9e \u3092 \u52c9 \u5f37 \u3057\u3066\u3044\u307e\u3059 \u6f22 \u5b57 \u3068\u304b\u306a\u304b\u3099 \u6df7 \u3055\u3099\u308b \u6587 \u3066\u3099\u3059")
rej("plain-japanese", "segmentation", "Ideographs grouped into one run (letters-only rule without the Ideographic class)",
    {"op": "replace-tokens", "tokens": "JA-RUN"})

vec(P, "plain-chinese", ["non-latin", "no-spaces"], "Chinese without spaces: nine Ideographic tokens.",
    "\u6211\u4eec\u5728\u5317\u4eac\u5b66\u4e60\u4e2d\u6587\u3002",
    "\u6211 \u4eec \u5728 \u5317 \u4eac \u5b66 \u4e60 \u4e2d \u6587", "\u6211 \u4eec \u5728 \u5317 \u4eac \u5b66 \u4e60 \u4e2d \u6587")
rej("plain-chinese", "segmentation", "Two ideographs merged", {"op": "replace-tokens", "tokens": "ZH-MERGE"})

vec(P, "plain-thai", ["non-latin", "no-spaces", "limit"],
    "Thai: no dictionary segmentation, so each space-delimited phrase is one token (stated limit).",
    "\u0e2a\u0e27\u0e31\u0e2a\u0e14\u0e35\u0e04\u0e23\u0e31\u0e1a \u0e22\u0e34\u0e19\u0e14\u0e35\u0e15\u0e49\u0e2d\u0e19\u0e23\u0e31\u0e1a",
    "\u0e2a\u0e27\u0e31\u0e2a\u0e14\u0e35\u0e04\u0e23\u0e31\u0e1a \u0e22\u0e34\u0e19\u0e14\u0e35\u0e15\u0e49\u0e2d\u0e19\u0e23\u0e31\u0e1a",
    "\u0e2a\u0e27\u0e31\u0e2a\u0e14\u0e35\u0e04\u0e23\u0e31\u0e1a \u0e22\u0e34\u0e19\u0e14\u0e35\u0e15\u0e49\u0e2d\u0e19\u0e23\u0e31\u0e1a",
    "\u0e2a\u0e27\u0e31\u0e2a\u0e04\u0e35\u0e04\u0e23\u0e31\u0e1a \u0e22\u0e34\u0e19\u0e04\u0e35\u0e04\u0e49\u0e2d\u0e19\u0e23\u0e31\u0e1a")
rej("plain-thai", "segmentation", "Thai vowel sign treated as a separator",
    {"op": "split", "token": 0, "at": 2, "folded": ["\u0e2a\u0e27", "\u0e31\u0e2a\u0e14\u0e35\u0e04\u0e23\u0e31\u0e1a"],
     "skeleton": ["\u0e2a\u0e27", "\u0e31\u0e2a\u0e04\u0e35\u0e04\u0e23\u0e31\u0e1a"]})

HANGUL_FOLD = "\uac00 \ub098 \ub2e4 \ub77c \ub9c8 \ubc14 \uc0ac \uc544"
HANGUL_SKEL = "\u1100\u1161 \u1102\u1161 \u1103\u1161 \u1105\u1161 \u1106\u1161 \u1107\u1161 \u1109\u1161 \u110b\u1161"
vec(P, "plain-hangul", ["non-latin"], "Eight precomposed Hangul syllables separated by spaces.",
    "\uac00 \ub098 \ub2e4 \ub77c \ub9c8 \ubc14 \uc0ac \uc544", HANGUL_FOLD, HANGUL_FOLD, HANGUL_SKEL)
rej("plain-hangul", "skeleton", "Skeleton left precomposed (no final NFD)",
    {"op": "set", "token": 0, "field": "skeleton", "value": "\uac00"})

vec(P, "plain-hangul-jamo", ["nfd", "non-latin"], "The same syllables as conjoining jamo (NFD): folded recomposes them, so folded and skeleton equal plain-hangul.",
    "\u1100\u1161 \u1102\u1161 \u1103\u1161 \u1105\u1161 \u1106\u1161 \u1107\u1161 \u1109\u1161 \u110b\u1161", HANGUL_SKEL, HANGUL_FOLD, HANGUL_SKEL)
rej("plain-hangul-jamo", "fold", "Jamo not recomposed (Hangul composition missing from NFC)",
    {"op": "set", "token": 0, "field": "folded", "value": "\u1100\u1161"})

vec(P, "plain-cherokee", ["non-latin", "case", "casefold-expansion"],
    "Cherokee: UCD 17.0.0 NFKC_Casefold maps the small letters to the capitals (case folding goes to the older capitals for Cherokee). golang.org/x/text v0.39.0 cases.Fold leaves the small letters unchanged, so an implementation built on it diverges here.",
    "\u13e3\u13b3\u13a9 \uabb3\uab83\uab79 \u13e3\u13b3\u13a9",
    "\u13e3\u13b3\u13a9 \uabb3\uab83\uab79 \u13e3\u13b3\u13a9",
    "\u13e3\u13b3\u13a9 \u13e3\u13b3\u13a9 \u13e3\u13b3\u13a9",
    "\u13e3WY \u13e3WY \u13e3WY")
rej("plain-cherokee", "fold", "Small letters left unfolded (golang.org/x/text cases.Fold behaviour)",
    {"op": "set", "token": 1, "field": "folded", "value": "\uabb3\uab83\uab79"})

COMB_FOLD = "combining test \u1eb9\u0301 and \u03ac\u03b9 then z\u0336\u0337a plus \u0301abc done"
COMB_SKEL = "cornbining test e\u0323\u0301 and a\u0301i then z\u0335\u0338a plus \u0301abc done"
vec(P, "plain-combining-a", ["combining"],
    "Combining sequences: e + U+0301 + U+0323 (non-canonical order), alpha + U+0345 + U+0301 (non-canonical; U+0345 folds to iota), two overlay marks with equal ccc, and a token that starts with a combining mark.",
    "Combining test: e\u0301\u0323 and \u03b1\u0345\u0301 then z\u0336\u0337a plus \u0301abc done",
    ["Combining", "test", "e\u0301\u0323", "and", "\u03b1\u0345\u0301", "then", "z\u0336\u0337a", "plus", "\u0301abc", "done"],
    COMB_FOLD, COMB_SKEL)
rej("plain-combining-a", "fold", "Mapping applied before NFD (non-canonical order gives a different result)",
    {"op": "set", "token": 4, "field": "folded", "value": "\u03b1\u03af"})

vec(P, "plain-combining-b", ["combining", "nfd"],
    "Canonically equivalent spellings of plain-combining-a (precomposed U+1EB9 + U+0301, U+1FB4): folded and skeleton identical, exact differs.",
    "Combining test: \u1eb9\u0301 and \u1fb4 then z\u0336\u0337a plus \u0301abc done",
    ["Combining", "test", "\u1eb9\u0301", "and", "\u1fb4", "then", "z\u0336\u0337a", "plus", "\u0301abc", "done"],
    COMB_FOLD, COMB_SKEL)
rej("plain-combining-b", "skeleton", "Overlay marks mapped in the wrong order / not mapped",
    {"op": "set", "token": 6, "field": "skeleton", "value": "z\u0336\u0337a"})

vec(P, "plain-bidi", ["bidi", "non-latin", "default-ignorable"],
    "Mixed-direction text with isolates (U+2067, U+2069), RLM and an RLO/PDF pair inside a word: bidi controls are Default_Ignorable, so they are outside spans at token edges and deleted inside tokens. Spans stay in logical (memory) order.",
    "The word \u2067\u05e9\u05dc\u05d5\u05dd\u2069 means peace; \u200f\u0627\u0644\u0633\u0644\u0627\u0645\u200f \u0639\u0644\u064a\u0643\u0645 is a greeting and ab\u202ecd\u202c is one token.",
    ["The", "word", "\u05e9\u05dc\u05d5\u05dd", "means", "peace", "\u0627\u0644\u0633\u0644\u0627\u0645", "\u0639\u0644\u064a\u0643\u0645", "is", "a",
     "greeting", "and", "ab\u202ecd", "is", "one", "token"],
    "the word \u05e9\u05dc\u05d5\u05dd means peace \u0627\u0644\u0633\u0644\u0627\u0645 \u0639\u0644\u064a\u0643\u0645 is a greeting and abcd is one token",
    "the word \u05e9\u05dcl\u05dd rneans peace l\u0644\u0633\u0644l\u0645 \u0639\u0644\u0649\u0643\u0645 is a greeting and abcd is one token")
rej("plain-bidi", "segmentation", "Isolate characters included at the token edges",
    {"op": "replace-tokens", "tokens": "BIDI-EDGE"})

# ------------------------------------------------------------------ errors

vec(P, "plain-err-lone-continuation", ["invalid-utf8"], "Lone continuation byte.", b"abc \x80 def", error=("invalid-utf8", 4))
vec(P, "plain-err-overlong", ["invalid-utf8"], "Overlong encoding of '/'.", b"\xc0\xaf", error=("invalid-utf8", 0))
vec(P, "plain-err-surrogate", ["invalid-utf8"], "Encoded surrogate U+D800.", b"ok \xed\xa0\x80", error=("invalid-utf8", 3))
vec(P, "plain-err-truncated", ["invalid-utf8"], "Truncated three-byte sequence at end of input.", b"end \xe2\x82", error=("invalid-utf8", 4))
vec(P, "plain-err-above-max", ["invalid-utf8"], "Four-byte sequence above U+10FFFF.", b"\xf4\x90\x80\x80", error=("invalid-utf8", 0))
vec(P, "plain-err-nul", ["nul"], "NUL inside text.", b"word\x00word", error=("nul", 4))
vec(P, "plain-err-nul-then-invalid", ["nul", "invalid-utf8"], "NUL at 0 and an invalid byte at 7: the encoding check runs first.",
    b"\x00 then \xff", error=("invalid-utf8", 7))
rej("plain-err-nul", "error", "NUL reported at the wrong offset", {"op": "error", "code": "nul", "offset": 5})
rej("plain-err-nul-then-invalid", "error", "NUL reported before the encoding check", {"op": "error", "code": "nul", "offset": 0})
rej("plain-err-surrogate", "error", "Invented error code", {"op": "error", "code": "surrogate", "offset": 3})

# ------------------------------------------------------------------ limits

vec(L, "limit-exact", ["limit-size"], "Exactly maxInputBytes = 16 bytes: accepted.", "sixteen byte txt",
    "sixteen byte txt", "sixteen byte txt", config="config-text-plain-limit16.json")
rej("limit-exact", "error", "Input of exactly maxInputBytes rejected", {"op": "error", "code": "input-too-large", "offset": 0})
vec(L, "limit-over", ["limit-size"], "17 bytes: input-too-large at 0.", "seventeen bytes x", error=("input-too-large", 0),
    config="config-text-plain-limit16.json")
vec(L, "limit-over-invalid", ["limit-size", "invalid-utf8"], "17 bytes including an invalid byte: the size check runs first.",
    b"sixteen bytes\xff...", error=("input-too-large", 0), config="config-text-plain-limit16.json")

# ------------------------------------------------------------------ Markdown

MD_SYNTAX = ("# Shared passages\n\n"
             "Shared *passages* can **survive** when a writer copies a [paragraph](https://example.com/a_(b) \"title\")\n"
             "into another `document` and then reflows the lines.\n\n"
             "> A quote with <span class=\"x\">inline HTML</span> &amp; an entity.\n\n"
             "| left | right |\n| ---- | ----- |\n| one  | two   |\n\n"
             "1. First item\n- Second ![alt text](img/pic.png) item <https://example.org/x>\n")
MD_TOK = ("Shared passages Shared passages can survive when a writer copies a paragraph into another document and then reflows "
          "the lines A quote with inline HTML an entity left right one two 1 First item Second alt text item")
MD_FOLD = MD_TOK.lower()
MD_SKEL = ("shared passages shared passages can survive when a writer copies a paragraph into another docurnent and then reflows "
           "the lines a quote with inline htrnl an entity left right one two l first itern second alt text itern")


def md_masks(text, pieces):
    """Byte ranges of hand-listed masked substrings, located left to right."""
    out, pos = [], 0
    for p in pieces:
        j = text.index(p, pos)
        a = len(text[:j].encode())
        out.append([a, a + len(p.encode())])
        pos = j + len(p)
    return out


vec(M, "md-syntax", ["markdown"],
    "Common Markdown: heading, emphasis, inline link with nested parentheses and a title, code span (kept), blockquote with inline HTML and an entity, table, ordered and bullet list, image, autolink. Masked: the link and image destinations, the two tags, the entity and the autolink.",
    MD_SYNTAX, MD_TOK, MD_FOLD, MD_SKEL,
    masked=md_masks(MD_SYNTAX, ["(https://example.com/a_(b) \"title\")", "<span class=\"x\">", "</span>", "&amp;",
                                "(img/pic.png)", "<https://example.org/x>"]))
rej("md-syntax", "markdown", "Link destination not masked (front end treats Markdown as plain text)",
    {"op": "set-masked", "masked": "MD-NO-DEST"})

MD_STRIPPED = ("Shared passages\n\nShared passages can survive when a writer copies a paragraph\n"
               "into another document and then reflows the lines.\n\nA quote with inline HTML & an entity.\n\n"
               "left right\none two\n\n1. First item\nSecond alt text item\n")
vec(M, "md-stripped", ["markdown"], "Plain rendering of md-syntax, extracted with text-markdown: identical hashes in every channel.",
    MD_STRIPPED, MD_TOK, MD_FOLD, MD_SKEL)
rej("md-stripped", "segmentation", "Ampersand made a token", {"op": "replace-tokens", "tokens": "MD-AMP"})

vec(P, "plain-md-syntax", ["markdown"], "The md-syntax bytes under text-plain: URLs, tag names and the entity name become tokens.",
    MD_SYNTAX,
    "Shared passages Shared passages can survive when a writer copies a paragraph https example com a b title into another document "
    "and then reflows the lines A quote with span class x inline HTML span amp an entity left right one two 1 First item Second "
    "alt text img pic png item https example org x",
    "shared passages shared passages can survive when a writer copies a paragraph https example com a b title into another document "
    "and then reflows the lines a quote with span class x inline html span amp an entity left right one two 1 first item second "
    "alt text img pic png item https example org x",
    "shared passages shared passages can survive when a writer copies a paragraph https exarnple corn a b title into another docurnent "
    "and then reflows the lines a quote with span class x inline htrnl span arnp an entity left right one two l first itern second "
    "alt text irng pic png itern https exarnple org x")
rej("plain-md-syntax", "segmentation", "Markdown masks applied under text-plain", {"op": "replace-tokens", "tokens": "PLAIN-MASKED"})

MD_FENCE = ("Before the code we write prose.\n\n```go\nfunc main() { fmt.Println(\"hidden\") }\n```\n\n"
            "~~~~\ntilde fence ```\n~~~~~\n\nAfter the code more prose follows here.\n")
vec(M, "md-fence", ["markdown"], "A backtick fence with an info string and a tilde fence closed by a longer run: both masked line by line.",
    MD_FENCE, "Before the code we write prose After the code more prose follows here",
    "before the code we write prose after the code more prose follows here",
    "before the code we write prose after the code rnore prose follows here",
    masked=md_masks(MD_FENCE, ["```go", "func main() { fmt.Println(\"hidden\") }", "```", "~~~~", "tilde fence ```", "~~~~~"]))
rej("md-fence", "markdown", "Closing fence line left unmasked (closing line not treated as part of the fence)",
    {"op": "set-masked", "masked": "FENCE-EARLY"})

MD_FENCE_OPEN = "Prose before an unclosed fence.\n\n```\ncode that never closes\nmore code\n"
vec(M, "md-fence-unclosed", ["markdown"], "An unclosed fence masks to the end of input.",
    MD_FENCE_OPEN, "Prose before an unclosed fence", "prose before an unclosed fence",
    masked=md_masks(MD_FENCE_OPEN, ["```", "code that never closes", "more code"]))
rej("md-fence-unclosed", "markdown", "Unclosed fence not masked", {"op": "set-masked", "masked": []})

MD_FM = "---\ntitle: Hidden title\ntags: [a, b]\n---\nVisible prose starts after the front matter block ends.\n"
vec(M, "md-front-matter", ["markdown"], "YAML front matter at offset 0 is masked through its closing line.",
    MD_FM, "Visible prose starts after the front matter block ends",
    "visible prose starts after the front matter block ends", "visible prose starts after the front rnatter block ends",
    masked=[[0, len("---\ntitle: Hidden title\ntags: [a, b]\n---")]])
rej("md-front-matter", "markdown", "Front matter left unmasked", {"op": "set-masked", "masked": []})

MD_FM_CRLF = "---\r\ntitle: x\r\n---\r\nVisible words follow the CRLF front matter here.\r\n"
vec(M, "md-front-matter-crlf", ["markdown", "crlf"],
    "Front matter with CRLF line ends: the masked range ends after the closing line's CR, before its LF.",
    MD_FM_CRLF, "Visible words follow the CRLF front matter here", "visible words follow the crlf front matter here",
    "visible words follow the crlf front rnatter here", masked=[[0, len("---\r\ntitle: x\r\n---\r")]])
rej("md-front-matter-crlf", "markdown", "Masked range stops before the CR (content end instead of line end)",
    {"op": "set-masked", "masked": [[0, len("---\r\ntitle: x\r\n---")]]})

MD_FM_OPEN = "---\ntitle: Shown title\nVisible prose follows without a closing line.\n"
vec(M, "md-front-matter-unclosed", ["markdown"], "Front matter without a closing line is not front matter: its words are tokens.",
    MD_FM_OPEN, "title Shown title Visible prose follows without a closing line",
    "title shown title visible prose follows without a closing line")
rej("md-front-matter-unclosed", "markdown", "Unclosed front matter masked to end of input",
    {"op": "set-masked", "masked": [[0, len(MD_FM_OPEN) - 1]]})

MD_CMT = "Keep this <!-- hidden\nacross lines --> visible text and <!--x--> more words here.\n"
vec(M, "md-html-comment", ["markdown"], "HTML comments, one spanning two lines; scanning resumes mid-line after -->.",
    MD_CMT, "Keep this visible text and more words here", "keep this visible text and more words here",
    "keep this visible text and rnore words here",
    masked=md_masks(MD_CMT, ["<!-- hidden\nacross lines -->", "<!--x-->"]))
rej("md-html-comment", "segmentation", "Comment body tokenized", {"op": "replace-tokens", "tokens": "CMT-BODY"})

MD_CMT_OPEN = "Start <!-- never closed so these words stay visible in the token stream\n"
vec(M, "md-html-comment-unclosed", ["markdown"], "<!-- without --> is ordinary text.",
    MD_CMT_OPEN, "Start never closed so these words stay visible in the token stream",
    "start never closed so these words stay visible in the token stream",
    "start never closed so these words stay visible in the token strearn")
rej("md-html-comment-unclosed", "markdown", "Unclosed comment masked to end of input",
    {"op": "set-masked", "masked": [[6, len(MD_CMT_OPEN) - 1]]})

MD_REF = ("See the [guide][g] and the footnote.[^1]\n\n[g]: https://example.com/guide \"Guide title\"\n"
          "[^1]: Footnote prose remains visible.\n")
vec(M, "md-link-reference", ["markdown"], "A link reference definition line is masked; a footnote definition ([^ label) is not.",
    MD_REF, "See the guide g and the footnote 1 1 Footnote prose remains visible",
    "see the guide g and the footnote 1 1 footnote prose remains visible",
    "see the guide g and the footnote l l footnote prose rernains visible",
    masked=md_masks(MD_REF, ["[g]: https://example.com/guide \"Guide title\""]))
rej("md-link-reference", "markdown", "Footnote definition masked", {"op": "set-masked", "masked": "REF-FOOTNOTE"})

MD_PAREN = ("Read [the article](https://en.wikipedia.org/wiki/Fold_(higher-order_function)) about folds, then "
            "[broken](no close paren on this line\nand continue reading.\n")
vec(M, "md-link-nested-parens", ["markdown"], "Balanced parentheses inside a destination; a destination not closed on its line is not masked.",
    MD_PAREN, "Read the article about folds then broken no close paren on this line and continue reading",
    "read the article about folds then broken no close paren on this line and continue reading",
    masked=md_masks(MD_PAREN, ["(https://en.wikipedia.org/wiki/Fold_(higher-order_function))"]))
rej("md-link-nested-parens", "markdown", "Destination ends at the first ) (no nesting)",
    {"op": "set-masked", "masked": "PAREN-FIRST"})

MD_LT = "If a < b and c > d then x<y but 3 <4 and <Tag attr> is masked while <1> stays.\n"
vec(M, "md-angle-brackets", ["markdown"], "Only < [/] ASCII-letter ... > on one line, with no < in between, is a tag.",
    MD_LT, "If a b and c d then x y but 3 4 and is masked while 1 stays",
    "if a b and c d then x y but 3 4 and is masked while 1 stays",
    "if a b and c d then x y but 3 4 and is rnasked while l stays",
    masked=md_masks(MD_LT, ["<Tag attr>"]))
rej("md-angle-brackets", "markdown", "x<y ... > taken as a tag across the later <",
    {"op": "set-masked", "masked": "LT-GREEDY"})

MD_ENT = "Caf&eacute; costs &#163;3 &amp; tea &#x20AC;2, &bogus stays, &;\n"
vec(M, "md-entities", ["markdown", "limit"], "Named, decimal and hex character references are masked as separators (not decoded): Caf&eacute; gives Caf.",
    MD_ENT, "Caf costs 3 tea 2 bogus stays", "caf costs 3 tea 2 bogus stays",
    masked=md_masks(MD_ENT, ["&eacute;", "&#163;", "&amp;", "&#x20AC;"]))
rej("md-entities", "fold", "Entity decoded into the token's folded value",
    {"op": "set", "token": 0, "field": "folded", "value": "caf\xe9"})

MD_IND = "Prose line.\n\n    indented code is tokenized\n"
vec(M, "md-indented-code", ["markdown", "limit"], "Indented code blocks are not recognized (stated deviation from CommonMark).",
    MD_IND, "Prose line indented code is tokenized", "prose line indented code is tokenized")
rej("md-indented-code", "segmentation", "Indented code dropped", {"op": "replace-tokens", "tokens": "IND-DROP"})

vec(M, "md-syntax-only", ["markdown", "empty"], "Markdown syntax with no words: an unclosed --- is not front matter, and every character is punctuation.",
    "---\n***\n> \n- \n| |\n", "", "")
rej("md-syntax-only", "status", "Reported ok with no tokens", {"op": "status", "status": "ok"})

vec(M, "md-empty", ["empty", "markdown"], "Empty input under text-markdown.", "", "", "")
rej("md-empty", "markdown", "Phantom masked range", {"op": "set-masked", "masked": [[0, 0]]})

vec(M, "md-err-invalid-utf8", ["invalid-utf8", "markdown"], "Invalid UTF-8 after a heading.", b"# T\xc3\x28", error=("invalid-utf8", 3))
vec(M, "md-err-nul", ["nul", "markdown"], "NUL on the second line.", b"# Title\n\x00", error=("nul", 8))
rej("md-err-nul", "error", "NUL ignored as a separator", {"op": "error", "code": "invalid-utf8", "offset": 8})

# ------------------------------------------------------------------ pairs

PAIRS[P] = [
    {"a": "plain-reflow-a", "b": "plain-reflow-b", "channels": CHANNELS, "relation": "identical-hashes"},
    {"a": "plain-reflow-a", "b": "plain-crlf", "channels": CHANNELS, "relation": "identical-hashes"},
    {"a": "plain-reflow-a", "b": "plain-bom", "channels": CHANNELS, "relation": "identical-hashes"},
    {"a": "plain-reflow-a", "b": "plain-upper", "channels": ["folded", "skeleton"], "relation": "identical-hashes"},
    {"a": "plain-reflow-a", "b": "plain-upper", "channels": ["exact"], "relation": "different-hashes"},
    {"a": "plain-reflow-a", "b": "plain-zero-width", "channels": ["folded", "skeleton"], "relation": "identical-hashes"},
    {"a": "plain-nfc", "b": "plain-nfd", "channels": ["folded", "skeleton"], "relation": "identical-hashes"},
    {"a": "plain-nfc", "b": "plain-nfd", "channels": ["exact"], "relation": "different-hashes"},
    {"a": "plain-nfkc-ligature", "b": "plain-nfkc-ascii", "channels": ["folded", "skeleton"], "relation": "identical-hashes"},
    {"a": "plain-confusable-latin", "b": "plain-confusable-cyrillic", "channels": ["skeleton"], "relation": "identical-hashes"},
    {"a": "plain-confusable-latin", "b": "plain-confusable-cyrillic", "channels": ["exact", "folded"], "relation": "different-hashes"},
    {"a": "plain-punct-a", "b": "plain-punct-b", "channels": CHANNELS, "relation": "identical-hashes"},
    {"a": "plain-partial-source", "b": "plain-partial-host", "channels": ["folded", "skeleton"], "relation": "shares-fingerprint"},
    {"a": "plain-hangul", "b": "plain-hangul-jamo", "channels": ["folded", "skeleton"], "relation": "identical-hashes"},
    {"a": "plain-combining-a", "b": "plain-combining-b", "channels": ["folded", "skeleton"], "relation": "identical-hashes"},
]
PAIRS[M] = [{"a": "md-syntax", "b": "md-stripped", "channels": CHANNELS, "relation": "identical-hashes"}]


# ------------------------------------------------------------------ resolve named token-list mutations


def toks_of(vid):
    for f in VECTORS.values():
        for v in f:
            if v["id"] == vid:
                return v
    raise KeyError(vid)


def resolve():
    for r in REJECTIONS:
        m = r["mutation"]
        v = toks_of(r["vector"])
        res = v["result"]
        data = base64.b64decode(v["inputBase64"])
        name = m.get("tokens") if m["op"] == "replace-tokens" and isinstance(m.get("tokens"), str) else None
        mm = m.get("masked") if m["op"] == "set-masked" and isinstance(m.get("masked"), str) else None
        if name:
            t = [dict(x) for x in res["tokens"]]
            if name == "AT-KW1-PERIOD":
                t[-1] = {**t[-1], "text": "eight.", "span": [t[-1]["span"][0], t[-1]["span"][1] + 1]}
            elif name == "REFLOW-B-TAB":
                t[11] = {**t[11], "text": "another\t", "span": [t[11]["span"][0], t[11]["span"][1] + 1]}
            elif name == "CRLF-CR":
                for i, x in enumerate(t):
                    e = x["span"][1]
                    if data[e:e + 1] == b"\r":
                        t[i] = {**x, "text": x["text"] + "\r", "span": [x["span"][0], e + 1]}
            elif name == "BOM-IN-TOKEN":
                t[0] = {**t[0], "text": "\ufeff" + t[0]["text"], "span": [0, t[0]["span"][1]]}
            elif name == "CONF-MERGE":
                a, b = t[0], t[1]
                t[0:2] = [{"text": a["text"] + " " + b["text"], "span": [a["span"][0], b["span"][1]],
                           "folded": a["folded"] + b["folded"], "skeleton": a["skeleton"] + b["skeleton"]}]
            elif name == "PUNCT-APOS":
                a, b = t[1], t[2]
                t[1:3] = [{"text": "it\u2019s", "span": [a["span"][0], b["span"][1]], "folded": "it\u2019s", "skeleton": "it\u2019s"}]
            elif name == "NUM-DECIMAL":
                a, b = t[1], t[2]
                t[1:3] = [{"text": "3.14", "span": [a["span"][0], b["span"][1]], "folded": "3.14", "skeleton": "3.l4"}]
            elif name == "HYPHEN-JOIN":
                a, b = t[1], t[2]
                t[1:3] = [{"text": "exam-\nple", "span": [a["span"][0], b["span"][1]], "folded": "example", "skeleton": "exarnple"}]
            elif name == "HOST-SHIFT":
                x = t[3]
                t[3] = {**x, "span": [x["span"][0] + 1, x["span"][1] + 1]}
            elif name == "JA-RUN":
                a, b = t[0], t[2]
                t[0:3] = [{"text": "\u65e5\u672c\u8a9e", "span": [a["span"][0], b["span"][1]],
                           "folded": "\u65e5\u672c\u8a9e", "skeleton": "\u65e5\u672c\u8a9e"}]
            elif name == "ZH-MERGE":
                a, b = t[0], t[1]
                t[0:2] = [{"text": "\u6211\u4eec", "span": [a["span"][0], b["span"][1]], "folded": "\u6211\u4eec", "skeleton": "\u6211\u4eec"}]
            elif name == "BIDI-EDGE":
                x = t[2]
                t[2] = {**x, "text": "\u2067" + x["text"] + "\u2069", "span": [x["span"][0] - 3, x["span"][1] + 3]}
            elif name == "MD-AMP":
                t.insert(23, {"text": "&", "span": [0, 0], "folded": "&", "skeleton": "&"})
            elif name == "PLAIN-MASKED":
                t = [x for x in t if x["folded"] not in ("https", "example", "com", "title", "span", "class", "amp", "img", "pic", "png", "org", "x", "b")]
            elif name == "CMT-BODY":
                t.insert(2, {"text": "hidden", "span": [15, 21], "folded": "hidden", "skeleton": "hidden"})
            elif name == "IND-DROP":
                t = t[:2]
            else:
                raise SystemExit(name)
            m["tokens"] = t
        if mm:
            ms = [list(x) for x in res["masked"]]
            if mm == "MD-NO-DEST":
                ms = [x for i, x in enumerate(ms) if i not in (0, 4)]
            elif mm == "FENCE-EARLY":
                ms = ms[:5]
            elif mm == "REF-FOOTNOTE":
                foot = MD_REF.index("[^1]:")
                ms = ms + [[len(MD_REF[:foot].encode()), len(MD_REF.encode()) - 1]]
            elif mm == "PAREN-FIRST":
                a = ms[0][0]
                ms = [[a, a + len("(https://en.wikipedia.org/wiki/Fold_(higher-order_function)")]]
            elif mm == "LT-GREEDY":
                p = MD_LT.index("<y")
                q = MD_LT.index("<Tag attr>")
                ms = [[p, q + len("<Tag attr>")]]
            else:
                raise SystemExit(mm)
            m["masked"] = ms


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")


def config_negatives():
    base = json.loads(CONFIGS["config-text-plain.json"])

    def enc(cfg):
        return json.dumps(cfg, separators=(",", ":")) + "\n"

    negs = []

    def neg(i, desc, text):
        negs.append({"id": i, "description": desc, "configText": text,
                     "expectedResult": {"status": "error", "error": {"code": "unsupported-config", "offset": None},
                                        "profile": None, "profileVersion": None,
                                        "configSha256": hashlib.sha256(text.encode()).hexdigest(),
                                        "inputSha256": None, "inputLength": None}})

    neg("cfg-text-code-channels", "Code-profile channel names", enc({**base, "channels": ["exact", "normalized"]}))
    neg("cfg-text-two-channels", "Skeleton channel omitted (draft-1 requires all three)", enc({**base, "channels": ["exact", "folded"]}))
    neg("cfg-text-channel-order", "Channels reordered", enc({**base, "channels": ["exact", "skeleton", "folded"]}))
    neg("cfg-text-token-contract", "Code contract identifier", enc({**base, "contract": "traceweave-token-winnow-draft-1"}))
    neg("cfg-text-unknown-format", "Unknown front end", enc({**base, "profile": "text-html"}))
    neg("cfg-text-version", "Unknown profile version", enc({**base, "profileVersion": "draft-2"}))
    neg("cfg-text-k-above-bound", "k = 17", enc({**base, "k": 17}))
    neg("cfg-text-window-zero", "window = 0", enc({**base, "window": 0}))
    neg("cfg-text-max-above-bound", "maxInputBytes = 8388609", enc({**base, "maxInputBytes": 8388609}))
    neg("cfg-text-whitespace", "Insignificant whitespace", json.dumps(base, separators=(", ", ": ")) + "\n")
    neg("cfg-text-no-lf", "No trailing LF", enc(base)[:-1])
    neg("cfg-text-extra-key", "Extra key (format)", enc({**base, "format": "plain"}))
    pos = [{"id": "cfg-text-bounds-max", "configText": enc({**base, "profile": "text-markdown", "k": 16, "window": 128, "maxInputBytes": 8388608})},
           {"id": "cfg-text-bounds-min", "configText": enc({**base, "k": 1, "window": 1, "maxInputBytes": 1})}]
    return {"description": "Configurations that MUST be rejected with unsupported-config (profile section 11), and boundary configurations that MUST be accepted.",
            "negatives": negs, "boundaryPositives": pos}


def main():
    resolve()
    for name, raw in CONFIGS.items():
        (OUT / name).write_bytes(raw)
    for name, vs in VECTORS.items():
        dump(OUT / name, {"profileDraft": "research/drafts/extraction-profile-text.md", "vectors": vs, "pairs": PAIRS[name]})
    dump(OUT / "rejections.json", {"description": "Paired rejections: deliberately wrong expected results. Hashes, selections and fingerprints are recomputed after the mutation so that only the declared layer is wrong. check_text_vectors.py MUST reject each at that layer.",
                                   "rejections": REJECTIONS})
    dump(OUT / "config-negative-text.json", config_negatives())
    n = sum(len(v) for v in VECTORS.values())
    print(f"wrote {n} vectors, {len(REJECTIONS)} rejections")


if __name__ == "__main__":
    main()
