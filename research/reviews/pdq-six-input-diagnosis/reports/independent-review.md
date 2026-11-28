# Original independent review with PDQ-D1 finding — labelled portable adaptation

Original SHA-256 `1abe8a7a08cffd5dde65b4653455c7d7167f58b746f2cf0add511903377526eb`, 13792 bytes. Original retained unchanged privately. Markdown attachment/local-locator links are made inert; remaining body is unchanged. Inline artifact names describe the original package, not an assertion that every named file is published here. See the [retention manifest](../retention-manifest.json) and [package scope](../README.md). Historical pending/adverse statements keep their original date/scope; only the focused D1 addendum supersedes its report-correction condition. This adaptation is not an independent review of its own retention package.

---

# Independent review: retained six-input PDQ numeric diagnosis

**Numerical disposition: supported and independently reproduced at the bounded six-input/one-host scope. Exact report/package disposition: changes requested for PDQ-D1, an incorrect flip-sign table.** No arithmetic, fixture or gate correction is requested. The unchanged baseline remains **32/48 exact hashes, 6/6 exact qualities**, including both low-quality mismatches. This is not generalized parity or IMGF.5 eligibility.

Reviewed original diagnosis `report.md`, SHA-256 **`a81e276273276d095c568a3bb5dfb9abec02c0ac81d629184b13bc00c53f78c4`**, in the retained `pdq-mismatch-diagnosis` package. Its `SHA256SUMS` SHA-256 is **`7d27b104fe18fc4f1e8d2c75b85108160e0d8e97bf8ba4779b694e34e7d86f99`**. All **411 listed files** verify; the complete package has **412 files**, with only that manifest outside its own list. The preceding smoke report and prior independent review were read in full as context; original smoke's 64-entry manifest/65-file inventory also verify. Exact original inventories are in original-identities.json (original attachment/locator; see retention manifest).

## PDQ-D1 — report and generator reverse both flip sign masks

Affected author record: report.md:76 (original attachment/locator; see retention manifest) and line 77; the same text occurs at `write-report.py:78–79`.

The report table says:

- `flipx`: −B if **i odd**, else +B.
- `flipy`: −B if **j odd**, else +B.

Both retained implementations do the opposite:

- **Correct flipx: +B if i odd, else −B**, without transposition.
- **Correct flipy: +B if j odd, else −B**, without transposition.

Evidence: retained C++ `pdqhashing.cpp`, `dct16OriginalToFlipX`/`dct16OriginalToFlipY`, explicitly retain the value in the odd-index branch and negate it in the even-index branch. Frozen Python `pdq_np.py:181,183` uses `np.where(i & 1, b, -b)` / `np.where(j & 1, b, -b)`. These agree with actual dumped arrays and hashes. The independent scalar checker initially followed the report's two table entries and failed its exact observed-array check; the retained reported-table diagnostic (original attachment/locator; see retention manifest) / failure log (original attachment/locator; see retention manifest) exposes the mismatch. Using the actual source masks yields byte-identical observed transformed arrays and correct hashes for all 48 variants.

This is a **report/generator factual correction required before accepting this exact report unchanged**. Correct those two rows in the report and its generator, and refresh the package's affected identity/manifest records. Do not alter numeric outputs, implementation masks, frozen mappings, input membership, thresholds or equality counts. The arithmetic diagnosis itself survives; the issue does not identify a defect in either PDQ implementation.

## Verified instrumentation and unchanged baseline

Fresh scratch copy only; author package, original smoke and prior review trees were inventoried before use and checked unchanged afterward. `prepare.py` was executed only in the new copy after removing the copied instrumented-source directory. Its regenerated observation-only patch is byte-identical, SHA-256 `a3569a2fd63fe3ee7c32351645a8ad0646c0b514b5cf05df72d57397db20c4fe`.

The only modified source files in that copy are `pdqhashing.cpp` and `downscaling.cpp`. The patch adds stream/file helper code, reads of arrays/scalars, trace calls and a trace-name counter. It leaves all arithmetic expressions, constants, loop order, float storage, Torben call, strict predicate and hash packing untouched. The counter names eight per-process observations; each input runs in a separate process. Tracing can affect execution/optimization context in principle, so exact output checks remain necessary: all six instrumented stdout objects, qualities and all 48 hashes equal the unchanged baseline. No general uninstrumented-intermediate identity claim is needed.

