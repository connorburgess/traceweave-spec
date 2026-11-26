# Retention validation

Scope: local metadata, evidence-retention integrity and repository documentation checks. These checks do not run the products, reproduce experiments, render a browser, acquire dependencies or contact services. The author static build checks and independent correction checks remain separately described in [the record](README.md).

Validation results are recorded before committing this package. The exact final commit is reported separately so that this file does not attempt to hash itself or invent a future revision.

## Observed results

Used the existing pinned Python 3.12.14 environment and installed dependencies; no installation or acquisition. All checks below passed:

- `python tools/validate.py`: draft schemas, synthetic examples, fixture digests, commitment/DSSE framing vectors, local links, promoted schemas and vector checkers. Its explicit limit remains: no signature, timestamp authority, fingerprint detector or rights claim was verified.
- `python -m unittest discover -s tests -q`: 29 tests passed.
- `python tools/validate.py --links-all`: all local Markdown links passed. Public external URLs are pinned locators, not freshly contacted resources.
- `python tools/check_hygiene.py`: tracked tree passed. Final commit-message hygiene is also checked on the package's base-to-tip range after commit.
- `git diff --cached --check`: passed.
- Metadata/identity checks: 1,046 unique ledger IDs; 868 included and 178 excluded; every portable row matched the original metadata and all three UTF-8 field hashes plus its canonical original-row hash; 82 source Git blob/SHA identities checked against local pinned Git objects; 27 original artifact lengths/hashes matched unchanged bytes; all 12 Shelf and 14 website flagged IDs covered by the retained dispositions. No source re-extraction, text-map regeneration or app execution was needed.
- Publication-source safety: HEAD's accepted base was exact `d698811d743eef00de1121e4225ed2fad6cc4d1d`, descending from the curated lineage. Rejected revisions named by the publication-source workflow were not ancestors; the omitted raw blob was not reachable and its forbidden path was absent from the curated-source range. No omitted material was copied or encoded.
- Scope and preservation: every preexisting baseline file except the single WEB queue evidence-link addition was checked byte-for-byte equal. This includes all seven protected copied evidence JSON files, inspector/manifest, frozen data, ROADMAP criteria/status/counts/holds, publication-source workflow and public-history map. The complete changed-file list contains only the new records in this directory and `research/work-queue.md`. The source lineage branch, private branch and current public branch retain their original tips. No map regeneration or replay was performed.

The preceding author build/link results, and the reviewers' observed static correction checks, are separately attributed in [README](README.md). These retention checks add no runtime, visual, network, browser or gate acceptance evidence. No vector rebuild, product build, external service or new research experiment was run for retention.
