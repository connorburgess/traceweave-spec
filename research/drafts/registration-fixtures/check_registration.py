#!/usr/bin/env python3
"""Check the illustrative registration-record fixtures (draft-3) against ../registration-record.md.

Standard library only; Python 3.11 or later. This is not a registration verifier.
It verifies the fixtures' Ed25519 signatures (public, test-only keys) under the
strict rule set of the design (section 10.1) and the structural and outcome rules of
the design. Placeholder time evidence is labelled and never verified. The real-format
vectors in real-format/ (a local test-only TSA and a synthetic OpenTimestamps proof
against a locally mined header file) are verified for real, by realformat.py.

Every fixture in fixtures/ must produce no failure code. Every fixture in
negative/ must produce exactly its expected code (plus any listed in
expect.alsoReported). Files in aux/ and real-format/ are inputs referenced by other
fixtures. The run also performs (1) Ed25519 and PAE self-tests, (2) a
wrong-implementation self-test: plausible wrong verifier outputs are built in memory
and each must be rejected, and (3) a drift check: every failure code appears in the
design document and has a negative fixture.

Usage: python3 -I check_registration.py [--verbose]
Exit status 0 when everything behaves as expected, 1 otherwise.
"""

from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import importlib.util
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOC = HERE.parent / "registration-record.md"
_spec = importlib.util.spec_from_file_location("traceweave_realformat", HERE / "realformat.py")
RF = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RF)

STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PAYLOAD_TYPE = "application/vnd.in-toto+json"
PREDICATE_TYPE = "https://traceweave.org/predicate/registration/draft-3"
KEY_EVENT_TYPE = "https://traceweave.org/predicate/key-event/draft-3"
REGISTRATION_VERSION = "traceweave-registration-draft-3"
BUNDLE_VERSION = "traceweave-registration-bundle-draft-3"
EVIDENCE_VERSION = "traceweave-time-evidence-draft-3"
RESULT_VERSION = "traceweave-registration-verification-draft-3"
LINK_VERSION = "traceweave-registration-link-draft-3"
RENDERING_VERSION = "traceweave-registration-rendering-draft-3"
KEY_EVENT_VERSION = "traceweave-key-event-draft-3"
SET_VERSION = "traceweave-registration-set-draft-3"
WITNESS_TYPE = "https://traceweave.org/predicate/witness/draft-3"
WITNESS_VERSION = "traceweave-witness-draft-3"
WITNESS_REQUEST_VERSION = "traceweave-witness-request-draft-3"
A2A_EXTENSION = "https://traceweave.org/a2a/ext/registration/draft-1"
POSSESSION_SCHEME = "sha256-salted-possession-v1"
POSSESSION_DOMAIN = b"Traceweave-Possession-v1\x00"
CATALOGUE_SCHEME = "sha256-salted-catalogue-v1"
CATALOGUE_DOMAIN = b"Traceweave-Catalogue-v0.1\x00"

FIXTURE_NOTICE = ("Illustrative fixture for research/drafts/registration-record.md. Synthetic data and a public "
                  "test-only key; it registers nothing and proves nothing.")
PLACEHOLDER_NOTICE = ("PLACEHOLDER. Not a real time-stamp token, proof, log entry or cosignature. No service issued "
                      "it and it cannot be verified. Times in it are invented for illustration.")
REAL_NOTICE = ("TEST VECTOR. Real format, issued by a local test-only TSA or built against a locally mined header "
               "file. No external service issued it, and its trust anchor must never be trusted.")
NOT_SHOWN = ["authorship", "originality", "first-creation", "ownership", "permission"]
SENTENCE_LIMITS = ("It does not show who created the content, that it is original, that the registrant was first to "
                   "create it, who owns it, or that its use is permitted.")
SENTENCE_FIRST = "First to register is not first to create."
SENTENCE_ORDER = "Comparing the times of two registrations does not show which was made first."
REQUIRED_SENTENCES = [SENTENCE_LIMITS, SENTENCE_FIRST, SENTENCE_ORDER]
AGENT_SENTENCE = ("A registration made by or through an agent shows which key signed it and, for a hosted witness, which "
                  "authenticated caller presented the digest; it does not show whether a person or an agent created the "
                  "content, or on whose behalf.")

# type -> (root kind, body key for placeholders)
EVIDENCE_TYPES = {"rfc3161": ("tsa-certificate-chain", "rfc3161"), "opentimestamps": ("bitcoin-proof-of-work", "opentimestamps"),
                  "rekor-v2": ("log-key", "rekorV2"), "traceweave-witness": ("witness-service-key", "witness")}
OTS_MARGIN = timedelta(seconds=7200)
RETAIN_REASONS = {"unspecified", "affiliationChanged", "superseded", "cessationOfOperation"}  # RFC 3161 section 4 item 1
ALL_REASONS = RETAIN_REASONS | {"keyCompromise", None}
EVIDENCE_OUTCOMES = {"valid", "invalid", "wrong-target", "pending", "untrusted-root", "unsupported", "wrong-policy",
                     "revoked", "no-revocation-data", "expired-unrenewed", "insufficient-confirmations",
                     "placeholder", "placeholder-assumed-valid"}
COUNTED = ("valid", "placeholder-assumed-valid")

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX16 = re.compile(r"^[0-9a-f]{16}$")
OID = re.compile(r"^[0-2](\.(0|[1-9][0-9]*))+$")
SUBJECT_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SINGLE_VERDICT_KEYS = {"authentic", "isauthentic", "verdict", "overall", "overallresult", "verified"}
AUTHORSHIP_KEYS = {"author", "authorship", "owner", "ownership", "creator", "original", "originality"}
# Closed lists (design section 4.6).
FORBIDDEN_KEYS = {"fingerprints", "tokens", "source", "text", "content", "catalogueBytes", "opening", "nonceHex", "inputBase64"}
TIME_KEYS = {"provedAt", "timestamp", "notAfter", "genTime", "registeredAt", "recordedAt", "time", "provedTime"}
DENY_TEXT = re.compile(
    r"(?i)\b(author\w*|wrote|written|belongs?|yours?|claim to|registered to you|first to create|priority|creat(ed|or|ion of)|"
    r"own(s|ed|er|ership)?|original\w*|copyright|prove[sdn]?|proof|establish\w*|authentic\w*|verified|genuine|legitimate)\b")
ORDER_TEXT = re.compile(r"(?i)\b(before|after|earlier|later|first|sooner|preceded?|predates?|older|newer)\b")
T = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)"
K = r"([0-9a-f]{16})"
TEMPLATES = {
    "title": re.compile(r"^Registration of ([a-z0-9][a-z0-9._-]{0,63}) \(SHA-256 [0-9a-f]{8}…[0-9a-f]{4}\)\.$"),
    "digest": re.compile(r"^Content digest: (matches the file you supplied|does not match the file you supplied|not checked, because no file was supplied)\.$"),
    "signature": re.compile(r"^Signature by key " + K + r": (valid|invalid|unknown key); signer (trusted|not trusted|disputed by a key event|not evaluated) under your policy\.$"),
    "bound": re.compile(r"^This record shows that the content existed, and that key " + K + r" signed a statement naming it, no later than " + T + r"( \(according to one time source only\))?\.$"),
    "sources": re.compile(r"^Time sources for key " + K + r": (\d+) independent, (\d+) required; the earliest single source says " + T + r"\.$"),
    "no-bound": re.compile(r"^No proved time for key " + K + r"\.$"),
    "claimed": re.compile(r"^Creation time claimed by the registrant, not proved: " + T + r"\.$"),
    "witness": re.compile(r"^Witnessed: the caller ([A-Za-z0-9._-]+) presented the signature digest no later than " + T + r", according to the witness's time-stamp authority\.$"),
}

CODES = [
    "authorship-claim", "catalogue-does-not-open", "catalogue-not-report-input", "catalogue-unsalted",
    "claimed-as-proved", "duplicate-key", "envelope-shape", "evidence-shape", "evidence-wrong-target",
    "fixture-shape", "forbidden-field", "key-bound-misattributed", "key-event-ignored", "key-event-shape",
    "key-identity-by-hint", "log-time-claimed", "nonce-invalid", "nonce-reused", "notice-missing", "ordering-claim",
    "pending-counted", "placeholder-unlabelled", "possession-mismatch", "predicate-type", "profile-mismatch",
    "provenance-shape", "quorum-miscount", "rendering-unlisted-line", "report-digest", "result-mismatch",
    "root-not-anchored", "signature-invalid", "single-verdict", "statement-digest", "statement-shape",
    "subject-mismatch", "subject-name", "time-in-statement", "tsa-eku-invalid", "tsa-imprint-mismatch",
    "tsa-nonce-mismatch", "tsa-signature-invalid", "tsa-signing-cert-mismatch", "trust-without-quorum",
    "content-on-wire", "a2a-shape", "mcp-tool-shape", "witness-shape",
]

# A2A 1.0 field names (ProtoJSON of specification/a2a.proto at tag v1.0.1); required fields first.
A2A_CARD = ({"name", "description", "supportedInterfaces", "version", "capabilities", "defaultInputModes",
             "defaultOutputModes", "skills"}, {"provider", "documentationUrl", "securitySchemes", "securityRequirements",
                                               "signatures", "iconUrl"})
