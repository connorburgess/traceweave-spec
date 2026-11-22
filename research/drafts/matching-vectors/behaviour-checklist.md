# Behavioural conformance checklist (amendment A6)

Status: draft, 2026-11-22. Companion to [catalogue-report-contract.md](../catalogue-report-contract.md) §6.8 (rules B1–B10). These behaviours cannot be pinned by vectors. Each item is one command with an observable outcome: an exit status, files present or absent, file modes, or output bytes. Both implementations should script every item. The I2 probe `xcheck/probes/i2_behaviour.py` on `merge-i2` is the current executable record.

## Operations

Each implementation maps these abstract operations to its own command line:

| Operation | Meaning |
| --- | --- |
| `EXTRACT CFG IN` | Extract one input; the record goes to stdout |
| `BUILD CFG ARTS OUT` | Build a catalogue from sources or records and write it to OUT (B7: `-` means stdout) |
| `BODY R C CC [S] OUT` | Compare and write the canonical report body only |
| `DOC R C CC [S] OUT` | Compare and write a report document (body plus provenance) |
| `VALIDATE KIND FILE` | Validate a catalogue, configuration, record or report document |
| `OVERRIDE DIR` | The option that allows output into a working tree (B2) |

Exit statuses are the B3 classes: **0** result, **1** refused input, **2** usage, environment, location, I/O or provenance refusal.

## Setup

- `T`: an empty scratch directory with no version-control marker in it or above it.
- `H = T/home`: the fake `HOME` for every item. `TRACEWEAVE_PRIVATE_DIR` and `XDG_DATA_HOME` are unset unless an item sets them.
- `G = T/g`: `git init`, one commit; `G/out` and `G/other` exist.
- For each marker `M` in B1: `T/m-M/` containing `M`. `.git`, `.hg`, `.svn`, `.jj`, `.bzr` and `_darcs` are directories; `.git` is also tested as a file (`gitdir: x`); `.fslckout` and `_FOSSIL_` are empty files. Each has a subdirectory `sub/`.
- Inputs come from `matching-vectors/` and `extraction-vectors/`. "Expected bytes" means the vector's recorded bytes or digest.
- Builds:
  - **stamped**: built from a clean clone by the implementation's normal build;
  - **dirty-src**: the same clone with one source file changed before building;
  - **dirty-doc**: only `README.md` changed before building;
  - **unstamped**: built from a `git archive` export. For Go, also `go build -buildvcs=false`.

  `go run` is excluded from exit-status items, because it reports every failure as 1. It is covered by item 44, whose observable is the absence of a document.

## Items

### Results and refused inputs (B3)

1. `VALIDATE catalogue` on the `go-identical` reference catalogue: exit 0, verdict valid.
2. `VALIDATE catalogue` on the `k4-depth-65` reference bytes: exit 1, `malformed-catalogue`.
3. `VALIDATE catalogue` on the `k3-lone-surrogate` reference bytes: exit 1, `malformed-catalogue`.
4. `VALIDATE report` on `example-report.json`: exit 0.
5. `VALIDATE report` on `{"body":` + 64 × `[` + 64 × `]` + `,"provenance":{}}` (65 levels): exit 1, rejected before schema validation (B9).
6. `VALIDATE report` on a report document whose `provenance.implementation.name` is `"\ud800"`: exit 1 (B9).
7. `BUILD` from the records of `cat-text-plain`: exit 0, catalogue SHA-256 equals `expectedCatalogueSha256`.
8. `BUILD` with an empty artifact list: exit 1, no output file.
9. `BUILD` from the records of `build-unregistered-profile`: exit 1, no output file.
10. `BUILD` from the inline record of `build-tokencount-mismatch`: exit 1, no output file.
11. `BODY` for `go-config-mismatch`: exit 0 (a rejected body is a result), body SHA-256 equals `bodySha256`.
12. `EXTRACT` with an invalid configuration (`config-negative.json#cfg-whitespace`): exit 0, the record equals `records.json#rec-unsupported-config`.
13. `BODY` twice for `go-identical`: both exit 0, identical bytes, equal to `bodySha256`.

