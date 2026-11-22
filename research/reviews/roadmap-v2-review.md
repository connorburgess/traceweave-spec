# Independent review: roadmap v2 and implementation repository plan

> Adoption note: the draft reviewed here was adopted as [ROADMAP.md](../../ROADMAP.md) and the plan as [docs/implementation-repo-plan.md](../../docs/implementation-repo-plan.md). The `R:n` and `P:n` line references point to the drafts as committed in `6f75d55` (`research/drafts/roadmap-v2.md`, `research/drafts/implementation-repo-plan.md`).

Reviewed 2026-11-22 against the working tree (including uncommitted files). Scope: [roadmap-v2.md](../../ROADMAP.md) (R) and [implementation-repo-plan.md](../drafts/implementation-repo-plan.md) (P). I did not write either draft and did not rely on their self-reported checks.

## What I reran

| Command (from repo root unless noted) | Result |
| --- | --- |
| `.venv/bin/python tools/validate.py` | PASS, exit 0 |
| `.venv/bin/python -m unittest discover -s tests` | 6 tests, OK |
| `GOCACHE=$TMPDIR/gocache GOPROXY=off go test -count=1 -v ./...` in `research/experiments/go-carrier` (go1.27.3) | 6 top-level tests PASS |
| same in `research/experiments/go-census` | ok |
| `python3 research/experiments/rust-carrier/experiment.py --output $TMPDIR/rust-results.json` (rustc 1.97.1) | exit 0; JSON equal to committed `results.json` once timing and version fields are excluded; 32+30 recovered, 29+26 = 55 nonzero states collapsed |
| `python3 -m unittest test_fragments` (rust-carrier), `python3 -m unittest test_scanner` (rust-census) | OK, OK |

Not rerun: the signing harnesses (`run.py`, `run_policy.py`). They write over the recorded result files and use nested `sandbox-exec`. For M4.1/M4.2 I read [signing-interop-results.md](../lanes/signing-interop-results.md) and [signing-policy-results.md](../lanes/signing-policy-results.md) instead. R §1's count of 8 met, 3 negative-result and 28 open out of 39 is arithmetically correct.

## Findings, most severe first

### Blocking

**B1. M2E.1 and M2E.2 are "met" for a carrier the roadmap has already rejected, and no gate requires the same evidence for the next carrier. (R:66-67, R:71)** The ROADMAP M2E exit gate asks for reproducible embedding, a functionality/quality gate and recorded randomness for *the* embedding profile. M2E.3–M2E.5 reject the synthetic carriers. M2E.6 asks only for "behavior checks" for a new carrier. A future carrier could therefore reach M2E.7/M2E.8 without its own insertion-reproducibility gate or its own functionality gate, while the table already shows both as met. The counts are also generous. "62/62 raw states recover" includes 7 already-zero states per language, which [experiment-checkpoint.md:13](../experiment-checkpoint.md) says "demonstrate decoding, not intentional insertion"; intentional insertion is 55/55. "Marked outputs pass 248 Go / 372 Rust checks" counts canonicalized and direct-return attack outputs as marked outputs ([go-carrier-results.md:62](../lanes/go-carrier-results.md), [rust-carrier-results.md:61](../lanes/rust-carrier-results.md)). Of Go's 248, 124 are clean+formatted outputs. **Fix:** make M2E gates per candidate. Re-label the existing rows "M2E.1-syn/M2E.2-syn: evidence for a rejected candidate" and leave them out of the progress count. Add gates for the selected carrier covering reproducible insertion with recorded seeds, functionality checks on the marked outputs only, and the ROADMAP's private mark record and original/marked digests, which no gate currently covers. Correct the counts to 55/55 intentional and 124 Go marked outputs.

