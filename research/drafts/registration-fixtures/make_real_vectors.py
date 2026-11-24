#!/usr/bin/env python3
"""Make the real-format test vectors in real-format/ (design draft-3, section 6.5). Run once, by hand.

No external service is contacted. It uses:
  - the local `openssl` command, to create a test-only root CA and two test-only TSA certificates
    in a temporary directory and to issue RFC 3161 tokens over the digest of the fixture signature;
  - the standard library, to build an OpenTimestamps proof (python-opentimestamps format at
    8c3dc6fb) and a synthetic chain of Bitcoin-format block headers mined at regtest difficulty.

The private keys exist only in the temporary directory and are deleted at the end; only
certificates, requests, responses, proofs and headers are written to real-format/. The tokens
are not reproducible (they carry the issuing time and a random nonce), so this script is not part
of build_fixtures.py; the checker verifies what it wrote. Rerun it after any change to the
registration statement, because the tokens are bound to the statement's signature.

Usage: python3 -I make_real_vectors.py
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "real-format"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B = load("build_fixtures", HERE / "build_fixtures.py")
RF = B.C.RF
OPENSSL = "openssl"

CNF = """[req]
distinguished_name = dn
prompt = no
[dn]
CN = Traceweave TEST-ONLY root CA (never trust)
[v3_ca]
basicConstraints = critical,CA:true
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
[v3_tsa]
basicConstraints = critical,CA:false
keyUsage = critical,digitalSignature,nonRepudiation
extendedKeyUsage = critical,timeStamping
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid
[v3_ee]
basicConstraints = critical,CA:false
keyUsage = critical,digitalSignature
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid
[v3_int]
basicConstraints = critical,CA:true
keyUsage = critical,keyCertSign,cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid
[v3_tsa_noncrit]
basicConstraints = critical,CA:false
keyUsage = critical,digitalSignature,nonRepudiation
extendedKeyUsage = timeStamping
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid
"""
TSCNF = """[tsa]
default_tsa = tsa_config
[tsa_config]
serial = ./serial
crypto_device = builtin
signer_digest = sha256
default_policy = 2.999.1
digests = sha256
accuracy = secs:1
ordering = no
tsa_name = no
ess_cert_id_chain = no
ess_cert_id_alg = sha256
"""


def run(*args, cwd):
    return subprocess.run([OPENSSL, *args], cwd=cwd, check=True, capture_output=True).stdout


def der(path, cwd):
    return run("x509", "-in", path, "-outform", "DER", cwd=cwd)


def resign(resp, tmp, key, cert_der=None, serial=None, ess_hash=None):
    """Re-sign a TimeStampResp after editing it: optional replacement signer certificate and serial,
    optional ESSCertIDv2 hash. The RSA operation is done by `openssl pkeyutl` with the given key."""
    tree = RF.parse(resp)
    sd = tree[1][1][0]
    si = sd.children[-1][0]
    if cert_der is not None:
        certs = next(c for c in sd.children if c.tag == 0xA0)
        certs.children[0] = RF.parse(cert_der)
        si.children[1].children[1] = RF.Node(0x02, bytes([serial]))
    for attr in si[3].children:
        if RF.oid(attr[0]) == RF.OID_SIGNING_CERT_V2 and ess_hash is not None:
            cid = attr[1][0][0][0]
            idx = 0 if cid[0].tag == 0x04 else 1
            cid.children[idx] = RF.Node(0x04, ess_hash)
    signed = RF.encode(RF.Node(0x31, children=si[3].children))
    (tmp / "attrs.sha256").write_bytes(hashlib.sha256(signed).digest())
    sig = run("pkeyutl", "-sign", "-inkey", key, "-in", "attrs.sha256", "-pkeyopt", "digest:sha256", cwd=tmp)
    si.children[5] = RF.Node(0x04, sig)
    return RF.encode(tree)


def varuint(n):
    out = b""
    while True:
        b = n & 0x7F
        n >>= 7
        out += bytes([b | (0x80 if n else 0)])
        if not n:
            return out


def varbytes(b):
    return varuint(len(b)) + b


def mine(prev, merkle, t):
    bits = 0x207FFFFF
    target = (bits & 0xFFFFFF) * (1 << (8 * ((bits >> 24) - 3)))
    for nonce in range(1 << 32):
        hdr = (4).to_bytes(4, "little") + prev + merkle + t.to_bytes(4, "little") + bits.to_bytes(4, "little") + nonce.to_bytes(4, "little")
        h = hashlib.sha256(hashlib.sha256(hdr).digest()).digest()
        if int.from_bytes(h, "little") <= target:
            return hdr, h
    raise RuntimeError("no nonce")


def chain(attested_merkle, label, height=4, length=13, genesis=None, attested_time=None):
    """Header 0 at 2026-11-23T10:32:00Z, one header every 600 s, so height 4 is at 11:12:00Z.
    With `genesis`, the chain is re-mined on top of that header (a fork); `attested_time` overrides
    the attested header's time (the forged-time attack of review item D3)."""
    t0 = 1795429920  # 2026-11-23T10:32:00Z
    headers, prev = [], b"\x00" * 32
    if genesis is not None:
        headers, prev = [genesis], hashlib.sha256(hashlib.sha256(genesis).digest()).digest()
    for h in range(len(headers), length):
        merkle = attested_merkle if h == height else hashlib.sha256(f"{label} {h}; test only".encode()).digest()
        t = attested_time if (h == height and attested_time is not None) else t0 + 600 * h
        hdr, prev = mine(prev, merkle, t)
        headers.append(hdr)
    return b"".join(headers)


