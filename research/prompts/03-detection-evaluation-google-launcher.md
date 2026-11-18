# Google research workflow: detection and evaluation

## 1. Add the reference brief as a source

Upload or paste the full contents of [the Google reference brief](03-detection-evaluation-google.md). Name the source **Traceweave Lane 3 — Detection Evaluation Research Brief**. Ensure it is available as a source, not only as a saved note. The brief contains requirements, not evidence supporting its own claims.

## 2. Left-side Web / Deep Research query

Paste this self-contained query into the research field. It deliberately includes the core scope; do not rely on this field automatically receiving notebook sources.

```text
Research rigorous evaluation of embedded source-code watermarks and fingerprint detectors for Go/Rust: false alarms across windows, keys and catalogues; held-out calibration; correlated negatives; zero-error confidence bounds; partial-copy and transplant controls; and fair mark-only/fingerprint-only/hybrid comparisons. Use primary sources. Propose a small local pilot and scalable benchmark; distinguish detection from ancestry and ownership. No embedder is selected; do not assume payload capacity or universal thresholds.
```

Import the research results into the notebook when the run finishes.

## 3. Chat instruction after importing results

Select the reference brief and the imported evidence sources, then send:

```text
Use “Traceweave Lane 3 — Detection Evaluation Research Brief” as the full task instructions. Follow its questions, constraints and required eight-section report format. Use the imported research sources as evidence; the brief itself is not evidence. Produce the complete standalone Markdown report, titled 03-detection-evaluation.md, rather than summarizing the brief. Prioritize Go/Rust source marking, separate candidate verification from catalogue-wide discovery, and keep error units, denominators, uncertainty and abstentions explicit. Cite accessible primary sources with portable URLs and versions; identify unsupported claims and evidence gaps. Do not invent measurements or imply experiments were executed. If required sources are inaccessible, state that limitation and list the remaining research questions.
```

Review the resulting report before implementation. Preserve its original text locally under `research/gemini/03-detection-evaluation.md`; publish reviewed conclusions separately.
