# Draft plan: Traceweave implementation repository

Status: **draft for owner review. Nothing has been created.** Revised after the [independent review](roadmap-v2-review.md). No repository, remote, directory or package exists yet. Companion: [roadmap v2 draft](roadmap-v2.md), whose gate IDs (M1.4, M2.1, …) are referenced below.

## Name and location

- **Proposed:** `traceweave` at `<implementation repo>`. The specification stays in `traceweave-spec`. The CLI binary is `traceweave`.
- **Alternative:** `traceweave-ref`. Choose this if the owner expects several implementations and wants the name to say this one is not the only one. The cost is a longer CLI name, or a binary name that differs from the repository name.

## Scope and non-goals

In scope:

- Deterministic token-fingerprint extraction for Go and Rust source, with original UTF-8 byte spans. TypeScript/JavaScript follows after the TS gates.
- A local catalogue, matcher and localized evidence report, all offline.
- An evaluation harness that reads corpus manifests. Corpus bytes are never committed.
- DSSE sign/verify and commitments, with a second implementation of each.
- An embedding/detection profile, only for a candidate that meets M2E.1.

Non-goals:

- Normative text. The spec repository owns formats, profiles and vectors. This repository implements them and never forks them.
- Resolver, registry, transparency log or timestamp service. These come only after the RES gates and an owner decision.
- Network calls at runtime, telemetry and remote inference.
- Ownership, infringement or licence verdicts.
- Any detection guarantee beyond what a frozen M3 report measured.
- Private applications. They are not fixtures, corpora or test targets, and nothing from a pilot app is copied in.

## How it references the spec

**Recommended: a pinned, pushed spec commit, with vendored copies of the needed spec files and an upstream verification that is mandatory at every milestone exit.**

- **`spec.lock` contents.** It records:
  - the spec repository URL;
  - the full commit ID, which must exist on the remote, never a working tree;
  - the spec version string (currently `0.1.0-draft.1`);
  - a path and SHA-256 for every pinned file.
- **What is pinned.** Pinning covers the files that define behaviour, not only data:
  - `schemas/*.json`, `test-vectors/*.json` and `examples/*.json`, all vendored under `third_party/traceweave-spec/`;
  - `spec/*.md` and `profiles/*.md`, including the M1.1 profile and `conformance.md`.
- **`scripts/check-spec-pin --strict`.** This is used by every I1–I5 exit command. It obtains the pinned commit from a local spec mirror or by fetching once; offline runs use the mirror. It then compares every pinned path, byte-for-byte, against `git show <commit>:<path>`. It **fails** if the commit cannot be obtained, if any digest or byte differs, or if the version string differs. A vendored file and its lock entry edited together therefore still fail. Without `--strict`, the script checks local digests only, for quick local development.
- **Newer upstream.** Newer upstream commits that touch pinned paths are reported, not treated as failures. Changing the pin is a reviewed change.
- **Pin-update rule.** Once any implementation exists, a pin update that changes an expected output in a vector requires two things in the same change: a recorded decision, a changelog entry that gives the hand derivation of the new bytes and the reason; and a re-run of both implementations' conformance. `check-vector-precedence` fails without the decision entry.
- **`scripts/conformance`.** It runs `check-spec-pin --strict` first and refuses to run vectors if that fails.

Why this over a git submodule:

| Concern | Vendored + strict lock | Submodule |
| --- | --- | --- |
| Offline build (M2.1) | Plain clone, plus a local mirror for strict checks | Needs a recursive clone or a second fetch |
| Private, renamed or moved spec repository | Files present; strict check needs mirror access | CI needs credentials; clones break on rename |
| Reviewable updates | Diff shows exact vector and schema changes | Diff shows only a commit ID change |
| Drift or tampering | Strict check against upstream bytes fails | Detached HEAD and local edits are easy to miss |
| Cost | Small duplication plus a pin script | None; built-in git support |

**Licensing of vendored files.** JSON schemas, vectors and examples are Apache-2.0 ([LICENSE.md](../../LICENSE.md)). **Only non-Markdown files are vendored.** Spec and profile Markdown (CC BY 4.0) is pinned by digest and read from the pinned commit at check time, not copied. If Markdown is ever vendored, its CC BY 4.0 notice and attribution are kept beside it.

## Language

Constraints:

- The owner prefers Go and Rust over Python.
- [conformance.md](../../spec/conformance.md) requires two implementations for a stable profile. It requires two implementations, not two languages, but two languages give more independence.
- Python stays in the spec repository's validator and research harnesses only.

