# Contributing

Start with a concrete use case, affected draft sections, and an explanation of what changes. Include primary sources for external technical claims. Mark hypotheses and unpublished benchmark results explicitly.

Wire-format changes must update the schema, examples, negative cases, and version together. Profile proposals must specify deterministic extraction, supported inputs, matching semantics, test fixtures, and known failures. Numerical detection claims must include held-out evaluation and a stated false-alarm unit.

Do not submit private keys, real private catalogues, unpublished suspect content, or identifying investigation records. Use synthetic fixtures you have permission to distribute. Never label a similarity result as proof of infringement.

Run the commands in the README before proposing a change. Contributions are made under the applicable licenses in LICENSE.md; only contribute material you have authority to license. Maintainers review changes through pull requests. Draft identifiers may change before a stable release; released identifiers will not be silently repurposed.

The next release needs interoperability evidence and security review, not only document agreement. There is no certification program or standards-body approval.

## What CI runs, and what it does not

The only workflow is [.github/workflows/validate.yml](.github/workflows/validate.yml). It runs on every push and pull request on Ubuntu with Python 3.11, 3.12 and 3.13, with read-only repository permissions, no secrets, and only the checkout and setup-python actions (pinned to full commit SHAs). Dependencies come from `requirements-dev.txt`, which pins exact versions with hashes and is installed with `--require-hashes`. In order, it runs:

1. `python tools/validate.py`: schema structure, synthetic examples, fixture digests, commitment and DSSE framing vectors, links in the core directories, the promoted schemas, and each promoted vector checker (extraction, extraction token files of the matching vectors, matching with its self-tests, TypeScript, text), each of which must exit 0.
2. `python -m unittest discover -s tests`.
3. `python tools/validate.py --links-all`: local Markdown links in every Markdown file, including `research/`.
4. Every vector builder (`extraction`, `matching`, `extraction-typescript`, `extraction-text`), then `git diff --exit-code` and a clean `git status`: regenerated files must be byte-identical to the committed ones.
5. `python tools/check_hygiene.py --messages <range>`: no absolute home-directory paths, chat-session thread identifiers or AI-attribution trailers in tracked files or in the messages of the pushed commits. The same step also fails on long string literals in `tools/` that are trivially encoded (ROT13 or base64 text), in the tree and in every version of a `tools/` file reachable from the pushed commits.

CI does **not** run:

- the toolchain cross-check harnesses (`test-vectors/extraction/harness/crosscheck.py`, `test-vectors/extraction-text/harness/crosscheck_text.py`, `test-vectors/extraction-typescript/harness/crosscheck.js`), which need Go, Rust or Node and, for some, the Unicode data files;
- the Go and Rust signing, carrier and census experiments under `research/experiments/` (they need Go, Rust and network-isolated runs);
- the image experiment in `research/experiments/image-fingerprint/` (it needs a project-local Pillow, NumPy and iscc-core install and is a one-off frozen run);
- the evaluation-corpus manifest checker and any corpus acquisition;
- any implementation of the specification. The implementation repository has its own checks.

The vector checkers validate recorded outputs. Passing CI is not an interoperability result and not a conformance claim. To regenerate the pinned requirements, see the header of `requirements-dev.txt`.

## Publishing history

`tools/public_history_scrub.py` rewrites a local branch into a publishable one. It contains no rules: they are in a private file outside every working tree (`$TRACEWEAVE_EVAL_DIR/private/public-history-rules.json`, mode 0600, or the path in `TRACEWEAVE_SCRUB_RULES`), and the tool refuses to run without it. `tools/hooks/pre-push` is a pre-push hook that refuses refs whose history contains a rule-bearing version of that tool (the blob ids are read from the private file); install it with `install -m 755 tools/hooks/pre-push .git/hooks/pre-push`. Only the rewritten branch is pushed.

Future preparations must follow the [publication-source divergence workflow](docs/publication-source-workflow.md). The curated publication-source lineage, rather than raw-bearing private `roadmap-v2`, is the source for subsequent replay; its independent review and publication authorization remain separate.