Independent source checks verified all **17 retained C++/licence file SHA-256/Git blob identities** and all **13 Python file SHA-256 identities and frozen local Git bytes**. The retained source subset/licences reproduce; no new upstream commit-object authentication was added. Python vendor and NumPy port remain one arithmetic reference, not independent corroborating implementations. No acquisition script was executed.

Both baseline and instrumented binaries were rebuilt using existing Apple clang **21.0.0**, `-std=c++11 -O2 -fno-fast-math -ffp-contract=off`, the unchanged bridge and the three retained translation units. The rebuilt binary hashes happen to equal the author artifacts:

| Artifact | Reproduced SHA-256 |
| --- | --- |
| Baseline binary | `ba757a0791cb4a6b5ab1d2493daddb325d04ba02bb52fb9b0a098441b42bcfeb` |
| Instrumented binary | `bcd50af99b5d6db87ae729988a9aaf2dad6cf51c38ec256c7606cec17572c262` |
| Baseline comparison JSON | `a1cf1f2c738bf678f6b232621bda0ba92e6438f09ac9c51895106da2ac763a24` |
| Diagnosis JSON | `1138003d21fed6ad86ff8e418e913157f97a7bb187c6ae233f62e8908757a153` |
| Mixed-probe JSON | `27886d1715a7e3f2172cc3189d0fcf05bf55d0cb7e2d6f4f24e899594e59c744` |

All three numerical JSON records and **all 276 trace files** are byte-identical to the author package. Copied workspace/command locations differ appropriately. Five author diagnostic tests pass, including changed-observation, wrong-variant and non-strict-tie negatives. No full-study files or new inputs were run.

## Independent reconstruction and circularity assessment

The author's `cpp-D-f32` probe uses the **observed** C++ matrix. That is valid conditional recovery of T/B arithmetic given those coefficients; by itself it would not independently explain how the coefficients arose. The author's separate coefficient prediction reports the missing construction step. This review independently closes that distinction with independent-check.py (original attachment/locator; see retention manifest), without importing author numeric helpers or using an observed matrix/T/B value to construct its prediction:

1. Read only the six retained input payloads, independently check every sample against its declared integer rule/dimension and select decimation positions directly from original coordinates. All four blur-pass dumps equal the original integer luma payload; A agrees exactly. Window size is one in this set, so no larger-window inference follows.
2. Build D from the literal source formula: binary32-cast `sqrt(2/64)` scale, host scalar cosine using the retained double pi/order, then binary32 coefficient storage. All **1,024 coefficient bytes** agree in each of the six dumps. Independently formed binary64 Python coefficients agree with recorded Python D. Exactly **112/1,024** coefficients differ from merely final-rounding that Python D to binary32; maximum discrepancy is `1.4901161193847656e-08`.
3. Execute separate scalar k=0…63 loops, rounding with `struct.pack/unpack` for binary32 multiplication/addition. This uses the **predicted source-derived D**, not observed D. All **12 T/B byte comparisons** (six inputs × two stages) agree with actual C++ dumps, and all 48 C++ hashes follow with independent lower-median selection/packing. Separate scalar binary64 loops reproduce frozen Python T/B bytes and all Python hashes.
4. Independently implement all eight signed/transpose maps from source (with corrected flip masks), choose sorted lower median index127, compare strictly `>`, and place flat index k at integer bit `1<<k`. All 48 transformed C++ arrays agree byte-for-byte; actual recorded Torben medians equal the lower median numerically (signed-zero equality is numeric); all 48 C++ and Python hashes agree with their baselines.
5. Verify **every one of 1,606 affected CSV decisions**, not just row counts: variant/index/coordinates, both represented coefficients, both medians, both margins and both booleans. Sets/indices equal independent XOR decisions, with no missing/duplicate rows. Constant127 contributes **1,118** decisions and low-contrast **488**; the remaining four cases contribute zero. No tolerance or quality waiver is used.

See independent results (original attachment/locator; see retention manifest) and log (original attachment/locator; see retention manifest). The prediction still uses this host's scalar libm, exactly as its scope requires; this is not a platform-independent transcendental proof or a new PDQ reference implementation.

First differences agree with the report: D differs numerically at every entry versus Python binary64, but black products remain zero. On all five nonzero cases the first data-dependent discrepancy is **T[0,0]**, followed by B. T has 1,024 differing entries except tall's 1,022; B has 256 on each nonzero input. Blur/decimation do not explain these cases. The retained diagnosis's first coordinates, values and maximum numeric errors match independent calculations.

