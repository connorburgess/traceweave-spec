# Image-mark finding-aid fixtures (IMG.5 draft proposal)

These fixtures accompany [image-mark-finding-aid.md](../image-mark-finding-aid.md) and validate against [schemas/image-mark-finding-aid.schema.json](../../../schemas/image-mark-finding-aid.schema.json). They demonstrate the six IMG.5 detection-record fields, the explicit non-origin boundary, and optional linkage to a `tw1-` M4 registration record (`statementSha256` + `textReference`).

- `fixtures.json`: 5 valid records derived from committed `e-img-m-2` outputs (`tm:m2000000:jpeg90`, `tm:m2000000` marked-entry, `ps:m2000000:clean`, `tm:m2000000:cover`, and a decode-abstention case) plus 24 invalid records covering schema rejections, missing/broken IMG.5 fields, origin-proof violations, free-text origin/authorship claim wording, secret key injection, invalid `tw1-` references, cross-field invariants, and semantic inconsistencies.
- `check_finding_aid.py`: validates the schema, all valid and invalid fixtures, and a required-field deletion self-test. Standard library + `jsonschema` (`tools/validate.py` runs it).

```sh
.venv/bin/python -I research/drafts/image-mark-finding-aid/check_finding_aid.py
```
