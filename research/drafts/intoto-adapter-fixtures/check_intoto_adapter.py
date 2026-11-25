#!/usr/bin/env python3
"""Check the Traceweave <-> in-toto Statement v1 / DSSE adapter fixtures.

Standard library only; Python 3.11 or later.
Verifies DSSE envelopes (base64 standard & URL-safe, PAE over exact decoded
payload bytes, strict RFC 8032 cofactorless Ed25519 signatures, explicit
trusted-key digests with zero reliance on keyid hints), strict JSON parsing
(rejecting duplicate keys and non-finite constants), Traceweave adapter
schemas (core catalogue-commitment and registration draft-5 statements),
subject/commitment bindings, smuggling protections, and canonical round-tripping.

Usage: python3 -I research/drafts/intoto-adapter-fixtures/check_intoto_adapter.py [--verbose]
Exit status 0 when every accept and reject fixture and self-test passes, 1 otherwise.
"""

from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
DSSE_PAYLOAD_TYPE = "application/vnd.in-toto+json"
CORE_PREDICATE_TYPE = (
    "https://github.com/connorburgess/traceweave-spec/blob/main/spec/core.md#evidence-0.1.0-draft.1"
)
REG_PREDICATE_TYPE = "https://traceweave.org/predicate/registration/draft-5"
CORE_SPEC_VERSION = "0.1.0-draft.1"
REG_VERSION = "traceweave-registration-draft-5"
CATALOGUE_SCHEME = "sha256-salted-catalogue-v1"
POSSESSION_SCHEME = "sha256-salted-possession-v1"
CATALOGUE_DOMAIN = b"Traceweave-Catalogue-v0.1\x00"
POSSESSION_DOMAIN = b"Traceweave-Possession-v1\x00"

CORE_CONTENT_KINDS = {"code", "text", "image", "audio", "binary", "other"}
REG_CONTENT_KINDS = {"text", "source-code", "image", "other"}
AI_USE_DECLARED = {"generated", "modified", "no-generative-ai"}

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX16 = re.compile(r"^[0-9a-f]{16}$")
REG_SUBJECT_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
UTC_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
AI_TOOL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,63}$")

AUTHORSHIP_KEYS = {"author", "authorship", "owner", "ownership", "creator", "original", "originality"}
TIME_KEYS = {"provedAt", "timestamp", "notAfter", "genTime", "registeredAt", "time", "provedTime"}
FORBIDDEN_KEYS = {
    "privateKey",
    "fingerprints",
    "tokens",
    "source",
    "text",
    "content",
    "catalogueBytes",
    "opening",
    "nonceHex",
    "inputBase64",
}
HUMAN_ORIGIN_PARTS = {
    "human",
    "humans",
    "humanly",
    "person",
    "people",
    "handwritten",
    "handmade",
    "hand",
    "manual",
    "manually",
    "penned",
    "pen",
    "written",
    "wrote",
    "typed",
    "authored",
    "author",
    "by",
    "me",
    "myself",
    "self",
    "mine",
    "organic",
    "natural",
    "real",
    "genuine",
    "original",
}
NEGATION_PARTS = {"no", "not", "non", "none", "never", "without", "zero", "free", "nil", "null", "only"}
AUTHORSHIP_DENY = re.compile(
    r"(?i)\b(author\w*|wrote|written|belongs?|yours?|claim to|registered to you|first to create|"
    r"priority|creat(ed|or|ion of)|own(s|ed|er|ership)?|original\w*|copyright|prove[sdn]?|proof|"
    r"establish\w*|authentic\w*|verified|genuine|legitimate)\b"
)
SMUGGLED_VALUE_PHRASES = re.compile(
    r"(?i)\b(written by (a )?human|human[- ]written|human[- ]made|created by|owned by|belongs to|copyright)\b"
)

ALL_CODES = frozenset(
    {
        "authorship-claim",
        "catalogue-mismatch",
        "dsse-payload-type",
        "dsse-shape",
        "duplicate-key",
        "extra-field",
        "fixture-shape",
        "forbidden-field",
        "invalid-base64",
        "missing-required-field",
        "possession-mismatch",
        "predicate-type",
        "round-trip-mismatch",
        "signature-invalid",
        "statement-shape",
        "statement-type",
        "subject-count",
        "subject-digest-mismatch",
        "time-in-statement",
        "unknown-key",
        "untrusted-signer",
    }
)


class DupKeyError(ValueError):
    pass


