# Proposed image fingerprint profile draft-3: explicit ISCC normalization

Status: separate research proposal, 2026-11-26; not promoted, not a gate closure. This extends [draft-2](extraction-profile-image.md) only by specifying ISCC grey/resize arithmetic. It preserves that file, its configuration, the frozen `e-img-f-2` protocol/code and recorded results. The [bounded conformance directory](../experiments/image-normalization-draft3/README.md) supplies two arithmetic implementations, fixtures and a separate pinned Pillow comparison. Finite synthetic agreement is not universal equivalence or natural-image evidence.

## Identity and inherited scope

Profile id: `traceweave-image-fingerprint`; proposed version: `draft-3`. Exact extraction bytes are [extraction-config.json](../experiments/image-normalization-draft3/extraction-config.json), sorted-key compact ASCII JSON with one final LF; SHA-256 **`38b2dc7c534cc93e321160a9bba1f885e0106f8212760559d0c744f4ddb8654d`**. Relative to draft-2 only `profileVersion` and `iscc.normalization` change; the latter becomes `traceweave-iscc-normalization-draft-1`.

All other draft-2 clauses, including decode restrictions, trim, PDQ, ISCC hash core, variants, thresholds, matching and records, are inherited from specification commit `24bb4b8483dc86966cb7c8277130bb816b0c6b3f`; [frozen-pins.json](../experiments/image-normalization-draft3/frozen-pins.json) identifies inherited file bytes and the old experiment tree. Where §5's Pillow-defined grey/resize language conflicts with the rules below, these proposed rules take precedence for draft-3. No new input format, decoder, quality rule, extractor or matching mode is introduced.

Draft-2 extraction digest remains `c740e92de69a47904fa81bb3614c086194717be856fa6a44d89ad6fdba3bb927`. Matching bytes/digest remain `fe3fa0395d3701fa5b1b55839063998eba528851d4f9e3dcaca62d3a0f6c97ac`. Existing catalogues and experiment results retain their old identities; do not relabel them as draft-3. A changed extraction identity propagates to new catalogues/reports even if all feature bytes happen to agree. This proposal does not authorize a new full experiment or change the frozen protocol.

## Grey rule

Input is the RGB integer array after shared decode, white alpha flattening, orientation and the inherited border trim. For every pixel with `R,G,B` in `[0,255]`, compute with exact integer arithmetic:

```text
L = floor((19595*R + 38470*G + 7471*B + 32768)/65536)
```

Store `L` as an unsigned byte **before** resizing. There is no linearization, dithering, floating decimal luma calculation or reuse of PDQ luma. This equation is authoritative; Pillow's RGB-to-L conversion is a comparison target. Draft-2 already contained the equation; this proposal removes the remaining “defining implementation” qualification.

## Resize rule

Let `W,H` be positive post-trim dimensions. Resize the entire grey array to 32×32; no aspect preservation, extra crop box, padding or reducing pass. Trimming can produce a side below 32, including one pixel: do not add a post-trim minimum-size abstention.

The following is the complete coefficient and sampling algorithm. `trunc` converts toward zero; `floor` is mathematical floor. All coefficient arithmetic is IEEE-754 binary64 round-to-nearest ties-to-even after **each** elementary operation, using the displayed parentheses and left-associated additions/subtractions. Integer constants are converted exactly; sums begin at binary64 zero and increase in source-index order. No fused multiply-add, reassociation or extended intermediates. Coefficient integer conversion uses the separate sign-dependent rule below. Pixel multiplication/accumulation is exact signed integer arithmetic, not binary64.

```text
For an axis of length N != 32 and destination j = 0..31:
  s = N/32
  f = max(1,s)
  u = 1/f
  c = (j+0.5)*s
  h = 2*f
  lo = max(0,trunc((c-h)+0.5))
  hi = min(N,trunc((c+h)+0.5))
  For i = lo..hi-1:
    t = abs(((i-c)+0.5)*u)
    a_i = ((1.5*t-2.5)*t)*t+1         if t < 1
          (((t-5)*t+8)*t-4)*(-0.5)   if 1 <= t < 2
          0                           otherwise
  Z = sum(a_i, increasing i)
  b_i = a_i/Z if Z != 0, else a_i
  q_i = trunc(b_i*4194304 + (0.5 if b_i >= 0 else -0.5))

For each output pixel along that axis:
  S = 2097152 + sum(input_i*q_i, increasing i)
  output = min(255,max(0,floor(S/4194304)))
```

Only in-image taps `[lo,hi)` participate; normalization uses their sum. Do not reflect/wrap/pad edges, change negative lobes or force the quantized coefficients to sum to `2^22`. The coefficient signed rounding is ties away from zero. Sample rounding uses the positive half-offset, mathematical floor and saturation, including negative accumulated values; it is not coefficient rounding.

Skip any axis already of length 32. If both axes are unchanged, copy the input bytes. Choose pass order from the original post-trim dimensions:

```text
if H > 32 and H-32 > 2*(W-32): vertical, then horizontal
else:                         horizontal, then vertical
```

After **each performed pass**, store rounded/clipped 8-bit intermediate samples. The first pass retains the other dimension; each axis's coefficient table uses its original length. A skipped axis leaves bytes unchanged. The final output is 1,024 unsigned bytes, row-major, 32 rows × 32 columns. Optimizations are allowed only when specified coefficients/intermediate/output bytes remain unchanged.

