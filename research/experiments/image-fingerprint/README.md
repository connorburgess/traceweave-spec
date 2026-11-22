# Image fingerprint experiment (E-IMG-F): harness, generator and dry tests

Research only. This directory holds the code for the frozen protocol [`e-img-f-2`](../../drafts/image-experiment-protocol.md), a 200-image contract check of the draft [still-image fingerprint profile](../../drafts/extraction-profile-image.md) (`draft-2`; roadmap IMGF.1–IMGF.5). The earlier `e-img-f-1` (commit `4714735`, 2,000 images with pass lines) was retired unrun by coordinator decision on 2026-11-22. **The measured run has not been made.** Nothing in this directory is a result. Smoke runs use a seed range disjoint from the experiment and are labelled `SMOKE RUN - NOT A RESULT`.

Results: the frozen protocol was executed as `e-img-f-2`; the results, transcript and run records are in [results/e-img-f-2/](results/e-img-f-2/RESULTS.md). The protocol file itself still says "not yet run" because its bytes are frozen by digest and are not edited after the run.

Protocol digest (`e-img-f-2`, SHA-256 of [image-experiment-protocol.md](../../drafts/image-experiment-protocol.md) with its digest field set to 64 zeros): `44a67a14c6e4c3028bd20a093896390c308a89cf92fc2d521c788346ad6b90c4`

## Layout

| Path | What it is |
| --- | --- |
| `twimg/decode.py` | Shared decode stage (profile §3): Pillow decode, PNG bit-depth rule, JPEG-only EXIF orientation, explicit RGB conversion and alpha formula, closed abstention codes |
| `twimg/pdq_np.py` | NumPy port of the vendored PDQ, bit-identical by construction and by test |
| `twimg/iscc_img.py` | iscc-sdk 0.9.7 normalization (tolerant trim, `L`, 32×32 BICUBIC) and the iscc-core 1.5.0 Image-Code v0 hash, with 8 dihedral variants |
| `twimg/generator.py` | Seeded synthetic image generator `traceweave-synth-draft-1` |
| `twimg/transforms.py` | The 12 frozen edits |
| `twimg/profile.py` | Extraction and matching configuration bytes, digests, environment pin check |
| `run_experiment.py` | Harness: `smoke`, `full` and `compare` modes. `full` checks its own code identity, re-runs the vector check fresh, and probes the network with a loopback-only check. It reports counts without a pass line and the validity conditions V1–V5 |
| `check_vectors.py` | IMGF.2 evidence: PDQ and ISCC against published reference outputs; writes `vectors/check-results.json` |
| `fetch_wheels.py`, `fetch_pdq_vectors.py` | The only online steps: pinned wheels, and the 30 ThreatExchange vector images |
| `vectors/pdq-reference.json` | The 30 vector files (git blob id and SHA-256) and the three vendor reference-output sets, transcribed by script with source line numbers |
| `vectors/check-results.json` | The committed output of `check_vectors.py` (IMGF.2 evidence; not an experiment result) |
| `vendor/threatexchange_pdq/` | ThreatExchange pure-Python PDQ, unmodified, BSD; see its [PROVENANCE.md](vendor/threatexchange_pdq/PROVENANCE.md) |
| `vendor/iscc-sdk-LICENSE.txt` | Apache-2.0 licence of iscc-sdk. `trim_tolerant` in `iscc_img.py` is re-implemented following iscc-sdk 0.9.7 at commit `cc11f771e4efbf0a600f196c7e9155b529ad7598`, which ships no `NOTICE` file |
| `tests/test_harness.py` | 30 unit tests |
| `requirements-build.txt`, `requirements.txt` | Hash-locked pins |

Git-ignored: `.venv/`, `wheelhouse/`, `vectors/pdq-data/`, `out/`.

## Environment

