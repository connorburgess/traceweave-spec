"""Validate trusted repository fixtures; this is not an attestation verifier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = b"Traceweave-Catalogue-v0.1\x00"


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"Invalid JSON constant: {value}")


def read_json(path):
    return json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )


def catalogue_commitment(catalogue: bytes, nonce: bytes) -> str:
    if not isinstance(catalogue, bytes) or not isinstance(nonce, bytes):
        raise TypeError("Catalogue and nonce must be bytes")
    if len(nonce) != 32:
        raise ValueError("Nonce must be exactly 32 bytes")
    framed = DOMAIN + nonce + len(catalogue).to_bytes(8, "big") + catalogue
    return hashlib.sha256(framed).hexdigest()


def dsse_pae(payload_type: bytes, body: bytes) -> bytes:
    if not isinstance(payload_type, bytes) or not isinstance(body, bytes):
        raise TypeError("PAE operates on bytes")
    return (
        b"DSSEv1 " + str(len(payload_type)).encode("ascii") + b" "
        + payload_type + b" " + str(len(body)).encode("ascii") + b" " + body
    )


def schema_validator():
    schemas = [read_json(p) for p in sorted((ROOT / "schemas").glob("*.schema.json"))]
    registry = Registry()
    for schema in schemas:
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    # No retrieval callback: unknown schema references cannot cause network requests.
    return Draft202012Validator(
        read_json(ROOT / "schemas/statement.schema.json"),
        registry=registry,
        format_checker=FormatChecker(),
    )


SKIPPED_DIRECTORIES = {".git", ".venv", "node_modules", "target", "__pycache__"}


def check_links(all_markdown=False):
    """Check local Markdown links. By default the core directories; with
    all_markdown=True every Markdown file in the repository (research included)."""
    if all_markdown:
        files = [
            path for path in ROOT.rglob("*.md")
            if not SKIPPED_DIRECTORIES.intersection(path.relative_to(ROOT).parts)
        ]
    else:
        files = list(ROOT.glob("*.md"))
        for directory in ("spec", "profiles", "docs", "schemas", "examples", "test-vectors"):
            files.extend((ROOT / directory).rglob("*.md"))
    failures = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        # Examples inside fenced blocks and inline code are not links.
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        text = re.sub(r"(`+)(?:(?!\1).)+?\1", "", text)
        for target in re.findall(r"\]\(([^)\s]+)\)", text):
            target = target.strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or not parsed.path:
                continue
            resolved = (path.parent / unquote(parsed.path)).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                failures.append(f"{path.relative_to(ROOT)}: {target}")
    if failures:
        raise ValueError("Broken local links:\n" + "\n".join(failures))


# Independent checkers for the promoted experimental vector sets. Each is run in
# isolated mode (-I) from the repository root and must exit 0. They validate
# recorded outputs; none is an extractor, matcher or verifier.
VECTOR_CHECKERS = (
    ("extraction", ("test-vectors/extraction/check_vectors.py",)),
    ("extraction (matching-vector token files)", (
        "test-vectors/extraction/check_vectors.py",
        "test-vectors/matching/extraction-go.json",
        "test-vectors/matching/extraction-rust.json",
    )),
    ("matching (with self-tests)", ("test-vectors/matching/check_matching.py",)),
    ("typescript", ("test-vectors/extraction-typescript/check_vectors.py",)),
    ("text", ("test-vectors/extraction-text/check_text_vectors.py",)),
)
PROMOTED_SCHEMAS = ("catalogue", "report", "record")


def run_checker(arguments, cwd=ROOT):
    """Run one promoted checker; returns (exit code, combined output)."""
    completed = subprocess.run(
        [sys.executable, "-I", *arguments],
        cwd=cwd, capture_output=True, text=True, check=False,
    )
    return completed.returncode, completed.stdout + completed.stderr


def check_promoted_schemas():
    for name in PROMOTED_SCHEMAS:
        path = ROOT / "schemas" / f"{name}.schema.json"
        Draft202012Validator.check_schema(read_json(path))


def check_vector_checkers():
    failures = []
    for label, arguments in VECTOR_CHECKERS:
        code, output = run_checker(arguments)
        if code != 0:
            failures.append(f"{label}: exit {code}\n{output[-2000:]}")
    if failures:
        raise ValueError("Vector checker failures:\n" + "\n".join(failures))


def validate_repository(run_checkers=True):
    statement = read_json(ROOT / "examples/statement.json")
    schema_validator().validate(statement)
    predicate = statement["predicate"]
    artifact_digest = hashlib.sha256((ROOT / "examples/artifact.txt").read_bytes()).hexdigest()
    if statement["subject"][0]["digest"]["sha256"] != artifact_digest:
        raise ValueError("Artifact fixture digest mismatch")
    config_digest = hashlib.sha256((ROOT / "examples/profile-config.json").read_bytes()).hexdigest()
    if predicate["profile"]["configSha256"] != config_digest:
        raise ValueError("Profile configuration digest mismatch")
    vector = read_json(ROOT / "test-vectors/commitment.json")
    catalogue_path = (ROOT / vector["catalogue"]).resolve()
    if not catalogue_path.is_relative_to(ROOT):
        raise ValueError("Fixture path outside repository")
    commitment = catalogue_commitment(catalogue_path.read_bytes(), bytes.fromhex(vector["nonceHex"]))
    if commitment != vector["expectedSha256"] or commitment != predicate["catalogueCommitment"]["sha256"]:
        raise ValueError("Commitment vector mismatch")
    catalogue = read_json(catalogue_path)
    if catalogue["profile"] != predicate["profile"]:
        raise ValueError("Catalogue profile mismatch")
    if catalogue["references"][0]["artifactSha256"] != artifact_digest:
        raise ValueError("Catalogue artifact mismatch")
    for vector in read_json(ROOT / "test-vectors/dsse-pae.json"):
        actual = dsse_pae(vector["type"].encode("utf-8"), vector["body"].encode("utf-8"))
        if actual != vector["expectedUtf8"].encode("utf-8"):
            raise ValueError("DSSE PAE vector mismatch")
    check_promoted_schemas()
    check_links()
    if run_checkers:
        check_vector_checkers()


if __name__ == "__main__":
    if "--links-all" in sys.argv[1:]:
        check_links(all_markdown=True)
        print("PASS: local Markdown links in every Markdown file")
        raise SystemExit(0)
    validate_repository()
    print("PASS: draft schemas, synthetic examples, fixture digests, commitment and DSSE framing vectors, local links, promoted schemas and vector checkers")
    print("No signature, timestamp authority, fingerprint detector, or rights claim was verified.")