## One-factor substitutions and causal scope

All six existing diagnostic paths were independently recomputed on exactly the same six reconstructed A arrays and operation order; their T/B records and all variant hashes match the author's saved paths. No extra substitution/model, accumulation order or input was introduced.

- `rounded-python-D-f32` holds binary32 products/accumulation/storage fixed and changes coefficient construction (specifically removing the early scale-rounding effect).
- `wide-sum` holds the C++ coefficient values and binary32 products fixed, accumulates in binary64, then returns each T/B stage to binary32 storage. This isolates accumulator precision within the stated model.
- `wide-product` holds coefficient values and per-add binary32 accumulator/storage fixed, forms binary64 products, then rounds each added result to binary32. This isolates product precision within the stated model; it is not baseline binary32 multiplication or a proposed replacement implementation.
- `cpp-D-f64` is a broader arithmetic-precision intervention: products, sums and stage storage all become binary64 while coefficients remain widened C++ values. It must not be read as individually isolating product versus accumulator rounding. The mixed probes supply that separation.
- `cpp-D-f32` recovers all C++ observations; `python-D-f64` recovers frozen Python observations. Each of the three focused changes alters problematic hash decisions. None individually restores Python's eight hashes for either problematic case. This supports an interacting path explanation, not a standalone fix or a ranking of necessary contributions.

Thus the finite source-derived binary32 path is sufficient to account for the observed residuals and all bits; the observed-matrix conditional check is not being mistaken for an independent coefficient oracle. No untested ordering or platform hypothesis is needed to **explain these observations**, but other hosts, flags, dimensions, inputs or arithmetic paths have not been eliminated. “Precision explains this execution” is supported at that scope; universal exclusivity is not.

The saved question/addendum and prebuild/pre-mixed identities are consistent records of the stated sequence. They are not immutable independent preregistration or trusted timestamps; this review does not upgrade them into that stronger chronological proof.

## Network denial, reproduction and preservation

All compiler/core/probe commands ran as descendants of `/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)'`. The review launcher proves loopback `bind` fails with **EPERM before compilation/core/probes**; copied baseline/diagnosis launchers also enforce their pre-core denial check. The independent scalar checker separately proves the same precondition. No public endpoint was contacted or probed. Existing environment is CPython **3.14.6**, NumPy **2.5.5**, Pillow **13.0.0**; no dependency install or decoder operation was performed.

Reproduction evidence: reproduce.py (original attachment/locator; see retention manifest), command list (original attachment/locator; see retention manifest), top-level log (original attachment/locator; see retention manifest), compiler log (original attachment/locator; see retention manifest), baseline (original attachment/locator; see retention manifest), diagnosis (original attachment/locator; see retention manifest), mixed probes (original attachment/locator; see retention manifest), five tests (original attachment/locator; see retention manifest). Scratch locator (original attachment/locator; see retention manifest) identifies the fresh copied package/run roots. Re-run only into another fresh copy; never run the author's retained reproduction script in place. `prepare.py` is a one-time constructor; the review removes only the copied source directory before regenerating it. No `acquire.py`, new source export, full30/1400 study, corpus, M3, source-port edit, service, public record, publication or subagent was used.

Preservation result (original attachment/locator; see retention manifest) checks complete diagnosis/smoke/prior-review inventories after execution. All originals remain unchanged. Raw upstream metadata and these review copies remain private thread storage; no repository or public history was modified. Exact review artifact hashes are retained in review-identities.json (original attachment/locator; see retention manifest).

## Final boundary

**Numerical finding accepted in scope; PDQ-D1 blocks acceptance of the exact report wording until its two flip rows/generator and manifest identities are corrected.** Only a focused document/identity recheck is needed for that correction if arithmetic/source/output artifacts remain unchanged. No numerical rerun is requested solely for the table typo.

This remains a six-input integer common-luma diagnosis on one host/compiler/build, bypassing RGB conversion, decode and pre-resize and using unit blur windows. It does not establish noninteger behavior, other dimensions/windows/hosts, full vector/frozen-set agreement, threshold calibration, natural-image rates or authenticated upstream commit binding. Low-quality mismatches remain raw mismatches. IMGF.5 stays open, M3 stays held, and no generalized parity, gate change, full study or acquisition follows.
