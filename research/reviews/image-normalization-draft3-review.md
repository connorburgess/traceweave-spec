# Independent review of image normalization draft-3

Reviewed 2026-11-26: exact commit **`fce78938e9fd7d80a7ddd2d06686a857bfc458d5`**, initially clean in the isolated worktree. This record reviews that commit, not a later amended proposal. The review changed no author file.

**Disposition: no blocking correctness finding.** The proposed contract removes the remaining ISCC grey/resize arithmetic discretion, and the independent recount below locates all twelve items enumerated by ROADMAP IMGF.1. Draft-3 plus this review is eligible evidence for a coordinator's research IMGF.1 acceptance. This record itself changes no gate, count, normative profile, experiment protocol or existing result identity. The 48-repository M3 evaluation remains held. M5 publication and separate TypeScript fixture repairs are outside this review.

## Findings and evidence limits

1. **Nonblocking fixture coverage gap: no exact grey half tie in the committed RGB inputs.** `check.py` has binary64 tie anchors and RGB primary anchors, but the fourteen RGB fixtures contain zero pixels for which `(19595*R+38470*G+7471*B) % 65536 == 32768`. Thus the committed grey examples do not directly distinguish half-up from ties-to-even grey conversion. A separate review anchor `(1,53,185)` has numerator `3440640 = 52*65536+32768`; the contract, ordinary implementation, and rational oracle all give **53** (ties-to-even would give 52). This is a coverage observation, not an observed implementation error or a blocker to the explicit formula. A future fixture revision could retain that anchor without modifying frozen draft-2 evidence.
2. **Source provenance verification is bounded.** The three upstream file URLs, commit and SHA-256 values in `primary-source-pins.json` exactly match the retained original proposal metadata. The wheel's `PIL/Image.py` directly hashes to the stated upstream wrapper hash `04050c2d4dd67931ce8c3cfdbc49ac4a6944d379d037c8f1d5eeeb67fba29a10`. The retained investigation saved no C-source bytes. Consequently this review does **not** independently rehash or reread upstream `Resample.c`/`Convert.c`, re-resolve tag 13.0.0, or establish the wheel compiler flags. No source acquisition was authorized. Those remain recorded source-inspection provenance, corroborated by the bounded compiled-target comparison; they are not a fresh upstream-source audit. This does not leave the new contract dependent on C implementation discretion: its equations are authoritative and its binary64 requirements are expressly a new portability contract.

No other actionable defect was found in the reviewed scope. The findings above do not establish all-domain equivalence; finite agreement is qualified throughout the proposal.

## Contract and arithmetic assessment

The new [draft](../drafts/extraction-profile-image-draft3.md) inherits draft-2 at `24bb4b8483dc86966cb7c8277130bb816b0c6b3f` and overrides precisely the conflicting grey/resize definition. RGB comes after decode, alpha flattening, orientation and trim. Integer grey is stored before resize; it is separate from PDQ luma. The grey formula, signed coefficient rounding and sample rounding have different, explicit semantics.

The resize text supplies full-box 32×32 geometry, pixel centres, widened support, truncated support endpoints, in-image edge taps and renormalization. It specifies binary64 ties-to-even after each elementary coefficient operation, parentheses and sum order, and prohibits FMA, reassociation and extended intermediates. Quantization uses signed 22-bit coefficients with ties away from zero; sample accumulation is exact signed integer arithmetic with a positive half offset, mathematical floor division and saturation. Coefficients need not sum to `2^22`. The two kernel branches and support boundary match both supplied programs on inspection.

Pass order uses the original dimensions and a strict inequality. Each performed pass rounds/clips to bytes; each axis retains its own original length. Axes of length 32 are skipped. Identity, single-axis changes, upscaling and one-pixel sides are defined. There is no new post-trim minimum-size rule. These rules are sufficient to implement without choosing library rounding or edge behavior.