### Working trees and markers (B1)

14. `BUILD … G/out/c.json` with no override: exit 2, nothing written under `G`.
15. `BUILD … G/out/new/c.json`, where `new` does not exist: exit 2, `G/out/new` not created.
16.–24. For each marker in turn (`.git` directory, `.git` file, `.hg`, `.svn`, `.jj`, `.bzr`, `_darcs`, `.fslckout`, `_FOSSIL_`): `BUILD … T/m-M/sub/c.json` with no override: exit 2, no file written. That is 9 items.
25. `BUILD … T/plain/c.json`, where `T/plain` has no marker: exit 0, file written.

### Override scope (B2)

26. `BUILD … G/out/c.json` with `OVERRIDE G/out`: exit 0, file mode 0600, every directory the implementation creates has mode 0700.
27. Same with `OVERRIDE G` (an ancestor; the working-tree root): exit 2, no file.
28. Same with `OVERRIDE G/out/sub` (a descendant): exit 2, no file.
29. Same with `OVERRIDE G/other` (a sibling): exit 2, no file.
30. Same with `OVERRIDE G/out/c.json` (the file path): exit 2, no file.
31. With current directory `G`: `BUILD … out/c.json` with `OVERRIDE out` (relative paths resolved from the current directory): exit 0, file written.
32. With `L` a symbolic link to `G/out`: `BUILD … L/c.json` with `OVERRIDE G/out` (compared after resolving links): exit 0, file written at `G/out/c.json`.

### Location values (B4, B5)

33. `TRACEWEAVE_PRIVATE_DIR=G/priv`, default output location: exit 2, nothing under `G`.
34. `TRACEWEAVE_PRIVATE_DIR=rel/dir`: exit 2.
35. `TRACEWEAVE_PRIVATE_DIR=` (empty): treated as unset. The default location under `H` is used, exit 0.
36. `XDG_DATA_HOME=rel/dir` on an OS where the implementation consults it: exit 2. On an OS where it does not, the implementation's documentation says so and the item records "not consulted".
37. `XDG_DATA_HOME=` (empty), where consulted: treated as unset, exit 0.
38. `HOME` unset, with no `TRACEWEAVE_PRIVATE_DIR` and no explicit output path: exit 2.

### Stdout and options (B6, B7, B8)

39. `BUILD … -` (the stdout marker): exit 0, catalogue bytes on stdout, and no file named `-` in the current directory.
40. `BODY … - > G/body.json` (shell redirection into a working tree): exit 0, file written by the shell. Stdout is not policed.
41. `EXTRACT … > G/rec.json`: exit 0, bytes equal the expected record. Records go to stdout only, and their destination is the operator's responsibility.
42. An unknown option: exit 2. An unknown value of the implementation's fault-injection variable (`TRACEWEAVE_TEST_FAULT=bogus`, or its documented name): exit 2.

### Provenance (B10)

43. **Stamped:** `DOC` for `go-identical`: exit 0. `provenance.implementation.commit` equals the commit the binary was built from. `bodySha256` and `comparisonConfigSha256` equal the body's values. Any run-time option or variable that tries to set the commit: exit 2.
44. **dirty-src** and **dirty-doc:** `DOC`: exit 2, no document written. `BODY`: exit 0, bytes identical to item 13. The same holds for `go run` in a dirty tree, except that the observable is "no document written" rather than an exit status.
45. **Unstamped** (archive export; Go `-buildvcs=false`): `DOC`: exit 2, no document, with or without a run-time commit. `BODY`: exit 0, bytes identical to item 13.
46. **Atomic writes:** for each fault hook the implementation documents, a `BUILD` that fails at the hook exits 2, leaves the previous `OUT` byte-identical, and leaves nothing at `OUT` if there was no previous file (only a dot-temporary file may remain).

**Item count: 46.** Items 16–24 are nine marker items.
