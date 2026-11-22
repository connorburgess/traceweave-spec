# Non-author review: image mark protocol `e-img-m-1`, proposed UC-7 and harness

Reviewed 2026-11-23 at frozen commit `9165f19` on `roadmap-v2`: [image-mark-protocol.md](../drafts/image-mark-protocol.md), [image-mark-use-case.md](../drafts/image-mark-use-case.md), `research/experiments/image-mark/` and [lane 12](../lanes/12-image-mark-licences.md). Read against ROADMAP IMG.0–IMG.5, [lane 10](../lanes/10-evidence-review.md) and its [report audit](../lanes/10-report-audit.md).

I wrote none of it. I did not run `full`, and I generated no seed in 2,000,000–2,000,201. My scripts are in `$TMPDIR`. Network use was limited to read-only fetches of five licence and README texts from `raw.githubusercontent.com` at the pinned commits; I downloaded no model or data.

## What I ran

| Check | Result |
| --- | --- |
| Protocol digest (self-excluding, one occurrence replaced by zeros) | `bdae7d60…96a4`, equal to the recorded value |
| Harness files against `9165f19` | `git diff` is empty for `research/experiments/image-mark/`, `../image-fingerprint/twimg` and the protocol |
| `.venv/bin/python -I -m unittest discover -s tests -t .` (the existing project environment, offline) | OK, exit 0 |
| `run_mark.py smoke` twice into `$TMPDIR`, then `compare` | exit 0, 0, 0. Both runs give `resultsSha256` `0c1d421f…2f2c`, **equal to the author's three earlier smoke runs**, so the output is reproducible across processes and days on this host. Probe outside a sandbox: `bind allowed; … ECONNREFUSED`, as documented |
| Exact tails (my integers) | n = 100 → k = 74 (8.34×10⁻⁷; k−1: 2.35×10⁻⁶). n = 256 → k = 167 (6.22×10⁻⁷). n = 32 → k = 30. These match §5. Also n = 61 → k = 49 (9.85×10⁻⁷) and n = 96 → k = 72 (4.85×10⁻⁷) |
| Seed disjointness | The harness uses `range(2_000_000, 2_000_100)` with host offset 102, and smoke 3,000,000+. Earlier ranges: `e-img-f-1` 0–1,999, `e-img-f-2` 0–199, its smoke set 1,000,000–1,000,019 (tests up to 1,000,006). No test, `twmark` module or smoke log contains a seed from 2,000,000–2,000,201 |
| Code identity | `twmark/env.py` checks HEAD, porcelain, diff, ancestry and the version line, plus the imported `generator.py` and `transforms.py` against `6f39e50`. The abort limit is 4 h in code and in §10 |
| Network use in code | Only the probe sockets in `env.py`. TrustMark download is replaced by a refusing method; PixelSeal goes through `setup_model` |

## Findings, most severe first

**B1 (blocking; changes §5 and k, so a new version is needed). TrustMark's 100 tested bits are not 100 independent fair coins, so the stated 10⁻⁶ bound is wrong for `tm`.** Upstream `DataLayer.process_encode` appends `format(version, '04b')`. These are 4 bits fixed for every payload; the smoke entries all end in `0001`. The 35 ECC bits are a deterministic, linear function of the 61 data bits. A marked image's raw bits always carry the version bits. That holds in my smoke data for every `clean`, `wrongkey` and `overwrite` decode, and for 1 of 3 covers. So in P3 and P4, agreement on those 4 positions is certain, and the test effectively needs 70 of the 96 remaining bits: P(Bin(96, ½) ≥ 70) = **4.02×10⁻⁶**, about 4.8 times the stated 8.34×10⁻⁷. For wrong-entry and wrong-key comparisons of marked images, the disagreement is the weight of the sum of two BCH codewords, which follows the code's weight distribution, not Bin(n, ½). **Fix:** test TrustMark on the **61 data bits only** (raw positions 0–60 against the HMAC data bits). Those are exactly uniform and independent under §5's HMAC argument; n = 61 gives k = 49 (9.85×10⁻⁷). Keep the 100-bit agreement as a report-only field. PixelSeal (256 payload bits after the detection bit) and `dwtDct` (32) are unaffected. The UC-7 text repeats the 74-of-100 claim, so the same fix applies there.

