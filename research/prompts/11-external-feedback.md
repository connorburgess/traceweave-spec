# Lane 11 — External feedback on the Traceweave design

Prepared 2026-11-23. Three pieces: the full brief (paste into Perplexity as the prompt; add to NotebookLM as a copied-text source; or paste into Gemini Deep Research), the short NotebookLM source-discovery query, and the NotebookLM center-chat instruction.

The brief is self-contained and names no private application, path or person.

---

## 1. Full brief (Perplexity prompt / Gemini Deep Research prompt / NotebookLM source)

```
You are reviewing an early-stage open specification and reference implementation
called Traceweave. I want critical, evidence-based feedback, not encouragement.
Cite primary sources (papers, standards, tool documentation, source repositories)
for every factual claim, give exact figures with their units and denominators,
and say "no evidence found" where that is the case. Distinguish what a source
measured from what it claims. Negative findings are as useful as positive ones.

WHAT TRACEWEAVE IS TODAY

Goal: let a creator later recognise their own content when it reappears
elsewhere, and hand a third party evidence they can check themselves. Two
approaches were planned: (a) extracted fingerprints compared against a private
catalogue, and (b) marks embedded in the content that can be recovered later.

Current state, after about a week of work:

1. Extraction contract. Source code is lexed into tokens by a fully specified
   per-language lexer (Go and Rust implemented; TypeScript/JavaScript and plain
   text specified but not implemented). Two token streams are produced: "exact"
   and "normalized" (identifiers and literals mapped to class placeholders).
   k-grams of tokens (default k=5 for code, k=8 words for text) are hashed with
   SHA-256 truncated to 64 bits, and winnowing (window 4 for code, 8 for text,
   rightmost-minimum tie rule) selects fingerprints. Every fingerprint keeps a
   half-open UTF-8 byte span into the original bytes. Unicode 17.0.0 tables are
   pinned by digest. Bounds: k <= 16, window <= 128, input <= 8 MiB.

2. Catalogue and comparison contract. A catalogue stores fingerprints, spans
   and artifact digests, never source text. Comparison of a reference catalogue
   with a candidate catalogue turns shared fingerprints into seeds, merges
   seeds on the same diagonal within a gap into regions, and reports a closed
   set of outcomes: match, below-minimum-evidence, ambiguous, no-match,
   abstentions and rejections. Minimum evidence counts distinct hashes. Common
   code is suppressed only through an explicit boilerplate catalogue bound by
   digest. The report has a canonical body (byte-identical across
   implementations) and a separate provenance block. The report carries no
   score, no false-alert rate and no ownership claim.

3. Two independent implementations (Rust and Go) written from the contract
   text agree byte for byte on roughly 14 million differential extraction cases
   and 20,000 comparison cases per seed; a third clean-room implementation by a
   reviewer agrees on 5,000 generated pairs. Conformance is by hand-derived
   test vectors plus "wrong implementation" self-tests.

4. Evaluation protocol, frozen design, not yet run. 24 Go and 24 Rust public
   repositories with permissive licences, chosen mechanically from a search
   snapshot; grouped tuning/held-out splits by owner, dependency links and
   shared files; positives generated mechanically by nine transformations
   (verbatim file, whole function, partial fragments in eight size buckets,
   whitespace/comment changes, formatter runs, identifier renaming, declaration
   reordering, mixing into unrelated files); negatives are unrelated, same
   domain and same-stack repository pairs. Unit: one unordered repository pair
   is one search (132 held-out negative searches). Budget: at most 1 false
   alarm per 20 searches, i.e. met with <= 6 alarms; abstentions count as
   alarms. Tuning grid of 144 configurations selected on the tuning split only.

5. Embedded marks: negative so far. Synthetic Go/Rust carriers (declaration
   order, local names, literal spelling) survive formatters but are erased by
   cheap normalization; a small public-code census found almost no eligible
   sites. Literature reviewed and found wanting for our purpose: SrcMarker,
   RoSeMary, SEW, CLASP (needs the reference code; 2-32 bits), PLACEMARK
   (Python only). For existing prose, homoglyph and zero-width marks are erased
   by NFKC + Unicode confusables + invisible-character deletion. For images, an
   external benchmark shows PDQ and ISCC fail moderate crops and that forged
   marks pass a common watermark's baseline; our own run is a 200-synthetic-image
   contract check only.

6. Evidence and provenance. DSSE/in-toto signing interoperability was shown on
   synthetic statements between Go and Rust libraries; reports are not yet
   signed. A local "provenance stamp" names the implementation commit only when
   the binary was built from a verified clean export of that commit; this is
   explicitly evidence about cooperative builds, not a security boundary.

KNOWN WEAK POINTS (please test these, do not just repeat them)

- No measured evidence of usefulness yet.
- Token k-gram fingerprints miss heavy rewrites; inserting one token every k-1
  tokens removes every match; boilerplate alone matches without suppression.
- No viable embedded mark for code or text.
- 48 repositories can only test a coarse false-alarm budget.
- All review so far is by the same team; nothing has run on Linux or in CI.

QUESTIONS

A. Prior art and positioning. How does this design compare with MOSS and
   winnowing (Schleimer, Wilkerson, Aiken 2003), JPlag, Dolos, Sherlock,
   SourcererCC, NiCad, Deckard, CCFinder/CCAligner, Simian, SIM, simhash and
   MinHash/LSH systems, Software Heritage identifiers and its provenance index,
   ScanCode/licence scanners, and commercial snippet matchers (Black Duck,
   FOSSA, Snyk, SCANOSS and its open winnowing spec)? What do those tools do
   that this design lacks, and is anything here actually new or better
   specified? Is there an existing open standard this should adopt or align
   with instead of defining its own (for example the SCANOSS winnowing format,
   SWHID, SPDX snippet records, ISCC)?

B. Parameters and algorithm. For code, what k and window values do published
   tools use and why? What is the measured effect of token normalization on
   recall and false matches? Is seed merging on a diagonal with a gap a
   recognised approach (compare greedy string tiling, suffix structures,
   local alignment)? Is 64-bit truncated SHA-256 a sensible choice versus
   rolling hashes, and what collision or performance evidence exists?

C. Evaluation design. Critique the protocol against how clone and plagiarism
   detectors are evaluated in the literature (BigCloneBench and its known
   flaws, POJ-104, OJClone, SOCO, PAN source-code tasks, mutation-based
   frameworks such as the mutation/injection framework by Roy and Cordy).
   Are mechanically generated positives accepted as valid evidence, and what
   are the known threats to validity? Is "false alarms per repository-pair
   search" a meaningful unit, and what units do others report? What corpus
   size would be needed to support a 1-in-100 or 1-in-1000 claim, and how do
   others handle dependence between cases and real reuse among "negatives"?

D. Adversarial robustness. What is known about defeating winnowing-style
   detectors (token insertion, statement reordering, dead code, LLM
   paraphrase/translation of code)? What recall do recent papers report for
   token-based detectors against LLM-rewritten code, and which approaches do
   better (AST/PDG-based, learned embeddings such as code2vec, CodeBERT-style
   models, contrastive clone detectors), with what false-positive cost?

E. Embedded marks. Is our negative conclusion for source code and existing
   prose too pessimistic? Name any published scheme that embeds a recoverable
   identity payload in existing (not model-generated) source code or prose and
   survives formatting, identifier renaming and normalization, with measured
   capacity in authenticated bits, false-positive evidence and available code
   and licence. For images and audio, which schemes have independent
   (non-author) robustness and forgery evaluations?

F. Evidence and provenance. How do C2PA (including soft bindings), SLSA,
   in-toto, Sigstore/Rekor, and reproducible-builds practice handle what our
   "report + provenance block" tries to do? What would a third party need in
   order to trust a comparison report, and what is missing here? Are there
   legal or forensic standards for software similarity evidence (for example
   abstraction-filtration-comparison in US case law, expert-witness practice)
   that the report format should accommodate?

G. Privacy. A catalogue contains truncated hashes of token k-grams and spans.
   What is known about recovering or confirming source content from such
   fingerprints (dictionary/guessing attacks, membership inference)? How do
   comparable systems (private set intersection for code, k-anonymity style
   lookups, SCANOSS) limit leakage?

H. Biggest risks. Given all of the above, what are the three most likely ways
   this project fails or turns out redundant, and what is the cheapest
   experiment or decision that would reveal each one early?

OUTPUT FORMAT

1. A one-paragraph verdict.
2. A table of the closest existing systems and standards: what each does,
   licence, and how Traceweave differs (better / worse / same), with sources.
3. Answers to A-H, each with sources and explicit confidence.
4. A ranked list of concrete changes you recommend, each tied to evidence.
5. A list of claims in this brief that you could not verify or believe are
   wrong.
Do not invent thresholds, benchmarks or citations. If you propose a number,
say where it comes from.
```

---

## 2. NotebookLM: top-left source-discovery query (Web / Deep Research)

```
Source code similarity and plagiarism detection by token k-gram fingerprinting and winnowing: prior art (MOSS, JPlag, Dolos, SourcererCC, NiCad, SCANOSS winnowing, Software Heritage), evaluation methodology and benchmarks (BigCloneBench, mutation frameworks), false-positive rates, robustness to obfuscation and LLM rewriting, source-code and text watermarking of existing content, and provenance evidence standards (C2PA soft bindings, in-toto, SLSA)
```

## 3. NotebookLM: center-chat instruction (after the research sources are imported)

```
Using the source titled "Lane 11 — External feedback on the Traceweave design" as your instructions (it is a brief, not evidence), answer its questions A-H in the output format it specifies. Base every factual claim on the imported research sources and cite them; say "no evidence found" where they are silent. Give exact figures with units and denominators, separate what each source measured from what it claims, list any claim in the brief you could not verify or believe is wrong, and do not invent thresholds or citations.
```