# ------------------------------------------------------------------ strict Ed25519 (RFC 8032 5.1.7)

P = 2**255 - 19
Q = 2**252 + 27742317777372353535851937790883648493
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


def ed25519_public(seed: bytes) -> bytes:
    return _compress(_mul(_expand(seed)[0], G))


def ed25519_sign(seed: bytes, msg: bytes) -> bytes:
    a, prefix = _expand(seed)
    pub = _compress(_mul(a, G))
    r = _hq(prefix + msg)
    big_r = _compress(_mul(r, G))
    s = (r + _hq(big_r + pub + msg) * a) % Q
    return big_r + s.to_bytes(32, "little")


def ed25519_verify(pub: bytes, msg: bytes, sig: bytes) -> bool:
    if len(pub) != 32 or len(sig) != 64:
        return False
    a = _decompress(pub)
    r = _decompress(sig[:32])
    if a is None or r is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= Q or _equal(_mul(8, a), IDENTITY):
        return False
    return _equal(_mul(s, G), _add(r, _mul(_hq(sig[:32] + pub + msg), a)))


# ------------------------------------------------------------------ JSON, base64, PAE, commitments

def strict_loads(text: str):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise DupKeyError(f"Duplicate JSON key: {key}")
            out[key] = value
        return out

    def bad_const(value):
        raise ValueError(f"Non-finite JSON constant: {value}")

    return json.loads(text, object_pairs_hook=pairs, parse_constant=bad_const)


def jcs(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dsse_pae(payload_type: bytes, body: bytes) -> bytes:
    return (
        b"DSSEv1 "
        + str(len(payload_type)).encode("ascii")
        + b" "
        + payload_type
        + b" "
        + str(len(body)).encode("ascii")
        + b" "
        + body
    )


def b64d(text) -> bytes | None:
    if not isinstance(text, str) or not text:
        return None
    if any(ch.isspace() for ch in text):
        return None
    has_std = "+" in text or "/" in text
    has_url = "-" in text or "_" in text
    if has_std and has_url:
        return None
    try:
        if has_url:
            return base64.b64decode(text, altchars=b"-_", validate=True)
        return base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError, TypeError):
        return None


