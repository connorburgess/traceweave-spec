import copy
import tempfile
from pathlib import Path
import unittest

from jsonschema import ValidationError

from tools.validate import (
    PROMOTED_SCHEMAS, ROOT, VECTOR_CHECKERS, catalogue_commitment, dsse_pae,
    read_json, run_checker, schema_validator, validate_repository,
)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.statement = read_json(ROOT / "examples/statement.json")
        self.validator = schema_validator()

    def test_repository_vectors(self):
        validate_repository(run_checkers=False)

    def test_promoted_vector_checkers_exit_zero(self):
        for label, arguments in VECTOR_CHECKERS:
            with self.subTest(checker=label):
                code, output = run_checker(arguments)
                self.assertEqual(code, 0, output[-2000:])

    def test_promoted_schemas_are_canonical_and_valid(self):
        from jsonschema import Draft202012Validator
        for name in PROMOTED_SCHEMAS:
            with self.subTest(schema=name):
                schema = read_json(ROOT / "schemas" / f"{name}.schema.json")
                Draft202012Validator.check_schema(schema)
                self.assertFalse((ROOT / "test-vectors/matching" / f"{name}.schema.json").exists())

    def test_extraction_checker_rejects_a_tampered_vector(self):
        import json
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "extraction"
            shutil.copytree(ROOT / "test-vectors/extraction", copy, ignore=shutil.ignore_patterns("harness"))
            path = copy / "go.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            vector = next(v for v in data["vectors"] if v["result"].get("tokens"))
            vector["result"]["tokens"][0]["span"][1] += 1
            path.write_text(json.dumps(data, indent=1), encoding="utf-8")
            code, _ = run_checker([str(copy / "check_vectors.py")], cwd=copy)
            self.assertNotEqual(code, 0)

    def test_invalid_statement_contracts(self):
        cases = []
        for field, value in (("_type", "urn:in-toto:Statement:v1"), ("subject", []), ("extra", True)):
            changed = copy.deepcopy(self.statement)
            changed[field] = value
            cases.append(changed)
        for field, value in (("specVersion", "1.0.0"), ("recordedAt", "not-a-date"), ("timestamp", {"rfc3161": "2026-11-18T00:00:00Z"}), ("privateKey", "must-not-be-here")):
            changed = copy.deepcopy(self.statement)
            changed["predicate"][field] = value
            cases.append(changed)
        changed = copy.deepcopy(self.statement)
        changed["subject"][0]["digest"]["sha256"] = "ab12"
        cases.append(changed)
        changed = copy.deepcopy(self.statement)
        changed["predicate"]["catalogueCommitment"]["nonce"] = "public leak"
        cases.append(changed)
        for changed in cases:
            with self.subTest(changed=changed):
                with self.assertRaises(ValidationError):
                    self.validator.validate(changed)

    def test_commitment_rejects_wrong_nonce_length(self):
        for nonce in (b"", b"x" * 31, b"x" * 33):
            with self.subTest(length=len(nonce)), self.assertRaises(ValueError):
                catalogue_commitment(b"abc", nonce)

    def test_commitment_detects_changed_openings(self):
        nonce = bytes(range(32))
        original = catalogue_commitment(b"abc", nonce)
        self.assertNotEqual(original, catalogue_commitment(b"abc\n", nonce))
        self.assertNotEqual(original, catalogue_commitment(b"abc", nonce[::-1]))

    def test_pae_byte_lengths_and_field_boundaries(self):
        self.assertEqual(dsse_pae(b"x", "é".encode()), b"DSSEv1 1 x 2 \xc3\xa9")
        self.assertNotEqual(dsse_pae(b"ab", b"c"), dsse_pae(b"a", b"bc"))

    def test_ambiguous_or_nonstandard_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for content in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
                with self.subTest(content=content):
                    path.write_text(content)
                    with self.assertRaises(ValueError):
                        read_json(path)

    def test_image_mark_finding_aid_schema_and_boundary(self):
        from jsonschema import Draft202012Validator, FormatChecker
        schema = read_json(ROOT / "schemas/image-mark-finding-aid.schema.json")
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        doc = read_json(ROOT / "research/drafts/image-mark-finding-aid/fixtures.json")
        base = doc["valid"][0]["record"]
        validator.validate(base)
        bad_origin = copy.deepcopy(base)
        bad_origin["findingAidBoundary"]["provesOrigin"] = True
        with self.assertRaises(ValidationError):
            validator.validate(bad_origin)
        bad_secret = copy.deepcopy(base)
        bad_secret["keyReference"]["keyHex"] = "00" * 32
        with self.assertRaises(ValidationError):
            validator.validate(bad_secret)

    def test_intoto_core_accept_fixtures_match_statement_schema(self):
        import base64
        import json
        for name in ("accept-catalogue-core.json", "accept-catalogue-core-urlsafe.json"):
            with self.subTest(fixture=name):
                fx = read_json(ROOT / "test-vectors/intoto-adapter/accept" / name)
                payload_b64 = fx["envelope"]["payload"]
                raw = base64.b64decode(payload_b64, altchars=b"-_" if ("-" in payload_b64 or "_" in payload_b64) else None)
                self.validator.validate(json.loads(raw.decode("utf-8")))

    def test_record_schema_accepts_python_token_classes_and_error_codes(self):
        from jsonschema import Draft202012Validator, FormatChecker
        schema = read_json(ROOT / "schemas/record.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        base_examined = {
            "recordVersion": "traceweave-extraction-record-draft-1",
            "profile": "py-tokens",
            "profileVersion": "draft-1",
            "configSha256": "0" * 64,
            "inputSha256": "1" * 64,
            "inputLength": 10,
        }
        valid_tokens = copy.deepcopy(base_examined)
        valid_tokens["result"] = {
            "status": "insufficient-tokens",
            "tokenCount": 2,
            "tokens": [
                {"class": "fstring-start", "text": 'f"', "span": [0, 2]},
                {"class": "tstring-middle", "text": "x", "span": [2, 3]},
            ],
            "channels": {
                "exact": {"kgrams": [], "partialWindow": False, "windowSelections": [], "fingerprints": []},
                "normalized": {"kgrams": [], "partialWindow": False, "windowSelections": [], "fingerprints": [], "values": ["", "x"]},
            },
        }
        validator.validate(valid_tokens)
        for bad_class in ("fstring--start", "-start", "start-", "FString"):
            bad = copy.deepcopy(valid_tokens)
            bad["result"]["tokens"][0]["class"] = bad_class
            with self.subTest(bad_class=bad_class), self.assertRaises(ValidationError):
                validator.validate(bad)
        for err_code in ("inconsistent-indentation", "unmatched-dedent"):
            err_rec = copy.deepcopy(base_examined)
            err_rec["result"] = {"status": "error", "error": {"code": err_code, "offset": 4}}
            with self.subTest(err_code=err_code):
                validator.validate(err_rec)


if __name__ == "__main__":
    unittest.main()