A2A_INTERFACE = ({"url", "protocolBinding", "protocolVersion"}, {"tenant"})
A2A_SKILL = ({"id", "name", "description", "tags"}, {"examples", "inputModes", "outputModes", "securityRequirements"})
A2A_CAPS = (set(), {"streaming", "pushNotifications", "extensions", "extendedAgentCard"})
A2A_EXT = ({"uri"}, {"description", "required", "params"})
A2A_MESSAGE = ({"messageId", "role", "parts"}, {"contextId", "taskId", "metadata", "extensions", "referenceTaskIds"})
A2A_PART_CONTENT = {"text", "raw", "url", "data"}
A2A_PART_OTHER = {"metadata", "filename", "mediaType"}
A2A_TASK = ({"id", "status"}, {"contextId", "artifacts", "history", "metadata"})
A2A_ARTIFACT = ({"artifactId", "parts"}, {"name", "description", "metadata", "extensions"})
A2A_STATES = {"TASK_STATE_SUBMITTED", "TASK_STATE_WORKING", "TASK_STATE_COMPLETED", "TASK_STATE_FAILED",
              "TASK_STATE_CANCELED", "TASK_STATE_INPUT_REQUIRED", "TASK_STATE_REJECTED", "TASK_STATE_AUTH_REQUIRED"}
LOOPBACK = re.compile(r"^http://(127\.0\.0\.1|\[::1\]|localhost)(:\d+)?/")
MCP_TOOL = ({"name", "inputSchema"}, {"title", "description", "icons", "outputSchema", "annotations", "_meta"})
MCP_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


class Dup(ValueError):
    pass


# ------------------------------------------------------------------ Ed25519, strict profile (design section 10.1)
# RFC 8032 section 5.1.7 cofactorless verification, plus: S < L; A and R must be canonical
# encodings (y < p, and x = 0 never encoded with the sign bit set); A must not have small order.