**B2 (blocking wording; goes into the same new version). Say what the zero-accept lines and the attacks can and cannot show.** **P2–P4 are weak by construction.** With HMAC payloads, an accept needs a decoded string to hit a pseudorandom 61- or 256-bit target. Zero in 39,900 comparisons is therefore expected whatever the images or schemes do. These lines test the implementation (no payload reuse, correct comparison and search), not the schemes. There are two fixed public keys and 100 payloads per key, and the decoder outputs cluster (§5), so the comparisons are a handful of realizations, not 39,900 trials. The protocol must say this beside the verdict, as `e-img-f-2` §1 did. **Forgery and removal are lower bounds on attacker capability.** The protocol omits: WmForger and other learned forgers; VAE or diffusion regeneration; averaging or collusion over several marked images; above all, **decode-and-re-embed**. The decoders and encoders are public and unkeyed, so anyone can read M's raw bits and embed them into H with the same model, with no key. That forgery should succeed about as often as P1, because it is a clean marking of H with M's bits. A residual copy (H + M − C) is a weaker forgery than that. §1 must state that removal and forgery counts are a **lower bound** on what an attacker can do, and the result must not be read as forgery resistance. **Recommended for the new version:** add `reembed`. Decode M, re-embed the raw bits (TrustMark: BCH-decode to the 61 data bits and re-encode) into H with the pinned encoder, then test for M's entry. It needs no new weights.

**M1. PixelSeal integrity basis.** There is no publisher digest. The basis is TLS to Meta's host, plus the size, plus the S3 multipart ETag (an MD5 construction), and the SHA-256 is pinned at first download. Lane 12 says the ETag "guards against corruption, not against a deliberate collision". That is true, but it should also say plainly that this is **trust on first use**: a substitution at the host before the first download would be pinned. Add this outside the frozen paths (lane 12, or the results note).

**M2. W3 for neural decoders.** The two-run byte identity is realistic on one host. Torch runs on CPU with 4 threads, `use_deterministic_algorithms(True)` and a fixed environment, and my run reproduced the author's digest exactly. It can fail for benign reasons: a different thread count or a BLAS or OS update changes float reduction order. Treating a W3 failure as a "negative result for the harness" (§6) is harsh for that case. In the new version, classify a W3 failure with matching inputs as **invalid, rerun on the pinned host**. Keep a W3 failure with differing inputs as negative.

**M3. IMG.2 offline wording.** IMG.2 says `scripts/offline`. The roadmap accepted `sandbox-exec` with the probe for IMGF.4 only. Record the same acceptance for IMG.2 in ROADMAP. This is a roadmap edit, not a protocol edit.

**L1.** The FFmpeg notice in the OpenCV wheel lists macOS libraries (libmp3lame, libbluray and others) that this wheel does not contain. That is harmless: the notice is generic.

## 1. Licences, opened at the pinned commits

**TrustMark `4c60b9fd`.** **Code:** `LICENSE` (SHA-256 prefix `58d47a5c`, equal to lane 12) is "Copyright 2023 Adobe / All Rights Reserved", then a NOTICE paragraph pointing to "the license agreement accompanying it", then the MIT text. That preamble explains GitHub's NOASSERTION; I did not re-query the GitHub licence API. **Weights:** README:145 and python/README:147 say: "The MIT license covers both the code in this repo and the model files which are downloaded upon first use." FAQ:28 says commercial and non-commercial use; FAQ:80 says trained on licensed Adobe Stock. **Integrity:** the published MD5 values exist only in the code; the SHA-256 values are computed after the MD5 matches. Lane 12 is correct.

**PixelSeal `f12875a9`.** **Code:** `LICENSE` is MIT, Meta. **Weights:** README:41 says "All models, training code, and evaluation tools released under MIT license". `cards/pixelseal.yaml` names `dl.fbaipublicfiles.com/videoseal/pixelseal/checkpoint.pth`. README:221 ("The model is licensed under an MIT license") does not say which model; line 41 is the statement that covers PixelSeal. **Owner note:** the SA-1B training terms remain an owner item, as stated.

