# Results: E-TXT-1 Stage 1 prose evaluation (TXT.4)

Protocol: [PROTOCOL.md](../../PROTOCOL.md), version `e-txt-1`, digest `642bb221f18b0a4efb1097ecbafa5da4f3f089dca018525b452db7e1cc5de2ce`, frozen at commit `c708b203165f3b1ea21e7205e3e1d91c16f946a4`, reviewed at commit `acebacb59c19fbbf27e9bf7b4c2894ba5a473c56` ([protocol review](../../../../reviews/text-stage1-protocol-review.md)).

Executed twice (`run-1`, `run-2`) under OS network denial (`scripts/offline`, macOS `sandbox-exec` deny-network) from a clean working tree on branch `txt4-run` at `acebacb59c19fbbf27e9bf7b4c2894ba5a473c56`, using stamped Rust (`traceweave` `0.0.1`) and Go (`traceweave-go` `0.2.0-dev`) binaries built from a clean export of implementation `main` at commit `a6066d39b3fd0a66466f7a89d4553fc249479c28` (`specCommit` `6437c26528ff87e91f86d9dcea37b45d20cd5064`).

- **`summary.json` SHA-256 (byte-identical across `run-1` and `run-2`):** `eeef3f21e4f657e91f86d9d9b82baa1d0896cf843e8e556adcb01d897cad3` (see [summary.json](summary.json) and [compare.txt](compare.txt))
- **Harness exit codes:** `run-1` exited `3`, `run-2` exited `3`, `harness.py compare` exited `0`
- **Verdict:** **`negative-result`** (criterion (iii) triggered: `35` misses where an unchanged run `>= 15` tokens shared `>= 49` fingerprints yet comparison under `minRegionDistinctHashes = 1, mergeGap = 8` produced `outcome = "ambiguous"` instead of `"match"`)

## Preconditions and TXT.4 failure criteria (i)–(iii)

| Check / Criterion | Count | Detail |
| --- | --- | --- |
| Clean tree & frozen ancestry | pass | `HEAD = acebacb59c19fbbf27e9bf7b4c2894ba5a473c56`, `frozenCommit = c708b203165f3b1ea21e7205e3e1d91c16f946a4`, `pinnedDigestsCount = 27` |
| OS network denial | pass | `bind:errno=1; loopback:errno=1(EPERM); public:errno=1(EPERM)` |
| Stamped CLI commits | pass | Rust `traceweave` & Go `traceweave-go`: `stamp = "stamped"`, `commit = a6066d39b3fd0a66466f7a89d4553fc249479c28`, `specCommit = 6437c26528ff87e91f86d9dcea37b45d20cd5064` |
| Two-run determinism | pass | `run-1` and `run-2` byte-identical `summary.json` (`eeef3f21e4f657e91f86d9d9b82baa1d0896cf843e8e556adcb01d897cad3`) |
| TXT.2 vectors verified | 154 / 154 | `text-plain.json`: 55, `limits-text.json`: 3, `text-markdown.json`: 21, `records-text-plain.json`: 60, `config-negative-text.json`: 15 |
| **Criterion (i)** CLI agreement | **0** | 0 exit/byte divergences or TXT.2 expectation mismatches across Rust and Go |
| **Criterion (ii)** Byte-span fidelity | **0** | 0 token, k-gram, fingerprint, or comparison region/seed span mismatches |
| **Criterion (iii)** Winnowing locality | **35** | 32 `folded` misses (`8` transforms × `4` files) + 3 `skeleton` misses (`confusable` × `3` files); all `35` shared `49..1169` fingerprints but returned `outcome = "ambiguous"` |

## Transformations (11 CC BY 4.0 prose files × 13 transforms = 143 cases)