P = 2 ** 255 - 19
Q = 2 ** 252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
SQRT_M1 = pow(2, (P - 1) // 4, P)
IDENTITY = (0, 1, 1, 0)


def _add(a, b):
    x = (a[1] - a[0]) * (b[1] - b[0]) % P
    y = (a[1] + a[0]) * (b[1] + b[0]) % P
    c = 2 * a[3] * b[3] * D % P
    d = 2 * a[2] * b[2] % P
    e, f, g, h = y - x, d - c, d + c, y + x
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _mul(s, pt):
    acc = IDENTITY
    while s > 0:
        if s & 1:
            acc = _add(acc, pt)
        pt = _add(pt, pt)
        s >>= 1
    return acc


def _equal(a, b):
    return (a[0] * b[2] - b[0] * a[2]) % P == 0 and (a[1] * b[2] - b[1] * a[2]) % P == 0


def _recover_x(y, sign):
    if y >= P:
        return None  # non-canonical y
    x2 = (y * y - 1) * pow(D * y * y + 1, P - 2, P) % P
    if x2 == 0:
        return None if sign else 0  # x = 0 with the sign bit set is non-canonical
    x = pow(x2, (P + 3) // 8, P)
    if (x * x - x2) % P:
        x = x * SQRT_M1 % P
    if (x * x - x2) % P:
        return None
    if (x & 1) != sign:
        x = P - x
    return x


_GY = 4 * pow(5, P - 2, P) % P
_GX = _recover_x(_GY, 0)
G = (_GX, _GY, 1, _GX * _GY % P)


def _compress(pt):
    zi = pow(pt[2], P - 2, P)
    x, y = pt[0] * zi % P, pt[1] * zi % P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _decompress(raw):
    if len(raw) != 32:
        return None
    y = int.from_bytes(raw, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    return None if x is None else (x, y, 1, x * y % P)


def _hq(data):
    return int.from_bytes(hashlib.sha512(data).digest(), "little") % Q


def _expand(seed):
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def ed25519_public(seed):
    return _compress(_mul(_expand(seed)[0], G))


def ed25519_sign(seed, msg):
    a, prefix = _expand(seed)
    pub = _compress(_mul(a, G))
    r = _hq(prefix + msg)
    big_r = _compress(_mul(r, G))
    s = (r + _hq(big_r + pub + msg) * a) % Q
    return big_r + s.to_bytes(32, "little")


def ed25519_verify(pub, msg, sig, strict=True):
    """strict=False exists only for the wrong-implementation self-test."""
    if len(pub) != 32 or len(sig) != 64:
        return False
    a = _decompress(pub)
    r = _decompress(sig[:32])
    if a is None or r is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if strict:
        if s >= Q or _equal(_mul(8, a), IDENTITY):
            return False
    return _equal(_mul(s % Q if not strict else s, G), _add(r, _mul(_hq(sig[:32] + pub + msg), a)))


# ------------------------------------------------------------------ helpers

def strict_loads(text):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise Dup(key)
            out[key] = value
        return out

    def constant(value):
        raise ValueError("non-finite number")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def load_fixture(rel):
    return strict_loads((HERE / rel).read_text(encoding="utf-8"))["object"]


def jcs(value):
    # Restricted RFC 8785: the fixtures use strings, booleans, null and non-negative integers only.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pae(payload_type, body):
    t = payload_type.encode("utf-8")
    return b"DSSEv1 %d %s %d %s" % (len(t), t, len(body), body)


def b64d(text):
    """Standard or URL-safe base64; DSSE says verifiers MUST accept either (S7)."""
    if not isinstance(text, str):
        return None
    try:
        if "-" in text or "_" in text:
            return base64.b64decode(text, altchars=b"-_", validate=True)
        return base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError, TypeError):
        return None


def keyid(pub):
    return sha(pub)[:16]


def possession_digest(nonce_hex, artifact):
    return sha(POSSESSION_DOMAIN + bytes.fromhex(nonce_hex) + len(artifact).to_bytes(8, "big") + artifact)


def catalogue_commitment(nonce, catalogue):
    return sha(CATALOGUE_DOMAIN + nonce + len(catalogue).to_bytes(8, "big") + catalogue)


def parse_time(text):
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def fmt_time(value):
    return None if value is None else value.strftime("%Y-%m-%dT%H:%M:%SZ")


def load_source(ref):
    """Resolve 'path#selector' to bytes. Selectors: an extraction vector id (its inputBase64),
    or a JSON pointer starting with '/' (the JCS bytes of that value; design section 9)."""
    path, _, sel = ref.partition("#")
    data = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if sel.startswith("/"):
        for part in sel[1:].split("/"):
            data = data[int(part)] if isinstance(data, list) else data[part]
        return jcs(data)
    for vector in data["vectors"]:
        if vector.get("id") == sel:
            return base64.b64decode(vector["inputBase64"])
    raise KeyError(ref)


def walk_keys(value, path=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, path + "/" + key
            yield from walk_keys(item, path + "/" + key)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from walk_keys(item, f"{path}/{i}")


def shape(obj, spec, code, out):
    required, optional = spec
    if not isinstance(obj, dict) or not required <= set(obj) or set(obj) - required - optional:
        out.add(code)
        return False
    return True


# ------------------------------------------------------------------ statements

def check_statement(st, artifacts, out):
    if not isinstance(st, dict) or set(st) != {"_type", "subject", "predicateType", "predicate"}:
        out.add("statement-shape")
        return
    if st["_type"] != STATEMENT_TYPE:
        out.add("statement-shape")
    if st["predicateType"] != PREDICATE_TYPE:
        out.add("predicate-type")
        return
    subjects = st["subject"]
    if not isinstance(subjects, list) or not 1 <= len(subjects) <= 64:
        out.add("statement-shape")
        return
    seen = set()
    for s in subjects:
        if not isinstance(s, dict) or set(s) != {"name", "digest"} or not isinstance(s["digest"], dict) \
                or set(s["digest"]) != {"sha256"} or not HEX64.match(str(s["digest"]["sha256"])):
            out.add("statement-shape")
            return
        if not SUBJECT_NAME.match(str(s["name"])):
            out.add("subject-name")
        if s["digest"]["sha256"] in seen:
            out.add("statement-shape")
        seen.add(s["digest"]["sha256"])
    pred = st["predicate"]
    if not isinstance(pred, dict):
        out.add("statement-shape")
        return
    for key, _ in walk_keys(pred):
        if key in FORBIDDEN_KEYS:
            out.add("forbidden-field")
        if key in TIME_KEYS:
            out.add("time-in-statement")
    allowed = {"registrationVersion", "contentKind", "nonce", "possession", "catalogue", "implementation", "specCommit", "claims"}
    required = {"registrationVersion", "contentKind", "nonce", "possession", "implementation", "specCommit"}
    if not required <= set(pred) or set(pred) - allowed - FORBIDDEN_KEYS - TIME_KEYS:
        out.add("statement-shape")
        return
    if pred["registrationVersion"] != REGISTRATION_VERSION or pred["contentKind"] not in ("text", "source-code", "image", "other"):
        out.add("statement-shape")
    nonce = pred["nonce"]
    if not isinstance(nonce, str) or not HEX64.match(nonce) or nonce == "0" * 64:
        out.add("nonce-invalid")
        nonce = None
    impl = pred["implementation"]
    if not isinstance(impl, dict) or set(impl) != {"name", "version", "commit"} or not HEX40.match(str(impl.get("commit"))) \
            or not HEX40.match(str(pred["specCommit"])):
        out.add("provenance-shape")
    poss = pred["possession"]
    if not isinstance(poss, list) or len(poss) != len(subjects):
        out.add("statement-shape")
        poss = []
    for i, entry in enumerate(poss):
        if not isinstance(entry, dict) or set(entry) != {"subjectIndex", "scheme", "sha256"} or entry["subjectIndex"] != i \
                or entry["scheme"] != POSSESSION_SCHEME or not HEX64.match(str(entry["sha256"])):
            out.add("statement-shape")
            continue
        if artifacts.get(i) is not None and nonce and possession_digest(nonce, artifacts[i]) != entry["sha256"]:
            out.add("possession-mismatch")
    if "catalogue" in pred:
        cat = pred["catalogue"]
        if not isinstance(cat, dict) or set(cat) != {"scheme", "sha256", "profile"} or not HEX64.match(str(cat.get("sha256"))):
            out.add("statement-shape")
        elif cat["scheme"] != CATALOGUE_SCHEME:
            out.add("catalogue-unsalted")
    if "claims" in pred:
        claims = pred["claims"]
        if not isinstance(claims, dict) or set(claims) - {"createdAt"} or not TIME.match(str(claims.get("createdAt", ""))):
            out.add("statement-shape")
    for i, s in enumerate(subjects):
        if artifacts.get(i) is not None and sha(artifacts[i]) != s["digest"]["sha256"]:
            out.add("subject-mismatch")


# ------------------------------------------------------------------ envelopes and evidence

def read_keys(material, out):
    keys = {}
    entries = material.get("publicKeys") if isinstance(material, dict) else None
    if not isinstance(entries, list) or not entries:
        out.add("envelope-shape")
        return keys
    for k in entries:
        if not isinstance(k, dict) or set(k) != {"keyid", "alg", "publicKeyHex"} or k["alg"] != "ed25519":
            out.add("envelope-shape")
            continue
        pub = bytes.fromhex(k["publicKeyHex"])
        if keyid(pub) != k["keyid"]:
            out.add("envelope-shape")
        keys[k["keyid"]] = pub
    return keys


def open_envelope(env, keys, out):
    """Design section 10 steps 1-2. Key lookup: the keyid hint must name a key in the bundle; a missing or
    unmatched hint is `unknown-key` (no trial verification). Identity is SHA-256 of the full key (B3)."""
    if not isinstance(env, dict) or set(env) != {"payloadType", "payload", "signatures"} or env["payloadType"] != PAYLOAD_TYPE:
        out.add("envelope-shape")
        return None
    payload = b64d(env["payload"])
    sigs = env["signatures"]
    if payload is None or not isinstance(sigs, list) or not sigs:
        out.add("envelope-shape")
        return None
    sig_bytes, outcomes, kids, digests = [], [], [], []
    for s in sigs:
        raw = b64d(s.get("sig")) if isinstance(s, dict) else None
        if raw is None or set(s) - {"keyid", "sig"}:
            out.add("envelope-shape")
            return None
        sig_bytes.append(raw)
        kids.append(s.get("keyid"))
        pub = keys.get(s.get("keyid"))
        digests.append(sha(pub) if pub else None)
        if pub is None:
            outcomes.append("unknown-key")
            out.add("signature-invalid")
        elif ed25519_verify(pub, pae(PAYLOAD_TYPE, payload), raw):
            outcomes.append("valid")
        else:
            outcomes.append("invalid")
            out.add("signature-invalid")
    known = [d for d in digests if d]
    if len(known) != len(set(known)):
        out.add("envelope-shape")  # one key signs once per envelope
    try:
        st = strict_loads(payload.decode("utf-8"))
    except Dup:
        out.add("duplicate-key")
        return None
    except (ValueError, UnicodeDecodeError):
        out.add("statement-shape")
        return None
    return payload, st, sig_bytes, outcomes, kids, digests


def token_bytes(ev):
    if not isinstance(ev, dict):
        return None
    if ev.get("placeholder") is False:
        return b64d(ev.get("token"))
    return str(ev.get("token")).encode("utf-8")


def check_evidence(ev, sig_bytes, out, tokens=None):
    """Structural, target and producer-obligation checks (design section 6). Returns a summary dict or None."""
    base = {"evidenceVersion", "type", "placeholder", "notice", "target", "root", "token"}
    if not isinstance(ev, dict) or ev.get("type") not in EVIDENCE_TYPES or ev.get("evidenceVersion") != EVIDENCE_VERSION:
        out.add("evidence-shape")
        return None
    root_kind, body_key = EVIDENCE_TYPES[ev["type"]]
    real = ev.get("placeholder") is False
    extra = set(ev) - base
    allowed_extra = ({"request"} if ev["type"] == "rfc3161" else set()) if real else {body_key, "statedTime"}
    if not base <= set(ev) or extra - allowed_extra:
        out.add("evidence-shape")
        return None
    if real:
        if ev["notice"] != REAL_NOTICE or ev["type"] not in ("rfc3161", "opentimestamps"):
            out.add("placeholder-unlabelled")
    elif ev["placeholder"] is not True or ev["notice"] != PLACEHOLDER_NOTICE or not str(ev["token"]).startswith("PLACEHOLDER"):
        out.add("placeholder-unlabelled")
    tgt, root = ev["target"], ev["root"]
    if isinstance(tgt, dict) and tgt.get("kind") == "evidence-token" and ev["type"] == "rfc3161" and tokens is not None:
        if set(tgt) != {"kind", "evidenceIndex", "sha256"} or not isinstance(tgt["evidenceIndex"], int) \
                or not 0 <= tgt["evidenceIndex"] < len(tokens):
            out.add("evidence-shape")
            return None
        target = ("evidence", tgt["evidenceIndex"])
        if tokens[tgt["evidenceIndex"]] is None or sha(tokens[tgt["evidenceIndex"]]) != tgt["sha256"]:
            out.add("evidence-wrong-target")
    elif not isinstance(tgt, dict) or set(tgt) != {"kind", "signatureIndex", "sha256"} or tgt["kind"] != "dsse-signature" \
            or not isinstance(tgt["signatureIndex"], int) or not 0 <= tgt["signatureIndex"] < len(sig_bytes):
        out.add("evidence-shape")
        return None
    else:
        target = ("sig", tgt["signatureIndex"])
        if sha(sig_bytes[tgt["signatureIndex"]]) != tgt["sha256"]:
            out.add("evidence-wrong-target")
    if not isinstance(root, dict) or set(root) != {"kind", "anchorSha256"} or not HEX64.match(str(root.get("anchorSha256"))):
        out.add("root-not-anchored")
        return None
    if root["kind"] != root_kind:
        out.add("evidence-shape")
        return None
    s = {"type": ev["type"], "target": target, "anchors": [root["anchorSha256"]], "kind": root_kind, "pending": False,
         "time": None, "accuracy": None, "policyOid": None, "cert": None, "real": real, "inner": None}
    if "statedTime" in ev:
        out.add("log-time-claimed" if ev["type"] == "rekor-v2" else "evidence-shape")
        return None
    if real:
        return check_real_evidence(ev, tgt["sha256"], s, out)
    body = ev.get(body_key)
    if ev["type"] == "rekor-v2":
        if not isinstance(body, dict) or set(body) - {"logIndex"}:
            out.add("evidence-shape")
            return None
        return s
    if not isinstance(body, dict):
        out.add("evidence-shape")
        return None
    if ev["type"] == "traceweave-witness":
        return check_witness_evidence(body, tgt["sha256"], s, out)
    if ev["type"] == "opentimestamps":
        status = body.get("status")
        if status == "pending":
            if set(body) != {"status"}:
                out.add("pending-counted")
            s["pending"] = True
            return s
        if status != "complete" or set(body) != {"status", "blockTime"} or not TIME.match(str(body["blockTime"])):
            out.add("evidence-shape")
            return None
        s["time"] = parse_time(body["blockTime"]) + OTS_MARGIN
        return s
    req = {"genTime", "policyOid", "nonce", "requestNonce", "signerCertificate"}
    if not req <= set(body) or set(body) - req - {"accuracySeconds"} or not TIME.match(str(body["genTime"])) \
            or not OID.match(str(body["policyOid"])) or not HEX16.match(str(body["nonce"])) or not HEX16.match(str(body["requestNonce"])) \
            or not isinstance(body.get("accuracySeconds", 0), int) or not isinstance(body["signerCertificate"], dict) \
            or set(body["signerCertificate"]) != {"notBefore", "notAfter"} \
            or not all(TIME.match(str(v)) for v in body["signerCertificate"].values()):
        out.add("evidence-shape")
        return None
    if body["nonce"] != body["requestNonce"]:
        out.add("tsa-nonce-mismatch")
    s.update(time=parse_time(body["genTime"]), accuracy=body.get("accuracySeconds"), policyOid=body["policyOid"],
             cert=(parse_time(body["signerCertificate"]["notBefore"]), parse_time(body["signerCertificate"]["notAfter"])))
    return s


def check_real_evidence(ev, target_sha, s, out):
    """Real-format vectors (design 6.5): every field is read from the token or proof, never from the evidence."""
    data = b64d(ev["token"])
    if data is None:
        out.add("evidence-shape")
        return None
    try:
        if ev["type"] == "rfc3161":
            request = RF.parse_request(b64d(ev["request"])) if b64d(ev.get("request")) else None
            fields = RF.parse_response(data)
            signer = RF.check_token(fields, target_sha, request)
            s.update(time=fields["genTime"], accuracy=fields["accuracy"], policyOid=fields["policyOid"],
                     cert=(signer.not_before, signer.not_after), signer=signer, certs=fields["certs"])
            return s
        digest, atts = RF.ots_parse(data)
        if digest.hex() != target_sha:
            out.add("evidence-wrong-target")
            return None
        s["ots"] = [(int(RF._Reader(p).varuint()), c) for k, p, c in atts if k == RF.OTS_BITCOIN]
        s["pending"] = not s["ots"] and any(k == RF.OTS_PENDING for k, _, _ in atts)
        return s
    except RF.Bad as bad:
        out.add(bad.code)
        return None


def check_witness_evidence(body, target_sha, s, out):
    """A hosted witness's statement as time evidence (S4): its bound comes from its own TSA token, so it
    depends on two anchors: the witness key and that TSA."""
    if set(body) != {"bundle"}:
        out.add("evidence-shape")
        return None
    inner_out = set()
    w = check_witness_bundle(body["bundle"], target_sha, inner_out)
    out.update(inner_out)
    if w is None or not w["inner"]:
        return None
    if w["keyDigest"] != s["anchors"][0]:
        out.add("evidence-shape")
        return None
    s["inner"] = w["inner"]
    s["anchors"] = s["anchors"] + [e["anchors"][0] for e in w["inner"]]
    return s


def check_bundle(bundle, artifacts, out, statement_check=None):
    statement_check = statement_check or check_statement
    if not isinstance(bundle, dict) or set(bundle) != {"bundleVersion", "envelope", "verificationMaterial", "timeEvidence"} \
            or bundle["bundleVersion"] != BUNDLE_VERSION or not isinstance(bundle["timeEvidence"], list):
        out.add("envelope-shape")
        return None
    keys = read_keys(bundle["verificationMaterial"], out)
    opened = open_envelope(bundle["envelope"], keys, out)
    if opened is None:
        return None
    payload, st, sig_bytes, sig_outcomes, kids, digests = opened
    statement_check(st, artifacts, out)
    tokens = [token_bytes(ev) for ev in bundle["timeEvidence"]]
    evidence = [check_evidence(ev, sig_bytes, out, tokens) for ev in bundle["timeEvidence"]]
    return {"payload": payload, "statement": st, "sigs": sig_bytes, "sigOutcomes": sig_outcomes, "keyids": kids,
            "keyDigests": digests, "keys": keys, "evidence": evidence}


# ------------------------------------------------------------------ verification (design section 10)

def find_root(policy, anchor, kind):
    return next((r for r in policy["timeRoots"] if r["anchorSha256"] == anchor and r["kind"] == kind), None)


def evidence_outcome(i, summaries, policy, simulated, memo=None):
    """Returns (outcome, notAfter or None) for summary i under the policy; renewals are looked up in summaries."""
    memo = {} if memo is None else memo
    if i in memo:
        return memo[i]
    e = summaries[i]
    memo[i] = result = _outcome(i, e, summaries, policy, simulated, memo)
    return result


def _final(e, simulated, not_after):
    if e["real"]:
        return "valid", not_after
    return ("placeholder-assumed-valid", not_after) if simulated else ("placeholder", None)


def _outcome(i, e, summaries, policy, simulated, memo):
    if e is None:
        return "invalid", None
    if e["pending"]:
        return "pending", None
    root = find_root(policy, e["anchors"][0], e["kind"])
    if root is None:
        return "untrusted-root", None
    if e["type"] == "traceweave-witness":
        inner = e["inner"]
        sub = list(inner)
        best = None
        for j, ie in enumerate(sub):
            o, t = _outcome(None, ie, sub, policy, simulated, {})
            if o in COUNTED and t is not None and (best is None or t < best[1]):
                best = (o, t)
        if best is None:
            return "invalid", None
        return _final(e, simulated, best[1])
    if e["type"] == "opentimestamps":
        if not e["real"]:
            return _final(e, simulated, e["time"])
        if "headerFile" not in root:
            return "unsupported", None
        try:
            chain = RF.headers_from_file((HERE / root["headerFile"]).read_bytes())
        except RF.Bad:
            return "untrusted-root", None
        if not chain or sha(chain[0]) != root["anchorSha256"]:
            return "untrusted-root", None
        best = None
        for height, commitment in e["ots"]:
            if height >= len(chain) or not RF.header_ok(chain, height) or chain[height][36:68] != commitment:
                continue
            if len(chain) - 1 - height < root.get("minConfirmations", 6):
                return "insufficient-confirmations", None
            t = RF.header_time(chain[height]) + OTS_MARGIN
            best = t if best is None else min(best, t)
        return ("invalid", None) if best is None else ("valid", best)
    if e["type"] == "rekor-v2":
        return _final(e, simulated, None)
    # rfc3161, placeholder or real
    if e["real"]:
        if "rootCertificate" not in root:
            return "unsupported", None
        try:
            root_cert = RF.Cert((HERE / root["rootCertificate"]).read_bytes())
        except RF.Bad:
            return "untrusted-root", None
        if root_cert.sha256() != root["anchorSha256"]:
            return "untrusted-root", None
        if not RF.chain_to_root(e["signer"], e["certs"], root_cert):
            return "invalid", None
    if e["policyOid"] not in root.get("policyOids", []):
        return "wrong-policy", None
    if not e["cert"][0] <= e["time"] <= e["cert"][1]:
        return "invalid", None
    data = next((rd for rd in policy["revocationData"] if rd["anchorSha256"] == e["anchors"][0]), None)
    if data is None:
        return "no-revocation-data", None
    for rev in data["revocations"]:
        # RFC 3161 section 4 items 1-2: no reasonCode, or keyCompromise, invalidates every token of that key.
        if rev["reasonCode"] not in RETAIN_REASONS or e["time"] >= parse_time(rev["revokedAt"]):
            return "revoked", None
    accuracy = e["accuracy"] if e["accuracy"] is not None else root.get("accuracySeconds")
    if accuracy is None:
        return "unsupported", None
    if parse_time(policy["verificationTime"]) > e["cert"][1]:
        # Renewal (design 6.6, RFC 4998 timestamp renewal): a valid token over this token's bytes,
        # bounded no later than the expiry of this token's TSA certificate.
        renewed = False
        for j, other in enumerate(summaries):
            if i is not None and other is not None and other["target"] == ("evidence", i):
                o, t = evidence_outcome(j, summaries, policy, simulated, memo)
                if o in COUNTED and t is not None and t <= e["cert"][1]:
                    renewed = True
        if not renewed:
            return "expired-unrenewed", None
    return _final(e, simulated, e["time"] + timedelta(seconds=accuracy))


def independence_classes(policy, counted):
    """Union-find over the policy's independence groups (S4): an evidence that rests on several anchors
    joins their groups, so two evidences sharing any group count once."""
    groups = {r["anchorSha256"]: r["independenceGroup"] for r in policy["timeRoots"]}
    parent = {}

    def find(g):
        parent.setdefault(g, g)
        while parent[g] != g:
            parent[g] = parent[parent[g]]
            g = parent[g]
        return g

    for e in counted:
        gs = [groups.get(a, "unlisted:" + a) for a in e["anchors"]]
        for g in gs[1:]:
            parent[find(g)] = find(gs[0])
    return lambda e: find(groups.get(e["anchors"][0], "unlisted:" + e["anchors"][0]))


def signature_bounds(summaries, outcomes, policy, n_sigs):
    """Per-signature bounds (F1); classes from the policy's groups (F2, S4); renewals do not count."""
    counted = [(e, t) for e, (o, t) in zip(summaries, outcomes)
               if e is not None and o in COUNTED and t is not None and e["target"][0] == "sig"]
    cls = independence_classes(policy, [e for e, _ in counted])
    per_sig = [dict() for _ in range(n_sigs)]
    for e, t in counted:
        c = cls(e)
        m = per_sig[e["target"][1]]
        m[c] = t if c not in m else min(m[c], t)
    out = []
    for gmap in per_sig:
        b = sorted(gmap.values())
        q = policy["quorum"]
        out.append({"anyRoot": b[0] if b else None, "quorum": b[q - 1] if len(b) >= q else None, "distinct": len(b)})
    return out


def outcomes_for(ctx, policy, simulated):
    memo = {}
    return [evidence_outcome(i, ctx["evidence"], policy, simulated, memo) for i in range(len(ctx["evidence"]))]


FAR = datetime.max.replace(tzinfo=timezone.utc)


def load_events(event_paths, policy, simulated, out):
    evs = []
    for rel in event_paths:
        bundle = load_fixture(rel)
        inner = set()
        ctx = check_bundle(bundle, {}, inner, statement_check=lambda st, a, o: check_key_event_statement(st, o))
        if ctx is None or inner - {"signature-invalid"}:
            out.add("key-event-shape")
            continue
        pred = ctx["statement"]["predicate"]
        bound = signature_bounds(ctx["evidence"], outcomes_for(ctx, policy, simulated), policy, len(ctx["sigs"]))[0]
        evs.append({"hash": sha(ctx["payload"]), "file": sha((HERE / rel).read_bytes()),
                    "target": ctx["statement"]["subject"][0]["digest"]["sha256"], "signer": ctx["keyDigests"][0],
                    "event": pred["event"], "E": bound["quorum"], "sigok": ctx["sigOutcomes"][0] == "valid",
                    "claimed": parse_time(pred["compromisedNotBefore"]) if "compromisedNotBefore" in pred else None,
                    "successor": sha(bytes.fromhex(pred["successorPublicKeyHex"])) if "successorPublicKeyHex" in pred else None})
    return evs


def evaluate_events(evs, policy):
    """Order-independent (B2): events are taken in order of proved time E, ties by payload digest, and an
    event may rely only on events with a smaller E. Iterated until nothing changes, because a later
    compromise can dispute an earlier rotation (B1)."""
    lookback = timedelta(seconds=policy["compromiseLookbackSeconds"])
    order = sorted(evs, key=lambda e: (e["E"] or FAR, e["hash"]))
    disputed, state, applied = set(), None, []
    for _ in range(len(order) + 2):
        applied = []
        for e in order:
            if not e["sigok"] or e["E"] is None:
                continue
            if e["signer"] == e["target"] or any(
                    r["event"] == "rotated" and r["target"] == e["target"] and r["successor"] == e["signer"]
                    and r["E"] < e["E"] and r["hash"] not in disputed for r in applied):
                applied.append(e)
        new = set()
        for c in applied:
            if c["event"] == "compromised":
                start = max(c["claimed"], c["E"] - lookback)
                for r in applied:
                    if r is not c and r["target"] == c["target"] and r["event"] in ("rotated", "retired") and r["E"] >= start:
                        new.add(r["hash"])
        successors = {}
        for r in applied:
            if r["event"] == "rotated":
                successors.setdefault(r["target"], set()).add(r["successor"])
        for r in applied:
            if r["event"] == "rotated" and len(successors[r["target"]]) > 1:
                new.add(r["hash"])  # conflicting rotations of one key
        key = (tuple(e["hash"] for e in applied), frozenset(new))
        if key == state:
            break
        state, disputed = key, new
    applied_hashes = {e["hash"] for e in applied}
    results = []
    for e in order:
        if not e["sigok"]:
            o = "invalid-signature"
        elif e["E"] is None:
            o = "ignored-no-proved-time"
        elif e["hash"] in disputed:
            o = "disputed"
        elif e["hash"] in applied_hashes:
            o = "applied"
        else:
            o = "ignored-unauthorized"
        results.append({"eventSha256": e["hash"], "keySha256": e["target"], "event": e["event"], "outcome": o,
                        "provedAt": fmt_time(e["E"])})
    ok = [e for e in applied if e["hash"] not in disputed]
    return results, ok, applied


def signer_trust(digest, sig_outcome, bound, policy, ok_events, all_applied):
    if sig_outcome != "valid":
        return "not-evaluated"
    b = bound["quorum"]  # S1: event decisions use the quorum bound only
    trusted_from = {k: None for k in policy["trustedKeys"]}
    for r in sorted((e for e in ok_events if e["event"] == "rotated"), key=lambda e: (e["E"], e["hash"])):
        if r["target"] in trusted_from and r["successor"] not in trusted_from:
            trusted_from[r["successor"]] = r["E"]
    if digest not in trusted_from:
        return "untrusted"
    affected = any(e["target"] == digest or e["successor"] == digest for e in all_applied)
    if affected and b is None:
        return "disputed"
    since = trusted_from[digest]
    if since is not None and (b is None or b < since):
        return "untrusted"
    status = "trusted"
    lookback = timedelta(seconds=policy["compromiseLookbackSeconds"])
    for e in ok_events:
        if e["target"] != digest:
            continue
        if e["event"] == "compromised":
            start = max(e["claimed"], e["E"] - lookback)
            if b is None or b >= e["E"]:
                status = "untrusted"
            elif b >= start and status == "trusted":
                status = "disputed"
        elif b is None or b >= e["E"]:
            status = "untrusted"
    return status


def expected_result(ctx, artifacts, policy, simulated, bundle_sha, event_paths, out):
    st = ctx["statement"]
    pred = st["predicate"]
    outs = outcomes_for(ctx, policy, simulated)
    ev_out = []
    for i, (e, (o, t)) in enumerate(zip(ctx["evidence"], outs)):
        target = None if e is None else ({"signatureIndex": e["target"][1]} if e["target"][0] == "sig" else {"evidenceIndex": e["target"][1]})
        rd = None if e is None else next((r for r in policy["revocationData"] if r["anchorSha256"] == e["anchors"][0]), None)
        ev_out.append({"index": i, "target": target, "type": e["type"] if e else None, "anchorSha256": e["anchors"][0] if e else None,
                       "outcome": o, "notAfter": fmt_time(t), "revocationDataAsOf": rd["asOf"] if rd and e["type"] == "rfc3161" else None})
    bounds = signature_bounds(ctx["evidence"], outs, policy, len(ctx["sigs"]))
    ke_out, ok_events, all_applied = evaluate_events(load_events(event_paths, policy, simulated, out), policy)
    trust = [signer_trust(d, o, b, policy, ok_events, all_applied) for d, o, b in zip(ctx["keyDigests"], ctx["sigOutcomes"], bounds)]
    time = []
    for i, (kid, d, b) in enumerate(zip(ctx["keyids"], ctx["keyDigests"], bounds)):
        valid_sig = ctx["sigOutcomes"][i] == "valid"
        time.append({"signatureIndex": i, "keyid": kid, "keySha256": d,
                     "outcome": ("quorum-met" if b["quorum"] else ("below-quorum" if b["anyRoot"] else "none-valid")) if valid_sig else "none-valid",
                     "quorum": policy["quorum"], "distinctRoots": b["distinct"] if valid_sig else 0,
                     "notAfterAnyRoot": fmt_time(b["anyRoot"]) if valid_sig else None,
                     "notAfterQuorum": fmt_time(b["quorum"]) if valid_sig else None})
    # S11: compare only with signatures whose signer is trusted.
    compared = min((b["anyRoot"] for b, tr in zip(bounds, trust) if b["anyRoot"] and tr == "trusted"), default=None)
    created = pred.get("claims", {}).get("createdAt")
    if created is None:
        status = "absent"
    elif compared is None:
        status = "not-compared"
    else:
        status = "after-proved-bound" if parse_time(created) > compared else "claimed-only"
    subj, poss = [], []
    for i, s in enumerate(st["subject"]):
        art = artifacts.get(i)
        subj.append({"index": i, "outcome": "not-supplied" if art is None else ("match" if sha(art) == s["digest"]["sha256"] else "mismatch")})
        poss.append({"index": i, "outcome": "not-supplied" if art is None else
                     ("match" if possession_digest(pred["nonce"], art) == pred["possession"][i]["sha256"] else "mismatch")})
    return {
        "resultVersion": RESULT_VERSION,
        "simulated": simulated,
        "inputs": {"bundleSha256": bundle_sha, "artifacts": [{"subjectIndex": i, "sha256": sha(a)} for i, a in sorted(artifacts.items())],
                   "keyEvents": sorted(sha((HERE / p).read_bytes()) for p in event_paths)},
        "policy": policy,
        "outcomes": {
            "envelope": "ok",
            "statement": "ok",
            "signatures": [{"index": i, "keyid": k, "keySha256": d, "outcome": o}
                           for i, (k, d, o) in enumerate(zip(ctx["keyids"], ctx["keyDigests"], ctx["sigOutcomes"]))],
            "keyEvents": ke_out,
            "signerTrust": [{"index": i, "outcome": t} for i, t in enumerate(trust)],
            "subjects": subj,
            "possession": poss,
            "catalogue": "not-supplied" if "catalogue" in pred else "not-committed",
            "timeEvidence": ev_out,
            "time": time,
            "claimedCreatedAt": {"value": created, "status": status, "comparedWith": fmt_time(compared)},
        },
        "notShown": NOT_SHOWN,
    }


POLICY_KEYS = {"quorum", "timeRoots", "trustedKeys", "revocationData", "compromiseLookbackSeconds", "verificationTime"}
ROOT_KEYS = {"anchorSha256", "kind", "independenceGroup", "accuracySeconds", "policyOids", "rootCertificate", "headerFile", "minConfirmations"}


def check_policy(policy, out):
    if not isinstance(policy, dict):
        out.add("result-mismatch")
        return False
    if "trustedKeyids" in policy or any(HEX16.match(str(k)) for k in policy.get("trustedKeys", [])):
        out.add("key-identity-by-hint")  # B3: trust is by SHA-256 of the full key, never the 64-bit hint
        return False
    if set(policy) != POLICY_KEYS or not isinstance(policy["quorum"], int) or policy["quorum"] < 1 \
            or not all(HEX64.match(str(k)) for k in policy["trustedKeys"]) or not TIME.match(str(policy["verificationTime"])):
        out.add("result-mismatch")
        return False
    for r in policy["timeRoots"]:
        if not isinstance(r, dict) or not {"anchorSha256", "kind", "independenceGroup"} <= set(r) or set(r) - ROOT_KEYS:
            out.add("root-not-anchored" if isinstance(r, dict) and "id" in r else "result-mismatch")
            return False
        if not HEX64.match(str(r["anchorSha256"])):
            out.add("root-not-anchored")
            return False
    for rd in policy["revocationData"]:
        if set(rd) != {"anchorSha256", "source", "asOf", "revocations"} or not TIME.match(str(rd["asOf"])) \
                or any(set(rev) != {"revokedAt", "reasonCode"} or rev["reasonCode"] not in ALL_REASONS for rev in rd["revocations"]):
            out.add("result-mismatch")
            return False
    return True


def check_result(res, meta, out):
    for key, _ in walk_keys(res):
        k = key.lower()
        if k in SINGLE_VERDICT_KEYS:
            out.add("single-verdict")
        if k in AUTHORSHIP_KEYS:
            out.add("authorship-claim")
    if not isinstance(res, dict) or res.get("notShown") != NOT_SHOWN:
        out.add("notice-missing")
    if not check_policy(res.get("policy"), out):
        return
    bundle_path = HERE / meta["bundle"]
    bundle = strict_loads(bundle_path.read_text(encoding="utf-8"))["object"]
    artifacts = {a["subjectIndex"]: load_source(a["source"]) for a in meta.get("artifacts", [])}
    inner = set()
    ctx = check_bundle(bundle, artifacts, inner)
    if ctx is None or inner - {"subject-mismatch", "possession-mismatch", "signature-invalid"}:
        out.add("result-mismatch")
        return
    exp = expected_result(ctx, artifacts, res["policy"], res.get("simulated"), sha(bundle_path.read_bytes()),
                          meta.get("keyEvents", []), out)
    got_o, exp_o = res.get("outcomes", {}), exp["outcomes"]
    got_t, exp_t = got_o.get("time", []), exp_o["time"]
    claimed = exp_o["claimedCreatedAt"]["value"]
    for g, w in zip(got_t, exp_t):
        if claimed and claimed in (g.get("notAfterAnyRoot"), g.get("notAfterQuorum")) and claimed not in (w["notAfterAnyRoot"], w["notAfterQuorum"]):
            out.add("claimed-as-proved")
        if g.get("keyid") != w["keyid"] or g.get("keySha256") != w["keySha256"] \
                or (not w["notAfterAnyRoot"] and (g.get("notAfterAnyRoot") or g.get("notAfterQuorum"))):
            out.add("key-bound-misattributed")
        elif g.get("distinctRoots") != w["distinctRoots"] or (g.get("notAfterQuorum") and not w["notAfterQuorum"]):
            out.add("quorum-miscount")
    if len(got_t) != len(exp_t):
        out.add("key-bound-misattributed")
    for g, w in zip(got_o.get("timeEvidence", []), exp_o["timeEvidence"]):
        if w["outcome"] == "pending" and g.get("outcome") != "pending":
            out.add("pending-counted")
        if g.get("outcome") not in EVIDENCE_OUTCOMES:
            out.add("result-mismatch")
    for g, w, t in zip(got_o.get("signerTrust", []), exp_o["signerTrust"], exp_t):
        if w["outcome"] == "disputed" and g.get("outcome") == "trusted" and t["notAfterQuorum"] is None:
            out.add("trust-without-quorum")
        elif w["outcome"] in ("disputed", "untrusted") and g.get("outcome") == "trusted" and exp_o["keyEvents"]:
            out.add("key-event-ignored")
    if got_o.get("keyEvents") != exp_o["keyEvents"] and not out:
        out.add("key-event-ignored")
    if res != exp and not out:
        out.add("result-mismatch")


# ------------------------------------------------------------------ link, registration set and rendering

def check_link(link, meta, out):
    keys = {"linkVersion", "report", "registration", "links", "catalogueOpening", "notShown"}
    if not isinstance(link, dict) or set(link) != keys or link["linkVersion"] != LINK_VERSION:
        out.add("fixture-shape")
        return
    if link["notShown"] != NOT_SHOWN:
        out.add("notice-missing")
    report = json.loads((ROOT / link["report"]["path"]).read_text(encoding="utf-8"))
    body = report["body"]
    if sha(jcs(body)) != link["report"]["bodySha256"] or report["provenance"]["bodySha256"] != link["report"]["bodySha256"]:
        out.add("report-digest")
    bundle = load_fixture(link["registration"]["bundle"])
    inner = set()
    ctx = check_bundle(bundle, {}, inner)
    if ctx is None or inner:
        out.add("fixture-shape")
        return
    if sha(ctx["payload"]) != link["registration"]["statementSha256"]:
        out.add("statement-digest")
    st = ctx["statement"]
    for entry in link["links"]:
        pair = body["pairs"][entry["pair"]]
        subject = st["subject"][entry["subjectIndex"]]["digest"]["sha256"]
        if entry["role"] not in ("reference", "candidate") or not (pair[entry["role"]]["sha256"] == entry["sha256"] == subject):
            out.add("subject-mismatch")
    cat = st["predicate"].get("catalogue")
    if cat is not None and cat["profile"] != body["profile"]:
        out.add("profile-mismatch")
    opening = link["catalogueOpening"]
    if opening is not None:
        catalogue = load_source(opening["catalogue"])
        if cat is None or catalogue_commitment(bytes.fromhex(opening["nonceHex"]), catalogue) != cat["sha256"]:
            out.add("catalogue-does-not-open")
        if sha(catalogue) != body["inputs"]["referenceCatalogueSha256"]:
            out.add("catalogue-not-report-input")


def check_set(obj, meta, out):
    """Registrations by one producer: nonces must be fresh (design section 4.2). Only checkable across records."""
    if not isinstance(obj, dict) or set(obj) != {"setVersion", "registrations"} or obj["setVersion"] != SET_VERSION:
        out.add("fixture-shape")
        return
    seen = set()
    for rel in obj["registrations"]:
        inner = set()
        ctx = check_bundle(load_fixture(rel), {}, inner)
        if ctx is None or inner:
            out.add("fixture-shape")
            continue
        nonce = ctx["statement"]["predicate"]["nonce"]
        if nonce in seen:
            out.add("nonce-reused")
        seen.add(nonce)


def check_rendering(ren, meta, out):
    """Allow-list of line templates (design section 11), checked against the result they render."""
    if not isinstance(ren, dict) or not {"renderingVersion", "result", "lines"} <= set(ren) <= {"renderingVersion", "result", "lines", "context"} \
            or ren["renderingVersion"] != RENDERING_VERSION or ren.get("context", "creator") not in ("creator", "agent"):
        out.add("fixture-shape")
        return
    lines = ren["lines"]
    fixed = REQUIRED_SENTENCES + ([AGENT_SENTENCE] if ren.get("context") == "agent" else [])
    for sentence in fixed:
        if sentence not in lines:
            out.add("notice-missing")
    result = load_fixture(ren["result"])
    times = {t["keyid"]: t for t in result["outcomes"]["time"]}
    claimed = result["outcomes"]["claimedCreatedAt"]["value"]
    bound_keys = set()
    for line in lines:
        if line in fixed:
            continue
        kind, m = next(((k, rx.match(line)) for k, rx in TEMPLATES.items() if rx.match(line)), (None, None))
        if kind is None:
            out.add("rendering-unlisted-line")
            if DENY_TEXT.search(line):
                out.add("authorship-claim")
            if ORDER_TEXT.search(line):
                out.add("ordering-claim")
            if re.search(r"(?i)\b(authentic\w*|verified|genuine)\b", line):
                out.add("single-verdict")
            if claimed and claimed in line:
                out.add("claimed-as-proved")
            continue
        if kind == "bound":
            kid, when, single = m.group(1), m.group(2), m.group(3)
            t = times.get(kid)
            expected = None if t is None else (t["notAfterQuorum"] if t["notAfterQuorum"] else t["notAfterAnyRoot"])
            if when == claimed and when != expected:
                out.add("claimed-as-proved")
            elif t is None or expected is None or when != expected or bool(single) != (t["notAfterQuorum"] is None):
                out.add("key-bound-misattributed")
            bound_keys.add(kid)
        elif kind == "sources":
            t = times.get(m.group(1))
            if t is None or (int(m.group(2)), int(m.group(3)), m.group(4)) != (t["distinctRoots"], t["quorum"], t["notAfterAnyRoot"]):
                out.add("key-bound-misattributed")
        elif kind == "claimed" and m.group(1) != claimed:
            out.add("result-mismatch")
    for kid, t in times.items():
        if t["notAfterAnyRoot"] and kid not in bound_keys:
            out.add("notice-missing")


# ------------------------------------------------------------------ key events

def check_key_event_statement(st, out):
    """B3: the event names its target by subject digest = SHA-256 of the raw public key; `keyid` is only a hint
    and must agree with it."""
    pred = st.get("predicate", {}) if isinstance(st, dict) else {}
    subj = st.get("subject") if isinstance(st, dict) else None
    digest = subj[0].get("digest", {}).get("sha256") if isinstance(subj, list) and len(subj) == 1 and isinstance(subj[0], dict) else None
    ok = (isinstance(st, dict) and st.get("predicateType") == KEY_EVENT_TYPE and isinstance(pred, dict)
          and pred.get("eventVersion") == KEY_EVENT_VERSION and pred.get("event") in ("retired", "rotated", "compromised")
          and HEX64.match(str(digest)) and pred.get("keyid") == str(digest)[:16]
          and (pred.get("event") == "rotated") == ("successorPublicKeyHex" in pred)
          and (pred.get("event") == "compromised") == ("compromisedNotBefore" in pred)
          and set(pred) <= {"eventVersion", "keyid", "event", "successorPublicKeyHex", "compromisedNotBefore"})
    if not ok:
        out.add("key-event-shape")


def check_key_event(bundle, meta, out):
    inner = set()
    check_bundle(bundle, {}, inner, statement_check=lambda st, a, o: check_key_event_statement(st, o))
    out.update(inner)


# ------------------------------------------------------------------ A2A and MCP (design section 19)

def check_card(card, meta, out):
    """A2A 1.0 Agent Card, checked against the proto field lists (no published JSON Schema is committed)."""
    if not shape(card, A2A_CARD, "a2a-shape", out):
        return
    caps = card["capabilities"]
    if not shape(caps, A2A_CAPS, "a2a-shape", out):
        return
    exts = [e for e in caps.get("extensions", []) if shape(e, A2A_EXT, "a2a-shape", out) and e["uri"] == A2A_EXTENSION]
    if len(exts) != 1 or exts[0].get("required") is not True or exts[0].get("params", {}).get("wire") not in ("digests-only", "local-only"):
        out.add("a2a-shape")
        return
    wire = exts[0]["params"]["wire"]
    for itf in card["supportedInterfaces"]:
        if not shape(itf, A2A_INTERFACE, "a2a-shape", out):
            continue
        if itf["protocolBinding"] not in ("JSONRPC", "GRPC", "HTTP+JSON") or not re.match(r"^\d+\.\d+$", itf["protocolVersion"]):
            out.add("a2a-shape")
        local = bool(LOOPBACK.match(itf["url"]))
        if (wire == "local-only" and not local) or (wire == "digests-only" and not itf["url"].startswith("https://")):
            out.add("content-on-wire")
    for skill in card["skills"]:
        if not shape(skill, A2A_SKILL, "a2a-shape", out):
            continue
        if SENTENCE_FIRST not in skill["description"]:
            out.add("notice-missing")
        if wire == "digests-only" and set(skill.get("inputModes", card["defaultInputModes"])) - {"application/json"}:
            out.add("content-on-wire")
    if wire == "digests-only" and not card.get("securityRequirements"):
        out.add("a2a-shape")


def check_wire_parts(parts, out):
    for part in parts:
        if not isinstance(part, dict) or len(set(part) & A2A_PART_CONTENT) != 1 or set(part) - A2A_PART_CONTENT - A2A_PART_OTHER:
            out.add("a2a-shape")
            continue
        if "raw" in part or "url" in part:
            out.add("content-on-wire")
        for key, _ in walk_keys(part.get("data")):
            if key in FORBIDDEN_KEYS:
                out.add("forbidden-field")


def check_request(req, meta, out):
    """A2A SendMessageRequest to the hosted witness skill: digests only."""
    if not isinstance(req, dict) or not {"message"} <= set(req) <= {"message", "configuration", "metadata", "tenant"} \
            or not shape(req["message"], A2A_MESSAGE, "a2a-shape", out):
        out.add("a2a-shape")
        return
    msg = req["message"]
    if msg["role"] != "ROLE_USER" or A2A_EXTENSION not in msg.get("extensions", []):
        out.add("a2a-shape")
    check_wire_parts(msg["parts"], out)
    datas = [p["data"] for p in msg["parts"] if isinstance(p, dict) and "data" in p]
    if len(datas) != 1 or not isinstance(datas[0], dict):
        out.add("a2a-shape")
        return
    d = datas[0]
    if d.get("requestVersion") != WITNESS_REQUEST_VERSION or set(d) - {"requestVersion", "presented"} - FORBIDDEN_KEYS \
            or not isinstance(d.get("presented"), dict) or set(d["presented"]) != {"kind", "sha256"} \
            or d["presented"]["kind"] != "dsse-signature-sha256" or not HEX64.match(str(d["presented"]["sha256"])):
        out.add("a2a-shape")
        return
    if meta.get("bundle"):
        bundle = load_fixture(meta["bundle"])
        if d["presented"]["sha256"] != sha(b64d(bundle["envelope"]["signatures"][0]["sig"])):
            out.add("evidence-wrong-target")


def check_witness_bundle(wb, presented, out):
    """Returns {"keyDigest", "inner": [evidence summaries over the witness signature]} or None."""
    if not isinstance(wb, dict) or set(wb) != {"bundleVersion", "envelope", "verificationMaterial", "timeEvidence"}:
        out.add("witness-shape")
        return None
    keys = read_keys(wb["verificationMaterial"], out)
    opened = open_envelope(wb["envelope"], keys, out)
    if opened is None:
        return None
    _, st, sigs, _, _, digests = opened
    pred = st.get("predicate") if isinstance(st, dict) else None
    if st.get("predicateType") != WITNESS_TYPE or not isinstance(pred, dict):
        out.add("witness-shape")
        return None
    for key, _ in walk_keys(pred):
        if key.lower() in AUTHORSHIP_KEYS:
            out.add("authorship-claim")
    allowed = {"witnessVersion", "presentedKind", "receivedAt", "caller", "requestMessageId", "notShown"}
    if set(pred) - allowed - {k for k in pred if k.lower() in AUTHORSHIP_KEYS} or pred.get("witnessVersion") != WITNESS_VERSION \
            or pred.get("presentedKind") != "dsse-signature-sha256" or not TIME.match(str(pred.get("receivedAt"))) \
            or not isinstance(pred.get("caller"), dict) or set(pred["caller"]) != {"scheme", "issuer", "subject"}:
        out.add("witness-shape")
    if pred.get("notShown") != NOT_SHOWN:
        out.add("notice-missing")
    if st["subject"][0]["digest"]["sha256"] != presented:
        out.add("evidence-wrong-target")
    tokens = [token_bytes(ev) for ev in wb["timeEvidence"]]
    inner = [check_evidence(ev, sigs, out, tokens) for ev in wb["timeEvidence"]]
    inner = [e for e in inner if e is not None and e["type"] == "rfc3161" and e["target"][0] == "sig"]
    return {"keyDigest": digests[0], "inner": inner}


def check_task(task, meta, out):
    """A2A Task returned by the hosted witness: one artifact holding the witness bundle."""
    if not shape(task, A2A_TASK, "a2a-shape", out):
        return
    if task["status"].get("state") not in A2A_STATES or set(task["status"]) - {"state", "message", "timestamp"}:
        out.add("a2a-shape")
        return
    req = load_fixture(meta["request"])
    presented = [p["data"] for p in req["message"]["parts"] if "data" in p][0]["presented"]["sha256"]
    arts = task.get("artifacts", [])
    if task["status"]["state"] != "TASK_STATE_COMPLETED" or len(arts) != 1 or not shape(arts[0], A2A_ARTIFACT, "a2a-shape", out):
        out.add("a2a-shape")
        return
    check_wire_parts(arts[0]["parts"], out)
    datas = [p["data"] for p in arts[0]["parts"] if "data" in p]
    if len(datas) != 1:
        out.add("a2a-shape")
        return
    check_witness_bundle(datas[0], presented, out)


def check_mcp_tool(tool, meta, out):
    """MCP 2026-07-28 Tool definition for the local route (stdio). Field names from schema.ts."""
    if not shape(tool, MCP_TOOL, "mcp-tool-shape", out):
        return
    if not MCP_NAME.match(tool["name"]) or tool["inputSchema"].get("type") != "object":
        out.add("mcp-tool-shape")
    if SENTENCE_FIRST not in tool.get("description", ""):
        out.add("notice-missing")
    ann = tool.get("annotations", {})
    if ann.get("readOnlyHint", False) or ann.get("openWorldHint", True) is not True or ann.get("idempotentHint", False) \
            or ann.get("destructiveHint", True) is not False:
        out.add("mcp-tool-shape")
    for key, _ in walk_keys(tool.get("outputSchema", {})):
        if key in FORBIDDEN_KEYS - {"source"}:
            out.add("forbidden-field")


# ------------------------------------------------------------------ driver

CHECKS = {}


def check_object(kind, obj, meta):
    out = set()
    artifacts = {a["subjectIndex"]: load_source(a["source"]) for a in meta.get("artifacts", [])}
    if kind == "statement":
        check_statement(obj, artifacts, out)
    elif kind == "bundle":
        check_bundle(obj, artifacts, out)
    elif kind == "evidence":
        bundle = load_fixture(meta["bundle"])
        check_evidence(obj, [b64d(s["sig"]) for s in bundle["envelope"]["signatures"]], out,
                       [token_bytes(ev) for ev in bundle["timeEvidence"]])
    elif kind in CHECKS:
        CHECKS[kind](obj, meta, out)
    else:
        out.add("fixture-shape")
    return out


CHECKS.update({"verification-result": check_result, "report-link": check_link, "rendering": check_rendering,
               "key-event": check_key_event, "registration-set": check_set, "a2a-agent-card": check_card,
               "a2a-request": check_request, "a2a-task": check_task, "mcp-tool": check_mcp_tool})


def check_file(path):
    try:
        doc = strict_loads(path.read_text(encoding="utf-8"))
    except Dup:
        return {"duplicate-key"}, None
    meta, obj = doc.get("fixture", {}), doc.get("object")
    out = check_object(meta.get("kind"), obj, meta)
    if set(doc) != {"fixture", "object"} or meta.get("notice") != FIXTURE_NOTICE:
        out.add("fixture-shape")
    return out, meta


def self_test():
    # RFC 8032 section 7.1, TEST 1 and TEST 2.
    seed = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    assert ed25519_public(seed).hex() == "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    assert ed25519_sign(seed, b"").hex() == ("e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
                                             "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b")
    seed2 = bytes.fromhex("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb")
    sig2 = ed25519_sign(seed2, b"\x72")
    assert sig2.hex() == ("92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
                          "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00")
    pub2 = ed25519_public(seed2)
    assert ed25519_verify(pub2, b"\x72", sig2)
    assert not ed25519_verify(pub2, b"\x73", sig2)
    assert pae("http://example.com/HelloWorld", b"hello world") == b"DSSEv1 29 http://example.com/HelloWorld 11 hello world"


def wrong_implementation_self_test(verbose):
    """Each entry builds a plausible wrong output in memory; the checker must report at least one code."""
    cases = []
    seed2 = bytes.fromhex("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb")
    sig2 = ed25519_sign(seed2, b"\x72")
    s = int.from_bytes(sig2[32:], "little")
    malleated = sig2[:32] + (s + Q).to_bytes(32, "little")
    pub2 = ed25519_public(seed2)
    small = (1).to_bytes(32, "little")  # the identity point: small order
    forged = small + (0).to_bytes(32, "little")
    cases.append(("lenient Ed25519 accepts S >= L", ed25519_verify(pub2, b"\x72", malleated, strict=False),
                  not ed25519_verify(pub2, b"\x72", malleated)))
    cases.append(("lenient Ed25519 accepts a small-order key with R = identity, S = 0 for any message",
                  ed25519_verify(small, b"any message", forged, strict=False), not ed25519_verify(small, b"any message", forged)))
    noncanon = (P + 1).to_bytes(32, "little")  # y = p + 1, a non-canonical encoding of y = 1
    cases.append(("non-canonical point encoding", True, _decompress(noncanon) is None))

    def mutated(rel, fn):
        doc = strict_loads((HERE / rel).read_text(encoding="utf-8"))
        obj = copy.deepcopy(doc["object"])
        fn(obj)
        return check_object(doc["fixture"]["kind"], obj, doc["fixture"])

    def set_trust(value, index=0):
        def fn(r):
            r["outcomes"]["signerTrust"][index]["outcome"] = value
        return fn

    def set_quorum_to_earliest(r):
        r["outcomes"]["time"][0]["notAfterQuorum"] = r["outcomes"]["time"][0]["notAfterAnyRoot"]

    def statement_level_bound(r):
        r["outcomes"]["time"][1].update({k: r["outcomes"]["time"][0][k] for k in ("notAfterAnyRoot", "notAfterQuorum", "distinctRoots", "outcome")})

    def ignore_key_events(r):
        r["outcomes"]["signerTrust"][0]["outcome"] = "trusted"
        r["outcomes"]["keyEvents"] = []

    def drop_margin(r):
        for e in r["outcomes"]["timeEvidence"]:
            if e["type"] == "opentimestamps" and e["notAfter"]:
                e["notAfter"] = e["notAfter"].replace("13:12:00", "11:12:00")

    def label_roots(r):
        for root in r["policy"]["timeRoots"]:
            root["id"] = "tsa"

    def trust_by_hint(r):
        r["policy"]["trustedKeys"] = [k[:16] for k in r["policy"]["trustedKeys"]]

    def base64_target(e):
        e["target"]["sha256"] = sha(e["token"].encode())  # digest over text, not the raw signature bytes

    def ignore_revocation(r):
        for e in r["outcomes"]["timeEvidence"]:
            if e["outcome"] == "revoked":
                e["outcome"] = "placeholder-assumed-valid"

    def order_dependent(r):
        for e in r["outcomes"]["keyEvents"]:
            if e["event"] == "retired":
                e["outcome"] = "ignored-unauthorized"  # what a list-order evaluator gives when the retirement comes first

    def witness_as_independent(r):
        r["outcomes"]["time"][0].update(distinctRoots=2, outcome="quorum-met", notAfterQuorum="2026-11-23T10:00:04Z")

    def claim_against_any_signer(r):
        r["outcomes"]["claimedCreatedAt"].update(status="after-proved-bound", comparedWith="2026-11-23T10:00:01Z")

    def ignore_expiry(r):
        for e in r["outcomes"]["timeEvidence"]:
            if e["outcome"] == "expired-unrenewed":
                e.update(outcome="placeholder-assumed-valid", notAfter="2026-11-23T10:00:01Z")

    for name, rel, fn in [
        ("two-root bound taken as the earliest", "fixtures/verification-result.json", set_quorum_to_earliest),
        ("co-signer inherits the first signature's bound (W8)", "fixtures/verification-result-cosigned.json", statement_level_bound),
        ("key events ignored (W10)", "fixtures/verification-result-compromise-recent.json", ignore_key_events),
        ("OpenTimestamps margin dropped", "fixtures/verification-result.json", drop_margin),
        ("roots identified by producer labels (W3)", "fixtures/verification-result.json", label_roots),
        ("RFC 3161 revocation ignored", "fixtures/verification-result-revoked.json", ignore_revocation),
        ("target over text instead of signature bytes", "fixtures/evidence-rfc3161.json", base64_target),
        ("successor of a rotation made with a stolen key trusted (B1)", "fixtures/verification-result-rotation-hijack.json", set_trust("trusted")),
        ("successor of conflicting rotations trusted (B1)", "fixtures/verification-result-rotation-conflict.json", set_trust("trusted")),
        ("events evaluated in list order (B2)", "fixtures/verification-result-event-order-a.json", order_dependent),
        ("trust matched on the 64-bit keyid (B3)", "fixtures/verification-result.json", trust_by_hint),
        ("trust decided on one source after a key event (S1)", "fixtures/verification-result-single-source-event.json", set_trust("trusted")),
        ("witness and its TSA counted as two sources (S4)", "fixtures/verification-result-witness-shared-tsa.json", witness_as_independent),
        ("claimed time compared with an untrusted co-signer (S11)", "fixtures/verification-result-claim-trusted-only.json", claim_against_any_signer),
        ("expired TSA certificate accepted without renewal (S6)", "fixtures/verification-result-expired.json", ignore_expiry),
    ]:
        cases.append((name, True, bool(mutated(rel, fn))))
    for line in ["This registration establishes your claim to sum.go.", "sum.go is registered to you as its creator.",
                 "This record proves you wrote sum.go.", "Registered first: sum.go belongs to key cd76d6c6b4bb50ab.",
                 "sum.go was registered before host.go."]:
        got = mutated("fixtures/rendering.json", lambda r, line=line: r["lines"].insert(1, line))
        cases.append((f"rendering {line!r}", True, bool({"authorship-claim", "ordering-claim"} & got)))
    # S7: a verifier that accepts only standard base64 rejects a valid URL-safe envelope.
    doc = strict_loads((HERE / "fixtures/bundle-url-safe.json").read_text(encoding="utf-8"))
    try:
        env = doc["object"]["envelope"]
        for text in [env["payload"]] + [x["sig"] for x in env["signatures"]]:
            base64.b64decode(text, validate=True)
        strict_fails = False
    except (binascii.Error, ValueError):
        strict_fails = True
    cases.append(("standard-only base64 rejects a URL-safe envelope (S7)", strict_fails, not check_file(HERE / "fixtures/bundle-url-safe.json")[0]))
    # S2: a token check that ignores the target accepts a real token over another digest.
    ev = load_fixture("negative/neg-tsa-imprint-mismatch.json")
    fields = RF.parse_response(b64d(ev["token"]))
    lenient = RF.check_token(fields, fields["hash"], None) is not None
    try:
        RF.check_token(fields, ev["target"]["sha256"], None)
        strict = False
    except RF.Bad as bad:
        strict = bad.code == "tsa-imprint-mismatch"
    cases.append(("real RFC 3161 token accepted without the messageImprint check (S2)", lenient, strict))
    failures = 0
    for name, wrong_misbehaves, caught in cases:
        ok = wrong_misbehaves and caught
        failures += not ok
        if verbose or not ok:
            print(f"{'ok  ' if ok else 'FAIL'} wrong-implementation: {name}")
    return failures, len(cases)


def main(argv):
    verbose = "--verbose" in argv
    self_test()
    failures = 0
    counts = {"fixtures": 0, "negative": 0}
    for folder in ("fixtures", "negative"):
        for path in sorted((HERE / folder).glob("*.json")):
            counts[folder] += 1
            got, meta = check_file(path)
            if folder == "fixtures":
                want = set()
            elif meta is None:  # unparseable on purpose: expectation is in the file name
                want = {path.stem.removeprefix("neg-")}
            else:
                expect = meta.get("expect")
                want = {expect["code"], *expect.get("alsoReported", [])} if expect else {"<missing expect>"}
            ok = got == want
            failures += not ok
            if verbose or not ok:
                print(f"{'ok  ' if ok else 'FAIL'} {folder}/{path.name}: got {sorted(got)} want {sorted(want)}")
    wrong_failures, wrong_count = wrong_implementation_self_test(verbose)
    failures += wrong_failures
    text = DOC.read_text(encoding="utf-8")
    missing = [c for c in CODES if f"`{c}`" not in text]
    if missing:
        failures += 1
        print("FAIL doc-drift: codes not in the design document:", ", ".join(missing))
    exercised = set()
    for path in (HERE / "negative").glob("*.json"):
        try:
            exercised.add(strict_loads(path.read_text(encoding="utf-8"))["fixture"]["expect"]["code"])
        except Dup:
            exercised.add(path.stem.removeprefix("neg-"))
    unexercised = sorted(set(CODES) - exercised)
    if unexercised:
        failures += 1
        print("FAIL codes without a negative fixture:", ", ".join(unexercised))
    print(f"{counts['fixtures']} positive fixtures, {counts['negative']} negative fixtures, {wrong_count} wrong-implementation "
          f"cases, {len(CODES)} codes ({len(CODES) - len(unexercised)} exercised by a negative); "
          f"{'all as expected' if not failures else f'{failures} failure(s)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
