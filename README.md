# Traceweave

An open specification for transformation-resilient content fingerprinting, cryptographic provenance, and evidence of reuse across code, text, images, and audio.

**Status: experimental design draft, 0.1.0-draft.1.** Transformation resilience is a goal to measure per content profile, not a universal guarantee. This repository currently contains a proposed evidence format and validation tools. It does not yet contain a fingerprint detector, signing client, resolver, or production agent skill.

Traceweave separates three questions: which exact artifact a record describes, whether another artifact contains similar material, and what evidence supports that relationship. Cryptographic verification authenticates a record; it does not make a similarity claim true or establish ownership, infringement, or model training.

The specification and algorithms are public. Owners can keep their keys, reference catalogues, and investigation records private. The default design works locally and does not require publishing an identity, fingerprint vector, or signing event.

## Read the draft

| Document | Purpose |
| --- | --- |
| [Core](spec/core.md) | Record semantics, exact subjects and private commitments |
| [Attestations](spec/attestations.md) | DSSE/in-toto integration and verification boundaries |
| [Threat model](spec/threat-model.md) | Adversaries, privacy, false claims, and failure cases |
| [Conformance](spec/conformance.md) | What the checks establish and what remains unimplemented |
| [Code profile](profiles/code.md) | First fingerprinting experiment and reproducibility requirements |
| [Other content profiles](profiles/README.md) | Text, image, audio, and binary research scope |
| [Schemas](schemas/README.md) | Machine-readable draft formats |
| [Examples](examples/README.md) | Synthetic, unsigned records with known artifact bytes |
| [Evaluation](docs/evaluation.md) | Attack matrix and false-positive calibration |
| [Roadmap](ROADMAP.md) | Implementation gates and open decisions |
| [Draft review](docs/reviews/initial-draft-review.md) | Corrections to the supplied design |

## Check this repository

Python 3.11 or newer is required. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/validate.py
.venv/bin/python -m unittest discover -s tests -v
```

The validator checks schema structure, synthetic examples, exact fixture digests, commitment openings, DSSE framing vectors, and local Markdown links. It does **not** authenticate a signer, validate a timestamp authority, measure clone detection, or establish a false-positive rate. It performs no network requests.

## Contribute and reuse

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md). Discussion should distinguish proposed mechanisms, measured results, and normative requirements. Alternative implementations are welcome; the planned CLI and skill will be optional conveniences.

Specification prose is licensed under CC BY 4.0. Schemas, examples, test vectors, source code, and configuration are licensed under Apache 2.0. See [LICENSE.md](LICENSE.md). These licenses do not change the rights in content processed by an implementation.