| Transform | Recorded limit | Unchanged `folded` run ≥ 15 | `sharedFingerprints > 0` (`exact` / `folded` / `skeleton`) | `outcome == "match"` (`exact` / `folded` / `skeleton`) | Criterion (iii) misses |
| --- | --- | ---: | --- | --- | ---: |
| `reflow` | no | 11 / 11 | 11 / 11 / 11 | 8 / 7 / 8 | 4 (`folded` `ambiguous`) |
| `crlf` | no | 11 / 11 | 11 / 11 / 11 | 8 / 7 / 8 | 4 (`folded` `ambiguous`) |
| `nfc` | no | 11 / 11 | 11 / 11 / 11 | 8 / 7 / 8 | 4 (`folded` `ambiguous`) |
| `nfkc` | no | 11 / 11 | 11 / 11 / 11 | 9 / 7 / 8 | 4 (`folded` `ambiguous`) |
| `case-change` | no | 11 / 11 | 2 / 11 / 11 | 2 / 7 / 8 | 4 (`folded` `ambiguous`) |
| `zero-width-10` | no | 11 / 11 | 1 / 11 / 11 | 1 / 7 / 8 | 4 (`folded` `ambiguous`) |
| `confusable` | no | 0 / 11 (`11/11` `skeleton`) | 2 / 2 / 11 | 2 / 2 / 8 | 3 (`skeleton` `ambiguous`) |
| `markdown-strip` | no | 11 / 11 | 11 / 11 / 11 | 11 / 11 / 11 | 0 |
| `smart-quotes` | no | 11 / 11 | 11 / 11 / 11 | 8 / 7 / 8 | 4 (`folded` `ambiguous`) |
| `host-20x` | no | 11 / 11 | 11 / 11 / 11 | 8 / 7 / 8 | 4 (`folded` `ambiguous`) |
| `excerpt-kw1` | no | 11 / 11 | 11 / 11 / 11 | 11 / 11 / 11 | 0 |
| `distractor-kw2` | yes | 0 / 11 | 11 / 11 / 11 | 11 / 11 / 11 | 0 |
| `distractor-k1` | yes | 0 / 11 | 0 / 0 / 0 | 0 / 0 / 0 | 0 |

### Breakdown of the 35 Criterion (iii) misses

Every miss shared at least 49 fingerprints in the target channel, yet the comparison outcome under `minRegionDistinctHashes = 1, mergeGap = 8` was `ambiguous` rather than `match`:

- `folded` misses (32): `docs/sources.md` (`323` shared `folded` fingerprints), `docs/use-cases.md` (`1169` shared `folded` fingerprints; `1167` under `nfkc`), `profiles/README.md` (`49` shared `folded` fingerprints), and `profiles/code.md` (`423` shared `folded` fingerprints), across `reflow`, `crlf`, `nfc`, `nfkc`, `case-change`, `zero-width-10`, `smart-quotes`, and `host-20x`.
- `skeleton` misses (3): `docs/sources.md` (`339` shared `skeleton` fingerprints), `docs/use-cases.md` (`1138` shared `skeleton` fingerprints), and `profiles/code.md` (`407` shared `skeleton` fingerprints) under `confusable`. (`profiles/README.md` returned `match` in `skeleton` with `52` shared fingerprints.)

## Ordered negative pairs (`110` pairs) and boilerplate controls

| Comparison | `exact` | `folded` | `skeleton` |
| --- | ---: | ---: | ---: |
| Unsuppressed `minRegionDistinctHashes = 1` matches | **2 / 110** | **4 / 110** | **4 / 110** |
| Unsuppressed `minRegionDistinctHashes = 1` shared-fingerprint pairs | 2 / 110 | 4 / 110 | 4 / 110 |
| Unsuppressed `minRegionDistinctHashes = 1` self-pair matches (`11` pairs) | 8 / 11 | 7 / 11 | 8 / 11 |
| Unsuppressed `minRegionDistinctHashes = 2` matches | 2 / 110 | 0 / 110 | 0 / 110 |
| Unsuppressed `minRegionDistinctHashes = 2` shared-fingerprint pairs | 2 / 110 | 4 / 110 | 4 / 110 |
| Unsuppressed `minRegionDistinctHashes = 2` self-pair matches (`11` pairs) | 9 / 11 | 10 / 11 | 10 / 11 |
| Boilerplate-suppressed `minRegionDistinctHashes = 1` matches | 2 / 110 | 4 / 110 | 4 / 110 |
| Boilerplate cross-pairs (corpus × boilerplate, unsuppressed) | 0 / 66 | 0 / 66 | 0 / 66 |

- **Boilerplate catalogue SHA-256:** `9ea5e0521657fa2579a829fcc3cf438ca2411a5ad6f585324e46adf1e384c3fa`
- **Suppression control (`CONTRIBUTING.md` appended to `docs/evaluation.md`):** unsuppressed `{exact: "match", folded: "match", skeleton: "match"}`; suppressed `{exact: "common-only", folded: "common-only", skeleton: "common-only"}`.