`arithmetic.py` follows that contract using Python binary64 and exact integer sums; its vertical transpose is consistent with coordinate sampling. `oracle.py` imports neither that implementation nor Pillow. It evaluates rational elementary operations and rounds their results in software to a 53-bit significand, with ties-to-even; sign handling and the carry across a significand boundary are sound in the finite normal range exercised. Zero is handled explicitly. Subnormal/overflow handling is deliberately excluded by the oracle, rather than silently approximated; no claim of arbitrary binary64 emulation is warranted.

The oracle uses explicit x/y indexing instead of transposition, and integer output accumulation is separately written. However, both programs share the proposed kernel, support formulas, branch predicate and author. Fixture regeneration is a determinism check of that oracle, not independent correctness evidence. Agreement between those programs alone could hide a shared mistranscription. The independent wheel comparison and the review anchors below provide additional evidence against that risk, with finite-domain limits.

## Fourteen fixtures and two mutations reproduced

Used only the existing local CPython **3.14.6**, Darwin arm64, pinned experiment virtualenv and already provisioned wheel. No installation, download, decoder invocation, natural-image input, image study, hash-core evaluation, network probe or service was used. The bounded checks ran under `/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)'`.

The checker verified wheel SHA-256 **`d9b0a2bee3f3e03e9f29057aedb807dbf1e1d96ee1b9d0f422d9db6c8583271d`**, Pillow 13.0.0, and byte equality of the loaded `PIL/Image.py` and compiled `PIL/_imaging` against that wheel. Version strings alone were not the target identity check. Other Pillow modules and compiler flags are not independently attested by that check.

All fourteen cases agree on grey, first-pass and final bytes between the ordinary implementation, rational oracle, committed expectations and pinned Pillow. Coefficient tables agree between both arithmetic implementations and the committed aggregate digest. Fixture SHA-256 is **`94f2d1bc5027e474bdeb1718e16932b403ad171c418bf2ea63d964ef9e3f8981`**.

The reproduced JSON equals every field in the committed [comparison summary](../experiments/image-normalization-draft3/comparison-results.json); the fresh report additionally contains `pillowOutputHex` for every successful case, which the committed summary omits. This is not literal report byte identity. All reproduced target output bytes equal the fixture bytes.

| Fixture | Width × height | Order | Wrong-order differing final bytes / 1,024 | Final-only differing final bytes / 1,024 |
| --- | --- | --- | --- | --- |
| black | 32 × 32 | xy | 0 | 0 |
| white | 32 × 32 | xy | 0 | 0 |
| swatches | 32 × 32 | xy | 0 | 0 |
| identity | 32 × 32 | xy | 0 | 0 |
| width-only | 47 × 32 | xy | 0 | 0 |
| height-only | 32 × 47 | yx | 0 | 0 |
| noninteger | 37 × 41 | xy | 256 | 176 |
| order-equality | 48 × 64 | xy | 223 | 159 |
| vertical-first | 48 × 65 | yx | 236 | 183 |
| wide | 65 × 48 | xy | 232 | 183 |
| edge | 9 × 7 | xy | 31 | 22 |
| single-column | 1 × 9 | xy | 0 | 0 |
| single-row | 9 × 1 | xy | 0 | 0 |
| single-pixel | 1 × 1 | xy | 0 | 0 |

The equality fixture has `H-32 == 2*(W-32)` and correctly takes xy; the next-height fixture takes yx. Four identity-size fixtures do not exercise resampling. The single-pixel polynomial happens to be black. These are targeted cases, not fourteen independent population samples or complete boundary coverage.

Both mutations have five witnesses, including both order branches and their equality boundary. The final-only mutant retains unquantized intermediates and delays clipping/rounding; it tests that combined incorrect substitution, not rounding and clipping independently. All three `test_checker.py` tests passed: each injected wrong implementation makes the checker reject, and oracle regeneration is byte-identical. No expected file was regenerated on disk.

Reproduction commands, from repository root, with caller-supplied paths to the existing environment/artifact:

```sh
SB='(version 1)(allow default)(deny network*)'
/usr/bin/sandbox-exec -p "$SB" "$PINNED_PYTHON" -B \
  research/experiments/image-normalization-draft3/check.py \
  --pillow-wheel "$PILLOW_WHEEL" --report "$TMPDIR/imgf1-review-comparison.json"
/usr/bin/sandbox-exec -p "$SB" "$PINNED_PYTHON" -B -m unittest discover \
  -s research/experiments/image-normalization-draft3 -p test_checker.py
```

Both exited 0. Reuse the recorded pinned environment; these commands authorize no provisioning.

## Independent review anchors

A scratch review calculation used an expanded exact-rational Catmull–Rom polynomial, rather than copying either Horner evaluation. For dyadic axis sizes `1,2,4,8,16,64,128`, coordinates and unnormalized kernel operations fit exactly in binary64, so this algebraic route can be compared with the specified elementary-operation implementation. Normalized weights use Python's correctly rounded rational-to-float conversion. **224/224 coefficient rows** agreed with each supplied program. This check is deliberately restricted to these sizes; expanding a polynomial at arbitrary sizes would change rounding semantics.

Two concrete exact anchors:

- For `N=1`, every row is `(lo=0, q=[4194304])`, reproducing a constant pixel.
- For `N=64, j=0`, centre is 1, the taps are 0…4, and absolute distances are `1/4,1/4,3/4,5/4,7/4`. Raw kernel values are `[111,111,29,-9,-3]/128`, summing to `239/128`. Signed quantization of `4194304*[111,111,29,-9,-3]/239` gives **`[1947982,1947982,508932,-157945,-52648]`**, sum **4194303**. Both programs produce this exact row. This separately checks clipped edge normalization, negative lobes, signed rounding and the absence of coefficient-sum correction.

Core of the independent expanded-polynomial check (standard library; no Pillow):

```python
from fractions import Fraction as Q
# Import arithmetic and oracle from the reviewed conformance directory.
for n in (1, 2, 4, 8, 16, 64, 128):
    s = Q(n, 32)
    f = max(Q(1), s)
    table = []
    for j in range(32):
        c = Q(2*j+1, 2)*s
        lo = max(0, int(c-2*f+Q(1, 2)))
        hi = min(n, int(c+2*f+Q(1, 2)))
        raw = []
        for i in range(lo, hi):
            t = abs((Q(2*i+1, 2)-c)/f)
            raw.append(1-Q(5, 2)*t*t+Q(3, 2)*t**3 if t < 1 else
                       2-4*t+Q(5, 2)*t*t-Q(1, 2)*t**3 if t < 2 else Q(0))
        z = sum(raw)
        bs = [float(r/z if z else r) for r in raw]
        table.append((lo, [int(b*4194304+(-.5 if b < 0 else .5)) for b in bs]))
    assert table == arithmetic.coefficients(n) == oracle.weights(n)
```

This and the grey half-tie anchor passed under the same existing Python with network denied. They strengthen numerical checks without pretending to be a third complete resizer or an independent end-to-end implementation.

## Identity and frozen preservation

The draft-3 configuration is canonical sorted-key compact ASCII JSON plus LF; its SHA-256 independently recomputes to **`38b2dc7c534cc93e321160a9bba1f885e0106f8212760559d0c744f4ddb8654d`**. Inspection and the checker's AST comparison confirm exactly two extraction-field changes: `profileVersion` to `draft-3`, and `iscc.normalization` to `traceweave-iscc-normalization-draft-1`.

Independent AST extraction/canonicalization of the frozen configuration gives draft-2 extraction **`c740e92de69a47904fa81bb3614c086194717be856fa6a44d89ad6fdba3bb927`** and matching **`fe3fa0395d3701fa5b1b55839063998eba528851d4f9e3dcaca62d3a0f6c97ac`**. Matching, core, thresholds and quality rules are unchanged. New catalogues/reports must carry the new extraction identity even where output bytes agree; old evidence cannot be relabelled draft-3.

The checker verified all three frozen file hashes. In addition, the following Git diff exited 0 with no output:

```sh
git diff --exit-code 24bb4b8483dc86966cb7c8277130bb816b0c6b3f -- \
  research/drafts/extraction-profile-image.md research/drafts/image-experiment-protocol.md \
  research/experiments/image-fingerprint
```