**OpenCV wheel `opencv_python-5.1.0.95` (macOS arm64)**, inspected locally. `cv2/.dylibs` holds shared FFmpeg libraries: avcodec, avformat, avutil, avfilter, avdevice, swscale, swresample. libavcodec reports "license: LGPL version 2.1 or later". Its configure line has no `--enable-gpl` or `--enable-nonfree`. So this is the **LGPL-2.1+ build, dynamically linked**. Other bundled libraries are dav1d, libvpx and OpenSSL. **Redistribution:** none. The wheelhouse and `.venv` are git-ignored, and LGPL obligations arise only on redistribution.

**Dependency table.** The other licences in lane 12 match the families stated there. None is non-commercial.

## 2. Decision rule and false-accept analysis

- **k:** correct as computed (table above). **HMAC derivation:** unambiguous. HMAC-SHA256 with the 32-byte key over `e-img-m-1|<scheme>|<entry id>`, first n bits most significant first. TrustMark takes n = 61 and BCH-encodes it. **"Over the key":** the correct basis for a fixed decoder output, but with two caveats: B1 (fixed version bits and code structure); with the fixed public keys, the count observed under one key is one realization per distinct raw string, so clustered outputs make the 39,900 comparisons far fewer independent chances than they appear. **Union bounds:** N × 10⁻⁶ and N_K × N × 10⁻⁶ are correctly stated, once the per-comparison bound is right. **TrustMark ECC interaction:** the blind BCH result is recorded and never decisive, which is right. Its parity and version bits interact with the bit-agreement test (B1).

## 3. Pass lines

- **Set before data and decided by counts:** P1 ≥ 95/100, and P2–P4 = 0 in 20,000, 10,000 and 9,900 comparisons. Everything else is report-only with a denominator of 100; the code (`verdict()`) matches. **P1** is a sound premise check. **P2–P4** are trivially passable by construction (B2) and must be labelled as implementation checks. **What 0 of 200 unmarked bounds:** a per-source rate below 1.49% (one-sided 95%), for this generator only, as §13 says. **Synthetic images:** every zero here is weak on synthetic content, as with `e-img-f-2`.

## 4. Removal and forgery conditions

- **Offline and exactly specified:** conditions 1–24 are specified, with seeded noise, and runnable offline; the smoke run exercised all of them. The 12 edits are imported from `e-img-f-2`, not copied. **Residual transplant:** a fair minimal forgery. It already succeeded on 3/3 smoke images for both candidates, as E1 predicts. **What the literature attacks do that it does not:** optimize a perturbation against the decoder (WmForger); estimate the mark from many marked images (averaging); regenerate through a VAE or diffusion model; re-embed decoded bits.

  See B2.

## 5. Code identity, offline proof, budget

The code identity covers the imported files. The probe follows the `e-img-f-2` design. The budget figures are consistent with my smoke time (129.6 s for 3 images per scheme), and the abort limit is consistent between code and text. I saw no result-dependent choice in the harness: `full` refuses a scheme subset; seeds and conditions are constants; k is computed from n.

## 6. UC-7 wording (IMG.0)

- **Good:** every "Checked" item maps to an exit code or a count; "Fail" lists counts; ownership, authorship and permission are disclaimed; the payload is called "a keyed locator … not an identity claim, a signature or a licence"; "a match is not proof that the candidate derives from the original". **Fix with B1:** "74 of 100" and "whatever the image" (true only for the 61-bit test); add that **anyone can copy a mark without the key** by decoding and re-embedding (B2).

The owner still has to accept the wording.

## 7. IMG gates as worded

| Gate | Decidable by this protocol | Not decidable here |
| --- | --- | --- |
| IMG.0 | — | The owner's acceptance of UC-7 and its merge into `docs/use-cases.md` |
| IMG.1 | Commits, weight SHA-256, code, weight and dependency licences (verified above) | "Licensed non-private image set": the synthetic set is project-generated, so no licence question arises, but a real set is owner-gated |
| IMG.2 | Embed and detect under network denial: W2 plus P1 | The `scripts/offline` wording (M3) |
| IMG.3 | Transformation list, ReMark, PSNR floor, threshold, `dwtDct` control, transplant arm (frozen) | VAE regeneration excluded, which IMG.3 permits. The threshold must be corrected first (B1) |
| IMG.4 | Per-condition whole-message counts, unmarked (200 sources, 20,000 comparisons), wrong key, transplant, each with a denominator | Any rate claim beyond what n supports |
| IMG.5 | The §12 mapping. I agree the container's field list fits and that five fields have no home (model digests, statistic with n, threshold basis, key and derivation id, embedding quality). I add a sixth: **which bit positions are tested** (B1) | The schema change itself (CONTRIBUTING) |

