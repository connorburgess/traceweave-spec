import copy
import tempfile
from pathlib import Path
import unittest

from jsonschema import ValidationError

from tools.validate import (
    ROOT, catalogue_commitment, dsse_pae, read_json,
    schema_validator, validate_repository,
)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.statement = read_json(ROOT / "examples/statement.json")
        self.validator = schema_validator()

    def test_repository_vectors(self):
        validate_repository()

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


if __name__ == "__main__":
    unittest.main()
