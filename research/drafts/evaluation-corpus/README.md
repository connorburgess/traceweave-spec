# M3 evaluation corpus: manifest proposal

Status: **proposed, not acquired, 2026-11-22.** Nothing listed here has been downloaded, cloned or extracted. Acquisition was approved on 2026-11-23, with the mechanical replacements, storage at `~/traceweave-eval` and the licence recheck failing closed ([protocol §14.2](../evaluation-protocol.md#142-acquisition-approval-m31)).

These files accompany the [evaluation protocol](../evaluation-protocol.md) (`m3-eval-draft-4`). They are research material and change nothing normative.

## Files

| File | Contents |
| --- | --- |
| `manifest-proposal.json` | The pool snapshots (100 GitHub search results per language, retrieved 2026-11-22), the selection walk with every verdict and the facts behind it, and 48 proposed entries (24 Go, 24 Rust) with pinned revision, licence files and their digests, licence expression, redistribution status, sizes, split group, provisional split and rationale |
| `manifest.schema.json` | JSON Schema 2020-12 for the manifest. It uses only the keywords `verify_manifest.py` interprets |
| `verify_manifest.py` | Checker, Python standard library only, no network |
| `IMPLEMENTING.md` | Implementer brief: every harness script in order, with inputs, outputs, protocol section and pass/fail observable |

## Checking

```
python3 -I research/drafts/evaluation-corpus/verify_manifest.py
python3 -I research/drafts/evaluation-corpus/verify_manifest.py --self-test
python3 -I research/drafts/evaluation-corpus/verify_manifest.py --licence-dir DIR
```

The first exits 0 when the manifest is valid, 1 when it is not (printing the first error code), 2 on a usage or I/O error. It checks:
- every field against the schema;
- licence: each file classified into the allowlist, the expression equal to the sorted identifiers joined with ` AND `, the redistribution status implied by them, and licence URLs pinned to the revision;
- exclusions: the four census repositories, their owners and the development-exposed owners (`golang`, `rust-lang`) are listed and absent from the entries;
- the selection walk, recomputed from the pool snapshot: order, prefilter verdicts, fact-based verdicts, stopping point, and that the entries equal the accepted set with the same revisions, licence files and sizes;
- groups: one owner each, each group in exactly one split; no two entries dependency-linked; every acquisition-time rejection (`dependency-linked`, `duplicate-content`) carries its facts and names an accepted repository earlier in the walk (the tie rule), and their count stays within the replacement limit of 8 per language;
- the split assignment, recomputed from the hash rule, and the split digest;
- size limits and totals.

`--self-test` first requires the manifest to pass, then generates 42 broken manifests from it, one rule broken in each, and 4 broken licence-text cases built from synthetic licence texts (no third-party text is shipped), and requires every one to be rejected with its expected error code. It exits 0 only if all 46 are rejected.

`--licence-dir DIR` is the acquisition-time licence recheck (protocol §3.6, review item M5). For every entry it reads `DIR/<owner>/<repo>/<path>` for each recorded licence file, recomputes the SHA-256 and length, and reruns the licence classifier `m3-licence-classifier-v1`. Any missing file or difference exits 1. Run on 2026-11-22 against the 55 licence files re-fetched at the pinned revisions, it passed (exit 0).

## What the numbers are

- **Pinned revision:** the default-branch head on 2026-11-22, from `git ls-remote`, with the resolution time.
- **Licence:** classified from the text of each root licence file at the pinned revision (fetched from `raw.githubusercontent.com`; blob SHA-1 from the pinned tree, SHA-256 of the fetched bytes). GitHub's own detected licence is kept in the pool snapshot for information only; it is not used.
- **Sizes:** `githubSizeKiB` is GitHub's repository size including history (an upper bound on a clone). Eligible paths and bytes are counted from the pinned tree listing using the path rules of protocol §3.4. The content rule for generated files needs the files and is applied at acquisition.
- **Search count:** the checker reports held-out negative searches as **unordered** repository pairs (132 for 12 + 12 held-out groups), the M3.0 unit of protocol draft-2.
- **Split:** provisional. Acquisition-time rules (dependency edges, byte and token-digest duplicates, generated files, lexing and token count) can reject a repository and continue the walk, which can change groups and therefore the split. The split digest that M3.2 commits is the one computed after acquisition.

## How it was produced

A one-off lookup, on 2026-11-22, used only read-only public endpoints: two GitHub search requests, one pinned-tree request per looked-up repository, `git ls-remote` against `github.com`, and licence files from `raw.githubusercontent.com`. No repository was cloned and no source file other than a licence file was fetched. The lookup script is not kept; the manifest records everything it produced, and `verify_manifest.py` rechecks everything that follows from that record.

## Changes for draft-2

The entries, revisions, licence files, walk, sizes and split digest (`146acfc2…69dce3`) are unchanged: no draft-2 rule can be applied before acquisition, so none changes the proposal. What changed:
- `manifestVersion` is `traceweave-m3-corpus-manifest-draft-2` and `protocolVersion` `m3-eval-draft-2`;
- `groupMerges` is removed, because groups no longer merge: the later of two linked repositories is rejected;
- a new `acquisition` block records the replacement limit (8 per language), what approval covers, the fail-closed licence recheck, and the search unit (unordered repository pair);
- walk records may carry `linkedTo` for `dependency-linked` and `duplicate-content` rejections, and `dependencyEdges` record the manifest file that declares each edge;
- the checker counts searches as unordered pairs (132, was 264 ordered; 10 same-domain, was 20), adds the licence recheck, and its self-test grew from 34 to 45 rejected cases.

## Changes for draft-3

Only `protocolVersion`, now `m3-eval-draft-3`. The draft-3 changes (Go `rename` scope, inserted-`;` statement ends, the lexing-commit pin and excluded-file bound, struct/interface braces) apply at acquisition and case generation, so the entries, walk and split digest are unchanged and the checker's rules are unchanged.

## Changes for draft-4

Only `protocolVersion`, now `m3-eval-draft-4`, which records the owner decisions (budget `1/20`, acquisition approved, storage `~/traceweave-eval`). Entries, walk and split digest are unchanged. `IMPLEMENTING.md` is new.

## Draft-5

The protocol moved to `m3-eval-draft-5` (lane 11 audit: fold-S outcome count, `k` = 16, tuning table with the freeze, alarm audit, follow-ups). **The manifest is unchanged**, including its `protocolVersion` `m3-eval-draft-4`: no draft-5 rule touches selection, licences, groups or splits, and the checker's rules are the same. `IMPLEMENTING.md` follows draft-5.

## Draft-6

`manifestVersion` is now `traceweave-m3-corpus-manifest-draft-3` and `protocolVersion` `m3-eval-draft-6`; entries, walk and split digest are unchanged. The schema and checker gained (harness ruling A25):
- `status` (manifest and entries) may be `acquired`; entries must carry the manifest's status;
- the walk fact `eligibleFileCountAfterContentRules`, required in an acquired manifest for every repository that passed the path rules; below 10 it derives `too-few-eligible-files` as an acquisition-time rejection, counted against the replacement limit;
- acquisition-time rejections are refused in a manifest that is not acquired (`E-STATUS`).

The self-test now also builds three acquired variants that must pass (one with no rejection, and a Rust and a Go A25 rejection, each replaced by continuing the walk with synthetic facts) and four acquired variants that must fail, for 51 rejected cases in all.

## Draft-7

The protocol moved to `m3-eval-draft-7` (rulings O1–O8). Nothing in it touches the manifest, schema or checker, so the manifest keeps `protocolVersion` `m3-eval-draft-6` and is unchanged.

## Draft-8

The protocol moved to `m3-eval-draft-8` (direct-check shape, unbatched caching check, disk figures and a 10 GB minimum margin). The manifest, schema and checker are unchanged; the manifest keeps `protocolVersion` `m3-eval-draft-6`.
