# Behavioural conformance checklist (amendment A6)

Status: draft, 2026-11-22, amended by A7. Companion to [catalogue-report-contract.md](../catalogue-report-contract.md) §6.8 (rules B1–B13; B10 as refined by A8). Item numbers are stable: A7 rewords items 36, 37, 43 and 46 and appends items 47–58; A8 rewords item 55 and appends items 59–60; A9 rewords items 42, 46 and 47 and appends item 61. These behaviours cannot be pinned by vectors. Each item is one command with an observable outcome: an exit status, files present or absent, file modes, or output bytes. Both implementations should script every item. The I2 probe `xcheck/probes/i2_behaviour.py` on `merge-i2` is the current executable record.

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

Exit statuses are the B3 classes: **0** result, **1** refused input, **2** usage, environment, location, I/O or provenance refusal. A process killed by a fault hook's signal has no exit status; items that allow it say "or is terminated by the hook's signal". `TMP(OUT)` means the B8 temporary-file pattern for `OUT`: `.` + the output file name + `.tw-tmp-` + 1–32 characters from `[A-Za-z0-9]`, in `OUT`'s directory.

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
36. `XDG_DATA_HOME=rel/dir`, default output location (B11): on Linux and other non-macOS Unix, exit 2. On macOS (and Windows), where it is not consulted, exit 0, and the file is written under `$HOME/Library/Application Support/traceweave/private` (macOS).
37. `XDG_DATA_HOME=` (empty), default output location, on Linux: treated as unset, so the file is written under `H/.local/share/traceweave/private`, exit 0.
38. `HOME` unset, with no `TRACEWEAVE_PRIVATE_DIR` and no explicit output path: exit 2.

### Stdout and options (B6, B7, B8)

39. `BUILD … -` (the stdout marker): exit 0, catalogue bytes on stdout, and no file named `-` in the current directory.
40. `BODY … - > G/body.json` (shell redirection into a working tree): exit 0, file written by the shell. Stdout is not policed.
41. `EXTRACT … > G/rec.json`: exit 0, bytes equal the expected record. Records go to stdout only, and their destination is the operator's responsibility.
42. An unknown option: exit 2. `TRACEWEAVE_TEST_FAULT=bogus`, and each of the retired names `before-open`, `kill-after-partial` and `rename`: exit 2, no output written (B6).

### Provenance (B10)

43. **Stamped:** `DOC` for `go-identical`: exit 0. `provenance.implementation.commit` equals the commit the binary was built from. `bodySha256` and `comparisonConfigSha256` equal the body's values. A run-time **option** that tries to set the commit is an unknown option: exit 2 (B6). Environment variables that merely look like commit settings are not read; see item 54.
44. **dirty-src** and **dirty-doc:** `DOC`: exit 2, no document written. `BODY`: exit 0, bytes identical to item 13. The same holds for `go run` in a dirty tree, except that the observable is "no document written" rather than an exit status.
45. **Unstamped** (archive export; Go `-buildvcs=false`): `DOC`: exit 2, no document, with or without a run-time commit. `BODY`: exit 0, bytes identical to item 13.
46. **Atomic writes:** for each of the three `TRACEWEAVE_TEST_FAULT` values (B6), a `BUILD` to an existing `OUT` leaves `OUT` byte-identical, and a `BUILD` to a new `OUT` leaves nothing at `OUT`. `before-temp-open` and `rename-fails` exit 2 and leave no `TMP(OUT)` file. `after-partial-write` is terminated by SIGKILL (no exit status) and leaves at most one `TMP(OUT)` file (item 47).

### Temporaries, location consultation, links, stdout and messages (A7: B4, B6–B8, B10–B13)