**B2. Status "negative-result" can close gates that a release depends on. (R:5, R:154)** RC.1 accepts "all M1–M5 gates met *or negative-result*". Read literally, M1.4 "negative-result" (the two implementations disagree) or M2.2 negative (spans wrong) would still let a 1.0 candidate go ahead. M2E.6 is also a single row whose negative-result "closes it for that candidate". One failed proposal would make all of M2E look closed, after which M5.4 records embedding as omitted. That is the "completes too easily" route the owner complained about. **Fix:** label each gate either *engineering* (only met counts) or *research question* (negative-result allowed; this covers M2E.3–M2E.6, BIN and RES.2). RC.1 should require every engineering gate to be met. A negative M2E.6 should require an owner decision record before M5.4 can say embedding is omitted.

**B3. The I2 exit gate contradicts M2.4. (P:102, R:57)** M2.4 requires the report to record the implementation commit. I2 requires the report digest to equal a committed `fixtures/synthetic/expected-report.sha256`. Committing that digest changes the commit, which changes the report, so the gate can never pass as written. It would only pass if the commit field is quietly dropped. **Fix:** define a canonical report body that excludes the provenance block, compare digests over that body, and check the provenance block separately.

**B4. M1.4/I1 can be satisfied by two implementations agreeing with each other while both are wrong. (R:46, P:101)** "Byte-identical outputs over every M1.2 vector" does not say the outputs must equal the expected values committed in the vectors. If the vector outputs were generated by the Rust implementation, agreement is close to automatic. **Fix:** write it as "each implementation's output equals the expected bytes in the M1.2 vectors, which were committed in the spec repository before either implementation's first passing run (git ancestry check)". Require at least the 7 classes to be hand-derived and say so in the vector metadata.

**B5. The spec pin is not drift-proof as described. (P:31-35, P:44)** `check-spec-pin` only compares vendored files with `spec.lock`, and both live in the implementation repository. Editing a vector and its lock entry in the same change passes. Comparison with upstream (`git show <commit>:<path>`) runs only if the optional `TRACEWEAVE_SPEC_DIR` is set. The table row "Accidental drift: digest check fails" is accurate only for accidental edits to one file. Normative profile text (`profiles/*.md`, `spec/`) is not vendored or pinned at all, yet M1.1 defines the token serialization and config bytes there. **Fix:** milestone exit commands (I1–I5) must run with the upstream check mandatory, by fetching or using a checkout at the pinned commit. Pin and record digests for the profile document and conformance.md as well. Record the spec version string. The pinned commit must already be pushed and must not be an uncommitted working tree; the current spec working tree has many uncommitted and untracked research files.

### High

**H1. Several open criteria can be met trivially or need judgment calls.**
- M1.5/M5.1 (R:47, R:101): "0 unmapped" counts only author-assigned mappings. Fix: every mapped check must name a vector ID or test that fails when the requirement is violated. Add a negative fixture per MUST, or at minimum a reviewer spot-check of a stated sample.
- M2.2/M2.3 (R:55-56): N has no minimum and no required class mix, so N=1 passes. "Reported as N/N" does not say whether pass means reported or all correct. Fix: the manifest must contain at least one case per example-matrix row for UC-1 (exact, formatted fragment in a large host, rename, same-task, boilerplate, malformed). M2.2 passes only at N/N. M2.3 passes when every listed control class appears with its count.
- M2E.6(c) (R:71): the proposer freezes "the minimum net authenticated bits", so a tiny minimum passes. Fix: the owner approves the minimum, which must be derived from the payload UC-6 needs, before measurement. The census sample must come from a new approved protocol, as [public-census-checkpoint.md:24](../public-census-checkpoint.md) requires.
- M4.5 (R:94): "a written … description" passes on prose alone. The ROADMAP M4 deliverable is an in-toto *adapter*. Fix: require adapter fixtures (accept and reject) checked by `validate`, plus a stated decision on the optional timestamp adapter.
- M5.2 (R:102): what counts as a "claim" is a judgment call. Fix: claims are sentences in a marked README section, extracted by a script.
- M3.4 (R:83) is reporting-only, so M3 is "met" whether or not the result is useful. Fix: add M3.6, a recorded verdict against the M3.0 budget (met or negative-result). This keeps the no-guarantees rule while making usefulness an explicit outcome.
- RES.2 "what an adversary learns" (R:142) and SK.2 "0 occurrences" (R:150) have no defined measure. Fix: RES.2 names the adversary query model and metric before running. SK.2 seeds canary strings into catalogues and keys and greps the transcripts for them.