## Verdict

**Run may start after the listed fixes. B1 and B2 change the frozen protocol, so they require a new version, `e-img-m-2`, with a new digest, freeze commit and review confirmation.** **New version:** TrustMark tested on the 61 data bits with k = 49; the B2 statements; optionally the `reembed` condition; the M2 W3 classification. **Outside the frozen paths:** M1 (lane 12 wording) and M3 (ROADMAP IMG.2).

**Measured-run command sequence**, run outside any agent sandbox, with `FROZEN` set to the new version's 40-hex freeze commit:
```sh
SB='(version 1)(allow default)(deny network*)'
git worktree add --detach ../imgm-run "$FROZEN" && cd ../imgm-run/research/experiments/image-mark
python3 -I fetch_sources.py                                  # online, hash-checked (84/84)
/opt/homebrew/bin/python3.14 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir --no-index --find-links <shared checkout>/research/experiments/image-mark/wheelhouse --require-hashes --only-binary=:all: -r requirements.txt
python3 -I fetch_weights.py --verify                         # 6/6, models outside the tree
git rev-parse HEAD; git status --porcelain --untracked-files=all   # FROZEN, then nothing
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python -I -m unittest discover -s tests -t .
for r in 1 2; do /usr/bin/sandbox-exec -p "$SB" .venv/bin/python -I run_mark.py full --frozen-commit "$FROZEN" --require-network-denied --out out/full-$r; echo "exit $?"; done
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python -I run_mark.py compare out/full-1 out/full-2; echo "exit $?"
git status --porcelain --untracked-files=all                 # nothing
```

**Log in the results commit**, which must descend from the freeze commit and the review commit: every command with its exit code (all 0); from both summaries: `codeIdentity.ok` true, with HEAD = FROZEN; `networkProbe.denied` true (EPERM); weights 6/6, sources 84/84, goldens 3/3, 0 environment deviations; `recordValidation` 0 errors, and `statusAfterRun` empty; equal `resultsSha256`; `elapsedSeconds` ≤ 14,400.

## Confirmation pass: e-img-m-2

Checked 2026-11-23 on a `git archive` export of the frozen commit `d3af1ee`, offline, using the existing `.venv` and the weights in the eval directory. I did not run `full` and generated no seed in 2,000,000–2,000,201.

**Reruns.** **Digest:** the self-excluding digest recomputes to `cba36673…4110`; the version line reads `e-img-m-2`. **Smoke runs:** two runs and `compare` all exit 0 ("W3: identical"). `resultsSha256` `2d78db49…6ecd` equals the author's three runs. **Unit tests:** 22 tests. One (`test_fetch_refuses_work_tree`) fails on the export only, because `git archive` does not make a git work tree. In the shared checkout, whose `research/experiments/image-mark/` equals `d3af1ee`, all 22 pass.