The environment is CPython 3.14.6 (Homebrew) on macOS 26.4, Apple Silicon. Every file is pinned by SHA-256; see [requirements.txt](requirements.txt) and [requirements-build.txt](requirements-build.txt). The hashes are for macOS arm64 CPython 3.14 wheels, so the pins are platform-locked.

Licences were read from each file's metadata (`License-Expression`, `License` or classifiers) and, for data-url, from its `LICENSE` file:

| Package | Version | Licence | File |
| --- | --- | --- | --- |
| pillow | 13.0.0 | MIT-CMU (bundles libjpeg-turbo 3.2.0, zlib-ng 1.3.1 and others, each under its own licence in the wheel) | `pillow-13.0.0-cp314-cp314-macosx_11_0_arm64.whl` |
| numpy | 2.5.5 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | `numpy-2.5.5-cp314-cp314-macosx_14_0_arm64.whl` |
| iscc-core | 1.5.0 | Apache-2.0 | `iscc_core-1.5.0-cp314-cp314-macosx_11_0_arm64.whl` |
| annotated-types | 0.8.0 | MIT | py3 wheel |
| base58 | 2.1.1 | MIT | py3 wheel |
| bitarray | 3.12.4 | PSF-2.0 | cp314 arm64 wheel |
| blake3 | 1.0.11 | CC0-1.0 OR Apache-2.0 | cp314 arm64 wheel |
| data-url | 1.4.0 | MIT (licence file; no wheel exists, built locally from the pinned sdist) | `data_url-1.4.0.tar.gz` |
| jcs | 0.3.0 | Apache-2.0 | py3 wheel |
| loguru | 0.8.0 | MIT | py3 wheel |
| more-itertools | 11.2.1 | MIT | py3 wheel |
| pybase64 | 1.5.2 | BSD-2-Clause | cp314 arm64 wheel |
| pydantic | 2.14.4 | MIT | py3 wheel |
| pydantic-core | 2.50.5 | MIT | cp314 arm64 wheel |
| python-dotenv | 1.2.4 | BSD-3-Clause | py3 wheel |
| typing-extensions | 4.16.0 | PSF-2.0 | py3 wheel |
| typing-inspection | 0.4.5 | MIT | py3 wheel |
| uvarint | 1.2.0 | MIT (classifier; metadata licence field "UNKNOWN") | py3 wheel |
| xxhash | 4.1.0 | BSD-2-Clause | cp314 arm64 wheel |
| setuptools (build only) | 84.2.1 | MIT | py3 wheel |

Vendored code is not installed from PyPI:
- ThreatExchange PDQ at `9f627fb1d6d2a4a26c9b5ee1d6ca5e5ccc8e06a2`, BSD;
- re-implemented iscc-sdk functions, Apache-2.0.

The vector images are ThreatExchange `pdq/data` files at the same commit, BSD. They are fetched, not committed.

Only Pillow, NumPy and iscc-core are used directly. The other 16 packages are iscc-core's declared dependencies, imported when `iscc_core` loads. No model weights, datasets or real image sets are involved.

### Install (online once, then offline)

From this directory:

```sh
python3 fetch_wheels.py            # 20/20 pinned files into wheelhouse/ (curl, system TLS)
python3 fetch_pdq_vectors.py       # 30/30 vector images into vectors/pdq-data/
/opt/homebrew/bin/python3.14 -m venv .venv
.venv/bin/python -m pip install --no-index --find-links wheelhouse --require-hashes -r requirements-build.txt
.venv/bin/python -m pip install --no-index --find-links wheelhouse --require-hashes --no-build-isolation -r requirements.txt
```

`fetch_wheels.py` uses curl because, inside the agent sandbox used for this lane, pip's own TLS verification against the macOS trust store failed. Each file is matched to PyPI's published SHA-256 and checked again after download. pip then installs with `--require-hashes`.

## Dry tests (not results)

