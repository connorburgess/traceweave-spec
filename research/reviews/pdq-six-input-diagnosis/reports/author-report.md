# Revised author diagnosis — labelled portable adaptation

Original SHA-256 `2816c35b4ce7ace508170bb6f55a515fe4df60cec7a20d0d3603f66e30ebac95`, 15569 bytes. Original retained unchanged privately. Markdown attachment/local-locator links are made inert; remaining body is unchanged. Inline artifact names describe the original package, not an assertion that every named file is published here. See the [retention manifest](../retention-manifest.json) and [package scope](../README.md). Historical pending/adverse statements keep their original date/scope; only the focused D1 addendum supersedes its report-correction condition. This adaptation is not an independent review of its own retention package.

---

# IMGF.5 retained six-input mismatch diagnosis

2026-11-27. **Causal localization on the retained six-input common-luma set: DCT coefficient construction and binary32 product/accumulation roundoff account for every observed hash bit.** This is a diagnostic finding, not parity, a replacement implementation, or gate eligibility. The unchanged baseline remains **32/48 exact hashes, 6/6 exact qualities**, with constant127 and low-contrast mismatching in every variant. No case is waived.

## Scope and preservation

Only black, constant127, low-contrast, asymmetric, wide and tall from the original declaration were used. All six input byte hashes are in `baseline-artifact/comparison.json`; none was changed. No acquisition script, install, network request, corpus, decoder, RGB conversion, image/text-mark study, GPU, full30/1400 run, M3, service or sublane was used. All new files stay in this thread-storage directory. Shared repository Git status was empty at completion; no commit, gate or protocol change.

Read the original author smoke report and independent review first. The original 65-file inventory was saved before copying (`original-hashes.json`); every original was rehashed unchanged after diagnosis. Source/licence bytes and Python sources were checked against the retained 17-file/13-file manifests before baseline execution. Original author/reviewer records are not edited. The copied binary initially lacked execute permission (retained mode 0644): its first launch returned EACCES, then only the scratch binary was chmod u+x. No core output existed on that failed launch. The successful copied baseline `comparison.json` is byte-identical to the original. `baseline-artifact/workspace-path.txt` alone points at the scratch baseline root.

Source identity remains qualified exactly as the independent review requires: retained C++ subset labelled revision `9f627fb1d6d2a4a26c9b5ee1d6ca5e5ccc8e06a2`; manifest blob/file hashes checked, but no independent upstream commit-object authentication was added. Frozen Python export is spec `6f39e50f33026c9f1d9526c2a566d6a447219667`. The Python vendor and NumPy port are one arithmetic reference, not two independent implementations. Adjacent licences/notices remain retained. Raw upstream metadata remains in thread storage only.

## Declaration, instrumentation and commands

`questions.md` was written before any new core execution/instrumentation. It declares stage localization, strict-median/variant tracing and arithmetic substitutions. Its conditional mixed-product/accumulation addendum was saved before those runs. `prebuild-identities.json` records exact instrumented source and patch identities before compilation; `pre-mixed-identities.txt` records the follow-up declaration and code before execution.

`prepare.py` copies the retained source, then `instrumentation.patch` adds only writes: four Jarosz pass boundaries, DCT matrix and input A, first product T, eight transformed B arrays and their actual Torben medians. Dump files are native binary32 (this retained arm64 host is little endian). Python arrays/probe stages are explicitly little-endian binary64 `.f64`; binary32 diagnostic results are widened exactly for storage. No core arithmetic, constants, loop order or predicates are edited. Build used existing Apple clang 21.0.0, `-std=c++11 -O2 -fno-fast-math -ffp-contract=off`, identical to baseline. Compiler version is retained.

Every compiler/core/probe command ran under `/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)'`. Baseline and diagnostic Python launchers require loopback bind to fail with EPERM before importing/running the core. `commands-run.json` retains exact six instrumented argv and dump directories; `reproduce.sh` records baseline, build, analysis, probes and tests using the existing pinned Python3.14.6/NumPy2.5.5/Pillow13.0.0 environment. Run it with `sh reproduce.sh` in this retained location; it writes scratch outputs only and never calls `acquire.py`. `prepare.py` is a one-time source-copy constructor; don't rerun it over an existing instrumented directory. A relocated package must update only the copied workspace-path file and existing interpreter path first.

