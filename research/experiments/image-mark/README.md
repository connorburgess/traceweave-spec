# Image embedded-mark study: harness for protocol `e-img-m-2`

Protocol: [image-mark-protocol.md](../../drafts/image-mark-protocol.md), version `e-img-m-2` (supersedes `e-img-m-1`, retired unrun 2026-11-23 after its non-author review).
Protocol digest (SHA-256, self-excluding): `cba3667307941766f19b2ff9141e89c154b1f9b53a01e11391135ffe8ab64110`

Use case: [image-mark-use-case.md](../../drafts/image-mark-use-case.md) (proposed UC-7). Licences: [lane 12](../../lanes/12-image-mark-licences.md). This is research code. Nothing here is normative, and **no measured run has been made**. The measured run starts only after a non-author has reviewed the frozen protocol.

## What it does

It marks seeded synthetic images with TrustMark-Q and PixelSeal, and with `dwtDct` as a negative control. It then applies 12 edits, 5 removal attempts, a residual transplant, a keyless re-embedding forgery and an overwrite. It tests each candidate's raw decoded bits against key-derived expected payloads, on the bit positions that are direct keyed-hash output only (TrustMark: 49 of its 61 data bits; PixelSeal: 167 of 256; protocol §4–§5). Everything runs on CPU and offline.

| File | Role |
| --- | --- |
| `requirements.txt` | 49 distributions, one file each, by PyPI SHA-256 (CPython 3.14, macOS arm64) |
| `sources.json`, `fetch_sources.py` | 84 upstream source files (TrustMark `4c60b9fd`, videoseal `f12875a9`), by SHA-256 and git blob id, extracted into `third_party/` |
| `weights.json`, `fetch_weights.py` | 6 model files (1.38 GB), by size, publisher digest and SHA-256, stored under `$TRACEWEAVE_EVAL_DIR/models` (default `~/traceweave-eval/models`); refuses any location inside a git work tree |
| `fetch_wheels.py` | the pinned wheels into `wheelhouse/` |
| `twmark/env.py` | paths, offline settings, `av` and `pycocotools` fail-on-use stubs, environment, probe and code-identity checks |
| `twmark/payload.py` | keys, HMAC payloads, exact binomial k |
| `twmark/schemes.py` | the three adapters around unmodified upstream code; downloads disabled |
| `twmark/attacks.py` | the conditions of protocol §7; the 12 edits are imported from the frozen `e-img-f-2` harness |
| `run_mark.py` | `smoke`, `full`, `compare` |
| `tests/` | unit tests, including model round trips on smoke seeds |

The generator and edits are **imported** from `../image-fingerprint/twimg/`, never copied. The code-identity check requires them to equal their bytes at `6f39e50`.

## Provisioning (online, once)

Network access is needed only here. The hosts are pypi.org, files.pythonhosted.org, codeload.github.com, cai-watermark.adobe.net and dl.fbaipublicfiles.com.

```sh
python3 -I fetch_wheels.py                 # 49/49 verified
python3 -I fetch_sources.py                # 84/84 verified
/opt/homebrew/bin/python3.14 -m venv .venv
.venv/bin/python -m pip install --no-cache-dir --no-index --find-links wheelhouse \
    --require-hashes --only-binary=:all: -r requirements.txt
python3 -I fetch_weights.py                # writes outside the repository; 6/6 verified
python3 -I fetch_weights.py --verify       # exit 0; never touches the network
```

## Dry tests (never results)

```sh
.venv/bin/python -I -m unittest discover -s tests -t .
.venv/bin/python -I run_mark.py smoke --out out/smoke-a
.venv/bin/python -I run_mark.py smoke --out out/smoke-b
.venv/bin/python -I run_mark.py compare out/smoke-a out/smoke-b
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
    .venv/bin/python -I run_mark.py smoke --require-network-denied --out out/smoke-offline
```

## Running the measured experiment

This happens only after the non-author review. Follow protocol §9 exactly: use a dedicated work tree at the frozen commit, keep the network denied, run `full` twice, run `compare`, then commit the results under `results/e-img-m-2/` in a commit that descends from both the frozen commit and the review commit.

```sh
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
    .venv/bin/python -I run_mark.py full --frozen-commit <40-hex> --require-network-denied --out out/full-1
```

Exit status: 0 completed; 2 refused (digest, identity, inputs, runtime pins or probe); 3 aborted at 4 h; 4 a validity condition failed. `compare`: 0 identical; 5 invalid pair (outputs differ, recorded inputs equal: rerun under protocol §6); 1 negative.
