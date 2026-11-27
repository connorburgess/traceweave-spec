# Independent WEB.4 native fixture review

2026-11-27. Exact reviewed author revision: `d2dd3dfdffabf70d47d1249c42c30b133af15daf`, tree `0045a9c41cb86d49dd0aa3abd42977d95828ba7f`, based on curated-safe `7e329055d75a31f4bfd22e14480e0a46ea582cfa`. Reviewed the [fixture package](../drafts/web4-demo-fixtures/README.md), all 80 data artifacts, recipes/configs/expectations, runner/checker/tests, [failure account](../drafts/web4-demo-fixtures/failures.json) and [author report](web4-demo-fixture-author-report.md).

**Verdict: eligible for evidence-only integration, with the checker and isolation limitations below explicitly retained.** Independent exact-binary replay and independent arithmetic substantiate the supplied finite fixture results; the checker alone is insufficient provenance validation. No blocking mismatch in the reviewed evidence was found. This is not WEB.4 closure: no testing page, hand-edit interaction, live side-by-side updates or browser reproduction was tested. WEB.6 protocol/budgets, all gates/counts and M3 hold remain unchanged.

## Results and independent checks

| Case | Transformation/control | Exact | Normalized | Counts as both-mode miss |
| --- | --- | --- | --- | --- |
| D1 | Comment/whitespace reformat | match | match | no |
| D2 | Systematic identifier rename | no shared fingerprints | match | no |
| D3 | Swap two function declarations | abstain: ambiguous | abstain: ambiguous | no |
| D4 | Insert `break ;` after each fourth original token | no shared fingerprints | no shared fingerprints | yes |
| D5 | Replace function with unrelated type | no shared fingerprints | no shared fingerprints | yes |
| D6 | Append five-token prefix to unrelated type host | no shared fingerprints | no shared fingerprints | yes |
| C-identical | Separate identical-input control | match; 14/14 both directions | match; 17/17 both directions | excluded control |
| C-unrelated | Separate unrelated pair | no shared fingerprints | no shared fingerprints | excluded control |

Exactly 3/6 demonstrations meet the miss category in both displayed modes. Identity/unrelated controls are separate comparisons outside that denominator, though they reuse source components; they are not statistically independent populations or mathematical oracles. D3 has actual ambiguous regions and remains abstention despite high containment (exact common distinct hashes 25, reference/candidate denominators 25/26; normalized 18 with denominators 18/19). Neither that ambiguity nor D2's exact-only miss inflates the numerator. D6 is genuinely no-shared-fingerprints, not relabelled below-minimum evidence. Five copied tokens fall below the unchanged-run locality threshold k+w−1=8; this is not a detection guarantee.

I independently verified the four source-file SHA-256/blob pins against local `git show` at spec `9cf78eec72d89c4a5383dc0ebf0fa98a4693d191`, implementation `dcaa0d42e9de63d23aa113d9306134de9b28942c`'s vendor lock, and its existing vendored bytes. Direct-source inputs match their named vectors; D3 is exactly b1+b2 versus b2+b1. D4 and D6 derivatives were independently reconstructed from **pinned vector expected tokens**, rather than trusting the runner's extracted token record to define the same expected transformation. Both config files match their historical pinned bytes: extraction `dfbc5fe3517e9da65189cf2ef32c4655b5ec662441f2e71f508543a0a5c8f7b2`, comparison `39345e9c8de2b566d19943563326062a46edd38e429a4a96f169307b15147333`. k=5, window=4, minRegionDistinctHashes=2, mergeGap=4 and no suppression were unchanged for every case.