def is_iso_datetime(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return "T" in value
    except ValueError:
        return False


def catalogue_commitment(nonce: bytes, catalogue_bytes: bytes) -> str:
    if len(nonce) != 32:
        raise ValueError("Catalogue nonce must be 32 bytes")
    return sha256_hex(CATALOGUE_DOMAIN + nonce + len(catalogue_bytes).to_bytes(8, "big") + catalogue_bytes)


def possession_digest(nonce_hex: str, artifact_bytes: bytes) -> str:
    return sha256_hex(
        POSSESSION_DOMAIN + bytes.fromhex(nonce_hex) + len(artifact_bytes).to_bytes(8, "big") + artifact_bytes
    )


def load_source(ref: str) -> bytes:
    path, _, sel = ref.partition("#")
    target = (ROOT / path).resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError(f"Source path escapes repository: {ref}")
    if not sel:
        return target.read_bytes()
    data = strict_loads(target.read_text(encoding="utf-8"))
    if sel.startswith("/"):
        for part in sel[1:].split("/"):
            data = data[int(part)] if isinstance(data, list) else data[part]
        return jcs(data)
    for vector in data.get("vectors", []):
        if vector.get("id") == sel:
            return base64.b64decode(vector["inputBase64"])
    raise KeyError(f"Selector not found: {ref}")


def token_parts(token: str) -> list[str]:
    out = []
    for chunk in re.split(r"[._+\-]+", token):
        out.extend(w.lower() for w in re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+", chunk))
    return out


def tool_has_origin_claim(token: str) -> bool:
    parts = token_parts(token)
    joined = " ".join(parts)
    if AUTHORSHIP_DENY.search(joined):
        return True
    if set(parts) & (HUMAN_ORIGIN_PARTS | NEGATION_PARTS):
        return True
    return False


# ------------------------------------------------------------------ adapter encode / decode

def adapter_decode(statement: dict) -> dict:
    """Decode a validated Traceweave in-toto Statement v1 into normalized adapter fields."""
    ptype = statement["predicateType"]
    subjects = [
        {"name": item["name"], "sha256": item["digest"]["sha256"]}
        for item in statement["subject"]
    ]
    pred = statement["predicate"]
    if ptype == CORE_PREDICATE_TYPE:
        record = {
            "adapterKind": "catalogue",
            "predicateType": ptype,
            "subjects": subjects,
            "specVersion": pred["specVersion"],
            "contentKind": pred["contentKind"],
            "profile": copy.deepcopy(pred["profile"]),
            "catalogueCommitment": copy.deepcopy(pred["catalogueCommitment"]),
        }
        if "recordedAt" in pred:
            record["recordedAt"] = pred["recordedAt"]
        return record
    if ptype == REG_PREDICATE_TYPE:
        record = {
            "adapterKind": "registration",
            "predicateType": ptype,
            "subjects": subjects,
            "registrationVersion": pred["registrationVersion"],
            "contentKind": pred["contentKind"],
            "nonce": pred["nonce"],
            "possession": copy.deepcopy(pred["possession"]),
            "implementation": copy.deepcopy(pred["implementation"]),
            "specCommit": pred["specCommit"],
            "claims": copy.deepcopy(pred["claims"]),
        }
        if "catalogue" in pred:
            record["catalogue"] = copy.deepcopy(pred["catalogue"])
        return record
    raise ValueError(f"Unsupported predicateType: {ptype}")


def adapter_encode(record: dict) -> dict:
    """Encode a normalized Traceweave adapter record into an in-toto Statement v1."""
    kind = record["adapterKind"]
    subjects = [
        {"name": item["name"], "digest": {"sha256": item["sha256"]}}
        for item in record["subjects"]
    ]
    if kind == "catalogue":
        predicate = {
            "specVersion": record["specVersion"],
            "contentKind": record["contentKind"],
            "profile": copy.deepcopy(record["profile"]),
            "catalogueCommitment": copy.deepcopy(record["catalogueCommitment"]),
        }
        if "recordedAt" in record:
            predicate["recordedAt"] = record["recordedAt"]
        return {
            "_type": STATEMENT_TYPE,
            "subject": subjects,
            "predicateType": CORE_PREDICATE_TYPE,
            "predicate": predicate,
        }
    if kind == "registration":
        predicate = {
            "registrationVersion": record["registrationVersion"],
            "contentKind": record["contentKind"],
            "nonce": record["nonce"],
            "possession": copy.deepcopy(record["possession"]),
            "implementation": copy.deepcopy(record["implementation"]),
            "specCommit": record["specCommit"],
            "claims": copy.deepcopy(record["claims"]),
        }
        if "catalogue" in record:
            predicate["catalogue"] = copy.deepcopy(record["catalogue"])
        return {
            "_type": STATEMENT_TYPE,
            "subject": subjects,
            "predicateType": REG_PREDICATE_TYPE,
            "predicate": predicate,
        }
    raise ValueError(f"Unsupported adapterKind: {kind}")


# ------------------------------------------------------------------ validation

def _scan_smuggling(
    node,
    in_predicate: bool,
    reg_mode: bool,
    codes: set[str],
    in_subject: bool = False,
    in_subject_name: bool = False,
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in AUTHORSHIP_KEYS:
                codes.add("authorship-claim")
            if in_predicate:
                if key in TIME_KEYS or (reg_mode and key == "recordedAt"):
                    codes.add("time-in-statement")
                if key in FORBIDDEN_KEYS:
                    codes.add("forbidden-field")
            next_pred = in_predicate or key == "predicate"
            next_subj = in_subject or (not in_predicate and key == "subject")
            next_subj_name = in_subject and not in_predicate and key == "name"
            _scan_smuggling(value, next_pred, reg_mode, codes, next_subj, next_subj_name)
    elif isinstance(node, list):
        for item in node:
            _scan_smuggling(item, in_predicate, reg_mode, codes, in_subject, in_subject_name)
    elif isinstance(node, str) and (in_predicate or in_subject_name):
        if SMUGGLED_VALUE_PHRASES.search(node) or AUTHORSHIP_DENY.search(node):
            codes.add("authorship-claim")


def _smuggled_keys() -> set[str]:
    return TIME_KEYS | FORBIDDEN_KEYS


def _check_keys(obj: dict, required: set[str], optional: set[str], codes: set[str], extra_ignored: set[str]) -> bool:
    if not isinstance(obj, dict):
        codes.add("statement-shape")
        return False
    ok = True
    if not required <= set(obj):
        codes.add("missing-required-field")
        ok = False
    unknown = {
        k
        for k in (set(obj) - required - optional)
        if k.lower() not in AUTHORSHIP_KEYS and k not in extra_ignored
    }
    if unknown:
        codes.add("extra-field")
        ok = False
    return ok


def validate_statement(st, artifacts: list[dict], cat_opening: dict | None, codes: set[str]) -> dict | None:
    if not isinstance(st, dict):
        codes.add("statement-shape")
        return None

    ptype = st.get("predicateType")
    reg_mode = ptype == REG_PREDICATE_TYPE
    _scan_smuggling(st, False, reg_mode, codes)

    if "_type" not in st:
        codes.add("missing-required-field")
    elif st["_type"] != STATEMENT_TYPE:
        codes.add("statement-type")

    if "predicateType" not in st:
        codes.add("missing-required-field")
    elif ptype not in (CORE_PREDICATE_TYPE, REG_PREDICATE_TYPE):
        codes.add("predicate-type")

    top_ok = _check_keys(st, {"_type", "subject", "predicateType", "predicate"}, set(), codes, set())
    if not top_ok or st.get("_type") != STATEMENT_TYPE or ptype not in (CORE_PREDICATE_TYPE, REG_PREDICATE_TYPE):
        return None

    subjects = st["subject"]
    if not isinstance(subjects, list):
        codes.add("statement-shape")
        return None
    if ptype == CORE_PREDICATE_TYPE:
        if len(subjects) != 1:
            codes.add("subject-count")
            return None
    else:
        if not (1 <= len(subjects) <= 64):
            codes.add("subject-count")
            return None

    seen_digests = set()
    for item in subjects:
        if not _check_keys(item, {"name", "digest"}, set(), codes, set()):
            return None
        name = item["name"]
        if ptype == CORE_PREDICATE_TYPE:
            if not isinstance(name, str) or not name:
                codes.add("statement-shape")
        else:
            if not isinstance(name, str) or not REG_SUBJECT_NAME.fullmatch(name):
                codes.add("statement-shape")
        digest = item["digest"]
        if not _check_keys(digest, {"sha256"}, set(), codes, set()):
            return None
        digest_hex = digest["sha256"]
        if not isinstance(digest_hex, str) or not HEX64.fullmatch(digest_hex):
            codes.add("statement-shape")
            return None
        if digest_hex in seen_digests:
            codes.add("subject-count")
            return None
        seen_digests.add(digest_hex)

    pred = st["predicate"]
    ignored = _smuggled_keys() | ({"recordedAt"} if reg_mode else set())
    if ptype == CORE_PREDICATE_TYPE:
        if not _check_keys(
            pred,
            {"specVersion", "contentKind", "profile", "catalogueCommitment"},
            {"recordedAt"},
            codes,
            ignored,
        ):
            return None
        if pred["specVersion"] != CORE_SPEC_VERSION or pred["contentKind"] not in CORE_CONTENT_KINDS:
            codes.add("statement-shape")
        if "recordedAt" in pred and not is_iso_datetime(pred["recordedAt"]):
            codes.add("statement-shape")
        prof = pred["profile"]
        if _check_keys(prof, {"id", "version", "configSha256"}, set(), codes, ignored):
            if (
                not isinstance(prof["id"], str)
                or not prof["id"]
                or not isinstance(prof["version"], str)
                or not prof["version"]
                or not isinstance(prof["configSha256"], str)
                or not HEX64.fullmatch(prof["configSha256"])
            ):
                codes.add("statement-shape")
        comm = pred["catalogueCommitment"]
        if _check_keys(comm, {"scheme", "sha256"}, set(), codes, ignored):
            if (
                comm["scheme"] != CATALOGUE_SCHEME
                or not isinstance(comm["sha256"], str)
                or not HEX64.fullmatch(comm["sha256"])
            ):
                codes.add("statement-shape")
        cat_sha = comm.get("sha256") if isinstance(comm, dict) else None
    else:
        if not _check_keys(
            pred,
            {"registrationVersion", "contentKind", "nonce", "possession", "implementation", "specCommit", "claims"},
            {"catalogue"},
            codes,
            ignored,
        ):
            return None
        if (
            pred["registrationVersion"] != REG_VERSION
            or not isinstance(pred["contentKind"], str)
            or pred["contentKind"] not in REG_CONTENT_KINDS
            or not isinstance(pred["nonce"], str)
            or not HEX64.fullmatch(pred["nonce"])
            or pred["nonce"] == "0" * 64
            or not isinstance(pred["specCommit"], str)
            or not HEX40.fullmatch(pred["specCommit"])
        ):
            codes.add("statement-shape")
        poss = pred["possession"]
        if not isinstance(poss, list) or len(poss) != len(subjects):
            codes.add("statement-shape")
        else:
            for i, entry in enumerate(poss):
                if _check_keys(entry, {"subjectIndex", "scheme", "sha256"}, set(), codes, ignored):
                    idx = entry["subjectIndex"]
                    if (
                        not isinstance(idx, int)
                        or isinstance(idx, bool)
                        or idx != i
                        or entry["scheme"] != POSSESSION_SCHEME
                        or not isinstance(entry["sha256"], str)
                        or not HEX64.fullmatch(entry["sha256"])
                    ):
                        codes.add("statement-shape")
        impl = pred["implementation"]
        if _check_keys(impl, {"name", "version", "commit"}, set(), codes, ignored):
            if (
                not isinstance(impl["name"], str)
                or not impl["name"]
                or not isinstance(impl["version"], str)
                or not impl["version"]
                or not isinstance(impl["commit"], str)
                or not HEX40.fullmatch(impl["commit"])
            ):
                codes.add("statement-shape")
        claims = pred["claims"]
        if _check_keys(claims, {"createdAt"}, {"aiUse"}, codes, ignored):
            if not isinstance(claims["createdAt"], str) or not UTC_TIME.fullmatch(claims["createdAt"]):
                codes.add("statement-shape")
            if "aiUse" in claims:
                ai = claims["aiUse"]
                if _check_keys(ai, {"declared"}, {"tool"}, codes, ignored):
                    if ai["declared"] not in AI_USE_DECLARED:
                        codes.add("statement-shape")
                    if "tool" in ai:
                        tool = ai["tool"]
                        if ai["declared"] == "no-generative-ai" or not isinstance(tool, str) or not AI_TOOL.fullmatch(tool):
                            codes.add("statement-shape")
                        elif tool_has_origin_claim(tool):
                            codes.add("authorship-claim")
        cat_sha = None
        if "catalogue" in pred:
            cat = pred["catalogue"]
            if _check_keys(cat, {"scheme", "sha256", "profile"}, set(), codes, ignored):
                if (
                    cat["scheme"] != CATALOGUE_SCHEME
                    or not isinstance(cat["sha256"], str)
                    or not HEX64.fullmatch(cat["sha256"])
                ):
                    codes.add("statement-shape")
                prof = cat["profile"]
                if _check_keys(prof, {"id", "version", "configSha256"}, set(), codes, ignored):
                    if (
                        not isinstance(prof["id"], str)
                        or not prof["id"]
                        or not isinstance(prof["version"], str)
                        or not prof["version"]
                        or not isinstance(prof["configSha256"], str)
                        or not HEX64.fullmatch(prof["configSha256"])
                    ):
                        codes.add("statement-shape")
                cat_sha = cat.get("sha256")

    # Artifact & possession bindings
    poss_by_idx = {}
    if reg_mode and isinstance(pred.get("possession"), list):
        for entry in pred["possession"]:
            if (
                isinstance(entry, dict)
                and isinstance(entry.get("subjectIndex"), int)
                and not isinstance(entry.get("subjectIndex"), bool)
            ):
                poss_by_idx.setdefault(entry["subjectIndex"], entry)
    for art in artifacts:
        idx = art.get("subjectIndex")
        if not isinstance(idx, int) or not (0 <= idx < len(subjects)):
            codes.add("fixture-shape")
            continue
        raw_bytes = load_source(art["source"])
        if sha256_hex(raw_bytes) != subjects[idx]["digest"]["sha256"]:
            codes.add("subject-digest-mismatch")
        if reg_mode and idx in poss_by_idx:
            if HEX64.fullmatch(str(pred.get("nonce", ""))):
                expected_poss = possession_digest(pred["nonce"], raw_bytes)
                if poss_by_idx[idx].get("sha256") != expected_poss:
                    codes.add("possession-mismatch")

    # Catalogue commitment opening check if provided
    if cat_opening is not None and cat_sha is not None:
        cat_bytes = load_source(cat_opening["source"])
        cat_nonce = bytes.fromhex(cat_opening["nonceHex"])
        if catalogue_commitment(cat_nonce, cat_bytes) != cat_sha:
            codes.add("catalogue-mismatch")

    if codes:
        return None
    return st


def check_fixture(fx: dict) -> tuple[set[str], dict | None]:
    codes: set[str] = set()
    required = {"fixtureVersion", "id", "kind", "notice", "envelope", "verificationMaterial", "trustedKeys"}
    if not isinstance(fx, dict) or not required <= set(fx):
        return {"fixture-shape"}, None

    env = fx["envelope"]
    if not isinstance(env, dict) or set(env) != {"payloadType", "payload", "signatures"}:
        return {"dsse-shape"}, None

    ptype_bytes = env["payloadType"]
    if not isinstance(ptype_bytes, str):
        codes.add("dsse-shape")
        return codes, None
    if ptype_bytes != DSSE_PAYLOAD_TYPE:
        codes.add("dsse-payload-type")

    raw_payload = b64d(env["payload"])
    if raw_payload is None:
        codes.add("invalid-base64")
        return codes, None

    sigs = env["signatures"]
    if not isinstance(sigs, list) or not sigs:
        codes.add("dsse-shape")
        return codes, None

    vm = fx["verificationMaterial"]
    keys_by_hint: dict[str, tuple[bytes, str]] = {}
    if not isinstance(vm, dict) or not isinstance(vm.get("publicKeys"), list):
        codes.add("fixture-shape")
        return codes, None
    for pk in vm["publicKeys"]:
        if not isinstance(pk, dict) or set(pk) != {"keyid", "alg", "publicKeyHex"}:
            codes.add("fixture-shape")
            return codes, None
        if pk["alg"] != "ed25519" or not HEX16.fullmatch(str(pk["keyid"])) or not HEX64.fullmatch(str(pk["publicKeyHex"])):
            codes.add("fixture-shape")
            return codes, None
        pub_bytes = bytes.fromhex(pk["publicKeyHex"])
        pub_sha = sha256_hex(pub_bytes)
        if pub_sha[:16] != pk["keyid"]:
            codes.add("fixture-shape")
            return codes, None
        keys_by_hint[pk["keyid"]] = (pub_bytes, pub_sha)

    trusted = fx["trustedKeys"]
    if not isinstance(trusted, list) or any(not isinstance(k, str) or not HEX64.fullmatch(k) for k in trusted):
        codes.add("fixture-shape")
        return codes, None
    trusted_set = set(trusted)

    pae_msg = dsse_pae(ptype_bytes.encode("utf-8"), raw_payload)
    seen_signers = set()
    for entry in sigs:
        if not isinstance(entry, dict) or set(entry) != {"keyid", "sig"}:
            codes.add("dsse-shape")
            continue
        sig_bytes = b64d(entry["sig"])
        if sig_bytes is None:
            codes.add("invalid-base64")
            continue
        if len(sig_bytes) != 64:
            codes.add("signature-invalid")
            continue
        hint = entry["keyid"]
        if not isinstance(hint, str) or hint not in keys_by_hint:
            codes.add("unknown-key")
            continue
        pub_bytes, pub_sha = keys_by_hint[hint]
        if pub_sha in seen_signers:
            codes.add("dsse-shape")
            continue
        seen_signers.add(pub_sha)
        if not ed25519_verify(pub_bytes, pae_msg, sig_bytes):
            codes.add("signature-invalid")
        if pub_sha not in trusted_set:
            codes.add("untrusted-signer")

    # Decode payload regardless of signature/trust outcome unless invalid base64,
    # matching spec/attestations.md (signature and subject/statement checks stay separate).
    try:
        payload_text = raw_payload.decode("utf-8")
    except UnicodeDecodeError:
        codes.add("statement-shape")
        return codes, None

    try:
        statement = strict_loads(payload_text)
    except DupKeyError:
        codes.add("duplicate-key")
        return codes, None
    except ValueError:
        codes.add("statement-shape")
        return codes, None

    validated = validate_statement(
        statement,
        fx.get("artifacts", []),
        fx.get("catalogueOpening"),
        codes,
    )
    if validated is None or codes:
        return codes, None

    decoded_record = adapter_decode(validated)
    reencoded = adapter_encode(decoded_record)
    if reencoded != validated or jcs(reencoded) != jcs(validated):
        codes.add("round-trip-mismatch")
        return codes, None

    expected_rt = fx.get("expectedRoundTrip")
    if expected_rt is not None:
        if sha256_hex(raw_payload) != expected_rt.get("statementSha256"):
            codes.add("round-trip-mismatch")
        if sha256_hex(jcs(validated)) != expected_rt.get("canonicalStatementSha256"):
            codes.add("round-trip-mismatch")
        if decoded_record != expected_rt.get("record"):
            codes.add("round-trip-mismatch")

    return codes, decoded_record


# ------------------------------------------------------------------ self-test

def run_self_test(accept_fixtures: list[dict]) -> list[str]:
    errors: list[str] = []

    # 1. Verify PAE framing property: field lengths count UTF-8 bytes, never characters or base64 text.
    if dsse_pae(b"x", "é".encode("utf-8")) != b"DSSEv1 1 x 2 \xc3\xa9":
        errors.append("PAE UTF-8 byte-length self-test failed")

    # 2. Verify every accept fixture breaks when required fields are deleted or unexpected fields added.
    for fx in accept_fixtures:
        raw = b64d(fx["envelope"]["payload"])
        stmt = strict_loads(raw.decode("utf-8"))
        for field in ("_type", "subject", "predicateType", "predicate"):
            mutated = copy.deepcopy(stmt)
            del mutated[field]
            mut_codes: set[str] = set()
            validate_statement(mutated, [], None, mut_codes)
            if "missing-required-field" not in mut_codes:
                errors.append(f"{fx['id']}: deleting top-level {field!r} was not rejected")

        for field in list(stmt["predicate"]):
            if field in ("recordedAt", "catalogue"):
                continue
            mutated = copy.deepcopy(stmt)
            del mutated["predicate"][field]
            mut_codes = set()
            validate_statement(mutated, [], None, mut_codes)
            if "missing-required-field" not in mut_codes:
                errors.append(f"{fx['id']}: deleting predicate.{field!r} was not rejected")

        mutated = copy.deepcopy(stmt)
        mutated["unexpectedTop"] = True
        mut_codes = set()
        validate_statement(mutated, [], None, mut_codes)
        if "extra-field" not in mut_codes:
            errors.append(f"{fx['id']}: adding extra top-level field was not rejected")

        # 3. Signing base64 text instead of decoded payload bytes must be rejected.
        seed = hashlib.sha256(b"traceweave intoto adapter self-test key").digest()
        pub = ed25519_public(seed)
        kid = sha256_hex(pub)[:16]
        b64_payload = fx["envelope"]["payload"]
        bad_sig = ed25519_sign(seed, dsse_pae(DSSE_PAYLOAD_TYPE.encode("utf-8"), b64_payload.encode("ascii")))
        mut_fx = copy.deepcopy(fx)
        mut_fx["envelope"]["signatures"] = [{"keyid": kid, "sig": base64.b64encode(bad_sig).decode("ascii")}]
        mut_fx["verificationMaterial"]["publicKeys"] = [{"keyid": kid, "alg": "ed25519", "publicKeyHex": pub.hex()}]
        mut_fx["trustedKeys"] = [sha256_hex(pub)]
        got_codes, _ = check_fixture(mut_fx)
        if "signature-invalid" not in got_codes:
            errors.append(f"{fx['id']}: signature over base64 text instead of decoded bytes was accepted")

    # 4. Ed25519 strictness self-tests (S >= Q, non-canonical R, small-order A) and hint-only trust rejection.
    seed = hashlib.sha256(b"traceweave intoto adapter ed25519 self-test").digest()
    pub = ed25519_public(seed)
    kid = sha256_hex(pub)[:16]
    base_fx = copy.deepcopy(accept_fixtures[0])
    raw_msg = dsse_pae(DSSE_PAYLOAD_TYPE.encode("utf-8"), b64d(base_fx["envelope"]["payload"]))
    good_sig = ed25519_sign(seed, raw_msg)

    # (a) Malleated S = s + Q (>= Q)
    s_val = int.from_bytes(good_sig[32:], "little") + Q
    mal_sig = good_sig[:32] + s_val.to_bytes(32, "little")
    fx_s = copy.deepcopy(base_fx)
    fx_s["envelope"]["signatures"] = [{"keyid": kid, "sig": base64.b64encode(mal_sig).decode("ascii")}]
    fx_s["verificationMaterial"]["publicKeys"] = [{"keyid": kid, "alg": "ed25519", "publicKeyHex": pub.hex()}]
    fx_s["trustedKeys"] = [sha256_hex(pub)]
    if "signature-invalid" not in check_fixture(fx_s)[0]:
        errors.append("Ed25519 S >= Q malleated signature was accepted")

    # (b) Non-canonical R (x = 0, y = 1, sign bit set)
    noncan_r = (1 | (1 << 255)).to_bytes(32, "little") + bytes(32)
    fx_r = copy.deepcopy(fx_s)
    fx_r["envelope"]["signatures"] = [{"keyid": kid, "sig": base64.b64encode(noncan_r).decode("ascii")}]
    if "signature-invalid" not in check_fixture(fx_r)[0]:
        errors.append("Ed25519 non-canonical R was accepted")

    # (c) Small-order public key A (identity point, R = A, S = 0)
    small_pub = (1).to_bytes(32, "little")
    small_kid = sha256_hex(small_pub)[:16]
    small_sig = small_pub + bytes(32)
    fx_a = copy.deepcopy(base_fx)
    fx_a["envelope"]["signatures"] = [{"keyid": small_kid, "sig": base64.b64encode(small_sig).decode("ascii")}]
    fx_a["verificationMaterial"]["publicKeys"] = [{"keyid": small_kid, "alg": "ed25519", "publicKeyHex": small_pub.hex()}]
    fx_a["trustedKeys"] = [sha256_hex(small_pub)]
    if "signature-invalid" not in check_fixture(fx_a)[0]:
        errors.append("Ed25519 small-order public key A was accepted")

    # (d) 16-hex hint in trustedKeys must be rejected
    fx_hint = copy.deepcopy(base_fx)
    fx_hint["trustedKeys"] = [base_fx["verificationMaterial"]["publicKeys"][0]["keyid"]]
    if "fixture-shape" not in check_fixture(fx_hint)[0]:
        errors.append("16-hex keyid hint in trustedKeys was not rejected")

    return errors


def main(argv: list[str]) -> int:
    verbose = "--verbose" in argv
    accept_dir = HERE / "accept"
    reject_dir = HERE / "reject"
    accept_paths = sorted(accept_dir.glob("*.json"))
    reject_paths = sorted(reject_dir.glob("*.json"))
    if len(accept_paths) < 3 or len(reject_paths) < 12:
        print(f"FAIL: insufficient fixtures (accept={len(accept_paths)}, reject={len(reject_paths)})")
        return 1

    problems = 0
    accept_fixtures = []
    seen_reject_codes: set[str] = set()

    for path in accept_paths:
        try:
            fx = strict_loads(path.read_text(encoding="utf-8"))
        except (DupKeyError, ValueError) as exc:
            print(f"FAIL accept/{path.name}: {exc}")
            problems += 1
            continue
        accept_fixtures.append(fx)
        codes, _ = check_fixture(fx)
        if codes:
            print(f"FAIL accept/{path.name}: unexpected codes {sorted(codes)}")
            problems += 1
        elif verbose:
            print(f"PASS accept/{path.name}")

    for path in reject_paths:
        try:
            fx = strict_loads(path.read_text(encoding="utf-8"))
        except (DupKeyError, ValueError) as exc:
            print(f"FAIL reject/{path.name}: {exc}")
            problems += 1
            continue
        expect = fx.get("expect") or {}
        expected_code = expect.get("code")
        if expected_code not in ALL_CODES:
            print(f"FAIL reject/{path.name}: unknown expected code {expected_code!r}")
            problems += 1
            continue
        wanted = {expected_code} | set(expect.get("alsoReported", []))
        codes, _ = check_fixture(fx)
        seen_reject_codes.update(codes)
        if codes != wanted:
            print(f"FAIL reject/{path.name}: expected {sorted(wanted)}, got {sorted(codes)}")
            problems += 1
        elif verbose:
            print(f"PASS reject/{path.name}: rejected with {sorted(codes)}")

    for err in run_self_test(accept_fixtures):
        print(f"FAIL self-test: {err}")
        problems += 1

    # Verify every core reject category requested is exercised.
    required_exercised = {
        "statement-type",
        "predicate-type",
        "subject-digest-mismatch",
        "missing-required-field",
        "extra-field",
        "invalid-base64",
        "dsse-payload-type",
        "authorship-claim",
        "duplicate-key",
        "signature-invalid",
        "untrusted-signer",
        "time-in-statement",
        "forbidden-field",
        "subject-count",
        "statement-shape",
        "unknown-key",
        "dsse-shape",
    }
    missing_cov = required_exercised - seen_reject_codes
    if missing_cov:
        print(f"FAIL coverage: missing reject fixtures for {sorted(missing_cov)}")
        problems += 1

    if problems:
        print(f"FAIL in-toto adapter check: {problems} problem(s)")
        return 1

    print(
        f"PASS in-toto adapter (M4.5): {len(accept_paths)} accept, {len(reject_paths)} reject, "
        f"{len(required_exercised)}/{len(required_exercised)} reject codes covered, self-tests passed"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