**Earlier findings.** **B1 resolved.** **Exact tail:** P(Bin(61, ½) ≥ 49) = 2,271,115,189,673 / 2⁶¹ = 9.85×10⁻⁷ ≤ 10⁻⁶, and at 48 it is 3.83×10⁻⁶. So k = 49 is the smallest value, as §5 states. **Tested positions in code:** `tm` `tested()` = raw[:61]. Upstream `process_encode` puts the 61 data bits first, then ECC, then version, so these are the HMAC data bits; the test checks the trailing `0001`. `ps` uses `preds[0, 1:]` (256 bits; the detection bit is excluded). `dw` uses 32 bits. Every tested bit is direct keyed output. **100-bit agreement:** kept as the report-only `agree100True`. **B2 resolved.** **§1:** P2–P4 are labelled implementation checks, "close to guaranteed by construction"; removal and forgery counts are "a lower bound on what an attacker can do"; and the text says anyone can copy a mark without the key. **`reembed` (condition 20):** decodes the `clean` raw bits, takes `forge_bits` (TrustMark: BCH data bits when valid with version 1, else raw 0–60), embeds them into H with the public encoder, and uses no key. **Copied bits survive:** in my smoke run the forged images decode to exactly the copied bits, 3/3 for `tm` (61/61, `forgedFrom: bch`) and 3/3 for `ps` (256/256). Both are accepted for the donor's entry. `dw` agreed on 26/32, 32/32 and 32/32 bits, consistent with the control's weakness. **M1 resolved** (lane 12): "This is trust on first use", including the host-side substitution case. **M2 resolved.** The runtime pins are listed in §10 and checked in W1. In `compare`: exit 0 means identical; exit 5 means outputs differ while every recorded input (environment, runtime pins, versions, weights, sources, goldens, digest, HEAD) is equal; exit 1 means some recorded input differs. **It cannot be used to discard an inconvenient result.** The classification depends only on byte equality and recorded inputs, never on counts. Every invalid pair is kept and reported. At most two fresh pairs may be rerun; a third invalid pair goes to the owner, and any change is a new version. The rule is mechanical, so no one chooses when to rerun. **M3 not resolved, outside the frozen paths.** ROADMAP IMG.2 still says "under `scripts/offline`". Before IMG.2 is marked met, add "(`sandbox-exec` deny-network with the harness probe failing first)" as IMGF.4 does. This does not block the run.

**Diff scope.** The changes are the review items only. The 25 conditions and 7,500 query lines follow from `reembed`, and P1–P4 keep their thresholds, adding only the label "implementation check". **Report-only lines are unchanged.** E5 is a stated expectation. The k values for PixelSeal and `dwtDct` are unchanged. **The `dwtDct` smoke outputs changed** because of the OpenCV threading pin; that is recorded, and no measured run exists. **Nothing was chosen after data:** every change was requested by the review before any experiment-range seed existed.

**Measured-run commands**, run outside any agent sandbox, with `FROZEN=d3af1ee07595bde53ff53fcce0f3880ad04fb62c`:
```sh
SB='(version 1)(allow default)(deny network*)'; export TRACEWEAVE_EVAL_DIR="$HOME/traceweave-eval"
git worktree add --detach ../imgm-run "$FROZEN" && cd ../imgm-run/research/experiments/image-mark
python3 -I fetch_sources.py                                   # online once; 84/84 by SHA-256 and git blob id
/opt/homebrew/bin/python3.14 -m venv .venv && .venv/bin/python -m pip install --no-cache-dir --no-index --find-links <shared checkout>/research/experiments/image-mark/wheelhouse --require-hashes --only-binary=:all: -r requirements.txt
/usr/bin/sandbox-exec -p "$SB" python3 -I fetch_weights.py --verify   # 6/6 size + SHA-256 in $TRACEWEAVE_EVAL_DIR/models, offline
git rev-parse HEAD; git status --porcelain --untracked-files=all        # FROZEN, then nothing
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python -I -m unittest discover -s tests -t .
for r in 1 2; do /usr/bin/sandbox-exec -p "$SB" .venv/bin/python -I run_mark.py full --frozen-commit "$FROZEN" --require-network-denied --out out/full-$r; echo "exit $?"; done
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python -I run_mark.py compare out/full-1 out/full-2; echo "exit $?"   # 0; 5 → §6 rerun rule; 1 → negative
git status --porcelain --untracked-files=all                  # nothing
```
`full` re-verifies the 6 weight SHA-256 pins (W1) before loading any model.

**Log in the results commit** (`results/e-img-m-2/`), which must descend from `FROZEN` and from this review's commit: every command with its exit code; from both summaries: `codeIdentity.ok` true, with HEAD = FROZEN; `networkProbe.denied` true (EPERM); weights 6/6, sources 84/84, goldens 3/3; 0 environment and runtime deviations before and after the run; `recordValidation` 0 errors; `statusAfterRun` empty; equal `resultsSha256`; `elapsedSeconds` ≤ 14,400. the `compare` output, and any invalid pair, kept.

**Verdict: the run may start as frozen (`e-img-m-2`, `d3af1ee`).** No blocking item remains. M3 (the ROADMAP IMG.2 wording) must be fixed before IMG.2 is marked met.
