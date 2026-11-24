"""Real-format time evidence for the registration fixtures (design draft-3, section 6.5).

Standard library only. A minimal DER reader and writer, X.509 and CMS field access,
RSA PKCS #1 v1.5 (SHA-256) signature verification, RFC 3161 TimeStampResp checks,
and an OpenTimestamps proof reader verified against a local Bitcoin-style header file.

This is research code for checking the committed test vectors in real-format/. It is
not a general certificate-path validator (no name constraints, policy mappings or
revocation fetching) and must not be used as one.

The checker loads this file by path; it is never imported from the current directory.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone, timedelta

SHA256_OID = "2.16.840.1.101.3.4.2.1"
SHA1_OID = "1.3.14.3.2.26"
RSA_OIDS = {"1.2.840.113549.1.1.1", "1.2.840.113549.1.1.11"}
OID_SIGNED_DATA = "1.2.840.113549.1.7.2"
OID_TSTINFO = "1.2.840.113549.1.9.16.1.4"
OID_CONTENT_TYPE = "1.2.840.113549.1.9.3"
OID_MESSAGE_DIGEST = "1.2.840.113549.1.9.4"
OID_SIGNING_CERT = "1.2.840.113549.1.9.16.2.12"
OID_SIGNING_CERT_V2 = "1.2.840.113549.1.9.16.2.47"
OID_EKU = "2.5.29.37"
OID_KP_TIMESTAMPING = "1.3.6.1.5.5.7.3.8"
OID_BASIC_CONSTRAINTS = "2.5.29.19"
OID_KEY_USAGE = "2.5.29.15"
# Extensions this validator understands; an unknown critical extension fails path validation (RFC 5280 4.2).
UNDERSTOOD_EXTENSIONS = {OID_BASIC_CONSTRAINTS, OID_KEY_USAGE, OID_EKU, "2.5.29.14", "2.5.29.35"}
HASHES = {SHA256_OID: hashlib.sha256, "2.16.840.1.101.3.4.2.2": hashlib.sha384, "2.16.840.1.101.3.4.2.3": hashlib.sha512, SHA1_OID: hashlib.sha1}
DIGESTINFO_SHA256 = bytes.fromhex("3031300d060960864801650304020105000420")


class Bad(ValueError):
    """A structural or cryptographic failure, with a code from the design."""

    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}")
        self.code = code


# ------------------------------------------------------------------ DER

class Node:
    __slots__ = ("tag", "value", "children")

    def __init__(self, tag, value=b"", children=None):
        self.tag, self.value, self.children = tag, value, children

    @property
    def constructed(self):
        return bool(self.tag & 0x20)

    def __getitem__(self, i):
        return self.children[i]

    def __len__(self):
        return len(self.children)


def _read(data, pos):
    if pos + 2 > len(data):
        raise Bad("evidence-shape", "truncated DER")
    tag = data[pos]
    if tag & 0x1F == 0x1F:
        raise Bad("evidence-shape", "high tag numbers are not used here")
    length = data[pos + 1]
    pos += 2
    if length & 0x80:
        n = length & 0x7F
        if n == 0 or n > 4 or pos + n > len(data):
            raise Bad("evidence-shape", "bad DER length")
        length = int.from_bytes(data[pos:pos + n], "big")
        if length < 128 or data[pos] == 0:
            raise Bad("evidence-shape", "non-minimal DER length")
        pos += n
    end = pos + length
    if end > len(data):
        raise Bad("evidence-shape", "DER length beyond data")
    content = data[pos:end]
    node = Node(tag, content)
    if tag & 0x20:
        node.children = []
        p = 0
        while p < len(content):
            child, p = _read(content, p)
            node.children.append(child)
    return node, end


def parse(data):
    node, end = _read(data, 0)
    if end != len(data):
        raise Bad("evidence-shape", "trailing bytes after DER")
    return node


def _len(n):
    if n < 128:
        return bytes([n])
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(b)]) + b


def encode(node):
    content = b"".join(encode(c) for c in node.children) if node.children is not None else node.value
    return bytes([node.tag]) + _len(len(content)) + content


def oid(node):
    if node.tag != 0x06:
        raise Bad("evidence-shape", "expected an OID")
    subids, v = [], 0
    for byte in node.value:
        v = (v << 7) | (byte & 0x7F)
        if not byte & 0x80:
            subids.append(v)
            v = 0
    first = subids[0]
    top = min(first // 40, 2)
    return ".".join(str(x) for x in [top, first - 40 * top] + subids[1:])


def integer(node):
    if node.tag != 0x02:
        raise Bad("evidence-shape", "expected an INTEGER")
    return int.from_bytes(node.value, "big", signed=True)


def gtime(node):
    """GeneralizedTime or UTCTime, rounded UP to the whole second (design N1)."""
    text = node.value.decode("ascii")
    if node.tag == 0x17:
        year = int(text[:2])
        text = ("19" if year >= 50 else "20") + text
    elif node.tag != 0x18:
        raise Bad("evidence-shape", "expected a time")
    if not text.endswith("Z"):
        raise Bad("evidence-shape", "time must be UTC")
    base, frac = text[:14], text[14:-1]
    t = datetime.strptime(base, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    if frac:
        if not frac.startswith(".") or not frac[1:].isdigit() or frac.endswith("0"):
            raise Bad("evidence-shape", "bad fractional seconds")
        t += timedelta(seconds=1)
    return t


# ------------------------------------------------------------------ X.509 and RSA

class Cert:
    def __init__(self, der):
        self.der = der
        root = parse(der)
        self.tbs_der = encode(root[0])
        tbs = root[0]
        i = 1 if tbs[0].tag == 0xA0 else 0
        self.serial = integer(tbs[i])
        self.issuer_der = encode(tbs[i + 2])
        self.subject_der = encode(tbs[i + 4])
        validity = tbs[i + 3]
        self.not_before, self.not_after = gtime(validity[0]), gtime(validity[1])
        spki = tbs[i + 5]
        if oid(spki[0][0]) != "1.2.840.113549.1.1.1":
            raise Bad("tsa-signature-invalid", "only RSA keys are supported in these vectors")
        rsa = parse(spki[1].value[1:])
        self.n, self.e = integer(rsa[0]), integer(rsa[1])
        self.sig_alg = oid(root[1][0])
        self.signature = root[2].value[1:]
        self.extensions = {}
        for child in tbs.children[i + 6:]:
            if child.tag == 0xA3:
                for ext in child[0].children:
                    critical = len(ext) == 3 and ext[1].tag == 0x01 and ext[1].value != b"\x00"
                    self.extensions[oid(ext[0])] = (critical, ext[-1].value)

    def sha256(self):
        return hashlib.sha256(self.der).hexdigest()

    def basic_constraints(self):
        """(cA, pathLenConstraint or None); (False, None) when the extension is absent."""
        if OID_BASIC_CONSTRAINTS not in self.extensions:
            return False, None
        seq = parse(self.extensions[OID_BASIC_CONSTRAINTS][1])
        ca, path_len = False, None
        for c in seq.children:
            if c.tag == 0x01:
                ca = c.value != b"\x00"
            elif c.tag == 0x02:
                path_len = integer(c)
        return ca, path_len

    def key_usage(self):
        """Set of bit numbers asserted, or None when the extension is absent (RFC 5280 4.2.1.3)."""
        if OID_KEY_USAGE not in self.extensions:
            return None
        bits = parse(self.extensions[OID_KEY_USAGE][1]).value
        out = set()
        for i, byte in enumerate(bits[1:]):
            for j in range(8):
                if byte & (0x80 >> j):
                    out.add(8 * i + j)
        return out

    def unknown_critical(self):
        return [o for o, (crit, _) in self.extensions.items() if crit and o not in UNDERSTOOD_EXTENSIONS]


def rsa_verify(n, e, message, signature):
    k = (n.bit_length() + 7) // 8
    if len(signature) != k:
        return False
    m = pow(int.from_bytes(signature, "big"), e, n).to_bytes(k, "big")
    t = DIGESTINFO_SHA256 + hashlib.sha256(message).digest()
    return m == b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t


def cert_signed_by(cert, issuer):
    return cert.issuer_der == issuer.subject_der and cert.sig_alg == "1.2.840.113549.1.1.11" \
        and rsa_verify(issuer.n, issuer.e, cert.tbs_der, cert.signature)


def eku_is_timestamping_only_and_critical(cert):
    if OID_EKU not in cert.extensions:
        return False
    critical, value = cert.extensions[OID_EKU]
    purposes = [oid(c) for c in parse(value).children]
    return critical and purposes == [OID_KP_TIMESTAMPING]


# ------------------------------------------------------------------ RFC 3161

def parse_request(der):
    req = parse(der)
    imprint = req[1]
    fields = {"hashAlg": oid(imprint[0][0]), "hash": imprint[1].value.hex(), "nonce": None}
    for child in req.children[2:]:
        if child.tag == 0x02:
            fields["nonce"] = integer(child)
    return fields


def parse_response(der):
    """Returns a dict of TSTInfo fields and the material needed for checks. Raises Bad on structure."""
    resp = parse(der)
    if integer(resp[0][0]) not in (0, 1):
        raise Bad("evidence-shape", "TimeStampResp status is not granted")
    if len(resp) < 2:
        raise Bad("evidence-shape", "no timeStampToken")
    token = resp[1]
    if oid(token[0]) != OID_SIGNED_DATA:
        raise Bad("evidence-shape", "token is not SignedData")
    sd = token[1][0]
    encap = sd[2]
    if oid(encap[0]) != OID_TSTINFO:
        raise Bad("evidence-shape", "eContentType is not id-ct-TSTInfo")
    tst_der = encap[1][0].value
    tst = parse(tst_der)
    certs = []
    signer_infos = None
    for child in sd.children[3:]:
        if child.tag == 0xA0:
            certs = [Cert(encode(c)) for c in child.children]
        elif child.tag == 0x31:
            signer_infos = child
    if signer_infos is None or len(signer_infos) != 1:
        raise Bad("tsa-signature-invalid", "exactly one SignerInfo is required (S2)")
    si = signer_infos[0]
    if integer(tst[0]) != 1:
        raise Bad("evidence-shape", "TSTInfo version must be 1")
    fields = {"version": integer(tst[0]), "policyOid": oid(tst[1]), "hashAlg": oid(tst[2][0][0]),
              "hash": tst[2][1].value.hex(), "serial": integer(tst[3]), "genTime": gtime(tst[4]),
              "accuracy": None, "nonce": None, "tstDer": tst_der, "certs": certs}
    for child in tst.children[5:]:
        if child.tag == 0x30:  # Accuracy
            secs = millis = micros = 0
            for a in child.children:
                if a.tag == 0x02:
                    secs = integer(a)
                elif a.tag == 0x80:
                    millis = int.from_bytes(a.value, "big")
                elif a.tag == 0x81:
                    micros = int.from_bytes(a.value, "big")
            fields["accuracy"] = secs + (1 if millis or micros else 0)  # rounded up (N1)
        elif child.tag == 0x02:
            fields["nonce"] = integer(child)
    sid = si[1]
    if sid.tag != 0x30:
        raise Bad("tsa-signing-cert-mismatch", "only issuerAndSerialNumber identifiers are supported here")
    fields["sid"] = (encode(sid[0]), integer(sid[1]))
    attrs_node = si[3]
    if attrs_node.tag != 0xA0:
        raise Bad("tsa-signature-invalid", "signed attributes are required")
    oids = [oid(a[0]) for a in attrs_node.children]
    if len(oids) != len(set(oids)):
        raise Bad("tsa-signature-invalid", "duplicate signed attribute")
    attrs = {oid(a[0]): a[1] for a in attrs_node.children}
    fields["signedAttrsDer"] = encode(Node(0x31, children=attrs_node.children))
    fields["sigAlg"] = oid(si[4][0])
    fields["signature"] = si[5].value
    fields["digestAlg"] = oid(si[2][0])
    if oid(attrs[OID_CONTENT_TYPE][0]) != OID_TSTINFO:
        raise Bad("tsa-signature-invalid", "contentType attribute is not id-ct-TSTInfo")
    fields["messageDigest"] = attrs[OID_MESSAGE_DIGEST][0].value
    ess = []
    if OID_SIGNING_CERT_V2 in attrs:
        for cid in attrs[OID_SIGNING_CERT_V2][0][0].children:
            alg = SHA256_OID if cid[0].tag != 0x30 else oid(cid[0][0])
            h = cid[0].value if cid[0].tag == 0x04 else cid[1].value
            ess.append((alg, h.hex()))
    elif OID_SIGNING_CERT in attrs:
        for cid in attrs[OID_SIGNING_CERT][0][0].children:
            ess.append((SHA1_OID, cid[0].value.hex()))
    fields["essCertIds"] = ess
    return fields


def check_token(fields, target_sha256, request):
    """Producer- and structure-level checks (design 6.5). Returns the signer certificate. Raises Bad."""
    if fields["hashAlg"] != SHA256_OID or fields["hash"] != target_sha256:
        raise Bad("tsa-imprint-mismatch", "messageImprint does not equal the target digest")
    if request is not None and (request["hash"] != fields["hash"] or request["nonce"] != fields["nonce"]):
        raise Bad("tsa-nonce-mismatch", "token nonce or imprint differs from the request")
    signer = next((c for c in fields["certs"] if (c.issuer_der, c.serial) == fields["sid"]), None)
    if signer is None:
        raise Bad("tsa-signing-cert-mismatch", "signer certificate not in the token")
    if not fields["essCertIds"]:
        raise Bad("tsa-signing-cert-mismatch", "no SigningCertificate attribute (RFC 5816 section 2)")
    alg, h = fields["essCertIds"][0]
    if alg not in HASHES:
        raise Bad("tsa-signing-cert-mismatch", "unsupported ESSCertIDv2 hash algorithm")
    expected = HASHES[alg](signer.der).hexdigest()
    if h != expected:
        raise Bad("tsa-signing-cert-mismatch", "ESSCertID does not identify the signer certificate")
    if not eku_is_timestamping_only_and_critical(signer):
        raise Bad("tsa-eku-invalid", "signer certificate EKU is not exactly id-kp-timeStamping, critical")
    if fields["digestAlg"] != SHA256_OID or fields["sigAlg"] not in RSA_OIDS:
        raise Bad("tsa-signature-invalid", "unsupported digest or signature algorithm")
    if fields["messageDigest"] != hashlib.sha256(fields["tstDer"]).digest():
        raise Bad("tsa-signature-invalid", "messageDigest does not match TSTInfo")
    if not rsa_verify(signer.n, signer.e, fields["signedAttrsDer"], fields["signature"]):
        raise Bad("tsa-signature-invalid", "CMS signature does not verify")
    return signer


def validate_path(signer, certs, root, at):
    """RFC 5280 path validation at time `at` (design 6.2 step 6), restricted to what these vectors need.
    Returns the list of certificates from the signer to the pinned root, or raises Bad("path-invalid", ...).
    Checked: every signature; every certificate valid at `at`; every issuer has basicConstraints cA=TRUE and,
    if keyUsage is present, keyCertSign; pathLenConstraint; no unknown critical extension anywhere; the
    leaf's keyUsage, if present, asserts digitalSignature or nonRepudiation."""
    path, current = [signer], signer
    while not (current.issuer_der == root.subject_der and cert_signed_by(current, root)):
        nxt = next((c for c in certs if c.subject_der == current.issuer_der and c is not current and c not in path), None)
        if nxt is None or not cert_signed_by(current, nxt) or len(path) > 5:
            raise Bad("path-invalid", "no signature path to the pinned root")
        path.append(nxt)
        current = nxt
    path.append(root)
    for k, cert in enumerate(path):
        if not cert.not_before <= at <= cert.not_after:
            raise Bad("path-invalid", "a certificate in the path is not valid at genTime")
        if cert.unknown_critical():
            raise Bad("path-invalid", "unknown critical extension")
        if k == 0:
            ku = cert.key_usage()
            if ku is not None and not ku & {0, 1}:
                raise Bad("path-invalid", "leaf keyUsage lacks digitalSignature and nonRepudiation")
            continue
        ca, path_len = cert.basic_constraints()
        ku = cert.key_usage()
        if not ca or (ku is not None and 5 not in ku):
            raise Bad("path-invalid", "issuer is not a CA certificate")
        intermediates_below = k - 1
        if path_len is not None and intermediates_below > path_len:
            raise Bad("path-invalid", "pathLenConstraint exceeded")
    return path