These binary64 constraints are an explicit proposed portability contract, not a verified description of every historical wheel compiler. Source inspection identified the dimension-dependent pass order; always-horizontal-first or final-only rounding changes some committed fixtures. The separate mathematical oracle implements software binary64 rounding through exact rationals rather than asking Pillow for expected output.

## Primary-source identities and evidence boundary

[primary-source-pins.json](../experiments/image-normalization-draft3/primary-source-pins.json) records official Pillow commit **`293218ad059d994baf1777d882911bed6a49704a`**, resolved from tag 13.0.0 during the preceding read-only investigation, and complete-file SHA-256 values:

| Source | SHA-256 |
| --- | --- |
| [Resample.c](https://github.com/python-pillow/Pillow/blob/293218ad059d994baf1777d882911bed6a49704a/src/libImaging/Resample.c) | `880ea65963006a99e758f994673c7d51b51c26e3164be770f8299856563e9f20` |
| [Convert.c](https://github.com/python-pillow/Pillow/blob/293218ad059d994baf1777d882911bed6a49704a/src/libImaging/Convert.c) | `9bfdb3fbcd69935282cf4214f97f8d37c4f6e8d708920cb5b87b82b67d27969b` |
| [Image.py](https://github.com/python-pillow/Pillow/blob/293218ad059d994baf1777d882911bed6a49704a/src/PIL/Image.py) | `04050c2d4dd67931ce8c3cfdbc49ac4a6944d379d037c8f1d5eeeb67fba29a10` |

The comparison target is the already provisioned macOS arm64 CPython 3.14 Pillow 13.0.0 wheel, SHA-256 `d9b0a2bee3f3e03e9f29057aedb807dbf1e1d96ee1b9d0f422d9db6c8583271d`. See the checker/README for the machine-checked full wheel pin; the inherited decoder pin remains unchanged. Source is corroborating evidence; the formula above defines the new proposed rule. No source was downloaded in this implementation task; metadata comes from the prior investigation. SDK 0.9.7 `cc11f771e4efbf0a600f196c7e9155b529ad7598` remains historical trim provenance, with equality to SDK outputs untested. ISCC core 1.5.0 and PDQ pins are inherited, not retested by this normalization checker.

## Twelve-item map

The roadmap list has twelve items; this map has twelve rows. It locates the inherited answers and the two explicit arithmetic steps. It is not independent review of the newly authored draft or a gate-status change.

| # | IMGF.1 item | Proposed answer |
| --- | --- | --- |
| 1 | Decoder and version | Draft-2 §1, §3.8, exact inherited pins/settings |
| 2 | EXIF orientation | Draft-2 §3.9, JPEG only, stated transforms/fallback |
| 3 | Colour conversion | Draft-2 §3.8/10/11, explicit accepted modes and ignored colour metadata |
| 4 | Alpha flattening | Draft-2 §3.10, integer white-background formula |
| 5 | Multi-frame policy | Draft-2 §3.5, abstain |
| 6 | Luminance formula | Draft-2 §4.1 PDQ; grey equation above for ISCC |
| 7 | Resize filter and size | Draft-2 §4.2–4 PDQ; full ISCC coefficient/pass/rounding rule above |
| 8 | Border crop | Draft-2 §5.1 tolerant trim; no change |
| 9 | Hash algorithm and bit length | Draft-2 §4 PDQ 256 bits; §5.5–6 ISCC v0 64 bits |
| 10 | Quality abstention threshold | Draft-2 §4.9 PDQ ≤49; §5.7 ISCC none |
| 11 | Dihedral variants | Draft-2 §4.10 and §5.8, eight query variants/catalogue original |
| 12 | Distance metric | Draft-2 §4.11/§5.9 and §6, Hamming minimum over variants, existing ties/list policy |

## Bounded verification and limitations

The [comparison record](../experiments/image-normalization-draft3/comparison-results.json) covers 15 synthetic post-trim arrays. The ordinary implementation, independent rational-arithmetic oracle and pinned Pillow agreed on all grey, first-pass and final bytes; coefficient tables agreed between the two arithmetic implementations. Five fixtures detect each of wrong pass order and final-only rounding. Fixture expected bytes were computed by the mathematical oracle, not hand-derived or produced by Pillow. Both arithmetic programs were authored in this change; mathematical independence does not establish independent implementer review.

This is not end-to-end normalization conformance: decoding, border-trim correctness, ISCC DCT/digest, whole-image variants, matching and inherited PDQ are not exercised. Small post-trim arrays test resize directly, without claiming those arrays alone satisfy the original decode minimum side. Single-host finite fixtures do not establish all-domain, cross-host/compiler, SDK or historical result equivalence. No natural images, corpus, external services, full study rerun, normative promotion or gate change is included. Preserve any future mismatch with its bytes/counts; never regenerate expected bytes from the target to make a comparison pass.

The exact-grey-half-tie follow-up adds a 32×32 constant `(1,53,185)` RGB fixture: `19595 + 38470*53 + 7471*185 = 52*65536 + 32768`, so the specified output byte is 53. A ties-to-even mutation yields 52 and is detected on all 1,024 pixels. This is an independent integer anchor, not a target-derived expectation. The independent reviewer of `fce7893` lacked upstream C bytes for fresh hash verification; that limitation is preserved and no upstream acquisition was performed for this follow-up.