def main():
    OUT.mkdir(exist_ok=True)
    sig = B.envelope(B.statement())[1][0]
    digest = hashlib.sha256(sig).hexdigest()
    other = hashlib.sha256(B.C.jcs(B.statement())).hexdigest()
    manifest = {"note": "Real-format TEST vectors made locally by make_real_vectors.py; no external service. Never trust these anchors.",
                "openssl": run("version", cwd=HERE).decode().strip(), "targetSha256": digest, "files": {}}
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as tmpname:
        tmp = Path(tmpname)
        (tmp / "ca.cnf").write_text(CNF)
        (tmp / "ts.cnf").write_text(TSCNF)
        (tmp / "serial").write_text("01\n")
        run("req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", "ca.key", "-out", "ca.pem", "-days", "3650",
            "-config", "ca.cnf", "-extensions", "v3_ca", "-set_serial", "1", cwd=tmp)
        for name, serial in (("tsa", "2"), ("tsa_noncrit", "3")):
            run("req", "-newkey", "rsa:2048", "-nodes", "-keyout", f"{name}.key", "-out", f"{name}.csr",
                "-subj", f"/CN=Traceweave TEST-ONLY {name} (never trust)", cwd=tmp)
            run("x509", "-req", "-in", f"{name}.csr", "-CA", "ca.pem", "-CAkey", "ca.key", "-out", f"{name}.pem", "-days", "1825",
                "-extfile", "ca.cnf", "-extensions", f"v3_{name}", "-set_serial", serial, cwd=tmp)
        # D4: a TSA certificate issued by an end-entity certificate, and one under an intermediate expired in 2021.
        run("req", "-newkey", "rsa:2048", "-nodes", "-keyout", "ee.key", "-out", "ee.csr", "-subj", "/CN=Traceweave TEST-ONLY end entity (never trust)", cwd=tmp)
        run("x509", "-req", "-in", "ee.csr", "-CA", "ca.pem", "-CAkey", "ca.key", "-out", "ee.pem", "-days", "1825",
            "-extfile", "ca.cnf", "-extensions", "v3_ee", "-set_serial", "4", cwd=tmp)
        run("req", "-newkey", "rsa:2048", "-nodes", "-keyout", "int.key", "-out", "int.csr", "-subj", "/CN=Traceweave TEST-ONLY expired intermediate (never trust)", cwd=tmp)
        run("x509", "-req", "-in", "int.csr", "-CA", "ca.pem", "-CAkey", "ca.key", "-out", "int.pem", "-not_before", "20200101000000Z",
            "-not_after", "20210101000000Z", "-extfile", "ca.cnf", "-extensions", "v3_int", "-set_serial", "5", cwd=tmp)
        for name, ca, serial in (("tsa_by_ee", "ee", "6"), ("tsa_by_int", "int", "7")):
            run("req", "-newkey", "rsa:2048", "-nodes", "-keyout", f"{name}.key", "-out", f"{name}.csr",
                "-subj", f"/CN=Traceweave TEST-ONLY {name} (never trust)", cwd=tmp)
            run("x509", "-req", "-in", f"{name}.csr", "-CA", f"{ca}.pem", "-CAkey", f"{ca}.key", "-out", f"{name}.pem", "-days", "1825",
                "-extfile", "ca.cnf", "-extensions", "v3_tsa", "-set_serial", serial, cwd=tmp)
        files = {"test-root-ca.der": der("ca.pem", tmp)}
        for label, dg in (("", digest), ("-other-digest", other)):
            run("ts", "-query", "-digest", dg, "-sha256", "-cert", "-out", f"q{label}.tsq", cwd=tmp)
            run("ts", "-reply", "-config", "ts.cnf", "-queryfile", f"q{label}.tsq", "-signer", "tsa.pem", "-inkey", "tsa.key",
                "-out", f"r{label}.tsr", cwd=tmp)
            files[f"rfc3161-request{label}.der"] = (tmp / f"q{label}.tsq").read_bytes()
            files[f"rfc3161-response{label}.der"] = (tmp / f"r{label}.tsr").read_bytes()
        for label, signer, chain_pem in (("-issued-by-end-entity", "tsa_by_ee", "ee.pem"), ("-expired-intermediate", "tsa_by_int", "int.pem")):
            run("ts", "-reply", "-config", "ts.cnf", "-queryfile", "q.tsq", "-signer", f"{signer}.pem", "-inkey", f"{signer}.key",
                "-chain", chain_pem, "-out", f"r{label}.tsr", cwd=tmp)
            files[f"rfc3161-response{label}.der"] = (tmp / f"r{label}.tsr").read_bytes()
        good = files["rfc3161-response.der"]
        fields = RF.parse_response(good)
        gt = fields["genTime"].strftime("%Y%m%d%H%M%S").encode()
        pos = good.index(gt, good.index(fields["tstDer"])) + len(gt) - 1  # last digit of genTime
        tampered = bytearray(good)
        tampered[pos] = ord("0") + (tampered[pos] - ord("0") + 1) % 10
        files["rfc3161-response-tampered.der"] = bytes(tampered)
        noncrit = der("tsa_noncrit.pem", tmp)
        files["rfc3161-response-noncritical-eku.der"] = resign(good, tmp, "tsa_noncrit.key", cert_der=noncrit, serial=3,
                                                               ess_hash=hashlib.sha256(noncrit).digest())
        files["rfc3161-response-wrong-ess.der"] = resign(good, tmp, "tsa.key", ess_hash=hashlib.sha256(noncrit).digest())
        # Cross-check every token against openssl (review item D4): record its verdict.
        manifest["opensslVerify"] = {}
        for name, data in sorted(files.items()):
            if not name.startswith("rfc3161-response"):
                continue
            (tmp / "check.tsr").write_bytes(data)
            query = "q-other-digest.tsq" if "other-digest" in name else "q.tsq"
            res = subprocess.run([OPENSSL, "ts", "-verify", "-queryfile", query, "-in", "check.tsr", "-CAfile", "ca.pem",
                                  "-untrusted", "ee.pem", "-untrusted", "int.pem"], cwd=tmp, capture_output=True, text=True)
            lines = [l for l in (res.stdout + res.stderr).splitlines() if "Verification" in l or "error" in l.lower()]
            manifest["opensslVerify"][name] = " | ".join(l.split(":", 5)[-1].strip() if "error" in l.lower() else l.strip() for l in lines[:3])
        for name in ("ca.key", "tsa.key", "tsa_noncrit.key", "ee.key", "int.key", "tsa_by_ee.key", "tsa_by_int.key"):
            os.remove(tmp / name)
    nonce = hashlib.sha256(b"traceweave OpenTimestamps fixture nonce; test only").digest()[:16]
    leaf = hashlib.sha256(b"traceweave OpenTimestamps fixture other leaf; test only").digest()
    step = hashlib.sha256(bytes.fromhex(digest) + nonce).digest()
    merkle = hashlib.sha256(leaf + step).digest()
    head = RF.OTS_MAGIC + b"\x01" + b"\x08" + bytes.fromhex(digest) + b"\xf0" + varbytes(nonce) + b"\x08"
    files["opentimestamps-proof.ots"] = head + b"\xf1" + varbytes(leaf) + b"\x08" + b"\x00" + RF.OTS_BITCOIN + varbytes(varuint(4))
    files["opentimestamps-pending.ots"] = head + b"\x00" + RF.OTS_PENDING + varbytes(varbytes(b"https://calendar.invalid/"))
    other_proof_digest = hashlib.sha256(b"not the fixture signature").digest()
    files["opentimestamps-other-digest.ots"] = RF.OTS_MAGIC + b"\x01\x08" + other_proof_digest + b"\x00" + RF.OTS_BITCOIN + varbytes(varuint(4))
    headers = chain(merkle, "traceweave synthetic chain")
    files["headers.bin"] = headers
    # D3: the same pinned first header, re-mined at the same easy difficulty with the proof's commitment at
    # height 4 and a forged time of 2001-01-01T00:00:00Z.
    files["headers-forked.bin"] = chain(merkle, "forged branch", genesis=headers[:80], attested_time=978307200)
    manifest["checkpoint"] = {"height": 12, "headerSha256": hashlib.sha256(headers[12 * 80:13 * 80]).hexdigest()}
    files["headers-other.bin"] = headers[:80] + chain(hashlib.sha256(b"different").digest(), "other branch")[80:]
    for name, data in sorted(files.items()):
        (OUT / name).write_bytes(data)
        manifest["files"][name] = hashlib.sha256(data).hexdigest()
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("wrote", len(files), "files to", OUT.name)
    for name, verdict in manifest["opensslVerify"].items():
        print(f"  openssl ts -verify {name}: {verdict}")


if __name__ == "__main__":
    main()