Each instrumented stdout object was compared with the corresponding unchanged baseline BEFORE drawing conclusions; all six matched exactly, including qualities and all 48 hashes. Instrumentation did not alter the baseline. A separate software reconstruction using the observed C++ matrix and sequential binary32 multiply/add yields bit-identical T and B bytes on all six inputs (12/12 stage checks), and exact hashes for all eight variants of each input.

## First differing intermediate

All four row/column Jarosz pass arrays and the decimated 64×64 A agree numerically exactly on every input. Window size is 1 on these dimensions; integer arithmetic is exact through the running sums here. Thus neither blur nor decimation explains these mismatches. These observations do not generalize to larger dimensions/windows.

The DCT matrix has 1024/1024 entries numerically different when C++ binary32 is widened and compared with Python binary64. More specifically, 112/1024 C++ entries differ even from simply rounding the Python matrix to binary32 (maximum 1.4901161193847656e-08). C++ rounds `sqrt(2/64)` to binary32 first (0.1767766922712326); Python keeps 0.1767766952966369. Using the rounded scale, the existing host's scalar cosine and a final binary32 cast reconstructs **all 1024 C++ coefficient bytes**. There is no residual matrix discrepancy requiring a cosine/transcendental-constant or accumulation-order hypothesis on this host.

For black the DCT input and all computed products remain zero despite differing coefficients. For every nonzero input the first data-dependent difference is T[0,0], followed by B; table counts use numeric equality (bitwise software-reconstruction checks are retained separately).

| Input | T entries differing /1024 | B entries differing /256 | B maximum absolute difference | Exact hashes /8 | Quality Python/C++ |
|---|---:|---:|---:|---:|---|
| black | 0 | 0 | 0 | 8 | 0/0 |
| constant127 | 1024 | 256 | 6.5938365878537297e-12 | 0 | 0/0 |
| low-contrast | 1024 | 256 | 5.5487693313982511e-06 | 0 | 11/11 |
| asymmetric | 1024 | 256 | 0.00010090162007259096 | 8 | 100/100 |
| wide | 1024 | 256 | 8.498892046304718e-05 | 8 | 100/100 |
| tall | 1022 | 256 | 0.00010896503536450552 | 8 | 100/100 |

Exact first coordinates/values and maximum errors for each stage are in `diagnosis.json`. No quality or matching thresholds were changed.

## Controlled arithmetic probes

Each variant below uses only the SAME six decimated A arrays, k=0…63 in the frozen order, the original median and strict `>` bit rule. These are diagnostic substitutions, not proposed implementations. Each cell reports exact hashes versus **C++ / Python**, out of8. Nonzero high-contrast inputs and black retain8/8 versus both in all probes; numeric B still changes for high-contrast inputs.

| Diagnostic | constant127 | low-contrast |
|---|---|---|
| cpp-D-f32 | 8/0 | 8/0 |
| rounded-python-D-f32 | 0/0 | 0/0 |
| cpp-D-f64 | 0/0 | 0/0 |
| python-D-f64 | 0/8 | 0/8 |
| wide-sum | 0/0 | 0/0 |
| wide-product | 0/0 | 0/0 |

- cpp-D-f32: observed C++ matrix, rounded binary32 products and binary32 additions/storage. Reproduces C++ T/B bytes and all48 hashes.
- rounded-python-D-f32: same binary32 arithmetic/order, but final-cast Python coefficients without the earlier scale rounding. This isolates coefficient construction's contribution.
- cpp-D-f64: same observed coefficients widened exactly, sequential binary64 products/additions. Changes arithmetic precision alone.
- python-D-f64: original Python coefficients and sequential binary64 arithmetic. Reproduces frozen Python T/B and hashes.
- wide-sum: C++ coefficients, binary32 products accumulated in binary64, T/B stored back to binary32. Isolates accumulator precision from baseline; no reordering.
- wide-product: C++ coefficients, binary64 products added to binary32 accumulators, rounded after each addition, T/B stored binary32. Isolates product precision from baseline; no reordering.

