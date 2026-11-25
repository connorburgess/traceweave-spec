#!/usr/bin/env python3
"""Validate IMG.5 image-mark finding-aid schema and valid/invalid fixtures.

Run in isolated mode from the repository root:
  .venv/bin/python -I research/drafts/image-mark-finding-aid/check_finding_aid.py
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCHEMA_PATH = ROOT / "schemas" / "image-mark-finding-aid.schema.json"
FIXTURES_PATH = HERE / "fixtures.json"

REF_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
REF_PREFIX = "tw1-"
REF_BITS = 130
REF_PATTERN = re.compile(r"^tw1-[0-9A-HJKMNP-TV-Z]{27}$")
ORIGIN_CLAIM_TEXT = re.compile(
    r"(?i)\b(author(?:ship)?|creator|own(?:s|ed|er|ership)|origin(?:al|ality)?|first[- ]to[- ]create|"
    r"first[- ]creation|copyright|infring\w*|prove[sdn]?|proof|belongs?\s+to)\b"
)


def strict_load(path: Path):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError(f"Duplicate key {k!r} in {path}")
            out[k] = v
        return out

    def bad_const(val):
        raise ValueError(f"Invalid JSON constant {val!r} in {path}")

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=bad_const)


def luhn32_check(body: str) -> str:
    factor, total = 2, 0
    for ch in reversed(body):
        addend = factor * REF_ALPHABET.index(ch)
        factor = 1 if factor == 2 else 2
        total += addend // 32 + addend % 32
    return REF_ALPHABET[(32 - total % 32) % 32]


def text_reference(statement_sha256_hex: str) -> str:
    val = int(statement_sha256_hex, 16) >> (256 - REF_BITS)
    body = "".join(REF_ALPHABET[(val >> (5 * (25 - i))) & 31] for i in range(26))
    return REF_PREFIX + body + luhn32_check(body)


def semantic_errors(rec: dict) -> list[str]:
    errs: list[str] = []
    decode = rec["artifact"]["decode"]
    raw = rec["raw"]
    region = rec["region"]
    tb = rec["testedBits"]
    stat = rec["statistic"]
    thresh = rec["threshold"]
    outcome = rec["outcome"]

    if rec["carrier"]["algorithm"] in ("trustmark", "pixelseal") and not rec["carrier"]["models"]:
        errs.append("models-missing")

    if tb["end"] <= tb["start"] or tb["end"] > tb["rawBitCount"]:
        errs.append("tested-bits-range")
    if tb["end"] - tb["start"] != tb["count"] or tb["count"] != stat["n"]:
        errs.append("tested-bits-mismatch")

    if decode["status"] == "ok":
        if raw["status"] != "decoded":
            errs.append("decode-raw-mismatch")
        else:
            if len(raw["bitsHex"]) != (raw["bitCount"] + 3) // 4:
                errs.append("raw-hex-length")
            if raw["bitCount"] != tb["rawBitCount"]:
                errs.append("tested-bits-range")
        if region is None:
            errs.append("region-missing")
        else:
            if region["imageWidth"] != decode["width"] or region["imageHeight"] != decode["height"]:
                errs.append("region-size-mismatch")
            if region["x"] + region["width"] > region["imageWidth"] or region["y"] + region["height"] > region["imageHeight"]:
                errs.append("region-bounds")
            if region["scope"] == "whole-image" and (
                region["x"] != 0
                or region["y"] != 0
                or region["width"] != region["imageWidth"]
                or region["height"] != region["imageHeight"]
            ):
                errs.append("region-whole-image-mismatch")
    else:
        if raw["status"] != "abstain" or raw["code"] != decode["code"]:
            errs.append("decode-raw-mismatch")
        if region is not None:
            errs.append("region-on-abstain")

    accepted = stat["acceptedEntries"]
    for entry in accepted:
        if entry["n"] != stat["n"]:
            errs.append("statistic-n-mismatch")
        if entry["matchedBits"] < thresh["k"]:
            errs.append("threshold-violation")

    scope = thresh["searchScope"]
    expected_bound = min(1.0, scope["catalogueEntries"] * scope["keysSearched"] * thresh["perComparisonFalseAcceptBound"])
    if scope["perQueryUpperBound"] + 1e-12 < expected_bound:
        errs.append("search-scope-bound")

    if outcome["class"] == "match":
        if outcome["code"] != "expected-payload" or len(accepted) != 1:
            errs.append("outcome-mismatch")
        elif stat["matchedBits"] != accepted[0]["matchedBits"]:
            errs.append("statistic-matched-mismatch")
    elif outcome["class"] == "no-match":
        if outcome["code"] != "no-match" or len(accepted) != 0:
            errs.append("outcome-mismatch")
    elif outcome["class"] == "abstain":
        if outcome["code"] == "ambiguous":
            if len(accepted) < 2:
                errs.append("outcome-mismatch")
        else:
            if (
                decode["status"] != "abstain"
                or outcome["code"] != decode["code"]
                or accepted
                or stat["matchedBits"] is not None
            ):
                errs.append("outcome-mismatch")

    link = rec["registrationLink"]
    if link is not None:
        ref = link["textReference"]
        if not REF_PATTERN.fullmatch(ref):
            errs.append("reference-shape")
        elif luhn32_check(ref[len(REF_PREFIX):-1]) != ref[-1]:
            errs.append("reference-check")
        elif text_reference(link["statementSha256"]) != ref:
            errs.append("reference-mismatch")

    free_texts = [tb["excludedNote"], thresh["basis"], thresh["calibrationId"]]
    if link is not None:
        free_texts.append(link["note"])
    for text in free_texts:
        if ORIGIN_CLAIM_TEXT.search(text):
            errs.append("origin-claim-wording")

    return sorted(set(errs))


def apply_case(base_record: dict, case: dict) -> dict:
    rec = copy.deepcopy(base_record)
    if "mutations" in case:
        for mut in case["mutations"]:
            *parents, leaf, value = mut
            node = rec
            for key in parents:
                node = node[key]
            node[leaf] = value
    elif "mutation" in case:
        *parents, leaf, value = case["mutation"]
        node = rec
        for key in parents:
            node = node[key]
        node[leaf] = value
    elif "delete" in case:
        *parents, leaf = case["delete"]
        node = rec
        for key in parents:
            node = node[key]
        del node[leaf]
    else:
        raise ValueError(f"Invalid negative fixture spec: {case['id']}")
    return rec


def main() -> int:
    schema = strict_load(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    doc = strict_load(FIXTURES_PATH)
    valid_cases = doc["valid"]
    invalid_cases = doc["invalid"]
    if len(valid_cases) < 3 or len(invalid_cases) < 10:
        print("FAIL: insufficient finding-aid fixtures")
        return 1

    problems = 0
    for item in valid_cases:
        rec = item["record"]
        try:
            validator.validate(rec)
        except ValidationError as exc:
            print(f"FAIL valid/{item['id']}: schema rejected: {exc.message}")
            problems += 1
            continue
        serrs = semantic_errors(rec)
        if serrs:
            print(f"FAIL valid/{item['id']}: semantic errors {serrs}")
            problems += 1

    valid_by_id = {item["id"]: item["record"] for item in valid_cases}
    base_record = valid_cases[0]["record"]
    for item in invalid_cases:
        source_record = valid_by_id[item["baseId"]] if "baseId" in item else base_record
        rec = apply_case(source_record, item)
        expect = item["expect"]
        schema_failed = False
        try:
            validator.validate(rec)
        except ValidationError:
            schema_failed = True
        if expect == "schema":
            if not schema_failed:
                print(f"FAIL invalid/{item['id']}: expected schema rejection, but passed schema")
                problems += 1
        else:
            if schema_failed:
                print(f"FAIL invalid/{item['id']}: expected semantic code {expect!r}, but failed schema")
                problems += 1
                continue
            serrs = semantic_errors(rec)
            if serrs != [expect]:
                print(f"FAIL invalid/{item['id']}: expected [{expect}], got {serrs}")
                problems += 1

    # Self-test: every required top-level field deleted from valid_cases[0] must fail schema validation.
    required_top = schema["required"]
    for field in required_top:
        mutated = copy.deepcopy(base_record)
        del mutated[field]
        try:
            validator.validate(mutated)
            print(f"FAIL self-test: deleting required top-level field {field!r} passed schema")
            problems += 1
        except ValidationError:
            pass

    if problems:
        print(f"FAIL image-mark finding-aid check: {problems} problem(s)")
        return 1

    print(
        f"PASS image-mark finding-aid (IMG.5): {len(valid_cases)} valid, "
        f"{len(invalid_cases)} invalid, {len(required_top)}/{len(required_top)} required-field deletions rejected"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