```sh
.venv/bin/python check_vectors.py
.venv/bin/python -m unittest discover -s tests
.venv/bin/python run_experiment.py smoke --out out/smoke-a
.venv/bin/python run_experiment.py smoke --out out/smoke-b
.venv/bin/python run_experiment.py compare out/smoke-a out/smoke-b
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  .venv/bin/python run_experiment.py smoke --out out/smoke-c --require-network-denied
.venv/bin/python run_experiment.py compare out/smoke-a out/smoke-c
```

Smoke mode uses seeds from 1,000,000 up, records the code identity without enforcing it, reads the stored vector results, and withholds all counts.

## Running the measured experiment

Do not run this until `e-img-f-2` has had its non-author review (protocol §14). `FROZEN` is the 40-hex commit that froze `e-img-f-2`; it is given in the coordinator report, not in this file (protocol §0).

```sh
git worktree add ../imgf-run "$FROZEN"     # a clean tree whose HEAD is the frozen commit
cd ../imgf-run/research/experiments/image-fingerprint
# install as above (wheelhouse/, vectors/pdq-data/ and .venv/ are git-ignored)
SB='(version 1)(allow default)(deny network*)'
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python -m unittest discover -s tests
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python run_experiment.py full --frozen-commit "$FROZEN" --require-network-denied --out out/full-1
/usr/bin/sandbox-exec -p "$SB" .venv/bin/python run_experiment.py full --frozen-commit "$FROZEN" --require-network-denied --out out/full-2
.venv/bin/python run_experiment.py compare out/full-1 out/full-2
```

Before generating any image, `full` refuses (exit 2) unless all of these hold:
- HEAD equals `--frozen-commit`;
- `git status --porcelain --untracked-files=all` is empty;
- the frozen paths do not differ from the frozen commit, and the frozen commit is an ancestor of HEAD;
- the protocol version line reads `e-img-f-2`, and the protocol digest matches;
- the environment pin holds;
- the network probe is refused with EPERM;
- a fresh `check_vectors.py` passes V1 and leaves the tree clean.

Every check is logged in `summary.json` (`codeIdentity`, `statusAfterVectorCheck`, `statusAfterRun`). The roadmap accepts `sandbox-exec` deny-network as the substitute for `scripts/offline`.

## Dry-test record

Run on 2026-11-22 on the `e-img-f-2` code, in the shared checkout (not a clean tree), before the protocol digest was recorded. Not a result.

| Check | Outcome |
| --- | --- |
| `fetch_wheels.py` in a fresh directory (run during `e-img-f-1`; the pins are unchanged) | 20/20 pinned files verified; byte-identical to the wheelhouse used for the install |
| `fetch_pdq_vectors.py` | 30/30 vector files verified (git blob id and SHA-256) |
| `check_vectors.py` | V1 passes: port 30/30; C++ within 10 bits 8/8 and quality 8/8; Python within 16 bits 12/12 and 18/18; ISCC 3/3 compiled and 3/3 pure. Exact equality with published PDQ (not required): C++ 0/8, README 4/12, unit test 8/18 |
| Unit tests | 30/30 pass |
| Smoke runs a and b | each 130 queries and 140 extractions, about 76 s, peak RSS about 0.65 GB; vendor cross-check 140/140; 0 record errors; byte-identical; `resultsSha256` `9e83ee10be5805acbfd7ee5b5fecbd5d35ca4bae973397713ad35c32ebd07eb3` |
| Smoke run c under `sandbox-exec` deny-network | probe `bind refused errno 1; loopback connect refused errno 1 (EPERM)`; byte-identical to a. Outside the sandbox the probe reports `ECONNREFUSED`, and no packet leaves the host |
| Code identity in smoke run c | `ok: false`, as expected in the shared checkout (18 porcelain lines from other lanes; the protocol file then still said `e-img-f-1`). `full` mode was not run |

Running `sandbox-exec` needed the command to run outside the agent's own sandbox, which does not allow a nested sandbox profile.
