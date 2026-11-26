# TS.2 exclusion-decision and stage-1 pairing evidence

Author resolution based on `1c8f09a62faabfa2304b14315ee80d1b324304d7`, addressing the held TS.2 recommendation in [the portable non-author recount](img-ts-txt-criterion-recount.md). Independent review of this new evidence is required. This document does not mark TS.2, IMG.5, TS.1, TXT.1 or TXT.2 met, or change any gate wording/count.

## Exclusion-decision coverage

The missing file-selection judgments now live in [selection-decisions.json](../../test-vectors/extraction-typescript/selection-decisions.json): **55 hand-authored cases**, checked by [check_selection.py](../../test-vectors/extraction-typescript/check_selection.py). They apply the existing `profiles/typescript.md` §2 rules:

| Rule | Positive and negative boundary evidence |
| --- | --- |
| Declaration filenames | `.d.ts`, `.d.mts`, `.d.cts`, `*.d.*.ts` including multiple intermediate components; near patterns/case/suffixes that do not qualify. A `.tsx` near-pattern is deferred rather than extracted. |
| Generated markers | Both exact markers at the beginning, ending at byte 2048, crossing to 2049 and starting after 2048; case/partial-marker near misses; multibyte prefix distinguishing bytes from characters. |
| Minified filenames | `.min.js`, `.min.mjs`, `.min.cjs`; `.min.ts`, case differences, embedded/extended suffixes and `minimum` near misses. |
| Minified line length | 4096 accepted versus 4097 excluded, including multibyte UTF-8. LF, CR, CRLF, LS and PS split two at-limit lines; an over-limit second line is still excluded. |
| Stage boundary | `.tsx`/`.jsx` and known JSX in `.js` deferred; a D-16 self-closing case remains deferred even though lexing could succeed. A TS type assertion is not guessed to be JSX. |

`inputParts` expresses literal content/repetition; expected decisions and rationales were written independently of the selector. The adapter supplies no product behavior. `jsxKnown` is declared fixture knowledge, not a detection method. Exclusion is a selection decision, never a lexical error. The fixtures do not decide directory policies or precedence for files satisfying both exclusion and deferral predicates. Unsupported filenames and such overlapping cases are outside this adapter's evidence; no new selection semantics are defined.

All **24/24 wrong-selector variants** are rejected by the committed expectations: omitted declaration rules/patterns, overbroad declaration matching, 2047/2049/all-file/character-indexed marker windows, omitted markers, case-folded/partial markers, missing/overbroad minified suffix rules, LF-only/missing-LF/LS/PS splitting, character-counted lines, inclusive length threshold, missing line limit and missing deferral. These test sensitivity against realistic wrong rule choices, not only malformed fixture JSON.

## Pairing repair without changing frozen vectors

The original checker resolved every paired pointer across both TS and deferred TSX fixtures. The independent recount found that two of 47 stage-1 positives depended on deferred TSX errors. The [supplemental stage-1 pair file](../../test-vectors/extraction-typescript/stage1-rejection-pairs.json) supplies explicit overrides:

| Positive | Historical deferred partner (unchanged) | New stage-1 rejected input |
| --- | --- | --- |
| `ts-html-comment` | `tsx-err-html-comment` | Original bytes followed by `/*`; `unterminated-comment` at the appended opener. |
| `ts-type-assertion` | `tsx-err-ts-type-assertion` | Original bytes followed by `)`; `unbalanced-delimiter` at that closer. |

The additional errors are hand-derived and checked against the existing frozen-profile lexer, with exact expected code and UTF-8 offset. The adapter verifies the malformed suffix relation to each original positive, both override IDs, no unused supplemental error, and **47/47** positive-to-error pairings using only stage-1 input fixtures. The two original pointers remain useful historical cross-profile contrasts; neither is counted as stage-1 error behavior.

This resolves the stronger within-stage pairing reading as well as the missing exclusion classes. The prior recount remains a historical review of the old evidence, not an independent approval of these repairs. **TS.2 remains held pending non-author review.**

## Identity, validation and limits

Both new JSON files carry SHA-256 identities for the unchanged `profiles/typescript.md`, `ts.json`, `limits-ts.json`, `config-ts.json`, and `config-ts-limit16.json`, plus the exact source revision. The checker refuses source drift. Original token outputs, errors, hashes, configuration digests, profile versions and frozen vector bytes are unchanged. The sidecar does not standardize a new wire format or confer TSX support. The portable recount's independent arithmetic script still reproduces its recorded result.

The new checker is wired into `tools/validate.py`; `tests/test_contract.py` adds **14 adversarial evidence corruptions** covering exclusion/boundary/deferral decisions, a missing boundary, a duplicate fixture, a source identity mismatch, wrong rejection code/offset, a missing override and a deferred partner. Each must exit 1 with a clean `FAIL TS.2` message. Existing extraction checkers and self-tests remain in place.

Validation passed using the pinned development environment: `tools/validate.py`; `tools/validate.py --links-all`; `python -m unittest discover -s tests -v` (**29/29**, including the 14 evidence-corruption subcases); `tools/check_hygiene.py`; and `git diff --cached --check`. The portable arithmetic script also passed and its parsed JSON exactly equals the committed recount result. No download, corpus/study run, external service, push or sublane is part of this work. Queue reconciliation and image-profile draft work are outside this change.
