# Deep research prompt: Robustness and adversarial evaluation

Output filename: `02-robustness-attacks.md`

## Decision to enable

What threats must an embedding prototype survive to be useful, what transformations defeat plausible schemes, and how should we test those claims fairly?

## Questions to investigate

- Build a threat model with public algorithm/source, private owner keys where applicable, attacker access to one or many marked versions, and zero/limited/adaptive detector-query access. Distinguish accidental edits from targeted removal.
- Cover formatting, comment stripping, renaming, dead-code elimination, structural refactoring, function extraction/inlining, minification/transpilation, partial copying, and repeated AI rewrites including code-to-description-to-code. Cross-language ports are a separate experimental regime, not an assumed capability.
- Cover transplantation/forged attribution, overwriting with another mark, averaging or combining differently marked releases, collusion between recipients, and adaptive oracle attacks. Distinguish recovering a key from removing a detectable signal.
- Separate mark presence, artifact ancestry and owner attribution: a transplanted mark may be a correct presence detection but a false attribution. Define labels for each objective.
- Explain how to validate transformed programs and distinguish broken attacks from behavior-preserving evasions. Include transformation composition, budgets, repeated attempts and selection of the best attack output.
- Identify empirical and formal limits. Explain the assumptions behind any impossibility or robustness claim rather than asserting universal guarantees.

## Specific deliverable

Produce an attack matrix with attacker knowledge, transformation, expected mechanism affected, success criteria, quality checks and primary evidence. Propose a minimal reproducible attack suite plus an extended suite. Record tool/model versions, prompts, seeds, query/compute budget, unsuccessful attempts and licensing. Do not make live calls to paid models or attack third-party services; give an unexecuted plan where needed. Hand statistical calibration to lane 3 and artifact/record binding to lane 4.

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
