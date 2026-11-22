# NotebookLM launch: Text and document profile candidates

Use a separate notebook for this lane. The complete [09-text-profile.md](09-text-profile.md) is the same brief to submit to Perplexity Research. For NotebookLM, add its complete text as a pasted-text source titled **Traceweave research brief: Text and document profile candidates**. The brief is instructions, not evidence.

## Top-left Web / Deep Research query

Select Web and Deep Research in the source-discovery box. Paste only this standalone search query; do not assume source discovery can follow a reference to an existing source:

```text
Research fingerprinting and embedded marks for existing prose and Markdown text: winnowing, shingling, MinHash and SimHash baselines; Unicode, whitespace, homoglyph, synonym and syntactic marks; survival under normalization, reflow, copy-paste, translation and LLM paraphrase. Use primary papers, author code and licences; report units, denominators, negative results, minimum fragment length and offline CPU use. Separate fingerprint baselines from embedded marks and presence detection from identity. Recommend one bounded experiment or none; no ownership inference.
```

## Center chat after research completes and sources are imported

Select the full brief and the relevant imported primary sources. Paste:

```text
Use “Traceweave research brief: Text and document profile candidates” as the full task instructions, not as evidence. Read the imported research sources and produce the complete eight-section standalone Markdown report requested by that brief, named 09-text-profile.md. Do not merely summarize the brief. If its full text is unavailable, say so rather than inventing instructions.

Answer the decision question with one bounded experiment candidate or a justified no-go. Preserve the supplied project findings as provisional context; do not claim you independently reproduced them. Distinguish published measurements, formal assumptions, your inferences and unexecuted proposals. Separate fingerprint comparison baselines from embedded marks, and presence detection from identity. State units and denominators, negative results, licences and offline/CPU evidence. Identify source gaps and contradictory evidence. Include primary-source URLs, versions/dates and decisive sections/tables; NotebookLM-only citation markers are not sufficient for the exported report. Do not cite the brief as scientific support. Do not assume a blind or zero-knowledge detector; private reference catalogues are allowed. No ownership inference, universal-robustness or cross-media generalization from a narrow result.
```

Save the returned report separately under the provider's local directory; do not overwrite this prompt. Keep the first Google/Perplexity passes independent before comparing their reports.