| Option | Strengths | Costs and risks |
| --- | --- | --- |
| **A (recommended): Rust primary CLI + Go second implementation** | `rustc_lexer` (pinned `ra_ap_rustc_lexer`) is the compiler's own Rust lexer. Byte spans are natural. Builds a single static binary. Mature tree-sitter bindings (core in C) for TS later. Go's stdlib `go/scanner` is the reference Go lexer. Go DSSE comes from the DSSE maintainers' `go-securesystemslib` | Two toolchains. The Go side needs a Rust-source lexer written to the spec, which is the costliest item. The `ra_ap_*` API changes, so pin exactly. **Risk:** the profile could drift into "whatever `rustc_lexer` emits". M1.1 must define token classes independently, and the Go lexer must match the spec, not rustc |
| B: Go primary + Rust second | Faster to write; continuity with the Go harnesses | Rust-source lexing in Go is still hand-written or uses cgo tree-sitter. The primary binary is weaker on Rust-source fidelity |
| C: one language, two independent implementations | One toolchain | Same-language implementations share libraries and idioms, so less independence, and the second still needs a second lexer. Satisfies conformance.md in form only |

Parser and lexer choice for the token profile:

- **Use lexers, not parsers.** The M1 profile is token-level. `syn` parses items and needs `proc-macro2` span locations for byte ranges. `go/parser` adds an AST the profile does not need. Parsers come in only for STRUCT.1.
- **Independence over uniformity.** If both implementations use tree-sitter, they share grammar bugs. Preferred pairs:
  - Go source: `go/scanner` (Go) vs `tree-sitter-go` (pinned) or a spec-written lexer (Rust).
  - Rust source: `rustc_lexer` (Rust) vs a spec-written lexer (Go).
- **Tree-sitter errors.** ERROR and MISSING nodes become explicit refusals, never silent repair ([fragment checkpoint](../fragment-policy-checkpoint.md)).
- **Reuse measured pins as starting points.** These are `go-securesystemslib v0.11.1`, `wsc-dsse =0.12.1`, `ed25519-compact =2.3.0` and `sha2 =0.10.9` ([signing-interop results](../lanes/signing-interop-results.md)). Recheck current security notes before adopting them (TW-06). Native duplicate-key and key-hint handling differs between them, so each implementation needs its own strict parser (M4.4).

## Licence

- Apache-2.0 for code, configuration, fixtures and vendored JSON. This matches [LICENSE.md](../../LICENSE.md) and [LICENSES/](../../LICENSES/Apache-2.0.txt).
- Prose docs can be CC BY 4.0, as in the spec repository, or the repository can be Apache-2.0 only.
- Keep `LICENSES/` with the original instruments.
- `NOTICE` is optional (the spec repository has none). If present, it names the pinned spec commit.
- Owner chooses.

## Repository layout

```
traceweave/
  spec.lock                      pinned pushed spec commit, version string, per-file SHA-256
  third_party/traceweave-spec/   vendored JSON only: schemas/, test-vectors/, examples/
  rust-toolchain.toml            pinned Rust toolchain
  crates/
    tw-core/                     bytes, spans, profile IDs, config bytes, error codes
    tw-lex-go/  tw-lex-rust/     profile lexers -> token streams with byte spans
    tw-fingerprint/              serialization, hashing, winnowing (k, w, rightmost ties)
    tw-catalogue/ tw-match/      local catalogue, retrieval, alignment, containment
    tw-report/                   canonical report body + separate provenance block
    tw-evidence/                 DSSE, commitments, trust policy, mark records
    traceweave/                  CLI binary
  go/                            second implementation; go.mod with go + toolchain lines
    cmd/tw-verify/  internal/{lexgo,lexrust,fingerprint,report,dsse,commit}/
  conformance/                   runner; vector ID -> implementation output
  eval/                          harness, corpus manifests (no corpus bytes), frozen configs
  fixtures/synthetic/            redistributable walkthrough inputs and expected bodies
  scripts/                       check, check-spec-pin, conformance, offline, walkthrough, eval
  .github/workflows/             written in I0; run locally until the owner enables CI
  LICENSE  LICENSES/  README.md  [NOTICE]
```

## Milestones

The commands below are proposed names; none exists yet. `scripts/offline CMD` runs `CMD` with the network denied: `sandbox-exec` with `(deny network*)` on macOS, `unshare -rn` or `bwrap --unshare-net` on Linux. It first runs a network probe that must fail, and aborts if the probe succeeds.

