# Deep research prompt: Private provenance and evidence verification

Output filename: `04-provenance-verification.md`

## Decision to enable

How should Traceweave bind marks and reference content to private evidence that another party can later verify, without confusing authenticity, time, mark presence or ownership?

## Questions to investigate

- Review DSSE pre-authentication encoding, in-toto Statement v1, relevant Sigstore bundle modes and RFC 3161 with updates/errata. Explain what each supplies and does not supply. Identify existing libraries; do not design a new signature primitive.
- Design a proposed binding among original artifact digest, marked artifact digest, embedding/detection profile and version, exact configuration, mark identity or private mark record, and extracted fingerprint catalogue. Analyze whether disclosing each field reveals the mark, key, identity or participation.
- Scrutinize the repository's proposed salted exact-byte catalogue commitment: domain separation, nonce handling, framing, retained bytes, opening, correlation risks and full-disclosure limitations. Do not describe it as audited or as zero knowledge. Examine what a timestamp binds and what can actually be inferred from it.
- Separate signature validity, signer trust, exact subject match, commitment opening, trusted time, mark detection and similarity findings. Explain mixed outcomes and malformed/duplicate-key JSON rejection while preserving signed bytes.
- Address false signed claims, copied public content, mark transplantation, replay/context confusion, key rotation, compromise and evidence retained across algorithm changes. Include malicious record sizes and unsafe automatic fetches.
- Compare fully local/private signing with optional external timestamp or transparency services, including metadata disclosure. No mandatory public log or prefix-query anonymity assumption.
- Briefly assess C2PA interoperability only where relevant to future media profiles; keep it out of the critical path unless an explicit mapping is justified.

## Specific deliverable

Provide a minimal proposed evidence relationship model and verification decision table, then a library-based interoperability test plan with positive and negative cases. Include changed payload/type/signature, untrusted key, changed subject, wrong commitment opening, missing/invalid timestamp and unavailable private reference material. Separate protocol evidence from legal interpretation. Hand mark survival to lane 2 and detector calibration to lane 3.

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