def chain_to_root(signer, certs, root, at=None):
    """Kept for the wrong-implementation self-test: signatures only, which is NOT path validation (D4)."""
    current, seen = signer, 0
    while seen < 4:
        if cert_signed_by(current, root):
            return True
        nxt = next((c for c in certs if c.subject_der == current.issuer_der and c is not current), None)
        if nxt is None or not cert_signed_by(current, nxt):
            return False
        current, seen = nxt, seen + 1
    return False


# ------------------------------------------------------------------ OpenTimestamps (python-opentimestamps at 8c3dc6fb)

OTS_MAGIC = b"\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94"
OTS_BITCOIN = bytes.fromhex("0588960d73d71901")
OTS_PENDING = bytes.fromhex("83dfe30d2ef90c8e")


class _Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, n):
        if self.pos + n > len(self.data):
            raise Bad("evidence-shape", "truncated OpenTimestamps proof")
        b = self.data[self.pos:self.pos + n]
        self.pos += n
        return b

    def varuint(self):
        value, shift = 0, 0
        while True:
            b = self.take(1)[0]
            value |= (b & 0x7F) << shift
            if not b & 0x80:
                return value
            shift += 7

    def varbytes(self):
        return self.take(self.varuint())


def ots_parse(data):
    """Returns (file digest, list of (attestation kind, payload, commitment)). Linear and forked proofs."""
    r = _Reader(data)
    if r.take(len(OTS_MAGIC)) != OTS_MAGIC or r.take(1) != b"\x01":
        raise Bad("evidence-shape", "not an OpenTimestamps proof, version 1")
    if r.take(1) != b"\x08":
        raise Bad("evidence-shape", "file hash op must be sha256")
    digest = r.take(32)
    out = []

    def walk(msg, depth):
        if depth > 256:
            raise Bad("evidence-shape", "proof too deep")
        while True:
            tag = r.take(1)
            if tag == b"\xff":
                walk_one(msg, r.take(1), depth + 1)
                continue
            walk_one(msg, tag, depth + 1)
            return

    def walk_one(msg, tag, depth):
        if tag == b"\x00":
            kind = r.take(8)
            payload = r.varbytes()
            out.append((kind, payload, msg))
            return
        if tag == b"\xf0":
            msg = msg + r.varbytes()
        elif tag == b"\xf1":
            msg = r.varbytes() + msg
        elif tag == b"\x08":
            msg = hashlib.sha256(msg).digest()
        else:
            raise Bad("evidence-shape", f"unsupported op 0x{tag.hex()}")
        walk(msg, depth)

    walk(digest, 0)
    if r.pos != len(data):
        raise Bad("evidence-shape", "trailing bytes after proof")
    return digest, out