**I0 prerequisites:**
- a pushed spec commit to pin;
- the Go module path (owner);
- `rust-toolchain.toml` and the Go `toolchain` line;
- JSON Schema 2020-12 validators that can reject unknown fields, chosen and pinned for Rust and Go (for example the `jsonschema` crate and `santhosh-tekuri/jsonschema`; verify draft support before adopting).

| ID | Deliverable | Exit gate (runnable) | Spec gate satisfied |
| --- | --- | --- | --- |
| I0 | Scaffold; checks run locally; spec pin; existing vectors (`commitment.json`, `dsse-pae.json`) in both languages | `cargo fmt --check && cargo clippy --workspace --all-targets --locked -- -D warnings && cargo test --workspace --all-targets --locked && (cd go && go vet ./... && go test ./...) && scripts/check-spec-pin --strict && scripts/conformance --level 2` | None. Repository readiness only; conformance levels 1–2 for this implementation |
| I1 | Token-fingerprint extractor for Go and Rust source with UTF-8 byte spans, in both languages | `scripts/conformance --level 4 --extraction-only --profile <M1.1 id>`: each implementation equals the committed hand-derived expected bytes of every M1.2 vector, and every negative returns its code. `scripts/check-vector-precedence` verifies that the commit first adding each extractor already pins a spec commit containing those vectors, and flags any later pin update that changes an expected output (see the pin-update rule) | M1.4, M1.6 |
| I2 | Catalogue, matcher, localized-report CLI; offline walkthrough | `scripts/offline scripts/walkthrough` checks: the canonical report body (excluding provenance) equals `fixtures/synthetic/expected-body.sha256`; the provenance block is checked separately (config digest, commit = `git rev-parse HEAD`, spec pin); spans N/N; every control class listed. `scripts/conformance --level 4` then completes with the M2.6 matching vectors | M2.1–M2.5, M2.7–M2.11 (vectors from M2.6; M2.7, M2.10 and M2.11 vectors and schemas from spec) |
| I3 | Evaluation harness, licensed public corpus, grouped splits, frozen thresholds | `scripts/eval verify-manifest && scripts/eval verify-freeze && scripts/eval run --split heldout`. `verify-freeze` uses `git merge-base --is-ancestor` to require that the freeze commits are ancestors of the first held-out result commit | M3.1–M3.5 (needs M3.0) |
| I4 | DSSE sign/verify, trust policy (Rust); independent Go verifier with its own strict parser | `scripts/offline scripts/conformance --level 3`: identical bytes and reason codes for every M4.3 vector | M4.4 (M4.3 vectors) |
| I5a | Embedding/detection for candidate C; starts after I2 **and** M2E.1 met | `scripts/conformance --level 4 --profile <embedding id> && scripts/eval run --suite m2e-controls` | M2E.2–M2E.6 (M2E.4 schema from spec) |
| I5b | Mark/fingerprint/combined comparison; after I3 and I5a | `scripts/eval run --suite m2e-combined --split heldout` | M2E.7 |

If M2E.1 is negative-result, I5 is not built, and M2E.0 records the owner's decision.

## What moves out of research/experiments, and what stays

Nothing is moved. The checkpoints cite exact paths and result files, and moving them would break the evidence for the SYN records and for M4.1/M4.2.

- **Reimplemented, not copied without review:**
  - DSSE library pins and policy findings (`signing-interop/`);
  - commitment framing (its `go/` and `rust/` drivers);
  - `go/parser` and `go/ast` patterns;
  - the refusal/abstention vocabulary from the fragment harnesses.
- **Stays as frozen research records:** the SYN carriers, the census scanners and manifests, and the Python rustc harness. The census sample stays out of M3 held-out data.
- **May be consumed later:** carrier-generated synthetic hosts, regenerated from the pinned spec commit, as extra M2E control inputs.

## Needs the owner

1. **Repository creation.** Create the GitHub repository and choose its name and visibility. Push a spec commit that can be pinned; the current spec working tree has much uncommitted research. Decide whether `traceweave-spec` becomes public.
2. **Language.** Confirm option A, or choose B or C.
3. **Licence.** Apache-2.0 only, or the Apache-2.0/CC BY 4.0 split.
4. **Hosted CI.** Whether it may be enabled. Until then, checks run locally.
5. **Independent implementers.** Whether a stable profile (RC.2) needs a second implementer who is a different person. Two languages by one author check that the spec is precise, not that it is read independently.
6. **Thresholds.** The M3.0 false-alarm budget and the M2E.1(c) payload minimum.
