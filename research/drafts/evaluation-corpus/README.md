# M3 evaluation corpus: manifest proposal

Status: **proposed, not acquired, 2026-11-22.** Nothing listed here has been downloaded, cloned or extracted. Acquisition needs the owner's approval (roadmap M3.1, [protocol §14.2](../evaluation-protocol.md#142-acquisition-approval-m31)).

These files accompany the [evaluation protocol](../evaluation-protocol.md) (`m3-eval-draft-1`). They are research material and change nothing normative.

## Files

| File | Contents |
| --- | --- |
| `manifest-proposal.json` | The pool snapshots (100 GitHub search results per language, retrieved 2026-11-22), the selection walk with every verdict and the facts behind it, and 48 proposed entries (24 Go, 24 Rust) with pinned revision, licence files and their digests, licence expression, redistribution status, sizes, split group, provisional split and rationale |
| `manifest.schema.json` | JSON Schema 2020-12 for the manifest. It uses only the keywords `verify_manifest.py` interprets |
| `verify_manifest.py` | Checker, Python standard library only, no network |

## Checking

```
python3 -I research/drafts/evaluation-corpus/verify_manifest.py
python3 -I research/drafts/evaluation-corpus/verify_manifest.py --self-test
```

The first exits 0 when the manifest is valid, 1 when it is not (printing the first error code), 2 on a usage or I/O error. It checks:
- every field against the schema;
- licence: each file classified into the allowlist, the expression equal to the sorted identifiers joined with ` AND `, the redistribution status implied by them, and licence URLs pinned to the revision;
- exclusions: the four census repositories, their owners and the development-exposed owners (`golang`, `rust-lang`) are listed and absent from the entries;
- the selection walk, recomputed from the pool snapshot: order, prefilter verdicts, fact-based verdicts, stopping point, and that the entries equal the accepted set with the same revisions, licence files and sizes;
- groups: derived from owners (and recorded merges), each group in exactly one split, dependency edges inside a group;
- the split assignment, recomputed from the hash rule, and the split digest;
- size limits and totals.

`--self-test` first requires the manifest to pass, then generates broken manifests from it, one rule broken in each, and requires every one to be rejected with its expected error code. It exits 0 only if all are rejected and there are at least ten.

## What the numbers are

- **Pinned revision:** the default-branch head on 2026-11-22, from `git ls-remote`, with the resolution time.
- **Licence:** classified from the text of each root licence file at the pinned revision (fetched from `raw.githubusercontent.com`; blob SHA-1 from the pinned tree, SHA-256 of the fetched bytes). GitHub's own detected licence is kept in the pool snapshot for information only; it is not used.
- **Sizes:** `githubSizeKiB` is GitHub's repository size including history (an upper bound on a clone). Eligible paths and bytes are counted from the pinned tree listing using the path rules of protocol §3.4. The content rule for generated files needs the files and is applied at acquisition.
- **Split:** provisional. Acquisition-time rules (dependency edges, duplicate files, generated files) can reject a repository and continue the walk, which can change groups and therefore the split. The split digest that M3.2 commits is the one computed after acquisition.

## How it was produced

A one-off lookup, on 2026-11-22, used only read-only public endpoints: two GitHub search requests, one pinned-tree request per looked-up repository, `git ls-remote` against `github.com`, and licence files from `raw.githubusercontent.com`. No repository was cloned and no source file other than a licence file was fetched. The lookup script is not kept; the manifest records everything it produced, and `verify_manifest.py` rechecks everything that follows from that record.