The entire experiment tree at the reviewed commit is **`ff397613374a0c7487338be373c4fc0e91a4ab74`**, equal to `frozen-pins.json`. Thus preservation includes code, protocol/configuration and recorded `e-img-f-2` results, beyond the three-file runtime guard. No frozen run was executed.

## Independent IMGF.1 recount

Counted from ROADMAP's explicit criterion, then located each answer in the inherited profile and proposed replacement. Twelve distinct enumerated items, twelve mapped answers, no missing item or unresolved grey/resize choice:

| # | Criterion | Located answer |
| --- | --- | --- |
| 1 | Decoder and version | Draft-2 §§1, 3.8: Pillow/wheel, JPEG and zlib pins/settings |
| 2 | EXIF orientation | §3.9: JPEG-only transforms, identity fallback; PNG ignored |
| 3 | Colour conversion | §§3.7–11: accepted modes, integer/table conversion, ignored colour metadata |
| 4 | Alpha flattening | §3.10: white, integer half-up channel formula |
| 5 | Multi-frame policy | §3.5: abstain |
| 6 | Luminance formula | §4.1 PDQ ordered float64; draft-3 authoritative integer ISCC grey |
| 7 | Resize filter and size | §§4.2–4 PDQ blur/64×64 sampling; draft-3 complete ISCC 32×32 coefficient/pass arithmetic |
| 8 | Border crop | §4 full-image PDQ; §5.1 tolerant ISCC trim and single-side tolerance-8 condition |
| 9 | Hash algorithm and bit length | §§4.6–8 PDQ 256; §§5.5–6 ISCC v0 64 |
| 10 | Quality abstention threshold | §4.9 PDQ ≤49 abstains; §5.7 ISCC none |
| 11 | Dihedral variants | §§4.10, 5.8: eight query variants, catalogue original |
| 12 | Distance metric | §§4.11, 5.9 and 6: minimum Hamming, thresholds, ties and full within-threshold list |

Lane 10's prose additionally mentions vendor vectors after these twelve items. That extra evidence phrase is not silently counted as a thirteenth ROADMAP item: draft-2 §7 and IMGF.2 separately locate vendor/core conformance. This review does not revalidate those old results.

## Validation and limits

The existing repository Python 3.12 environment also passed local Markdown links (`tools/validate.py --links-all`), all **28** repository unit tests, and tree hygiene. These are local checks, not a claim about hosted CI. Final record validation also passed `tools/validate.py` (schemas, fixtures, local links and promoted vector checkers) and `git diff --check`.

The new evidence covers synthetic post-trim RGB-to-grey/resize arithmetic only. It does not cover decoding, correctness/reachability of trim boxes, ISCC DCT/digest, variants, matching, PDQ, SDK parity, cross-host/compiler agreement, all allowed dimensions or historical universal output equivalence. Small arrays are post-trim inputs and do not expand accepted decoded-image formats. The original proposal's suggested resulting ISCC digests are outside this narrower checker, explicitly disclosed rather than represented as tested.

IMGF.1 specification eligibility is distinct from IMGF.5 independent implementation evidence and IMGF.6 natural-image work. Neither is supplied here. No normative promotion, acquisition, full image study, natural-image performance claim, M3 work, gate/count edit, push, service or subagent was performed. Only this new review record is committed.

## Follow-up review: exact grey half-tie fixture

Independently reviewed exact **`db2848c1e8ec7c8465c066f5bff26863a803d440`** on 2026-11-26, initially clean in the same isolated worktree. This is an addendum to the exact-commit review above; it does not reinterpret the original fourteen-case evidence.

**Disposition: the nonblocking exact-grey-half-tie coverage gap is resolved by `db2848c1e8ec7c8465c066f5bff26863a803d440`. No new blocking or nonblocking defect was found in this narrow follow-up.** Draft-3 and the two reviews remain eligible evidence for coordinator acceptance of the research IMGF.1 specification criterion. No gate/count or normative status is changed here. The upstream C-source verification limitation in finding 2 remains in full.