def headers_from_file(data):
    if len(data) % 80:
        raise Bad("evidence-shape", "header file length is not a multiple of 80")
    return [data[i:i + 80] for i in range(0, len(data), 80)]


def header_ok(chain, height):
    """Proof of work and linkage from the pinned first header to `height`."""
    for h in range(height + 1):
        hdr = chain[h]
        bits = int.from_bytes(hdr[72:76], "little")
        target = (bits & 0xFFFFFF) * (1 << (8 * ((bits >> 24) - 3)))
        if int.from_bytes(hashlib.sha256(hashlib.sha256(hdr).digest()).digest(), "little") > target:
            return False
        if h and hdr[4:36] != hashlib.sha256(hashlib.sha256(chain[h - 1]).digest()).digest():
            return False
    return True


def header_hash(hdr):
    return hashlib.sha256(hashlib.sha256(hdr).digest()).digest()


def linked_to_checkpoint(chain, height, checkpoint_height, checkpoint_sha256):
    """D3: the attested header must be an ancestor of a pinned checkpoint header. The checkpoint is the
    SHA-256 of the raw 80-byte header at `checkpoint_height`, taken from the verifier's own node. A fork cannot
    contain the checkpoint without reproducing every header back to the attested one."""
    if checkpoint_height >= len(chain) or hashlib.sha256(chain[checkpoint_height]).hexdigest() != checkpoint_sha256:
        return False
    for h in range(checkpoint_height, height, -1):
        if chain[h][4:36] != header_hash(chain[h - 1]):
            return False
    return True


def header_time(hdr):
    return datetime.fromtimestamp(int.from_bytes(hdr[68:72], "little"), tz=timezone.utc)