All three one-factor interventions (coefficient construction, product precision, accumulator precision) change problematic bit decisions. No ordering or platform-constant experiment is needed to explain the observed residuals. The combined specified binary32 path is sufficient to recover every C++ intermediate/bit; the frozen binary64 path recovers every Python bit. This is causal evidence for this exact execution path and six inputs, not proof that precision is the only possible source of disagreement across hosts or the full profile.

## Median, mappings and affected bits

All48 actual C++ medians equal the sorted lower median (index127), as do Python medians. All48 C++ transformed B arrays match the frozen mapping; independent integer packing of `B > median` reproduces all48 output hashes. No median algorithm, bit order or transform-direction defect was observed.

Using untransformed B[i,j], zero-based:

| Variant | Mapping |
|---|---|
| orig | B[i,j] |
| rot90 | transpose of (+B if j odd, else −B), CCW convention |
| rot180 | −B if i+j odd, else +B |
| rot270 | transpose of (+B if i odd, else −B) |
| flipx | +B if i odd, else −B (top/bottom) |
| flipy | +B if j odd, else −B (left/right) |
| flipp | transpose B |
| flipm | transpose of (−B if i+j odd, else +B) |

Every affected bit is retained in `traces/INPUT/affected-bits.csv`: variant, flat bit index=i×16+j, coordinates, both exact represented coefficients, both medians/margins and both boolean decisions. The hash integer places this index at 1<<index; hexadecimal displays most significant words first. `diagnosis.json` retains per-variant indices, tie counts, magnitudes and maximum changed-bit margins. There are no hidden tolerances; the following decimal magnitudes are explanatory summaries only.

| Input/variant | Differing bits | C++ median | Python median | Median ties C++/Python | Max changed-bit C++ abs margin | Max changed-bit Python abs margin |
|---|---:|---:|---:|---:|---:|---:|
| constant127/orig | 138 | 0 | 0 | 100/2 | 6.5938365878537297e-12 | 8.9614598833106941e-28 |
| constant127/rot90 | 145 | -0 | 3.1554436208840472e-30 | 100/4 | 6.5938365878537297e-12 | 8.9299054471018536e-28 |
| constant127/rot180 | 138 | -0 | 6.3108872417680944e-30 | 100/7 | 6.5938365878537297e-12 | 8.8983510108930132e-28 |
| constant127/rot270 | 138 | -0 | 3.1554436208840472e-30 | 100/3 | 6.5938365878537297e-12 | 8.9299054471018536e-28 |
| constant127/flipx | 138 | -0 | 3.1554436208840472e-30 | 100/3 | 6.5938365878537297e-12 | 8.9299054471018536e-28 |
| constant127/flipy | 145 | 0 | 3.1554436208840472e-30 | 100/4 | 6.5938365878537297e-12 | 8.9299054471018536e-28 |
| constant127/flipp | 138 | 0 | 0 | 100/2 | 6.5938365878537297e-12 | 8.9614598833106941e-28 |
| constant127/flipm | 138 | 0 | 6.3108872417680944e-30 | 100/7 | 6.5938365878537297e-12 | 8.8983510108930132e-28 |
| low-contrast/orig | 48 | -2.2737367544323206e-13 | -1.5762477729328444e-16 | 1/1 | 8.4912937836634228e-07 | 2.4337153188829821e-15 |
| low-contrast/rot90 | 46 | 1.1084466677857563e-12 | 8.2672622867162037e-28 | 1/1 | 8.4913025943933462e-07 | 2.5913400961754398e-15 |
| low-contrast/rot180 | 82 | -5.6843418860808015e-14 | 1.8932661725304283e-29 | 7/2 | 8.4912909414924798e-07 | 2.5913400961762476e-15 |
| low-contrast/rot270 | 68 | 8.5265128291212022e-14 | 8.2672622867162037e-28 | 2/1 | 8.4912906572753855e-07 | 2.5913400961770933e-15 |
| low-contrast/flipx | 68 | 8.5265128291212022e-14 | 8.2672622867162037e-28 | 2/1 | 8.4912906572753855e-07 | 2.5913400961770933e-15 |
| low-contrast/flipy | 46 | 1.1084466677857563e-12 | 8.2672622867162037e-28 | 1/1 | 8.4913025943933462e-07 | 2.5913400961754398e-15 |
| low-contrast/flipp | 48 | -2.2737367544323206e-13 | -1.5762477729328444e-16 | 1/1 | 8.4912937836634228e-07 | 2.4337153188829821e-15 |
| low-contrast/flipm | 82 | -5.6843418860808015e-14 | 1.8932661725304283e-29 | 7/2 | 8.4912909414924798e-07 | 2.5913400961762476e-15 |