A separate standard-library calculation, without importing the package checker or native hashing implementation, checked original-byte token spans and recomputed **980 k-gram hashes** across the 16 source records/two channels. It used the pinned spec's length-prefixed domain/profile/version/channel/classes/values and uint32be(k), first eight SHA-256 bytes, lexical identifier/literal erasure, and rightmost-minimum windows. Selected positions match the records. Independently intersecting distinct selected-hash sets reproduces both containment numerators/denominators for every case. D4/D5/D6 and C-unrelated have empty intersections in both modes; identity has equal nonempty sets. This avoids treating agreement between Go/Rust or duplicated package metadata as an independent mathematical oracle. It remains conditional on the inspected tokenization; it is not a new full Go lexer or independent seed/merge/ambiguity implementation.

The D4 control-flow insertions are not valid/functionality-preserving Go transformations; D6 is incomplete. Other samples are snippets with external names, not standalone compiling programs. No compilation, runtime behavior, natural-code robustness, prevalence, performance or wider profile claim follows. The author documents these limitations and the older implementation spec pin honestly.

## Storage incident and replay isolation

Before invoking a binary I read `run.py`, retained command arguments and the pinned CLI output/store code. Rust `catalogue_cmd.rs` starts with name `default`; absent `--out`, `output.rs` selects the private catalogue destination and `tw-store` uses atomic replacement. Thus the retained initial account is consistent with replacing `<default-private>/catalogues/default.catalogue.json`. The disclosed status-line catalogue hash `b1bba3c448c3b599de92f74906718e9d8c99687b4d09f7f17f3b4d0898d8eee6` equals the committed D1 Rust sample catalogue hash. It identifies the reported synthetic output, **not prior file contents or proof of no loss**.

Known retained account: first Rust D1 build omitted stdout output, exited successfully with a status line and reported writing the synthetic catalogue; validation of that status line failed. A later body-output omission occurred after temporary storage isolation and failed body validation. Go stdin/validation flag errors are separately retained. These are harness failures, not detector outcomes. The package retains structured failure descriptions and status hash rather than full original invocation/environment/raw stderr transcripts; independent historical reconstruction is therefore limited. Whether a default catalogue existed, its contents/value and any replacement loss remain unknown. No restoration can be justified from this evidence. I did not open, modify, restore or delete default-private catalogue contents or use them as fixture input; the incident was assessed from retained accounts/code only. A broad filename-only binary-location search was interrupted and subsequent searches were restricted to known build directories; no private catalogue contents were read.

For every new CLI invocation in this review, including version checks and any failure path, the parent environment explicitly set `TRACEWEAVE_PRIVATE_DIR` to a fresh temporary location outside all checkouts. No erroneous default-output incident was recreated. Data-path calls also receive `run.py`'s internal temporary private directory; all 64 build/compare command records contain explicit stdout `--out -` or `-out -`. No private-directory or help probe was necessary. Fault-injection/test variables and Python optimization were removed from the replay environment.

**Isolation limitation:** runner version calls happen before its internal temporary-directory block and inherit the caller's environment. The pinned Rust/Go version handlers return version data without invoking storage, but the runner does not itself give every subprocess an isolated environment. Consequently future replays/probes must use the explicit outer environment shown below, including version/help/failure calls where relevant. Prefer extending the runner's shared subprocess environment to version checks in a later author-owned change; do not describe the internal wrapper alone as isolation of every invocation.

## Replay and adversarial dispositions

The already existing binaries matched these exact SHA-256 values **before execution**:

- Rust: `5d22a4d37d6403c595f8ccab04172a496ca74368a52d5ee89a3b7e1b918308a3`.
- Go: `0219f19b4222ff71733d3709a57116aae0756f2fd0bba0d6f1e9251e025052b1`.

Both report stamped implementation `dcaa0d42e9de63d23aa113d9306134de9b28942c` and spec `9cf78eec72d89c4a5383dc0ebf0fa98a4693d191`. One new bounded full replay reproduced all **160 successful data-path command records**, both complete CLI identity records and all **80 physical artifact files**. The new entire run.json is byte-identical, SHA-256 `093b3b9f8f06b36e43f9b54bfd8c247957ca26355c2a1b693f9cb7d95c33cc9b`. I separately read/verified the retained second author run and all 80 artifact hashes; this supports the author's two-run account without representing it as my own second execution. No elapsed-time or resource measurement was taken.