**H2. M0.1 is narrower than the ROADMAP gate it closes. (R:34)** ROADMAP M0 requires "input, observable output, limit, *and verification plan*" for each proposed capability. [use-cases.md:7](../../docs/use-cases.md) has inputs, result and limit columns but no verification plan, and the status says "coordinator-reviewed only". Fix: restore the verification-plan clause and mark M0.1 open until each use case links to its gate IDs (the gate table could serve as that plan). Otherwise record that the owner accepts the narrower criterion.

**H3. Media lanes start before core gates and repeat the diagnosed failure. (R:113, R:163)** R §1.3 says work drifted to external lanes 06–08 instead of the baseline. §5.4 then starts IMG, BIN and RES "once I2" exists, before M3, using the same lane pattern. ROADMAP lists these under "Later, with separate gates", and [lane 08:11](../lanes/08-evidence-review.md) names deferral as the strongest alternative. Fix: in the diagram, IMG/BIN start only after M3.4, or only on an explicit owner override recorded in IMG.0/BIN. Make IMG.0 an explicit prerequisite of IMG.1–IMG.5.

**H4. The diagram makes M4 a prerequisite of M5. (R:109-111)** ROADMAP:27 allows "a detector-only experimental release [that] can remain explicitly unsigned", and requires M4 only before a release claims cryptographic verification. Fix: draw M4 → M5 as conditional and add a gate to M5.4 saying whether signing is included.

**H5. The I5 dependency text contradicts its own gate. (P:105-107)** "Embedding does not wait on them past I2", but the I5 exit includes M2E.8, which R:73 says needs M3, that is, I3. Fix: I5 is split, with M2E.7 after I2 and M2E.8 after I3.

### Medium

**M1. The negative results need narrower wording.** M2E.5 (R:70): the census says eligibility was *not established* and "is not proof that no implementation could mark these sources", and Go found 5 unassessed singleton sites ([public-census-checkpoint.md:16](../public-census-checkpoint.md)). That is inconclusive for the narrow patterns, not a measured absence. Restate it as "the narrow synthetic patterns: no eligible site established (inconclusive on safety)". M2E.3 and M2E.4 should name their candidate, "existing synthetic Go/Rust carriers", in the ID or the text.

**M2. Some evidence for met gates is uncommitted.** The fragment evidence (`go-carrier/fragment_test.go`, `rust-carrier/fragment_*`, and every `research/lanes/*-results.md` cited for M2E.4 and M4.2) is untracked. `go-carrier/go.mod` is modified from `go 1.23` to `go 1.27`. Under supervision rule 3, nobody can recheck a gate from a clean clone. Fix: commit the evidence with a toolchain record before the statuses are adopted, and revert or explain the go.mod bump.

**M3. The I0 gate depends on things that do not exist yet.** It needs a Go module path (P:84, marked "owner choice"), toolchain pins (`rust-toolchain.toml`, Go version), and JSON Schema validators in Rust and Go for conformance level 1. Level 1 requires rejecting unknown fields, but the plan names no libraries or schema draft. It needs a pushed spec commit to pin. And no spec gate is satisfied: R:118 maps I0 to "conformance levels 1–2", which has no gate ID. Fix: list these as I0 prerequisites. Add `--workspace --all-targets` to the cargo commands.

**M4. The I2 exit uses `/usr/bin/sandbox-exec` only (P:102).** That is macOS-only and deprecated, while M2.1 allows Linux and the plan writes `.github/workflows`. Fix: put a `scripts/offline` wrapper behind the exit command (sandbox-exec, or `unshare -n`/bwrap on Linux), and have the wrapper prove denial with a failing probe, as the signing harness did.

**M5. Conformance levels are used out of order.** I1 claims level 4 ("profile reproduction" of extraction *and matching* vectors) before matching exists in I2, and I4 claims level 3 after it. Fix: I1 claims level 4 for extraction vectors only, and I2 completes level 4 with matching vectors.