Constant127 has no true non-DC signal in exact mathematics; only tiny finite-arithmetic cancellation residuals remain (maximum abs B about6.59e−12 C++,8.96e−28 Python). In orig both medians are exactly0, but C++ has100 ties and Python2; strict greater-than turns different residual signs and exact ties into138 differing bits. Other signed/transposed variants change the ordering/tie pattern and give138 or145 flips, fully accounted in CSV.

Low-contrast has some real coefficients (max abs B≈0.04955), but its changed decisions lie at tiny Python median margins (at most≈2.44e−15 in orig; all variants recorded above). Binary32 cancellation residuals move these near-median values across the lower median, giving46…82 changed bits. This is not an excuse to omit a low-quality input: qualities remain11, and raw disagreements remain part of the result. High-contrast coefficient arrays also differ numerically, but their median decisions survive on these samples; this observation does not prove robustness generally.

## Verification and limits

`check-diagnosis.py`: five tests pass, checking all48 observed variants and affected-bit accounting, fixed six-case/baseline/probe accounting, and rejecting a changed coefficient observation, a wrong variant/hash association and a non-strict tie predicate. `tests.log` retains results. Diagnostic assertions separately stop if instrumented outputs drift, software binary32 T/B differs, median selection differs, any variant map differs or frozen Python output differs. `bitwise-checks.json` records exact software T/B byte checks. The immutable originals and copied manifests were rechecked after work (`preservation-check.json`).

The claim is localized causal explanation on one compiler/host and exactly these retained common-luma arrays. It does not cover RGB weights, decoder behavior, pre-resize, larger blur windows, arbitrary images or source-commit authentication. No frozen contract is repaired/changed, no tolerances are introduced, no raw mismatch becomes parity, and IMGF.5 remains open. The package is ready for independent audit; the coordinator owns any later disposition.

## Exact identities and retained files

- `instrumentation.patch` SHA-256 `a3569a2fd63fe3ee7c32351645a8ad0646c0b514b5cf05df72d57397db20c4fe`
- `prepare.py` SHA-256 `2870a2ded05f60ccb5eebbbd685280d21f54fcbb7d758a5c2d06a92005670cab`
- `diagnose.py` SHA-256 `569a5793d72f5185f7d009711b3321716972158c1bf2f32a8e1392744586bd1c`
- `mixed-probes.py` SHA-256 `3c7b00ad81448854b11ddab35cf5073f9ed13518f6512e8a398ec9baa23a27af`
- `check-diagnosis.py` SHA-256 `7a88311da8d7ca7feb2623b02504c72d464315aebc755d9e8566a158427bd14d`
- `pdq-instrumented` SHA-256 `bcd50af99b5d6db87ae729988a9aaf2dad6cf51c38ec256c7606cec17572c262`
- `baseline-run-root/pdq-cpp` SHA-256 `ba757a0791cb4a6b5ab1d2493daddb325d04ba02bb52fb9b0a098441b42bcfeb`
- `baseline-artifact/comparison.json` SHA-256 `a1cf1f2c738bf678f6b232621bda0ba92e6438f09ac9c51895106da2ac763a24`
- `diagnosis.json` SHA-256 `1138003d21fed6ad86ff8e418e913157f97a7bb187c6ae233f62e8908757a153`
- `mixed-probes.json` SHA-256 `27886d1715a7e3f2172cc3189d0fcf05bf55d0cb7e2d6f4f24e899594e59c744`

`SHA256SUMS` inventories all retained package files except itself; `original-hashes.json` identifies the unchanged originals; `prebuild-identities.json` fixes the instrumentation before build. Full source/input/output SHA-256 values are retained rather than shortened.
