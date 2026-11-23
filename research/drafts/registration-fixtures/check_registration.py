#!/usr/bin/env python3
"""Check the illustrative registration-record fixtures against ../registration-record.md.

Standard library only; Python 3.11 or later. This is not a registration verifier.
It verifies the fixtures' Ed25519 signatures (a public, test-only key) and the
structural rules of the design. It never verifies a time-stamp token, an
OpenTimestamps proof, a log entry or a cosignature: every time evidence here is a
labelled placeholder, and the checker rejects one that is not labelled.

Every fixture in fixtures/ must produce no failure code. Every fixture in
negative/ must produce exactly its expected code (plus any listed in
expect.alsoReported). The run also checks that every failure code appears in the
design document, so the two cannot drift apart.

Usage: python3 -I check_registration.py [--verbose]
Exit status 0 when every fixture behaves as expected, 1 otherwise.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOC = HERE.parent / "registration-record.md"

STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PAYLOAD_TYPE = "application/vnd.in-toto+json"
PREDICATE_TYPE = "https://traceweave.org/predicate/registration/draft-1"
KEY_EVENT_TYPE = "https://traceweave.org/predicate/key-event/draft-1"
REGISTRATION_VERSION = "traceweave-registration-draft-1"
BUNDLE_VERSION = "traceweave-registration-bundle-draft-1"
EVIDENCE_VERSION = "traceweave-time-evidence-draft-1"
RESULT_VERSION = "traceweave-registration-verification-draft-1"
LINK_VERSION = "traceweave-registration-link-draft-1"
RENDERING_VERSION = "traceweave-registration-rendering-draft-1"
KEY_EVENT_VERSION = "traceweave-key-event-draft-1"
WITNESS_TYPE = "https://traceweave.org/predicate/witness/draft-1"
WITNESS_VERSION = "traceweave-witness-draft-1"
WITNESS_REQUEST_VERSION = "traceweave-witness-request-draft-1"
A2A_EXTENSION = "https://traceweave.org/a2a/ext/registration/draft-1"
POSSESSION_SCHEME = "sha256-salted-possession-v1"
POSSESSION_DOMAIN = b"Traceweave-Possession-v1\x00"
CATALOGUE_SCHEME = "sha256-salted-catalogue-v1"
CATALOGUE_DOMAIN = b"Traceweave-Catalogue-v0.1\x00"

FIXTURE_NOTICE = ("Illustrative fixture for research/drafts/registration-record.md. Synthetic data and a public "
                  "test-only key; it registers nothing and proves nothing.")
PLACEHOLDER_NOTICE = ("PLACEHOLDER. Not a real time-stamp token, proof, log entry or cosignature. No service issued "
                      "it and it cannot be verified. Times in it are invented for illustration.")
NOT_SHOWN = ["authorship", "originality", "first-creation", "ownership", "permission"]
REQUIRED_SENTENCES = [
    "This record shows that the content existed, and that this key signed a statement naming it, no later than the time shown.",
    "It does not show who created the content, that it is original, that the registrant was first to create it, or who owns it.",
    "First to register is not first to create.",
]
AGENT_SENTENCE = ("A registration made by or through an agent shows which key signed it and, for a hosted witness, which "
                  "authenticated caller presented the digest; it does not show whether a person or an agent created the "
                  "content, or on whose behalf.")

EVIDENCE_ROOT = {"rfc3161": "tsa-certificate-chain", "opentimestamps": "bitcoin-proof-of-work",
                 "rekor-v2": "log-key", "cosigned-checkpoint": "witness-key"}
OTS_MARGIN = timedelta(seconds=7200)

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SUBJECT_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SINGLE_VERDICT_KEYS = {"authentic", "isauthentic", "verdict", "overall", "overallresult", "verified"}
AUTHORSHIP_KEYS = {"author", "authorship", "owner", "ownership", "creator", "original", "originality"}
FORBIDDEN_KEYS = {"fingerprints", "tokens", "source", "text", "content", "catalogueBytes", "opening", "nonceHex", "inputBase64"}
TIME_KEYS = {"provedAt", "timestamp", "notAfter", "genTime", "registeredAt", "recordedAt", "time", "provedTime"}
AUTHORSHIP_TEXT = re.compile(
    r"(?i)\b(prove[sd]?|proof|establish(es|ed)?|confirm(s|ed)?|show(s|n)?|demonstrat(es|ed))\b[^.]*"
    r"\b(author(ship)?|own(s|er|ership)?|original(ity)?|creat(ed|or)|copyright)\b")
NEGATED = re.compile(r"(?i)\b(does not|do not|is not|cannot|never|not)\b")

CODES = [
    "authorship-claim", "catalogue-does-not-open", "catalogue-not-report-input", "catalogue-unsalted",
    "claimed-as-proved", "duplicate-key", "envelope-shape", "evidence-shape", "evidence-wrong-target",
    "fixture-shape", "forbidden-field", "key-event-shape", "log-time-claimed", "nonce-invalid", "notice-missing",
    "pending-counted", "placeholder-unlabelled", "possession-mismatch", "predicate-type", "profile-mismatch",
    "provenance-shape", "quorum-miscount", "report-digest", "result-mismatch", "signature-invalid",
    "single-verdict", "statement-digest", "statement-shape", "subject-mismatch", "subject-name",
    "time-in-statement", "content-on-wire", "a2a-shape", "mcp-tool-shape", "witness-shape",
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


# ------------------------------------------------------------------ Ed25519 (RFC 8032 section 5.1)

P = 2 ** 255 - 19
Q = 2 ** 252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
SQRT_M1 = pow(2, (P - 1) // 4, P)


def _add(a, b):
    x = (a[1] - a[0]) * (b[1] - b[0]) % P
    y = (a[1] + a[0]) * (b[1] + b[0]) % P
    c = 2 * a[3] * b[3] * D % P
    d = 2 * a[2] * b[2] % P
    e, f, g, h = y - x, d - c, d + c, y + x
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _mul(s, pt):
    acc = (0, 1, 1, 0)
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
        return None
    x2 = (y * y - 1) * pow(D * y * y + 1, P - 2, P) % P
    if x2 == 0:
        return None if sign else 0
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


def ed25519_verify(pub, msg, sig):
    if len(pub) != 32 or len(sig) != 64:
        return False
    a = _decompress(pub)
    r = _decompress(sig[:32])
    if a is None or r is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= Q:
        return False
    return _equal(_mul(s, G), _add(r, _mul(_hq(sig[:32] + pub + msg), a)))


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


def jcs(value):
    # Restricted RFC 8785: the fixtures use strings, booleans, null and non-negative integers only.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pae(payload_type, body):
    t = payload_type.encode("utf-8")
    return b"DSSEv1 %d %s %d %s" % (len(t), t, len(body), body)


def b64d(text):
    try:
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
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def load_source(ref):
    """Resolve 'path#selector' to bytes. Selectors: an extraction vector id (its inputBase64),
    or a JSON pointer starting with '/' (canonical bytes of that value)."""
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

def open_envelope(env, keys, out):
    """Return (payload bytes, statement, list of signature bytes or None per signature, outcomes)."""
    if not isinstance(env, dict) or set(env) != {"payloadType", "payload", "signatures"} or env["payloadType"] != PAYLOAD_TYPE:
        out.add("envelope-shape")
        return None
    payload = b64d(env["payload"])
    sigs = env["signatures"]
    if payload is None or not isinstance(sigs, list) or not sigs:
        out.add("envelope-shape")
        return None
    sig_bytes, outcomes = [], []
    for s in sigs:
        raw = b64d(s.get("sig")) if isinstance(s, dict) else None
        if raw is None or set(s) != {"keyid", "sig"}:
            out.add("envelope-shape")
            return None
        sig_bytes.append(raw)
        pub = keys.get(s["keyid"])
        if pub is None:
            outcomes.append("unknown-key")
            out.add("signature-invalid")
        elif ed25519_verify(pub, pae(PAYLOAD_TYPE, payload), raw):
            outcomes.append("valid")
        else:
            outcomes.append("invalid")
            out.add("signature-invalid")
    try:
        st = strict_loads(payload.decode("utf-8"))
    except Dup:
        out.add("duplicate-key")
        return None
    except (ValueError, UnicodeDecodeError):
        out.add("statement-shape")
        return None
    return payload, st, sig_bytes, outcomes


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


def check_evidence(ev, sig_bytes, out):
    """Structural and target checks. Returns (notAfter or None, pending flag)."""
    base = {"evidenceVersion", "type", "placeholder", "notice", "target", "root", "token"}
    if not isinstance(ev, dict) or not base <= set(ev) or ev.get("type") not in EVIDENCE_ROOT \
            or ev.get("evidenceVersion") != EVIDENCE_VERSION:
        out.add("evidence-shape")
        return None, False
    if ev["placeholder"] is not True or ev["notice"] != PLACEHOLDER_NOTICE or not str(ev["token"]).startswith("PLACEHOLDER"):
        out.add("placeholder-unlabelled")
    tgt, root = ev["target"], ev["root"]
    if not isinstance(tgt, dict) or set(tgt) != {"kind", "signatureIndex", "sha256"} or tgt["kind"] != "dsse-signature" \
            or not isinstance(tgt["signatureIndex"], int) or not 0 <= tgt["signatureIndex"] < len(sig_bytes):
        out.add("evidence-shape")
        return None, False
    if sha(sig_bytes[tgt["signatureIndex"]]) != tgt["sha256"]:
        out.add("evidence-wrong-target")
    if not isinstance(root, dict) or set(root) != {"kind", "id"} or root["kind"] != EVIDENCE_ROOT[ev["type"]]:
        out.add("evidence-shape")
        return None, False
    kind = ev["type"]
    extra = set(ev) - base
    stated = ev.get("statedTime")
    if kind == "rekor-v2":
        if "statedTime" in ev:
            out.add("log-time-claimed")
        if extra - {"statedTime", "logIndex"}:
            out.add("evidence-shape")
        return None, False
    if kind == "opentimestamps":
        status = ev.get("status")
        if status not in ("complete", "pending") or extra - {"statedTime", "status"}:
            out.add("evidence-shape")
            return None, False
        if status == "pending":
            if "statedTime" in ev:
                out.add("pending-counted")
            return None, True
        if not isinstance(stated, dict) or set(stated) != {"blockTime"} or not TIME.match(str(stated["blockTime"])):
            out.add("evidence-shape")
            return None, False
        return parse_time(stated["blockTime"]) + OTS_MARGIN, False
    if kind == "rfc3161":
        if extra != {"statedTime"} or not isinstance(stated, dict) or set(stated) != {"genTime", "accuracySeconds"} \
                or not TIME.match(str(stated["genTime"])) or not isinstance(stated["accuracySeconds"], int):
            out.add("evidence-shape")
            return None, False
        return parse_time(stated["genTime"]) + timedelta(seconds=stated["accuracySeconds"]), False
    if extra != {"statedTime"} or not isinstance(stated, dict) or set(stated) != {"cosignatureTime"} \
            or not TIME.match(str(stated["cosignatureTime"])):
        out.add("evidence-shape")
        return None, False
    return parse_time(stated["cosignatureTime"]), False


def check_bundle(bundle, artifacts, out):
    """Returns a context dict for later checks, or None."""
    if not isinstance(bundle, dict) or set(bundle) != {"bundleVersion", "envelope", "verificationMaterial", "timeEvidence"} \
            or bundle["bundleVersion"] != BUNDLE_VERSION or not isinstance(bundle["timeEvidence"], list):
        out.add("envelope-shape")
        return None
    keys = read_keys(bundle["verificationMaterial"], out)
    opened = open_envelope(bundle["envelope"], keys, out)
    if opened is None:
        return None
    payload, st, sig_bytes, sig_outcomes = opened
    check_statement(st, artifacts, out)
    evidence = []
    for ev in bundle["timeEvidence"]:
        not_after, pending = check_evidence(ev, sig_bytes, out)
        evidence.append((ev, not_after, pending))
    return {"payload": payload, "statement": st, "sigs": sig_bytes, "sigOutcomes": sig_outcomes,
            "keyids": [s["keyid"] for s in bundle["envelope"]["signatures"]], "evidence": evidence}


# ------------------------------------------------------------------ verification result

def expected_result(ctx, artifacts, policy, simulated, bundle_sha):
    st = ctx["statement"]
    pred = st["predicate"]
    subjects = st["subject"]
    ev_out, per_root = [], {}
    for ev, not_after, pending in ctx["evidence"]:
        root = ev["root"]["id"]
        if pending:
            outcome = "pending"
        elif root not in policy["acceptedRoots"]:
            outcome = "untrusted-root"
        else:
            outcome = "placeholder-assumed-valid" if simulated else "placeholder"
        counted = outcome in ("valid", "placeholder-assumed-valid")
        ev_out.append({"index": len(ev_out), "type": ev["type"], "root": root, "outcome": outcome,
                       "notAfter": fmt_time(not_after) if counted and not_after else None})
        if counted and not_after:
            per_root[root] = min(per_root.get(root, not_after), not_after)
    bounds = sorted(per_root.values())
    q = policy["quorum"]
    any_root = fmt_time(bounds[0]) if bounds else None
    quorum = fmt_time(bounds[q - 1]) if len(bounds) >= q else None
    time = {"outcome": "quorum-met" if quorum else ("below-quorum" if bounds else "none-valid"),
            "quorum": q, "distinctRoots": len(bounds), "notAfterAnyRoot": any_root, "notAfterQuorum": quorum}
    created = pred.get("claims", {}).get("createdAt")
    if created is None:
        claim = {"value": None, "status": "absent"}
    elif any_root and parse_time(created) > bounds[0]:
        claim = {"value": created, "status": "after-proved-bound"}
    else:
        claim = {"value": created, "status": "claimed-only"}
    subj, poss = [], []
    for i, s in enumerate(subjects):
        art = artifacts.get(i)
        subj.append({"index": i, "outcome": "not-supplied" if art is None else ("match" if sha(art) == s["digest"]["sha256"] else "mismatch")})
        poss.append({"index": i, "outcome": "not-supplied" if art is None else
                     ("match" if possession_digest(pred["nonce"], art) == pred["possession"][i]["sha256"] else "mismatch")})
    return {
        "resultVersion": RESULT_VERSION,
        "simulated": simulated,
        "inputs": {"bundleSha256": bundle_sha, "artifacts": [{"subjectIndex": i, "sha256": sha(a)} for i, a in sorted(artifacts.items())]},
        "policy": policy,
        "outcomes": {
            "envelope": "ok",
            "statement": "ok",
            "signatures": [{"index": i, "keyid": k, "outcome": o} for i, (k, o) in enumerate(zip(ctx["keyids"], ctx["sigOutcomes"]))],
            "signerTrust": [{"index": i, "outcome": ("trusted" if k in policy["trustedKeyids"] else "untrusted") if o == "valid" else "not-evaluated"}
                            for i, (k, o) in enumerate(zip(ctx["keyids"], ctx["sigOutcomes"]))],
            "subjects": subj,
            "possession": poss,
            "catalogue": "not-supplied" if "catalogue" in pred else "not-committed",
            "timeEvidence": ev_out,
            "time": time,
            "claimedCreatedAt": claim,
        },
        "notShown": NOT_SHOWN,
    }


def check_result(res, meta, out):
    for key, _ in walk_keys(res):
        k = key.lower()
        if k in SINGLE_VERDICT_KEYS:
            out.add("single-verdict")
        if k in AUTHORSHIP_KEYS:
            out.add("authorship-claim")
    if not isinstance(res, dict) or res.get("notShown") != NOT_SHOWN:
        out.add("notice-missing")
    bundle_path = HERE / meta["bundle"]
    bundle = strict_loads(bundle_path.read_text(encoding="utf-8"))["object"]
    artifacts = {a["subjectIndex"]: load_source(a["source"]) for a in meta.get("artifacts", [])}
    inner = set()
    ctx = check_bundle(bundle, artifacts, inner)
    if ctx is None or inner - {"subject-mismatch", "possession-mismatch"}:
        out.add("result-mismatch")
        return
    exp = expected_result(ctx, artifacts, res.get("policy", {}), res.get("simulated"), sha(bundle_path.read_bytes()))
    if not isinstance(res.get("policy"), dict) or set(res["policy"]) != {"quorum", "acceptedRoots", "trustedKeyids"}:
        out.add("result-mismatch")
        return
    got_o, exp_o = res.get("outcomes", {}), exp["outcomes"]
    got_t, exp_t = got_o.get("time", {}), exp_o["time"]
    claimed = exp_o["claimedCreatedAt"]["value"]
    if claimed and claimed in (got_t.get("notAfterAnyRoot"), got_t.get("notAfterQuorum")) and claimed not in (exp_t["notAfterAnyRoot"], exp_t["notAfterQuorum"]):
        out.add("claimed-as-proved")
    for got, want in zip(got_o.get("timeEvidence", []), exp_o["timeEvidence"]):
        if want["outcome"] == "pending" and got.get("outcome") != "pending":
            out.add("pending-counted")
    if got_t.get("distinctRoots") != exp_t["distinctRoots"] or (got_t.get("notAfterQuorum") and not exp_t["notAfterQuorum"]):
        out.add("quorum-miscount")
    if res != exp and not out:
        out.add("result-mismatch")


# ------------------------------------------------------------------ link and rendering

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
    bundle = strict_loads((HERE / link["registration"]["bundle"]).read_text(encoding="utf-8"))["object"]
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


def check_rendering(ren, meta, out):
    if not isinstance(ren, dict) or not {"renderingVersion", "result", "lines"} <= set(ren) <= {"renderingVersion", "result", "lines", "context"} \
            or ren["renderingVersion"] != RENDERING_VERSION or ren.get("context", "creator") not in ("creator", "agent"):
        out.add("fixture-shape")
        return
    lines = ren["lines"]
    required = REQUIRED_SENTENCES + ([AGENT_SENTENCE] if ren.get("context") == "agent" else [])
    for sentence in required:
        if sentence not in lines:
            out.add("notice-missing")
    result = strict_loads((HERE / ren["result"]).read_text(encoding="utf-8"))["object"]
    claimed = result["outcomes"]["claimedCreatedAt"]["value"]
    for line in lines:
        if line in REQUIRED_SENTENCES or line == AGENT_SENTENCE:
            continue
        if AUTHORSHIP_TEXT.search(line) and not NEGATED.search(line):
            out.add("authorship-claim")
        if re.search(r"(?i)\bauthentic(ated|ity)?\b|\bverified\b(?!\s+separately)", line):
            out.add("single-verdict")
        if claimed and claimed in line and "claimed" not in line.lower():
            out.add("claimed-as-proved")


def shape(obj, spec, code, out):
    required, optional = spec
    if not isinstance(obj, dict) or not required <= set(obj) or set(obj) - required - optional:
        out.add(code)
        return False
    return True


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
        if REQUIRED_SENTENCES[2] not in skill["description"]:
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
        bundle = strict_loads((HERE / meta["bundle"]).read_text(encoding="utf-8"))["object"]
        if d["presented"]["sha256"] != sha(b64d(bundle["envelope"]["signatures"][0]["sig"])):
            out.add("evidence-wrong-target")


def check_witness_bundle(wb, presented, out):
    if not isinstance(wb, dict) or set(wb) != {"bundleVersion", "envelope", "verificationMaterial", "timeEvidence"}:
        out.add("witness-shape")
        return
    keys = read_keys(wb["verificationMaterial"], out)
    opened = open_envelope(wb["envelope"], keys, out)
    if opened is None:
        return
    _, st, sigs, _ = opened
    pred = st.get("predicate") if isinstance(st, dict) else None
    if st.get("predicateType") != WITNESS_TYPE or not isinstance(pred, dict):
        out.add("witness-shape")
        return
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
    for ev in wb["timeEvidence"]:
        check_evidence(ev, sigs, out)


def check_task(task, meta, out):
    """A2A Task returned by the hosted witness: one artifact holding the witness bundle."""
    if not shape(task, A2A_TASK, "a2a-shape", out):
        return
    if task["status"].get("state") not in A2A_STATES or set(task["status"]) - {"state", "message", "timestamp"}:
        out.add("a2a-shape")
        return
    req = strict_loads((HERE / meta["request"]).read_text(encoding="utf-8"))["object"]
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
    if REQUIRED_SENTENCES[2] not in tool.get("description", ""):
        out.add("notice-missing")
    ann = tool.get("annotations", {})
    # Registration contacts time services and adds a new record each call.
    if ann.get("readOnlyHint", False) or ann.get("openWorldHint", True) is not True or ann.get("idempotentHint", False) \
            or ann.get("destructiveHint", True) is not False:
        out.add("mcp-tool-shape")
    for key, _ in walk_keys(tool.get("outputSchema", {})):
        if key in FORBIDDEN_KEYS - {"source"}:
            out.add("forbidden-field")


def check_key_event(bundle, meta, out):
    inner = set()
    if not isinstance(bundle, dict) or set(bundle) != {"bundleVersion", "envelope", "verificationMaterial", "timeEvidence"}:
        out.add("key-event-shape")
        return
    keys = read_keys(bundle["verificationMaterial"], inner)
    opened = open_envelope(bundle["envelope"], keys, inner)
    out.update(inner & {"signature-invalid", "duplicate-key", "envelope-shape"})
    if opened is None:
        return
    _, st, sig_bytes, _ = opened
    pred = st.get("predicate", {}) if isinstance(st, dict) else {}
    if st.get("predicateType") != KEY_EVENT_TYPE or pred.get("eventVersion") != KEY_EVENT_VERSION \
            or pred.get("event") not in ("retired", "rotated", "compromised") or pred.get("keyid") not in keys \
            or (pred.get("event") == "rotated") != ("successorPublicKeyHex" in pred) \
            or (pred.get("event") == "compromised") != ("compromisedNotBefore" in pred):
        out.add("key-event-shape")
    for ev in bundle["timeEvidence"]:
        check_evidence(ev, sig_bytes, out)


# ------------------------------------------------------------------ driver

def check_file(path):
    out = set()
    try:
        doc = strict_loads(path.read_text(encoding="utf-8"))
    except Dup:
        return {"duplicate-key"}, None
    meta, obj = doc.get("fixture", {}), doc.get("object")
    if set(doc) != {"fixture", "object"} or meta.get("notice") != FIXTURE_NOTICE:
        out.add("fixture-shape")
    artifacts = {a["subjectIndex"]: load_source(a["source"]) for a in meta.get("artifacts", [])}
    kind = meta.get("kind")
    if kind == "statement":
        check_statement(obj, artifacts, out)
    elif kind == "bundle":
        check_bundle(obj, artifacts, out)
    elif kind == "evidence":
        bundle = strict_loads((HERE / meta["bundle"]).read_text(encoding="utf-8"))["object"]
        sigs = [b64d(s["sig"]) for s in bundle["envelope"]["signatures"]]
        check_evidence(obj, sigs, out)
    elif kind == "verification-result":
        check_result(obj, meta, out)
    elif kind == "report-link":
        check_link(obj, meta, out)
    elif kind == "rendering":
        check_rendering(obj, meta, out)
    elif kind == "a2a-agent-card":
        check_card(obj, meta, out)
    elif kind == "a2a-request":
        check_request(obj, meta, out)
    elif kind == "a2a-task":
        check_task(obj, meta, out)
    elif kind == "mcp-tool":
        check_mcp_tool(obj, meta, out)
    elif kind == "key-event":
        check_key_event(obj, meta, out)
    else:
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
    assert ed25519_verify(ed25519_public(seed2), b"\x72", sig2)
    assert not ed25519_verify(ed25519_public(seed2), b"\x73", sig2)
    assert pae("http://example.com/HelloWorld", b"hello world") == b"DSSEv1 29 http://example.com/HelloWorld 11 hello world"


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
            else:
                expect = (meta or {}).get("expect") if meta else None
                if meta is None:  # unparseable on purpose: expectation is in the file name
                    want = {path.stem.removeprefix("neg-")}
                else:
                    want = {expect["code"], *expect.get("alsoReported", [])} if expect else {"<missing expect>"}
            ok = got == want
            failures += not ok
            if verbose or not ok:
                print(f"{'ok  ' if ok else 'FAIL'} {folder}/{path.name}: got {sorted(got)} want {sorted(want)}")
    text = DOC.read_text(encoding="utf-8")
    missing = [c for c in CODES if f"`{c}`" not in text]
    if missing:
        failures += 1
        print("FAIL doc-drift: codes not in the design document:", ", ".join(missing))
    unused = set(CODES)
    for path in (HERE / "negative").glob("*.json"):
        try:
            unused.discard(strict_loads(path.read_text(encoding="utf-8"))["fixture"]["expect"]["code"])
        except Dup:
            unused.discard(path.stem.removeprefix("neg-"))
    print(f"{counts['fixtures']} positive fixtures, {counts['negative']} negative fixtures, "
          f"{len(CODES)} codes ({len(CODES) - len(unused)} exercised by a negative); "
          f"{'all as expected' if not failures else f'{failures} failure(s)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