The package's two test methods and ten negative corruption probes pass. Two additional independent adversarial mutations reveal **nonblocking checker gaps**:

1. Set `evidence/run.json`'s `cli` to `{}` in a scratch copy: `check.check(copy)` still returns 3. Its loop does not require both CLI identity entries, so a passing check alone cannot establish stamped provenance.
2. Replace the 160 command records with 160 copies of the first successful extraction record: the checker still returns 3. It checks only length and exit codes, not the command sequence, output-to-artifact bindings or complete operation coverage.

Neither defect occurs in the supplied package: I independently checked the actual CLI keys, exact binary bytes/stamps, stdout-output arguments, complete command equality to the fresh replay, native bytes and physical inventory. They therefore do not invalidate this evidence-only integration, but the checker must not be reused as a standalone provenance attestation. Recommended later fixes are explicit Rust/Go key-set assertions and a validated command plan/output binding with negative tests for these accepted corruptions. No author file was fixed in this review.

## Reproduction and repository boundaries

Use the exact existing binaries above and existing local Python; no install/build/acquisition is part of reproduction. Check hashes before invocation. Keep all outputs outside the worktree and supply outer isolation even for the runner's version calls:

```sh
WEB4_REVIEW_TMP=$(mktemp -d)
TRACEWEAVE_PRIVATE_DIR="$WEB4_REVIEW_TMP/private" PYTHONDONTWRITEBYTECODE=1   python research/drafts/web4-demo-fixtures/run.py   --rust "$RUST_CLI" --go "$GO_CLI" --out "$WEB4_REVIEW_TMP/replay"
python research/drafts/web4-demo-fixtures/check.py --replay "$WEB4_REVIEW_TMP/replay"
python3 -I research/drafts/web4-demo-fixtures/test_fixtures.py
python tools/validate.py --links-all
python3 -I tools/check_hygiene.py --messages 7e329055..HEAD
git diff --check 7e329055 HEAD
```

Unset `PYTHONOPTIMIZE`, `TRACEWEAVE_FAULT_INJECT` and any `TRACEWEAVE_TEST_`/`TW_TEST_` variables in the replay environment; this review used a filtered environment and did not change system variables. Scratch-copy mutations above require only Python JSON/copy/tempfile operations and the package `check` function, not CLI calls. Independent arithmetic is reproducible from pinned extraction §§6–8: LP strings use four-byte big-endian lengths, k=5, w=4, SHA-256 first-eight-byte hex, rightmost tie selection, distinct-set intersections. Retained vectors supply direct-source token/recipe checks; no downloads or new input cases are needed.

Reviewed runner/checker SHA-256: `run.py` `6043e56ca3eb70e535384c893f373b0179a3a2e3ee70aaba5bb5a4429ffdb52d`; `check.py` `3288193002f36070e540ecf43691bd3dd7798b3eca51556fd05065ff305ae33b`. Other package identity anchors: recipes `5107dfb249d610930e12439dad679955eb200e06e01357ff09dba6133afb45b3`; expectations `e416ab1785d7c2555f3aa66a422a1fba8298e62262ce8410bc913de7936ace96`; failures `81f837bdd24ed1ab55c5dd7001a4373fec568e666152f030d54610577f89355a`.

Checks pass for local links, whitespace and tree/message hygiene, repeated with this new review record included. The 107-file author commit adds only the new package and author report; ROADMAP, normative/shared tools, work queue and WEB.6 protocol remain unchanged. Curated-safe base is an ancestor and the forbidden private raw-bearing tip is not. Author bytes remain unchanged; this review adds only this record. No gate closure, performance baseline, browser, M3 evaluation, service, acquisition, push or sublane occurred. Future WEB.4 page integration still needs its own implementation/live-update/browser evidence and independent review.
