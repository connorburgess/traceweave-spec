# What Traceweave is for

Traceweave aims to help people **mark content so it can be recognized later, find candidate reuse, and preserve reviewable evidence**. Start locally with code. Text, images and audio are future profiles, not working detectors.

Today the repo supplies draft formats, synthetic fixtures and validation tools. The workflows below are planned. A match is evidence to review; it is not a verdict about ownership or permission.

| Case | Person and question | Inputs and workflow | Useful result | Important limit |
| --- | --- | --- | --- | --- |
| UC-1 — Find an extracted function | A software maintainer asks whether a larger project contains a fragment of their reference code | Catalogue an authorized reference snapshot; compare a locally available candidate; inspect aligned spans | Candidate source ranges, profile/config, exact artifact digests and comparison evidence | Heavy rewrites may evade detection; common code may match; no result does not establish absence |
| UC-2 — Review license history | A reviewer asks where a matched region came from and which historical notices need inspection | Combine UC-1 evidence with region origins, dependency records and archived license text | A reproducible review packet linking regions to historical evidence | A later restrictive license does not decide the status of all earlier expression; the detector makes no legal determination |
| UC-3 — Preserve a private reference | A creator wants to retain a record of a reference catalogue without publishing its contents | Keep exact catalogue bytes/config and a fresh commitment opening privately; optionally sign or timestamp the defined record | Later verification that disclosed bytes open the recorded commitment | Signing alone proves neither ownership nor earlier existence; a claimed date is not trusted time; opening currently reveals the whole catalogue |
| UC-4 — Check a received evidence packet | An auditor wants to separate authenticity from similarity | Verify payload bytes, subject digest, accepted signer and any time evidence independently; rerun comparison if authorized reference material is supplied | Separate verdicts with reasons and reproducible localized evidence | A valid signature on a false assertion remains possible; unavailable private material can prevent independent comparison |
| UC-5 — Assess transformations | An implementer asks whether renaming, extraction or rewriting defeats a profile | Apply recorded transformations to synthetic/licensed positives; include unrelated and independently written same-task controls | Held-out detection and false-alarm report, including failure cases and resource costs | Results apply to the tested profile, corpus and pipeline; they do not establish universal resilience |

## Primary use case: embed now, recognize later

**UC-6 — Recognize distributed content.** A creator embeds a profile-defined mark into content they are authorized to modify, validates the marked output, and distributes it. Later, they check a candidate for that mark and inspect the localized evidence. Preserve the original and marked artifact digests, embedding profile/configuration, and private mark record. A detection result is separate from ownership and permission.

The first embedding experiment must test unmarked controls, wrong marks or keys, removal, transplantation, partial extraction and transformations. Reject marked outputs that fail the profile’s functional or quality requirements. Detection can return insufficient evidence. No embedding scheme or survival guarantee is selected yet.

An **embedded mark** changes the content; an **extracted fingerprint** describes existing content; a **provenance record** binds claims to exact artifacts and verification material. These are separate mechanisms.

## First walkthroughs to build

For embedding: create a synthetic reference → embed a test mark → validate behavior → transform or extract a fragment → attempt detection → inspect the result. Include unmarked, independently marked and transplanted-mark controls. The mark recipe and language must be selected through the research gate, not invented for a demo.

For extracted matching:

A maintainer has a synthetic `reference.py` containing an original scoring function. A synthetic `candidate.py` contains that function inside a much larger file, with formatting changed. A `control.py` independently solves the same task.

1. Extract the reference with a pinned profile and retain its exact bytes, digest, configuration and private catalogue.
2. Compare candidate and control using the same supported profile.
3. Show candidate spans with their source coordinates and evidence. Show the control outcome even when it exposes a false alarm.
4. Report directional fragment containment separately from whole-file similarity. A small fragment inside a large file should not disappear behind a whole-file denominator.
5. Let a reviewer inspect the source and origin records. Keep permission assessment separate.

These filenames describe a proposed example; these three files and the detector do not exist yet. See the [example matrix](implementation-patterns.md#example-matrix) for its acceptance tests.

## Outside the first release

Internet-wide scanning, automatic enforcement, proving model-training membership, automatic ownership attribution, and guaranteed survival under arbitrary rewrites are outside the initial scope. Traceweave is not a DRM system. Optional provenance adapters do not turn similarity into proof.
