# Deep research prompt: Detection, false alarms and benchmarks

Output filename: `03-detection-evaluation.md`

## Decision to enable

How do we measure whether a detector is useful without mistaking coincidental similarity, correlated evidence or threshold tuning for proof of reliable recognition?

## Questions to investigate

- Compare mark-only, extracted-fingerprint-only and combined pipelines at the same operational false-alarm budget. Include exact/normalized matching, local alignment and directional containment baselines. Explain why feature selection or HMAC is not itself embedding.
- Define the unit of error: window, localized region, file, whole repository search, mark identity and attribution claim. Account for searches over many windows, keys, releases, reference artifacts and repeated queries.
- Design positive controls, unmarked negatives, wrong-mark/key controls, same-stack repositories, common algorithms, generated/vendor code and independently written same-task programs. Treat permitted historical copies as ancestry positives; keep rights labels separate. Label transplanted marks separately for presence and attribution.
- Group related repositories and versions into the same split; separate development, calibration and held-out evaluation. Define how thresholds are frozen and what happens after a failed held-out test.
- Address low base rates, confidence intervals, correlated samples, zero observed false alarms, multiple comparisons and adaptive attack selection. State assumptions for statistical formulas; do not equate a similarity score or p-value with probability of ownership or infringement.
- Measure recall by fragment size/transformation, mark-identity errors, localization accuracy, abstention, candidate-review burden, runtime and memory. Include unsupported and parser-error cases.
- Specify what a reviewer-facing result should expose so another implementation can reproduce it. Define how combined evidence avoids double-counting correlated signals.

## Specific deliverable

Provide a benchmark manifest design, split/calibration protocol and proposed result schema with illustrative synthetic values clearly marked as illustrative. Give a small pilot and a defensible path to larger evaluation; explain what claims the pilot cannot support. Operational false-alarm tolerances remain a user decision: present scenarios, not an invented universal threshold. Hand concrete embedding choices to lane 1 and trust/time verification to lane 4.

## Project context

Research for Traceweave, an experimental open specification: https://github.com/connorburgess/traceweave-spec . The goal is to embed marks into content before distribution so later reuse can be recognized, supported by extracted fingerprints and private provenance records. Start with Go and Rust source code, using Looptender and TalkQTE as intended pilot projects. TypeScript/JavaScript is a later priority. Do not default to Python because it is convenient for research tooling. Do not assume evidence from one language transfers to another. Text, images and audio need separate future profiles.

Distinguish three mechanisms throughout: (1) embedded marks change content, (2) extracted fingerprints describe existing content without changing it, (3) cryptographic signatures authenticate evidence records. None alone proves ownership, infringement or model-training membership. Signing a record does not embed a mark in source code. A detected transplanted mark does not establish the origin of the surrounding content.

The project currently has draft evidence schemas, synthetic examples, commitment and DSSE framing vectors, and validation tools. It has no implemented embedder, fingerprint detector or signature verifier, and no chosen embedding algorithm. Algorithms and specifications should be public; owner keys, mark records and reference catalogues can remain private. Local operation must be possible without mandatory public registration or logging. Exclude planted defects, hidden telemetry, callbacks, and deliberate behavioral changes. Application-specific behavior and performance checks are required; passing a test suite is not proof of universal equivalence.

Read the current README, ROADMAP.md, spec/core.md, spec/threat-model.md, profiles/code.md and docs/evaluation.md when accessible. Report which revision you consulted. If unavailable, proceed from this context and label that limitation; do not invent repository contents. Treat existing choices as proposals to scrutinize, not conclusions to defend.

## Research standard

Search the literature and current primary sources, including original papers, specifications and author-maintained implementations. Cover foundational work as well as newer results. Follow secondary sources to their primary evidence. Verify bibliographic details and links. Do not fabricate citations, results, library capabilities or runnable commands. If you have no browsing access, say so rather than imply a current literature review.

For each important claim cite the exact section, theorem, experiment or table where possible. Record publication date, version/commit, URL and access date. Distinguish author-reported measurements, independent replications, formal results under assumptions, and your own inference. If you do not execute experiments, label the reproduction plan unexecuted. Never turn results on a narrow corpus into a universal survival or false-positive guarantee. Include negative results and contradictory evidence. State when public evidence is missing.

## Required report format

Return a standalone Markdown report, not just a chat summary, using the requested filename. If file creation is supported, provide the .md file; otherwise return its full Markdown text. Target roughly 2,000–3,500 words plus evidence tables and references; prefer a shorter precise report to padding.

1. **Decision summary:** recommended next experiment, strongest alternative, reasons to reject weaker options, and confidence with reasons.
2. **Scope and terminology:** what question this lane answers and leaves to other lanes.
3. **Evidence/comparison table:** method or standard, source, assumptions, demonstrated results, known failures, implementation availability/license, and applicability to Traceweave.
4. **Detailed findings:** distinguish established facts from proposals and inference.
5. **Reproducible experiment or verification plan:** inputs, versions, controls, procedure, outputs, metrics, resource estimate, proposed acceptance/rejection gates, and untested assumptions. Do not present invented numerical gates as established standards.
6. **Spec implications:** concrete proposed additions or corrections, mapped to repository documents where known. Avoid rewriting the whole spec.
7. **Open questions and cross-lane handoff:** decisions requiring evidence from another lane or the project owner.
8. **Source ledger:** stable identifiers/links, source revisions, dates, relevant sections and the claims they support.

Do not modify the repository, publish findings, or inspect private repositories. Use public or redistributable synthetic examples. The output is a research report to review before implementation.