**M6. Some language trade-offs are not argued fairly (P:51-57).**
- Option C "fails M1.4 and M4.4 by construction" only because R wrote "Go and Rust implementations" into M1.4. conformance.md requires two implementations, not two languages.
- "Tree-sitter's primary bindings are Rust" overstates it: the core is C.
- Option A's risk is not stated. If `rustc_lexer` is the "authoritative" lexer, the profile risks becoming whatever its token kinds are (raw strings, nested comments, shebang/frontmatter), and the Go lexer would have to match that. M1.1 must define token classes independently of either lexer.

Fix: state these points. The recommendation can stand.

**M7. Licence: mostly consistent, with one gap (P:47, P:68).** Apache-2.0 for code, vectors and schemas matches [LICENSE.md:7](../../LICENSE.md). But vendoring `test-vectors/`, `schemas/` and `examples/` wholesale brings in Markdown (for example `test-vectors/README.md`), which is CC BY 4.0, not Apache-2.0. Fix: vendor only non-Markdown files, or keep the CC BY notice and attribution for the vendored Markdown. A `NOTICE` file is optional because the spec repository has none; that is fine, but say it is optional.

**M8. TW-04 is changed but not superseded.** ROADMAP TW-04 says "using the existing Python tooling". P:51 moves the reference to Rust and Go. R §5.1 only adds status columns. Fix: §5.1 should explicitly amend TW-04 and map TW-01…TW-08 to gate IDs.

### Low

- R:11 lists four dates ("11-18, 11-21, 11-21 and 11-22") for three linked checkpoints. The census checkpoint is dated 11-21. Fix the list.
- M3.3 (R:82): "git history order" should mean *ancestry*, not commit timestamps, which the author sets. P:103 `verify-freeze` should test ancestry.
- M4.6 and EXT.1 overlap on crypto review. State that EXT.1 may reuse M4.6 if the reviewer qualifies.
- BIN.2/BIN.3 look like padding: they measure carriers already rejected by canonicalization, and BIN.3 can close with a one-line "out of scope". Keep BIN.1 and drop BIN.2, or move BIN.2 to after M2E.6.
- M5 gates omit two ROADMAP M5 deliverables: versioned spec with migration notes, and a conformance matrix. Add M5.5.
- §4 has no gate for "structural/semantic matching" or "keyed feature selection", although ROADMAP:44-45 lists both as later items. Add one-line gates (compared on the same corpus and budget as M3) or state that they are deferred.

## What holds up

The arithmetic of the gate count, the M0.4/M4.1/M4.2 evidence, the M2E.3 negative-result (I reproduced 55/55 collapse in Rust and the Go tests pass), the supervision rule in §2, and the "nothing is moved out of research/experiments" decision are all sound. Vendored files plus a lock is the right direction compared with a submodule, once B5 is fixed.

## Verdict

**Adopt after listed fixes.** The structure is right, but several statuses and criteria still let work be declared complete too easily, which is the problem this draft was meant to solve.

Blocking fixes:
1. B1: make M2E gates per candidate, drop the rejected carriers' M2E.1/M2E.2 from the progress count, add insertion, functionality and mark-record gates for the selected carrier, and correct the counts (55/55, 124).
2. B2: separate engineering gates from research-question gates. RC.1 requires engineering gates to be met, and omitting embedding requires an owner decision.
3. B3: digest a canonical report body that excludes provenance.
4. B4: M1.4/I1 compare against expected outputs committed before the implementations.
5. B5: mandatory upstream pin check at milestone exits, with profile and spec text pinned too.
6. H1 items for M1.5, M2.2/M2.3 and M2E.6(c), whose current wording lets a gate pass trivially.

## Confirmation pass

Rechecked 2026-11-22 against the revised drafts (R = roadmap-v2.md, P = implementation-repo-plan.md). I reran nothing in this pass; the earlier reruns still apply.