Independent evidence:

- Direct integer calculation gives `19595*1 + 38470*53 + 7471*185 = 3440640 = 52*65536+32768`. Exact `Fraction(3440640,65536)` is `105/2`, so half-up is **53** and ties-to-even is **52**. This expectation does not come from either supplied arithmetic program or Pillow.
- The new `grey-half-tie` fixture is exactly 32×32, order `xy`, with RGB bytes `[1,53,185]` repeated 1,024 times. Each of `greyHex`, `firstHex` and `outputHex` is exactly 1,024 copies of `0x35`. Both axes are unchanged, isolating grey rounding from resampling. Both supplied arithmetic implementations agree with that independently derived expectation.
- A separate scratch mutation replaced `arithmetic.grey` with `round(Fraction(19595*r+38470*g+7471*b,65536))` per pixel. This uses Python's exact-rational ties-to-even operation rather than copying the author's quotient/remainder mutation. Every new-fixture grey byte becomes `0x34`. The checker rejects it with the single failure `grey-half-tie: fixture/arithmetic mismatch`; that fixture has **1,024/1,024 first-pass and final-byte differences**. This verifies rejection through ordinary output comparisons, beyond merely reporting that a mutant differs.
- The author's new quotient/remainder ties-to-even branch correctly handles both sides of a tie and odd/even quotients. Its witness list contains only `grey-half-tie`, with **1,024 grey-byte differences**. The dedicated fourth self-test injects the wrong grey implementation and asserts checker failure and 1,024 final-byte differences. Its integer anchor is separate from the oracle's expected-output calculation.
- Parsing old and new fixture JSON confirms that all fourteen prior cases are exactly unchanged, with no removals; only the new case is added. The aggregate coefficient digest is unchanged. Updated fixture SHA-256 is **`05797a1a742d9b53b5b57d4130bbc15216713f7eb8a5b3a06a1ed1e0413517ec`**. Fixture regeneration remains byte-identical in memory; no expected file was rewritten during review.

Reproduced the original bounded checker commands above using the same already provisioned CPython 3.14.6 / Darwin arm64 environment and pinned Pillow wheel, under `sandbox-exec` network denial. The target identity checks passed. All **15/15** cases agree on grey, first-pass and final bytes; coefficient checks pass; both resize mutations retain their original five witnesses each. The fresh report matches every committed summary field after removing the extra successful `pillowOutputHex` fields, and all four checker self-tests pass. Both commands exit 0.

Git preservation checks also exit 0 with empty diffs:

```sh
git diff --exit-code fce7893 db2848c -- \
  research/experiments/image-normalization-draft3/arithmetic.py \
  research/experiments/image-normalization-draft3/oracle.py \
  research/experiments/image-normalization-draft3/extraction-config.json \
  research/experiments/image-normalization-draft3/frozen-pins.json \
  research/experiments/image-normalization-draft3/primary-source-pins.json
git diff --exit-code 24bb4b8 db2848c -- \
  research/drafts/extraction-profile-image.md research/drafts/image-experiment-protocol.md \
  research/experiments/image-fingerprint
```

The draft-3 extraction digest stays **`38b2dc7c534cc93e321160a9bba1f885e0106f8212760559d0c744f4ddb8654d`**; draft-2 extraction, matching and frozen study identities remain as recorded above. The follow-up changes seven author files, limited to fixture generation, checker/self-test, comparison evidence and explanatory documentation. It changes no arithmetic contract, implementation, source pin or configuration. The twelve-item recount and original arithmetic assessment stand.

Local Markdown link validation, tree hygiene and the staged whitespace check passed for this addendum. This narrow review did not rerun unrelated repository tests or the full image experiment. No upstream source acquisition, new source-hash verification, natural-image evidence, SDK/end-to-end/cross-host equivalence, normative promotion, gate/count change, push, service or sublane is included. The 48-repository M3 evaluation remains held; M5 publication and separate TypeScript fixture repairs remain outside scope. Only this review addendum is committed.