47. After a `BUILD` with `TRACEWEAVE_TEST_FAULT=after-partial-write`: at most one file matching `TMP(OUT)` exists, with mode 0600 and non-empty content shorter than the expected catalogue. No other new file exists in `OUT`'s directory.
48. Then a normal `BUILD` to the same `OUT`: exit 0. `OUT` holds the expected bytes and no `TMP(OUT)` file remains. A pre-existing `.other.json.tw-tmp-x` (another output's temporary) is left untouched.
49. `TRACEWEAVE_PRIVATE_DIR=rel/dir` with `VALIDATE catalogue` (no location consulted): exit 0. With `BODY … -` to stdout: exit 0.
50. `TRACEWEAVE_PRIVATE_DIR=rel/dir` and `XDG_DATA_HOME=rel/dir` with `BUILD … T/plain/c.json` (an explicit absolute path outside any working tree): exit 0, file written. Compare item 34, where the default location is consulted and the result is exit 2.
51. `T/plain/c.json` is a symbolic link to `G/out/victim.json` (which holds known bytes): `BUILD … T/plain/c.json`: exit 0. `T/plain/c.json` is now a regular file holding the catalogue, and `G/out/victim.json` is byte-identical (B13).
52. `T/link` is a symbolic link to `G/out`: `BUILD … T/link/c.json` with no override: exit 2, nothing written under `G` (B1, after resolving links).
53. `OVERRIDE -` (`-` given to the directory option): exit 2, no file written (B7).
54. **Stamped**, run with `TRACEWEAVE_BUILD_COMMIT=` and `TRACEWEAVE_IMPL_COMMIT=` both set to 40 hex digits of another commit: `DOC`: exit 0, and `provenance.implementation.commit` still equals the build commit (B6, B10).
55. A `git archive` export **unpacked inside `G`** (another repository; the unpacked files are untracked there) and built there, with the implementation's documented verifying build step and with its plain toolchain build: `DOC`: exit 2, no document. `BODY`: exit 0, bytes identical to item 13. The export is not the root of a repository, so no commit can be verified (B10).
56. `XDG_DATA_HOME=T/xdg` (absolute), default output location: on Linux, the file is under `T/xdg/traceweave/private`; on macOS, it is under `$HOME/Library/Application Support/traceweave/private` and nothing is under `T/xdg`. With `TRACEWEAVE_PRIVATE_DIR=T/p` also set, it is under `T/p` on every platform (B11).
57. `VALIDATE record` (and `BUILD` from that record) where the record has an extra key `zzCanaryKey7`: exit 1, and neither stdout nor stderr contains `zzCanary` (B12).
58. `EXTRACT` (Go configuration) on the input `s := "zzCanaryText8` (an unterminated string): exit 0, an error record. Neither the record, stdout nor stderr contains `zzCanary`.

### Verified stamp (A8: B10)

59. **Ignored folder.** `G` has `.gitignore` containing `arch/`, committed. A `git archive` export is unpacked into `G/arch` and built there, both with the verifying build step and with the plain toolchain build. `DOC`: exit 2, no document. The toolchain may report `G`'s HEAD as a clean stamp, but that commit does not describe the code. `BODY`: exit 0, bytes identical to item 13.
60. **Plain toolchain build without the verifying step.** In a clean clone of the implementation's own repository, build with the toolchain's plain build command (for example `go build ./cmd/…` instead of the documented build script). `DOC`: exit 2, no document; `BODY`: exit 0. An implementation whose plain build command *is* the documented verifying step (for example a `build.rs` that performs both B10 checks) records that, and this item then expects item 43's outcome.

### Fault-injection values (A9: B6)

61. One harness, both implementations, `BUILD` to a new `OUT` outside any working tree. Each implementation must give the same observable result for each value:

    | Value | Outcome |
    | --- | --- |
    | `before-temp-open` | exit 2, no `TMP(OUT)` file |
    | `after-partial-write` | terminated by SIGKILL, one `TMP(OUT)` file with mode 0600 |
    | `rename-fails` | exit 2, no `TMP(OUT)` file |
    | empty (`TRACEWEAVE_TEST_FAULT=`) | exit 0, `OUT` holds the expected bytes |

    In every faulted case, nothing exists at `OUT`.

**Item count: 61.** Items 16–24 are nine marker items.