| Finding | Status | Where |
| --- | --- | --- |
| B1 per-candidate M2E; SYN uncounted; 55/55 and 124 corrected; insertion, functionality and mark-record gates | resolved | R:69-90 |
| B2 gate types; RC.1 needs E gates met; omitting embedding needs an owner record | resolved as worded, but see N1 | R:5-10, R:83, R:171 |
| B3 canonical body digested; provenance checked separately | resolved | R:64, P:127 |
| B4 equality with committed hand-derived vectors; precedence script | resolved | R:51-53, P:126 |
| B5 `--strict` upstream byte comparison at every exit; spec and profile Markdown pinned; pushed commit and version string | resolved | P:31-43 |
| H1 M1.5, M2.2/M2.3, M2E(c) approved by owner, M4.5, M3.6, RES.2, SK.2 | resolved | R:54, R:62-63, R:84, R:112, R:102, R:157, R:165 |
| H1 M5.2 claim map | partly: see N4 | R:120 |
| H2 M0.1 verification plan; now open | resolved | R:41 |
| H3 media lanes wait for M3.4 or an owner override | resolved | R:133-136, R:146 |
| H4 M4 required only for signed releases | resolved | R:129, R:122 |
| H5 I5 split into I5a (after I2) and I5b (after I3) | resolved | P:130-131 |

New problems introduced by the revision:

- **N1 (blocking): RC.1 cannot be reached when embedding is omitted.** RC.1 (R:171) requires every M1–M5 E gate to be met. If M2E.1 is negative-result, or M2E.0 records omission, then M2E.2–M2E.5 and M2E.7 can never be met. P:133 says I5 is then not built. That contradicts M5.4(a), which allows a release that omits embedding. **Fix:** RC.1 exempts M2E.2–M2E.7 when M2E.0 records omission.
- **N2 (blocking): M2E.1 has no pass condition, and M2E.6 is circular.** M2E.1 (R:84) lists what must be frozen and says "measured on a sample", but it no longer says the gate is met only if the frozen minimum holds; the earlier draft did. As written, freezing and measuring meets the gate. M2E.6 (R:89) passes against "the frozen criterion", but M2E.1(a)–(d) freezes no survival criterion. **Fix:**
  - M2E.1 is met only if the owner-approved minimum holds on the new census sample; otherwise it is negative-result.
  - Add M2E.1(e), "the survival rate required per declared transformation, frozen before measurement", and make M2E.6 refer to (e).
- **N3 (medium): "met (evidence uncommitted)" contradicts the draft's own supervision rule.** Supervision rule 1 (R:27) requires each closed gate to cite committed evidence. M4.1 and M4.2 (R:108-109) still count as met while `signing-interop-results.md` and `signing-policy-results.md` are untracked (checked with `git ls-files`). **Fix:** show them as "open: evidence pending commit" and give the count as 3 met (R:23) until the commit lands.
- **N4 (medium): M5.2 can still pass trivially.** M5.2 maps only the sentences the author places in a "marked README section", so a short section passes. **Fix:** scope the claim map to the whole README, keeping a script-recognised exclusion list for headings and links.
- **N5 (low): level-4 matching vectors have no source gate.** I2 (P:127) completes conformance level 4 "with the matching vectors", but no spec gate creates matching vectors; M1.2 covers extraction only. **Fix:** add M1.2b or M2.6, hand-derived matching vectors in `test-vectors/`, checked by `validate`.
- **N6 (low): expected outputs can still be rewritten after an implementation exists.** The precedence check (P:126) covers only the commit that first adds each extractor. A later pin update can change expected bytes once an implementation exists. **Fix:** `check-vector-precedence` flags any expected-output change in a pin update and requires a changelog entry giving the hand derivation.
- **N7 (low): one M1.2 phrase is still vague.** "Each vector carries … an expected output and a rejection case" (R:51) is unclear for vectors that are themselves negative. **Fix:** "each positive vector has a paired rejection vector".

Gate count check: R:23's figures of 41 counted gates, 5 met and 36 open are arithmetically correct (M0 4, M1 6, M2 5, M2E 8, M3 7, M4 6, M5 5). Correcting N3 gives 3 met and 38 open.

**Verdict: not yet ready to adopt. N1 and N2 are the remaining blocking items.** Both are one-line criterion edits. The rest can follow adoption.
