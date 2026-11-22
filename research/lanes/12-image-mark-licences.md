# Lane 12: licence check for the image embedded-mark study

Prepared 2026-11-23, before any weight download. This is step 1 of the image mark study (ROADMAP IMG.0–IMG.5). The owner approved opening the study on 2026-11-23, including model-weight downloads, **subject to licences being checked first**. This file is that check. It is a research record. It changes no normative file and gives no legal opinion. It records what each licensor states and where.

Read with: [lane 08](08-evidence-review.md) (TrustMark, I and I-code), [lane 10](10-evidence-review.md) including "After the report audit", the [lane 10 report audit](10-report-audit.md) (X1, X3), and the [06–08 checkpoint](../research-06-08-checkpoint.md#deferred-proposal-note-post-hoc-image-study) deferred-study note.

## Decision

| Candidate | Role | Code licence | Weight licence | Download |
| --- | --- | --- | --- | --- |
| TrustMark, variant Q | candidate | MIT (Adobe) | MIT, stated by the licensor for "the model files which are downloaded upon first use" | **cleared**; encoder, decoder and the author remover (ReMark) for Q only |
| PixelSeal | candidate | MIT (Meta) | MIT, stated by the licensor: "All models … released under MIT license" | **cleared**; one checkpoint, 1.24 GB. Training-data terms (SA-1B) are an owner note, below |
| invisible-watermark `dwtDct` | negative control only | MIT | no weights used (the method is classical); the wheel ships RivaGAN ONNX files that this study never loads | **cleared** (PyPI wheel) |
| WmForger (forgery attack, in the PixelSeal repository) | not used in this study | MIT (repository) | not checked; extra checkpoint `convnext_pref_model.pth` | **not downloaded**; see "Considered and not used" |

No third mark candidate is added. Lane 10 and its audit name only TrustMark and PixelSeal as post-hoc candidates. Stable Signature is generation-time and its code is CC BY-NC (08 audit B2), so it cannot mark existing images and is excluded on both grounds. VideoSeal 1.0 is the same family and repository as PixelSeal and adds nothing the evidence reviews ask for.

Nothing was declined for a licence reason. One item needs the owner's attention (SA-1B, below) and one was left out for scope and budget (WmForger).

## TrustMark

| Item | Value |
| --- | --- |
| Repository | [adobe/trustmark](https://github.com/adobe/trustmark) |
| Pinned commit | `4c60b9fdb4125fca3001f0803e6890a6b55371ac` (2026-11-11), the same commit lane 08 pinned. It was still the branch head on 2026-11-23 |
| Code licence file | [`LICENSE`](https://github.com/adobe/trustmark/blob/4c60b9fdb4125fca3001f0803e6890a6b55371ac/LICENSE) (SHA-256 prefix `58d47a5c`). It is the MIT text preceded by "Copyright 2023 Adobe / All Rights Reserved" and a NOTICE paragraph that points to "the license agreement accompanying it". GitHub's licence API reports `NOASSERTION` because of that header; the body is the MIT licence. `python/LICENSE` is the same size (1,218 bytes) |
| SPDX | MIT (by the body text, `setup.py` `license='MIT License'` and the classifier `License :: OSI Approved :: MIT License`) |
| Weight licence | README.md line 145 and python/README.md line 147 at the pinned commit: "The MIT license covers both the code in this repo and the model files which are downloaded upon first use." FAQ.md line 28: "allowing commercial and non-commercial use". FAQ.md line 80: the models "were trained on licensed Adobe Stock images" |
| Use restrictions | None beyond MIT: keep the copyright and permission notice. No research-only or non-commercial term was found |
| Weight host | `https://cai-watermark.adobe.net/watermarking/trustmark-models/` (`MODEL_REMOTE_HOST`, `python/trustmark/trustmark.py` line 29). The README notes the host moved from Netlify to S3 in April 2026 |
| Published weight hashes | MD5 only, in `python/trustmark/trustmark.py` lines 35–67 (`MODEL_CHECKSUMS`). No SHA-256 is published. The study's SHA-256 values are computed at download, after the MD5 and the size match, and are then pinned in `research/experiments/image-mark/weights.json` |
| CPU and offline | CPU is documented: the README's example output reads "Initializing TrustMark watermarking with ECC using [cpu]". The loader selects CUDA, then MPS, then CPU (lines 87–88). Offline use is **not** documented: `check_and_download` fetches any missing or MD5-mismatched file from the host (lines 141–151). The study's adapter passes `device='cpu'` and replaces that method with a verify-only check that never downloads |

Weight files used (variant Q only). Sizes are the host's `content-length` on 2026-11-23; MD5 is the publisher's pin; SHA-256 is computed by `fetch_weights.py` after both match.

| File | Bytes | Publisher MD5 (trustmark.py line) | SHA-256 (computed) |
| --- | --- | --- | --- |
| `trustmark_Q.yaml` | 2,009 | `fe40df84a7feeebfceb7a7678d7e6ec6` (43) | `43f37103f92efa8bd6b1c5902bb537cc12a981dc699fca19d9bb7de8c62d03d9` |
| `encoder_Q.ckpt` | 17,302,074 | `700328b8754db934b2f6cb5e5185d81f` (45) | `dc382c3f6b4fd568b27d6fbb763d6ffc2d2587126d84afe9d5ee95b4c5d99826` |
| `decoder_Q.ckpt` | 47,652,460 | `4ced90e9cfe13e3295ad082887fe9187` (44) | `e3d9cea5406a26590735719f8f15cb10802b11852ae69047eaf4cf17214df781` |
| `trustmark_rm_Q.yaml` | 1,658 | `8476bcd4092abf302272868f3b4c2e38` (46) | `d8ae92c8ad0135a5d085c295be8560fbb67af9b8f5ab46bbf25f4a1038a8626f` |
| `trustmark_rm_Q.ckpt` (ReMark remover) | 77,081,406 | `760337a5596e665aed2ab5c49aa5284f` (47) | `cb23dc28b69104ae551286f63da6e965d269f715a87748e3ae7fe0d790f7dc9a` |

The bounding-box detector (`trustmark_bbox_Q.*`) and variants B, C and P are not downloaded. Variant Q is the README default and the variant X1 reports.

**Code dependencies of the inference path** (imports read at the pinned commit): `torch`, `torchvision`, `omegaconf`, `einops`, `numpy`, `Pillow`, and `lightning` with `torchmetrics` (`model.py`, `denoise.py` subclass `LightningModule` and import `peak_signal_noise_ratio`). The remover's network is `trustmark.KBNet.kbnet_s_arch.KBNet_s`, which imports only `torch`. `KBNet/kbnet.py` imports `kornia`, but nothing on the inference path imports that module, so `kornia` is not installed.

**Install route.** PyPI carries only an sdist of `trustmark` 0.9.2 (2026-09-08), which predates the pinned commit and would need a build step. The study does not install it. `fetch_sources.py` takes the `python/trustmark/` files from the pinned commit's archive and checks each against the SHA-256 and git blob id recorded in `sources.json`.

## PixelSeal

| Item | Value |
| --- | --- |
| Paper | Souček et al., *Pixel Seal*, [arXiv:2512.16874v1](https://arxiv.org/abs/2512.16874v1) (audit X3) |
| Repository | [facebookresearch/videoseal](https://github.com/facebookresearch/videoseal) |
| Pinned commit | `f12875a9b5e711e0c6e2dc3a22aca18231ce4a1a` (2026-11-10), the commit the lane 10 audit pinned (X3). It was still the branch head on 2026-11-23 |
| Code licence file | [`LICENSE`](https://github.com/facebookresearch/videoseal/blob/f12875a9b5e711e0c6e2dc3a22aca18231ce4a1a/LICENSE), "MIT License, Copyright (c) Meta Platforms, Inc. and affiliates". GitHub's licence API: `MIT` |
| Weight licence | README.md line 41: "All models, training code, and evaluation tools released under MIT license"; line 221: "The model is licensed under an MIT license". Meta's Hugging Face mirror `facebook/video_seal` carries the tag `license:mit`; that mirror holds the VideoSeal checkpoint, not PixelSeal, so it is supporting context only |
| Use restrictions | None stated for the weights beyond MIT |
| Weight file | `https://dl.fbaipublicfiles.com/videoseal/pixelseal/checkpoint.pth` (model card `videoseal/cards/pixelseal.yaml`, `checkpoint_path`). 1,237,429,197 bytes; `last-modified` 2025-12-10; S3 version id `5XttukeFUuyDc4Uv97Jwy1PldRddPzG3`; multipart ETag `2a6bd4d67f6c182201975a96b1a5a9bb-148` |
| SHA-256 (computed) | `0c5665cff20eb6ce1b5aaa7d91c19dafb418bfee32d02dd3344e4ed60d9d75bd`, after the size and the recomputed multipart ETag matched |
| Published weight hash | **None.** Neither the README nor the model card publishes a digest. The only publisher-side value is the S3 multipart ETag. `fetch_weights.py` recomputes it (MD5 of the concatenated MD5s of 8 MiB parts; 148 parts fit the size exactly), then computes and pins SHA-256. The ETag is an MD5 construction, so it guards against corruption, not against a deliberate collision |
| Training data | SA-1B (paper, training section). See the owner note below |
| CPU and offline | Not documented. The loader reads checkpoints with `map_location='cpu'` (`videoseal/utils/cfg.py` lines 63 and 149). `videoseal.load` downloads the checkpoint with `requests` on first use (lines 242–287). The study calls `setup_model` with the local, hash-checked file and never `load` |

**Code dependencies.** `pyproject.toml` lists 20 packages, most for video, training and evaluation. The image inference path (`utils/cfg.setup_model`, `models/videoseal.py`, `models/wam.py`, `modules/*`) needs `torch`, `torchvision`, `omegaconf`, `einops`, `timm` (`modules/convnext.py`), `requests` (imported at the top of `utils/cfg.py`, not called), `tqdm` and `opencv-python` (imported by `augmentation/masks.py`). Three more packages are imported at module load but never called for still images: `av` (`augmentation/video.py`), `pycocotools` (`data/datasets.py`) and `decord` (`data/loader.py`, already guarded by `try`). `decord` has no macOS arm64 wheel and `pycocotools` has no CPython 3.14 wheel. The harness therefore registers fail-on-use stub modules for `av` and `pycocotools`: any attribute access raises. A unit test proves that embed and detect never touch them. `timm` is pinned to 0.9.16, as in the repository's `pyproject.toml`.

### Owner note: SA-1B training terms

The PixelSeal weights were trained on SA-1B. SA-1B is distributed under Meta's own dataset research licence; this check did not read those terms (the download page requires accepting them). The weights themselves carry Meta's MIT statement, and Meta is the licensor of both the dataset and the weights. My reading, not legal advice: the research download and use in this study are covered by the MIT statement, and any SA-1B restriction binds the dataset's licensees, not users of Meta's released weights. This is why the download is cleared. **Owner item:** if the study's results are later used to choose a carrier for distribution, the owner should confirm that reading, or have the SA-1B terms read, before that choice.

## Negative control: invisible-watermark `dwtDct`

| Item | Value |
| --- | --- |
| Repository | [ShieldMnt/invisible-watermark](https://github.com/ShieldMnt/invisible-watermark/tree/68d0376d94a4701ed240af0841ec12e00676e325) at `68d0376d94a4701ed240af0841ec12e00676e325`, the commit lane 10 pinned (F5). It was still the branch head on 2026-11-23 (last commit 2023-08-25) |
| Licence | `LICENSE`: "MIT License, Copyright (c) 2021 ShieldMnt" |
| Package | PyPI `invisible-watermark` 0.2.0, `invisible_watermark-0.2.0-py3-none-any.whl`, 1,633,253 bytes, SHA-256 `644311beed9cfe4a9a5a4a46c740f47800cef184fe2e1297f3f4542e2d992f8b` (PyPI-published) |
| Weights | None for `dwtDct` (block DCT quantization, `maxDct.py`). The wheel ships RivaGAN ONNX files; the study never loads them, and `onnxruntime` is not installed |
| Dependencies | Metadata requires `opencv-python`, `PyWavelets`, `numpy`, `Pillow` and `torch`. `dwtDct` itself uses `cv2`, `pywt` and `numpy` |
| CPU | Documented: README "Running Speed (CPU Only)" |
| Role | Negative control only (lane 10, F5). It has no key and no ECC, and its decoder always emits bits |

## Python dependencies

Resolved on 2026-11-23 with `uv pip compile` for CPython 3.14 on macOS arm64: 49 packages. NumPy 2.5.5 and Pillow 13.0.0 are fixed to the versions the `e-img-f-2` generator was frozen with. `requirements.txt` in the experiment directory pins one file per package with its PyPI-published SHA-256. Licences are from each release's PyPI metadata (SPDX expression where given, else the classifier).

| Licence family | Packages |
| --- | --- |
| BSD-3-Clause or "BSD" | torch 2.11.0, torchvision 0.26.0, numpy 2.5.5 (with 0BSD, MIT, Zlib, CC0-1.0 parts), click, fsspec, httpcore2, httpx2, idna, jinja2, markupsafe, mpmath, networkx, omegaconf, sympy |
| MIT or MIT-CMU | pillow 13.0.0 (MIT-CMU), einops, invisible-watermark, pywavelets (with BSD-3-Clause), pyyaml, six, anyio, attrs, filelock, h11, setuptools, truststore, urllib3, charset-normalizer |
| Apache-2.0 | lightning, pytorch-lightning, lightning-utilities, torchmetrics, timm 0.9.16, opencv-python 5.1.0.95, requests, safetensors, huggingface-hub, hf-xet, aiohttp (with MIT), aiosignal, frozenlist, multidict, propcache, yarl, packaging (or BSD-2-Clause) |
| MPL-2.0 (file-level copyleft; used unmodified) | certifi; tqdm (MPL-2.0 AND MIT) |
| PSF | typing-extensions, aiohappyeyeballs |

`opencv-python` wheels bundle third-party native libraries, FFmpeg among them, listed in the wheel's `LICENSE-3RD-PARTY.txt`. They are used unmodified, and nothing is redistributed. Several packages can make network calls (`requests`, `huggingface-hub`, `aiohttp`). The harness calls none of them, and the offline proof (protocol §8) runs every measured step with the network denied.

No dependency licence is non-commercial or research-only.

## Considered and not used

- **WmForger** (Souček et al., NeurIPS 2025; `wmforger/` in the PixelSeal repository). It is a black-box forging and removal attack, which matches the transplant question. It needs a second checkpoint (`https://dl.fbaipublicfiles.com/wmforger/convnext_pref_model.pth`), trained on SA-1B and not checked here, and it runs an optimisation loop whose CPU cost is unknown. It is left for a later protocol version. Adding it would need its own licence row and a budget.
- **VAE regeneration** (lane 10 F6). It would need a VAE checkpoint, which has its own licence. IMG.3 allows it "only if its weight licence is accepted". This study uses only regeneration-style attacks that need no extra model (protocol §4).
- **TrustMark variants B, C and P and the bounding-box detector.** They are the same licence, but out of scope for the first protocol version.

## Download record

Run on 2026-11-23, after this file's licence decision: `fetch_weights.py --pin`, outside the agent sandbox because it writes to `~/traceweave-eval/models`. All 6 files matched their size and the publisher's digest (5 MD5 pins, 1 recomputed S3 multipart ETag), and their SHA-256 values were then pinned in `weights.json`. Total 1,379,468,804 bytes, all outside the repository. The source files (`fetch_sources.py`) matched their recorded SHA-256 and git blob ids, 84 of 84. The blob ids were then compared with GitHub's tree API for both commits: 22 of 22 (TrustMark) and 62 of 62 (videoseal). The 49 wheels matched their PyPI SHA-256 values, 49 of 49.

## Validation

All facts above were read on 2026-11-23 over read-only HTTP: GitHub raw files at the pinned commits, the GitHub API (until its unauthenticated rate limit), PyPI's JSON API, `HEAD` requests to the two weight hosts and the Hugging Face model API. Before the licence decision, only two TrustMark YAML configuration files (3,667 bytes) were fetched, to read the class names they load; their MD5s matched the publisher's pins. No checkpoint was downloaded before this file was written.
