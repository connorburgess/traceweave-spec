# Lane 14: AI-origin signals in text, evidence review and design note (AIO)

Prepared 2026-11-24. This is a research (R) note. The owner asked whether Traceweave could also tell people, for free, whether content carries an AI provider's mark, or at least specify how. By the owner's scope note, the note covers **text channels**: the statistical text watermarks of Google, Anthropic and OpenAI; the routes to their detectors; unkeyed "AI text detectors"; how the [text profile](../../profiles/text.md) and its `exact`, `folded` and `skeleton` channels interact with them; and code as a sub-case of text. Images, audio and video get one short section (§9), which points to existing work.

**Not done.** Nothing was built or run. No provider API was called and no account was created. No form was submitted. No model, tokenizer or dataset was downloaded. No watermark removal or evasion was built or tested. Public pages, papers and repositories were read over read-only HTTP on 2026-11-24, at the versions in the [ledger](#source-ledger). Repository context: HEAD `21ae62b` on `roadmap-v2`. Read first: the [roadmap](../../ROADMAP.md) gate types and the image-mark finding of 2026-11-23 ("a mark … can serve as a finding aid, but not as evidence of origin"); the [text profile](../../profiles/text.md) §8; lanes [09](09-evidence-review.md) and [10](10-evidence-review.md); the [C2PA mapping draft](../drafts/c2pa-mapping.md); the [registration record design](../../spec/registration-record.md) §4.6, §11 and §19.5. Only this file and the new rows in the [source register](../../docs/sources.md) belong to this lane. ROADMAP.md is not changed; proposed gates are in §8.

**Not legal advice.** The EU rows quote what the official texts say. They do not say how any authority or court would apply them.

Labels: **S** = stated by the cited primary source (as the operator's or author's own claim unless marked independent); **M** = measured by a third party who does not operate the scheme; **I** = this note's inference; **N** = not found in any source read.

## Decision

**Recommendation:** for text, **do (c) now and specify (b) as a draft only**. Traceweave should not show any AI-origin result for text by default. It should document why, publish the claim sentences of §7 for any future adapter, and specify an **off-by-default provider-signal record** that sits outside both the comparison report and the registration statement. Nothing in it may be implemented or connected before the owner decides AIO.4. Keep (a), report-only reading of signed C2PA metadata, inside the existing C2PA track. For text it applies only to containerised text (PDFs and similar files), and today only OpenAI says it signs those (O4). **Never ship an unkeyed AI-text classifier** (§5).

Why, in one paragraph. **No free, open, offline tool can check any of the three text watermarks today.** Each one needs the operator's secret key (G1 Methods; A1; O2). Google publishes no text detector at all (G11, a Google moderator, 2026-11-16). Anthropic's and OpenAI's text detectors are open only to approved organisations (A2, A5; O1, O4). Neither has published terms for its text detector covering retention, reuse of results or prohibited uses (N for both). Every detector route sends the full text to the provider. That breaks Traceweave's promise that content never leaves the machine. On the evidence side, a positive result means, in the operators' own words, only that their system "was likely involved with the content at some point" (A1). A negative "does not prove human authorship" (O1). The only independent measurements of the SynthID family use the open implementation, not a deployed one. They show 39% detection at 200 tokens and 56–59% at 400 tokens, at a 1% false-positive rate (W14). They show near-chance detection on code (AUROC 0.55–0.57, W14), and large losses after paraphrase or translation (W10). None of this is a basis for showing people a verdict about a text, still less about a person.

**Strongest alternative:** build (b) now as an opt-in adapter for users who already have approved detector access, because the EU Code of Practice requires providers to offer a downloadable, signed detection result (L3 Sub-measure 2.1.2). Traceweave could store that result verbatim. It is rejected for now because no operator has published the terms that would allow storing or showing a result. The record format can still be drafted now (AIO.5). **Confidence:** high on who can verify what and on the operators' own caveats, which are quoted from primary pages. Medium on accuracy, because the deployed figures are operator claims with no sample sizes (O1), and the independent figures use the open implementation (W10, W14). Low on how long any route will stay as it is: the Code requires interoperable detection by 2 February 2027 (L3 Measure 3.4(c)).

## 1. Signals for text, per operator

### 1.1 Summary table

| Signal | Operator and scope | Who can verify | Route, cost and terms | Positive means (operator's words) | Negative means (operator's words) | Published accuracy |
| --- | --- | --- | --- | --- | --- | --- |
| **SynthID-Text** (tournament sampling; keyed seed from the previous H = 4 token IDs) | Google. S: "productionized and is currently watermarking responses in Gemini and Gemini Advanced" (G1). Which API and code surfaces are covered is stated only in forum replies, and those contradict each other (G11) | **Key holder only.** S: scoring needs "the tokenized text, the watermarking key k and the random seed generator" (G1 Methods). The open code verifies only text marked with your own key (G3) | **No text route.** S: "There is no public or self-service tool today to verify SynthID watermarks on text from hosted Gemini API endpoints" (G11 post 9). The SynthID Detector portal accepts only image, audio and video (G8, G9). Its terms forbid black-box attacks, scraping and evading quotas (G9 `/terms`) | For media, S: "it was likely edited or generated by a SynthID-enabled AI model" (G9). For text, none is published | For media, S: "does not rule out AI generation or manipulation"; "This is not a general AI detector" (G9) | S (G1 Fig. 3a, plot readings, Gemma 7B-IT, temperature 0.7, ELI5, TPR at 1% FPR): about 0.50 at 100 tokens, 0.70 at 200 and 0.87 at 400. The live Gemini test of about 20 million responses measured user feedback, not detection (G1) |
| **Claude text watermark** ("a version of the SynthID-Text approach", A1) | Anthropic. S: models released on or after 2 August 2026, "globally at launch", on the API, the Claude apps, Claude Code and cloud partners (A1, A2). On some older models, non-default `temperature`, `top_p` or `top_k` may drop the mark (A2, A3). No opt-out is mentioned (N) | **Approved organisations.** S: a "Detection API, which is currently in private preview for eligible organizations" (A6). The eligible groups listed are regulators, law enforcement, media, fact-checkers, independent researchers, educational organisations, EU civil society groups and obligated enterprises (A2, A4) | Application by form. It needs a free Claude Platform account with the Admin role (A5). Price, rate limits, retention, and terms for storing or showing results: **N** | S: "A watermark can only determine that Claude was likely involved with the content at some point. It cannot distinguish 'Claude wrote this' from 'Claude heavily edited this.'" (A1) | S (A2, as a list): an absence can come from an older model; text that was edited, paraphrased, translated or mixed; a short passage; or non-default sampling | **N.** No rate, FPR or length is published (A1–A4) |
| **textGrain** (keyed block optimal transport with Gumbel costs and an entropy budget) | OpenAI. S: "eligible ChatGPT and Codex text output in the European Union" only. In the API it is "off by default", with opt-in for select models (O1). Open source is planned, not released (O1) | **Approved organisations.** S: "Access will initially be limited to approved researchers and expert organizations" (O1); "available only to approved organizations including AI research and academic institutions" (O4) | Application by form (O5). S: "Text detector checks are currently free". Content "is not stored unless legally required and is not used to train OpenAI models" (O3). Use is "subject to the OpenAI Services Agreement" (O4). Detector-specific use limits: **N** | S: "evidence that an OpenAI tool likely processed the content"; it "does not establish who authored or owns the content" (O3) | S: "The absence of a detected watermark does not prove human authorship." (O1) | S (O1, no sample size given): at a 1% false-positive target, "about 80% of 200-token passages, compared with about 95% of 400-token passages, for content such as psychology"; mathematics "substantially lower". On 400-token passages, 10% synonym replacement took detection "from about 92% to 66%" and 25% took it to 17%. Across 24 languages (500 prompts, O3), 69.0% for Spanish down to 42.2% for Romanian |
| **Signed metadata (C2PA) on text files** | OpenAI: Content Credentials on "Images and PDFs" (O4). Anthropic: C2PA on files such as PNG and JPEG, "does not check text" (A2, A6). Google: none found for text (N) | **Anyone**, offline, under the verifier's own trust list. The [C2PA mapping draft](../drafts/c2pa-mapping.md) covers the format | Free. A1 and O6 provide public file checkers, but those are services. An offline reader is the C2PA track's job | A signed assertion of what the signer says happened (see the [C2PA mapping draft](../drafts/c2pa-mapping.md)) | Stripped metadata is normal and means nothing (A2 lists "metadata stripped" among the reasons for absence) | Not applicable: a signature verifies or it does not |

**Free-form text carries no metadata.** The Code states it directly: "given that free-form text cannot transport metadata, a single-layer of marking … is considered sufficient" (L3 Measure 1.1). So for pasted text, the only provider signal is the keyed statistical watermark.

### 1.2 What the law asks of providers, and what it does not ask of anyone else

- **The duty.** Providers "shall ensure that the outputs … are marked in a machine-readable format and detectable as artificially generated or manipulated" (L1 Art. 50(2)). The Regulation applies "from 2 August 2026" (L1 Art. 113). Systems already on the market before that date have until "2 December 2026" (L2 new Art. 111(4); L6 point 153).
- **Detection must be free, but text detection may be restricted.** S: "Signatories will make the detection solution available free of charge" (L3 Sub-measure 2.1.1). For free-form text, access "may" be restricted to "verified expert end-users", and "Any restriction to the access will be limited in time" (L3 Sub-measure 2.1.2). The A2/A4 and O1/O4 access rules match this restricted mode.
- **Signed, downloadable results.** S: "the detection result of specific content submitted for detection can be downloaded upon request in a digitally signed format, including at least a hash of the content submitted for detection, a URL or other identifier of the detection solution, and a timestamp" (L3 Sub-measure 2.1.2). **This is the natural import format for design option (b)** (§6).
- **Zero retention.** S: content "is stored only for the duration of the detection and is permanently deleted immediately thereafter" (L3 Sub-measure 2.1.3 (e)).
- **Short text and code are out of scope.** S: "'very short text' should be understood as text shorter than 200 tokens" (L3 Glossary). Source code, "regardless of whether it is composed of text characters", and including "natural-language comments … that form an integral part of the source code", falls "outside the scope of Article 50(2)" (L6 point 68).
- **Interoperability later.** S: providers implement an interoperable detection access method "by 2 February 2027" (L3 Measure 3.4(c)). Providers "must rely on publicly-available industry standard detection solutions that allow any third party to implement detection that is ideally locally executable on the digital device", although watermarking may rely on the provider's own solution for a limited time (L6 points 75–76).
- **No duty on independent tools.** No obligation on a third-party detector operator was found in L1, L3 or L6 (N). L6 point 78 keeps responsibility with the provider. The Code's preamble lets third-party marking and detection vendors sign voluntarily (L3).
- **Absence wording.** No sentence in the Code says that a negative result does not establish human authorship (N, searched L3 and its FAQ). That caveat comes from the operators (O1, G9), not the law.
- **Signatories.** "Google", "Anthropic" and "OpenAI" each appear in the official list under Section 1 (providers), last updated 18 November 2026 (L5, read through the fetch tool's extraction).

### 1.3 Independent evidence on these schemes

**No independent evaluation of the deployed Claude watermark or of deployed textGrain was found** (N; searches recorded in the ledger notes). W18 is theory about textGrain, with no experiment. All independent SynthID numbers below use the open implementation (often through the MarkLLM toolkit), not Google's deployed key or configuration.

| ID | What was tested | Result (unit, denominator, conditions) |
| --- | --- | --- |
| W19 | Deployed Gemini APIs, black-box, without the key | M: "all Gemini models are watermarked and they all share the same key except for Gemini 4 Argon and Gemini Carbon (because their tokenizer is different)", and "the context size of the watermark is 4 tokens". Up to 2,000 stories per model. A blog post, not peer-reviewed. Key recovery or spoofing against live Gemini: N |
| W14 | Open SynthID-Text, non-distortionary; Gemma-2-9B-IT and Llama-3.1-8B-IT; 500 prose prompts; 364 code problems × 10 samples; threshold at 1% FPR re-estimated at each length | M: prose TPR 39% at 200 tokens (both models); 59% and 56% at 400 tokens. **Code AUROC 0.55 and 0.57.** "between 25% and 31% of code samples were identical, character for character, with and without the watermark". On verification: "For neither deployment, however, can anyone outside the company currently verify them" |
| W10 | WaterPark: 10 schemes; Qwen2.5-14B-Instruct; TPR at FPR fixed at 1% | M, SynthID row: clean 0.998; **lower-case 0.856**; synonym 0.919; typo 0.321; DIPPER-40 0.498; translation 0.232; copy-paste CP1-10 0.039. Kirchenbauer's scheme ("TGRL"): clean 0.993, lower-case 0.831. "A single round of ChatGPT paraphrasing reduces detection rates of all watermarkers below 0.3" |
| W11 | Open SynthID-Text via MarkLLM; Sheared-LLaMA-1.3B; 200 watermarked and 200 human texts at 200 tokens; best-threshold metrics | M: unattacked TPR 1.0, FPR 0.0. DIPPER: TPR 0.895, FPR 0.23. Copy-paste into ten times as much human text: AUC 0.62, FPR 0.53. Back-translation via Chinese: TPR 0.675 |
| W12, W13 | Black-box attacks on re-implementations, mean-score detector only | M: TPR after attack 0.13–0.16 (W12, 1,000 texts of 100 tokens) and 0.00–0.01 (W13, 100 texts of 256 tokens). Neither attacks the Bayesian detector, which needs Google's training data (W13) |
| W15 | Open SynthID-Text, **50-token** texts, 30 per method | M: 80% false negatives before any attack; 5.4% (10 of 184) of paraphrased human controls flagged. Mostly shows that short-text detection fails |
| W5 | Watermark stealing (Kirchenbauer family), about 30,000 queries, "$42" at January 2024 API prices | M: spoofing success 0.54–0.97 at FPR 10⁻³ across five schemes; scrubbing raised from about 0.02 to 0.76–0.90. **Not tested on SynthID or the deployed schemes** |
| W3, W4, W7 | Paraphrase and translation against Kirchenbauer-family marks | M: DIPPER took detection at 1% FPR from 100% to 57.2% (W3, 300 tokens). Recursive paraphrase went from 99.3% to 9.7% (W4). Cross-lingual round trip brought AUC to 0.61 and 0.54 (W7) |
| W1, W2 | The scheme authors' own reliability study | S: after strong human paraphrase, "the watermark is detectable after observing 800 tokens on average, when setting a 1e-5 false positive rate" (W2). Low-entropy text is the main source of misses (W1 §4.1) |

**Reading (I).** A keyed text watermark is a finding aid for its operator. Outside its operator it is not evidence that anyone can recheck. This is the same conclusion the roadmap reached for image marks on `e-img-m-2`. Nobody outside the operator can recompute the statistic. The deployed figures have no denominators (O1). Spoofing has been shown on the scheme family (W5), so even a positive could be planted in a person's text by a third party. That alone rules out any rendering that attributes a result to the person who wrote the text.

## 2. What a free, open, offline tool can check today

| Signal | Offline, free, without any provider secret? | Why |
| --- | --- | --- |
| SynthID-Text in Gemini output | **No** | Needs Google's key, configuration and tokenizer (G1 Methods; G3 README: "The logits processor used for detection must have the same watermarking config as the one used for generation"). None is published for Gemini (G3; G11) |
| Claude watermark | **No** | Keyed. S: "the companies that provide it don't have our key" (A1); the mark "is invisible to anyone who does not have the detection API" (A4) |
| textGrain | **No** | S: "The detector requires only the generated text and the secret key" (O2). The open-source release is only planned (O1) |
| C2PA on PDFs and other text containers | **Yes**, with a C2PA reader and a trust list | Signed metadata. Report-only, inside the C2PA track (§6 (a)) |
| Black-box tests that an API applies *some* watermark (W19, W20) | Not applicable | These need many queries to the provider. They are research on a service, not a check of a given text, and are out of scope here |

**Provider APIs, against Traceweave's promise.** Every text route needs the full text uploaded to the provider. The only data-handling statement found is OpenAI's: "not stored unless legally required" (O3). Anthropic's is N for text; Anthropic's file checker runs in the browser (A6). The Code asks for zero retention (L3 Sub-measure 2.1.3 (e)), but a provider's practice is shown only by its own terms. **I:** any adapter therefore breaks "your content never leaves your machine" for the content checked. It must be explicit, per call, and impossible to trigger from a comparison, a catalogue build or a registration.

**Free tiers.** OpenAI: "currently free" for approved organisations (O3). Anthropic: a free account is required, and the price of detection calls is N (A5). Google: no text route (G11). The Code requires free access for the listed expert groups "without any restriction on the volume of requests" (L3 Sub-measure 2.1.1). **Whether results may be stored or shown to third parties: N for Anthropic and OpenAI.** This gap blocks (b).

## 3. Code as a sub-case of text

- **Law.** Source code is outside Art. 50(2) (L6 point 68). Providers have no duty to mark it.
- **Operators.** S: code "has generally less watermarking than some other forms of text" (A1). S: "Code is also harder to watermark because there are fewer plausible choices for what comes next" (O3). Google: no statement on code surfaces (N); a forum reply says API and "antigravity" text is marked (G11), which is not documentation.
- **Measurements.** M: SynthID-Text on code reaches AUROC 0.55 and 0.57, which is near chance (W14). For Kirchenbauer-family code marks, renaming took TPR from 0.79 to 0.57, and dead-code insertion took a Unigram mark from 0.76 to 0.01 (W9, 3 functions pooled per detection). The code-specific SWEET scheme lost to AUROC about 0.8 when all variables were renamed (W8, the authors' own result).
- **Unkeyed classifiers on code** are worse: average accuracy 47.83–50.83% across five detectors (D15 Table IV).
- **I:** for code, both "present" and "absent" carry almost no information. A tool should show "unknown" by default and never ask a provider about code unless the owner decides otherwise. This matches the repository's own negative embedded-code results (SYN records, roadmap finding of 2026-11-23).

## 4. Interaction with the text profile

### 4.1 Does folding preserve a token-choice watermark?

The premise "folding changes no word choice" is true of words and false of tokens. All three schemes score **token IDs**, after the detector re-tokenises the text with the provider's tokenizer. SynthID-Text seeds each position from "a hash of the most recent H tokens … we use H = 4" (G1). textGrain uses "a window of up to L_ctx preceding tokens" (O2). Kirchenbauer's paper names re-tokenisation as an attack surface: "Security against Homoglyph and tokenization attacks can be maintained using input normalization before the text is tested for watermarks … these characters must be removed through canonicalization" (W1 §7).

Per channel of the profile (§8 of [text.md](../../profiles/text.md)):

| Channel | What changes | Effect on a token-keyed watermark |
| --- | --- | --- |
| `exact` (original bytes) | Nothing | **Preserved.** This is the only input a provider check should ever receive |
| `folded`, NFKC part | Only compatibility characters: ligatures, full-width forms, superscripts (UAX #15) | I: on typical model output, which is mostly NFKC-stable, few tokens change. No paper measures NFKC alone on clean watermarked text (N) |
| `folded`, full case folding | Every upper-case letter: sentence starts, names, acronyms | **Measurably weakened.** The closest published proxy is WaterPark's "LowCase" transformation, measured M: SynthID 0.998 → 0.856 and Kirchenbauer 0.993 → 0.831 TPR at 1% FPR; Unigram 0.993 → 0.976 (W10 Table 2). Each changed token alters its own score and the H following seeds (I, from G1) |
| `folded`, Default_Ignorable deletion | Zero-width and other ignorable characters | I: removes nothing the providers put there. "Nothing is added to the text and there are no hidden characters" (A1); textGrain "does not add hidden characters" (O3). On text with ignorables from elsewhere, deletion re-tokenises, which W1 recommends before detection |
| `skeleton` | Confusable prototypes: `m` → `rn`, `0` → `O`, `1` → `l`, cross-script letters | I: far more tokens change than under case folding, so expect larger losses. W16 shows that single-character substitutions split one token "into at least 3 subword tokens" |

**The finding that matters for design (I).** The folded and skeleton values never leave the extractor as text. They feed k-gram hashes, and catalogues and reports hold hashes and spans, not text (profile §9–§10). So no Traceweave artifact could be sent to a provider detector even by mistake. A later provider check needs the **original bytes**, which the user keeps. The design rule is: *a provider check, if ever made, takes the exact bytes of the artifact named by its SHA-256, and nothing derived from them.* This makes the measurement below optional.

**An experiment that would test it without any removal attack (proposed AIO.3, owner-gated, not recommended now).** Use the open reference implementation at the pinned commit (G3), with **a key chosen by the experimenter**, and one small open model and tokenizer under a permissive licence. Generate n = 200 watermarked and n = 200 unwatermarked continuations at a frozen length (200 and 400 tokens). Score each with the frequentist detector at a threshold frozen before the run. Arms: original; NFKC; NFKC with full case folding; the profile's full `fold`; `skeleton(fold)`, each applied to the whole text with separators kept. Report detections per arm out of 200, plus false detections on the 200 unwatermarked texts, with denominators. It needs a model and tokenizer download (owner, as for TXT.5). Its output is also a measure of signal loss under a deterministic transformation, so the owner should confirm that it stays within the "no removal testing" rule before it runs. Its result would change no design decision, because of the rule above.

### 4.2 Could a registration record carry "provider signal"?

**Not inside the registration statement.** The statement is the registrant's signed claim about bytes they hold. Its key lists are closed (`statement-shape`, [design](../../spec/registration-record.md) §4.6). It deliberately has no creator or agent field (§19.5, `authorship-claim`). A provider signal differs on every axis that matters:
- it is a **third party's** observation, not the registrant's;
- it can change: detectors are upgraded or retired, and L3 Sub-measure 2.1.4 requires backward compatibility only for replacements;
- it describes involvement of a system, which the registration's required wording already says a record cannot show (§11, §19.5).

**As a separate record, yes.** §6 (b) drafts a `traceweave-provider-signal` record. It names the subject by the same SHA-256 of the exact bytes, so the two can be stored side by side, but neither references or changes the other. A comparison report never includes it. If the owner wants a creator's own statement about AI use, that is a different thing: a registrant **claim** (`claims.generator`, already floated in §19.5), shown as claimed and never as checked.

## 5. Unkeyed AI-text classifiers

| ID | Kind | Finding (unit, denominator) |
| --- | --- | --- |
| D1 | M, *Patterns* 2023 | 7 detectors on 91 human TOEFL essays: average false-positive rate **61.3%**; "All detectors unanimously identified 19.8% of the human-written TOEFL essays as AI authored" (18 of 91); at least one detector flagged 97.8% (89 of 91). The 88 US 8th-grade essays were classified with "near-perfect accuracy" |
| D2 | S, operator | OpenAI's classifier: 26% true positives and 9% false positives on its challenge set. Withdrawn: "As of July 20, 2023, the AI classifier is no longer available due to its low rate of accuracy." |
| D3 | M, 2023 | 14 tools, 54 documents: "even the highest accuracy values are below 80%" (best 76%, 41 of 54). False accusations on 18 human documents ranged from 0% to 50%. Machine translation of human text raised false positives. "Reports … cannot be used as the only basis for reporting students for cheating" |
| D4 | M, ACL 2024 | RAID, more than 6 million generations, results at 5% FPR per domain. Some detectors cannot reach low FPR at any threshold: "ZeroGPT plateaued at 16.9%". "Detectors are not yet robust enough for widespread deployment or high-stakes use." |
| D5–D7 | S, vendors | Turnitin: "less than 1% for documents with 20% or more AI writing"; sentence-level "around 4%" (D5). GPTZero: "no more than 1%" (D6). Pangram 4.1: 0.0090%, that is 70 of 781,981 English web texts (D7). No independent reproduction of Turnitin's document-level figure was found (N) |
| D8 | M, not peer-reviewed | 1,992 pre-2020 human passages with no student or non-native writing, thresholds tuned on the same corpus: Pangram FPR 0.0000–0.0075 by genre, GPTZero 0.0071 |
| D10, D13 | M; ombudsman | Significantly more Reddit posts by likely-autistic writers were flagged (D10, abstract only). The UK OIA faulted a provider that "did not consider whether Turnitin's AI detection might be less reliable for non-native English speakers" (D13) |
| D11, D12 | Institutions | Vanderbilt disabled the detector in 2023; its "around 750" figure is arithmetic on the vendor's 1% claim. Waterloo discontinued it in September 2025, citing reliability, bias against non-native writers, internal tests and cost |
| D14, L3 | Regulator, standards | S: detectors "perform little better than chance when given short texts", and classify non-native writers' text as AI more often (D14 §3.2.2.4). S: "forensic detection mechanisms were not deemed mature enough to comply with the quality requirements set in Article 50(2)" (L3 Measure 2.2) |
| W4, D4 | M, theory and attacks | The best possible AUROC is bounded by ½ + TV − TV²/2 (W4 Theorem 1). Homoglyphs cost one commercial detector 75.7 points (D4 Table 6) |

**Recommendation: never.** Close the question as a negative result (proposed AIO.6). An unkeyed classifier has no key, no denominator a user can check, and a measured bias against identifiable groups of people (D1, D10, D13, D14). Its output is a guess about a person's writing, not a fact about the bytes. It would also contradict Traceweave's stated purpose, which is evidence anyone can re-run under a declared configuration. Vendor figures cannot be reproduced without the vendor's model. The strongest counter-evidence, very low vendor-reported FPRs (D7) with one partial independent check (D8), covers corpora with no student or non-native writing, which are the groups at risk. What would change this answer: an open, pinned classifier with a frozen threshold and an independent held-out FPR, with its denominator, on student and non-native corpora. None exists in the sources read.

## 6. Design options

| Option | What it would claim | What it must never claim | Cost and exposure | Verdict |
| --- | --- | --- | --- | --- |
| **(a) Report-only reading of signed C2PA metadata** | "A C2PA manifest in this file, signed by key K (trusted or not under your list), asserts action A and digital source type D." | That the file *is* AI-made or human-made; anything about a stripped file; anything about pasted text | Offline, free. Already scoped in the [C2PA mapping](../drafts/c2pa-mapping.md); `digitalSourceType` is "unmapped" there today | **Keep in the C2PA track.** For text it covers only containerised text, such as OpenAI's PDFs (O4). Add a read-only row once C2PA.2 passes; no new gate here beyond AIO.2 |
| **(b) Optional online adapter to a provider detector** | "Provider P's detector D, asked by X at time T about the bytes with SHA-256 H, returned R", stored with P's own signed result when one is offered (L3 Sub-measure 2.1.2) | Authorship, ownership, originality, human origin, "AI-generated" as a property of the text, or anything about a person. Never mixed into a comparison report, a match outcome, a score or a registration | Sends the full text to P. Needs approved access, an account (A5) and terms that allow storing and showing results (N today). Off by default, per call, explicit consent; never automatic | **Specify only** (AIO.5). Build nothing until AIO.4 and AIO.7 |
| **(c) Do nothing for text, and document why** | Nothing | — | None | **Do now**: this note, plus a one-paragraph limit in the text profile's limits section when TXT.7 is written |

**Draft shape of the (b) record (for AIO.5; not a schema).** `traceweave-provider-signal-draft-1`, a standalone JSON document:
- `subject`: `{sha256, length}` of the **exact bytes** submitted, the same rule as registration §4.1;
- `provider` and `detector`: an identifier and the URL or ID the provider gives (L3 Sub-measure 2.1.2);
- `signalKind`: `watermark` or `metadata` (L3 Measure 2.3 requires results to say which);
- `result`: `present`, `absent` or `inconclusive`, mapped from the provider's own result strings, with the raw string kept verbatim;
- `providerAttestation`: the provider's signed result bytes, if offered, kept unmodified;
- `checkedBy`: who asked, as a claim;
- `claimedCheckedAt`: a claimed time. The only trusted time is the one inside `providerAttestation`;
- `renderedText`: the §7 sentences, generated from a closed template, never free text.

**Separation rules** (each a negative vector under AIO.5):
- a comparison report containing a provider-signal key is rejected;
- a registration predicate containing one is rejected (it already is: `statement-shape`);
- a provider-signal record whose subject was computed from folded or skeleton values, or from anything other than the exact bytes, is rejected;
- a `present` or `absent` result without a provider and detector identifier is rejected;
- `unknown` is the value when no check was made. It is never written as `absent`.

## 7. Claims discipline

**Sentences a tool may show.** They are modelled on A1, O1, O3 and G9. `{P}` is the provider and `{D}` the detector.

- **Present:** "{P}'s detector {D} reported a {P} watermark in the exact bytes checked. In {P}'s own words, this means {P}'s system was likely involved with this content at some point, for example by writing, editing or translating it. It does not show who wrote the content, how much of it the system produced, or who owns it."
- **Absent:** "{P}'s detector {D} did not report a {P} watermark in the exact bytes checked. This is not evidence that a person wrote the content. It may come from another system or an older model, or it may have been edited, translated, shortened or mixed with other text."
- **Inconclusive:** "{P}'s detector {D} could not reach a result for the exact bytes checked, for example because the text is too short. Nothing follows from this result."
- **Unknown (the default):** "No provider signal was checked for this content."
- **Added for every text result:** "Only {P}'s system can be detected by {P}'s detector, and only {P} can recompute this result."
- **Added for code, and for text under 200 tokens:** "Providers mark code and short text weakly or not at all (and are not required to: EU Guidelines C(2026) 7702, point 68; Code of Practice glossary). For this content, neither result carries useful information."
- **Added for C2PA:** "This describes what the signer of the manifest asserts. A file without a manifest says nothing about how it was made."

**Never shown** (closed list for the AIO.1 checker): "AI-generated" or "human-written" as a verdict; "authentic"; "original"; "plagiarised"; "cheated"; "authored by"; any percentage or likelihood that a text is AI-written; any sentence with a person, account or author as its subject; any combination of a provider signal with a match result in one sentence.

**Flag: accusation risk.** A provider signal attached to a person's text is, in practice, an accusation. Spoofing is shown on the scheme family (W5, W13). Classifier false positives fall disproportionately on non-native and autistic writers (D1, D10). An ombudsman has already faulted reliance on a detector against a non-native student (D13). A tool must therefore never produce a provider-signal result about content the user did not create or does not have the right to submit. It must never present one as a finding about a person. Any education, employment or disciplinary use is out of scope, and the tool should say so on the record (I; no operator published a prohibited-use list, N).

## 8. Proposed roadmap gates (AIO track; ROADMAP.md is not changed here)

| ID | Type | Verifiable criterion | Owner |
| --- | --- | --- | --- |
| AIO.0 | O | Owner accepts or amends the scope: "Traceweave reports provider signals only as separate, off-by-default records; it never infers AI or human origin of text." Prerequisite of AIO.4 and AIO.5 | S |
| AIO.1 | E | The §7 sentences and the closed never-shown list are committed as fixtures, with a checker. Every rendered provider-signal or C2PA-origin sentence equals a template instance. The checker rejects each never-shown phrase in at least 1 negative vector per phrase, with 0 failures | S |
| AIO.2 | E | After C2PA.2 passes: the C2PA reader reports `digitalSourceType` and the actions assertion of a pinned fixture as a signal record with the §7 C2PA sentence. A comparison report built from the same file contains 0 provider-signal keys (a checker counts them) | I |
| AIO.3 | R | Does the text profile's fold reduce detection of a token-keyed watermark? Measured as in §4.1, with the open reference implementation at a pinned commit, an experimenter-chosen key and n = 200 per arm. Each arm reports detections out of 200 and false detections out of 200. **Owner-gated** (model and tokenizer download; confirmation that it is not removal testing). Negative-result is acceptable. Not needed for any design decision (§4.1) | S |
| AIO.4 | O | Owner decides whether any provider detector may be contacted. That includes which provider, whether to apply for access (account creation), and acceptance of its terms after AIO.7. No paid service. Until recorded, no adapter code is merged | S |
| AIO.5 | E | A provider-signal record schema (draft) and the §6 separation rules, with at least 1 positive vector and 1 negative vector per rule. The validator rejects every negative vector. Registration-record and comparison-report validators reject a record embedded in them | S |
| AIO.6 | R | "Should Traceweave include an unkeyed AI-text classifier?" Closes **negative-result** when a non-author confirms §5 against D1–D4, D8, D14 and L3 Measure 2.2. It reopens only if an open, pinned classifier publishes an independent held-out FPR, with its denominator, on student and non-native corpora | S |
| AIO.7 | E | For each provider named in AIO.4: a terms record pinned by date and URL. It answers what content is sent, retention, whether results may be stored and shown to third parties, and prohibited uses, each with a quote or "not stated". Any "not stated" on storage or display blocks the adapter for that provider. Today all four answers are N for Anthropic, and N or partial for OpenAI (O3, O4) | S |
| AIO.8 | E | Watch item, rechecked on or after 2 February 2027: whether any of the three operators publishes an interoperable or locally executable text detection method (L3 Measure 3.4(c); L6 point 76) or open-sources its scheme (O1). Each recheck records a dated row: "available offline: yes/no" per operator, with a URL | S |

**Owner decisions needed:** AIO.0 (scope wording); AIO.3 (download, and the removal-rule boundary); AIO.4 (any contact with a provider, any account, any application form); confirmation that no paid service is used, now or later. Everything else can proceed without the owner.

## 9. Images, audio and video (pointer only)

This lane does not re-review media. The relevant work already exists:
- **Signed metadata:** the [C2PA mapping draft](../drafts/c2pa-mapping.md), C2PA.1–C2PA.3. `digitalSourceType` and the actions assertions are listed as "unmapped" there (§1.7). AIO.2 above is the only addition proposed.
- **Embedded marks:** the roadmap finding on `e-img-m-2` ([results recheck](../reviews/image-mark-protocol-review.md#results-recheck-e-img-m-2)): a mark can serve as a finding aid, but not as evidence of origin, because marks transferred between images without the key. Provider marks such as SynthID for images and audio are keyed like text and are checked only through the provider's portal, which requires sign-in (G9, G10). Uploads are deleted after detection, but "a digital signature … of your media" is kept for 24 hours (G9 privacy notice). The same separation and claims rules apply.
- **Fingerprints:** [lane 10](10-evidence-review.md).

## Source ledger

All sources were read on 2026-11-24, read-only. Company pages are living pages, pinned by publication or update date where one is shown; re-read them before relying on them. GitHub sources are pinned by commit. Where a page was read only through a summarising fetch tool, that is said; the load-bearing quotes from A1, O1 and W10 were re-checked verbatim in a second read on the same day.

| ID | Source and version | Sections used |
| --- | --- | --- |
| A1 | Anthropic, ["How Claude's text watermark works"](https://www.anthropic.com/news/claude-text-watermark), published 2026-08-14, updated 2026-09-01 | Method; "What does a watermark actually prove?"; ownership; code; small samples; global scope; no hidden characters; no accuracy figure |
| A2 | Anthropic Help Center, ["How Claude marks AI-generated content"](https://support.claude.com/en/articles/16266773-how-claude-marks-ai-generated-content) ("updated this week", no absolute date) | Model and surface tables; sampling caveat; eligible organisations; results; C2PA file types |
| A3 | Anthropic API docs, [text watermark](https://platform.claude.com/docs/en/build-with-claude/text-watermark) (undated) | No added tokens; no user information; sampling-parameter caveat |
| A4 | Anthropic, [model announcement](https://www.anthropic.com/claude-fable-and-mythos-5-1) (September 2026) | Detection API in private preview; "invisible to anyone who does not have the detection API" |
| A5 | Anthropic, Claude Watermark Detector Access Request Form (Google Form linked from A2; read, not submitted) | Fields; Admin account requirement; no terms stated |
| A6 | Anthropic, [content checker](https://claude.com/check-content) (undated) | "The tool does not check text"; files stay on the device |
| O1 | OpenAI, ["Our approach to EU text provenance rules"](https://openai.com/index/eu-text-provenance/), 2026-10-05 | Scope; API default; access; figures (length, synonyms); "does not prove human authorship"; open-source plan |
| O2 | Li, Wen, Chen, Long, Jain, Joly, Lam, Song, Su, ["textGrain: Entropy-Calibrated Watermarking for Language Model Text"](https://cdn.openai.com/pdf/e9508624-d767-41b6-a26d-e34ca798ada6/textgrain-entropy-calibrated-watermarking-for-language-model-text.pdf), OpenAI technical report, 2026-10-05 | Mechanism; context window; detector needs the secret key; null calibration caveat; no empirical results |
| O3 | OpenAI Help Center, [provenance signals](https://help.openai.com/articles/8912793-provenance-signals-content-credentials-synthid-in-openai-generated-content) ("updated 5 days ago", about 2026-11-19) | Code and short-text limits; "currently free"; data handling; 24-language figures; meaning of results |
| O4 | OpenAI API docs, [content provenance](https://developers.openai.com/api/docs/guides/content-provenance) (undated) | Approved organisations only; Services Agreement; C2PA on images and PDFs |
| O5 | OpenAI, [Content Provenance API form](https://openai.com/form/content-provenance-api/) (read, not submitted) | Eligibility wording |
| O6 | OpenAI, [verify](https://openai.com/verify) (undated) | "does not currently support text verification" |
| G1 | Dathathri et al., ["Scalable watermarking for identifying large language model outputs"](https://www.nature.com/articles/s41586-024-08025-4), *Nature* 634:818–823, 2024-10-23, with its Supplementary Information | Seed from H = 4 tokens and key; tournament sampling (m = 30); scoring needs the key and tokenizer; Fig. 3a (plot readings); Supplementary C.6 / Fig. C3 (paraphrase); production quality experiment; low entropy |
| G3 | [`google-deepmind/synthid-text`](https://github.com/google-deepmind/synthid-text/tree/6452fbb837d0ad4281ccddb94b0af75d219b1a14) at `6452fbb8`, Apache-2.0 and CC BY 4.0 | README (reference implementation, "not intended for production use"; same config needed for detection; Bayesian detector trained per key); `docs/tournament.md`; demo key |
| G4 | Hugging Face [`transformers`](https://github.com/huggingface/transformers/tree/d8f10a82213a3a9db48385aba3a4b57ab535de50) at `d8f10a82` | `SynthIDTextWatermarkingConfig`; `SynthIDTextWatermarkDetector` needs a trained detector and the tokenizer |
| G6 | Google DeepMind, ["Watermarking AI-generated text and video with SynthID"](https://deepmind.google/blog/watermarking-ai-generated-text-and-video-with-synthid/), 2024-05-14 | Factual prompts; rewriting and translation |
| G7 | Google, ["SynthID Detector — a new portal"](https://blog.google/innovation-and-ai/products/google-synthid-ai-content-detector/), 2025-05-20 | Text announced "in the coming weeks" |
| G8 | Google, ["Google expands SynthID Detector"](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/synth-id-ai-content/), 2026-10-07 | Public access for image, video and audio; no text |
| G9 | [synthid.com](https://synthid.com/) portal and `/terms`, strings read from the public JavaScript bundle served on 2026-11-24 | Routes and accepted types (no text); sign-in; additional terms; privacy notice; result wording |
| G10 | Gemini Apps Help, ["Verify AI-generated images, videos, and audio"](https://support.google.com/gemini/answer/16722517) (undated) | Media only; account; quotas; result wording |
| G11 | Google AI Developers Forum, [thread 177241](https://discuss.ai.google.dev/t/177241), posts 2026-08-05 to 2026-11-16 (Google-affiliated posters; informal) | Post 9: no public text verification; contradictory statements on API coverage |
| W1 | Kirchenbauer et al., ["A Watermark for Large Language Models"](https://arxiv.org/abs/2301.10226v4), ICML 2023, v4 | §2 detection; §4.1 entropy; §7 tokenisation, homoglyph and zero-width attacks and normalisation |
| W2 | Kirchenbauer et al., ["On the Reliability of Watermarks for Large Language Models"](https://arxiv.org/abs/2306.04634v4), ICLR 2024, v4 | Abstract; §4.1–§4.3 |
| W3 | Krishna et al., ["Paraphrasing evades detectors of AI-generated text …"](https://arxiv.org/abs/2303.13408v2), NeurIPS 2023 | Tables 1–2 |
| W4 | Sadasivan et al., ["Can AI-Generated Text be Reliably Detected?"](https://arxiv.org/abs/2303.11156v4), TMLR, v4 | §2 recursive paraphrase; §3 spoofing; §4 Theorem 1 |
| W5 | Jovanović, Staab, Vechev, ["Watermark Stealing in Large Language Models"](https://arxiv.org/abs/2402.19361v2), ICML 2024, v2 | Cost; Tables 2–4 |
| W7 | He et al., ["Can Watermarks Survive Translation?"](https://arxiv.org/abs/2402.14007v2), ACL 2024, v2 | §4.2 |
| W8 | Lee et al., ["Who Wrote this Code? Watermarking for Code Generation"](https://arxiv.org/abs/2305.15060v4), ACL 2024, v4 | Table 1; §6.4 renaming |
| W9 | Suresh et al., ["Is the Watermarking of LLM-Generated Code Robust?"](https://arxiv.org/abs/2403.17983v4), v4 | Table 2 |
| W10 | Liang et al., ["Watermark under Fire" (WaterPark)](https://arxiv.org/html/2411.13425v4), v4 | §4.1 metric (TPR at FPR 1%); §4.2 setting (Qwen2.5-14B-Instruct); Table 2 SynthID and TGRL rows (re-checked verbatim) |
| W11 | ["Robustness Assessment and Enhancement of Text Watermarking for Google's SynthID"](https://arxiv.org/abs/2508.20228v2), v2 | Tables I–V (read through a summarising tool) |
| W12 | Omidi, Dong, Wang, ["On Google's SynthID-Text LLM Watermarking System"](https://arxiv.org/abs/2603.03410v2), v2 | §4, Table 1 (summarising tool) |
| W13 | Omidi, Naderloui, Hong, Wang, ["A Unified Attack Framework against Statistical Generative Watermarks"](https://arxiv.org/abs/2610.27653v2), v2 | §7.1, Tables 2–4 (summarising tool) |
| W14 | Nemecek, Chaudhary, Ayday, ["Watermarks Without Verification: AI Text Watermarking After the EU AI Act"](https://arxiv.org/abs/2609.09604v1), v1 | §II–V, Table II |
| W15 | Tamim, Khan, ["AI Watermark Evidence Fails Forensic Readiness"](https://arxiv.org/abs/2607.16010v1), v1 | Abstract and setup (50-token texts) |
| W16 | Zhang et al., ["Character-Level Perturbations Disrupt LLM Watermarks"](https://arxiv.org/abs/2509.09112v1), NDSS 2026 | §IV-A mechanism; Table II |
| W18 | Bhattacharyya, Bonnerjee, ["textGrain watermarking is harder to detect …"](https://arxiv.org/abs/2610.17655v1), v1 | Abstract (theory only) |
| W19 | Gloaguen, Staab, Minchev, Vechev, ["Probing the SynthID-text deployment on Gemini APIs"](https://www.sri.inf.ethz.ch/blog/probing-synthid-gemini-apis), ETH SRI blog, 2026-10-21 | Findings (1)–(3) |
| W20 | Gloaguen et al., ["Black-Box Detection of Language Model Watermarks"](https://arxiv.org/abs/2405.20777v3), ICLR 2025, v3 | Abstract; §5.3 |
| D1 | Liang et al., ["GPT detectors are biased against non-native English writers"](https://pmc.ncbi.nlm.nih.gov/articles/PMC10382961/), *Patterns* 4(7):100779, 2023 (arXiv v3 gives 61.22%) | Results; Figure 1 |
| D2 | OpenAI, ["New AI classifier for indicating AI-written text"](https://openai.com/index/new-ai-classifier-for-indicating-ai-written-text/), 2023-01-31, withdrawal note 2023-07-20 | Figures; withdrawal wording |
| D3 | Weber-Wulff et al., ["Testing of detection tools for AI-generated text"](https://eprints.whiterose.ac.uk/207396/1/s40979-023-00146-z.pdf), *Int. J. Educ. Integr.* 19:26, 2023 | Tables 7 and 13; Discussion; Conclusion |
| D4 | Dugan et al., ["RAID"](https://arxiv.org/abs/2405.07940v2), ACL 2024, v2 | Findings 1–3; Tables 4 and 6; §7 |
| D5 | Turnitin, ["Understanding the false positive rate for sentences …"](https://www.turnitin.co.uk/blog/understanding-the-false-positive-rate-for-sentences-of-our-ai-writing-detection-capability), 2023-06-14 | Document and sentence rates (vendor claim) |
| D6 | GPTZero, [Technology](https://gptzero.me/technology) (undated) | FPR claim (vendor) |
| D7 | Pangram, [accuracy page and model card 4.1](https://www.pangram.com/accuracy), 2026-10-19 | FPR with denominator (vendor) |
| D8 | Jabarian, Imas, ["Artificial Writing and Automated Detection"](https://www.nber.org/system/files/working_papers/w34223/w34223.pdf), NBER WP 34223, 2025-09 | Tables 3 and 6; corpus |
| D10 | Chambers, Kelley, ["The Misclassification of Autistic Writing as AI-Generated"](https://arxiv.org/abs/2607.14729v1), LNCS 15879 (2025) | Abstract only |
| D11 | Vanderbilt University, ["Guidance on AI Detection and Why We're Disabling Turnitin's AI Detector"](https://www.vanderbilt.edu/brightspace/2023/08/16/guidance-on-ai-detection-and-why-were-disabling-turnitins-ai-detector/), 2023-08-16 | Reasons |
| D12 | University of Waterloo, ["Discontinuing use of AI detection functionality in Turnitin"](https://uwaterloo.ca/associate-vice-president-academic/discontinuing-use-ai-detection-functionality-turnitin), September 2025 | Reasons |
| D13 | UK Office of the Independent Adjudicator, case summaries [CS072504](https://www.oiahe.org.uk/resources-and-publications/case-summaries/ai-and-academic-misconduct-cs072504/) and [CS072501](https://www.oiahe.org.uk/resources-and-publications/case-summaries/ai-and-academic-misconduct-cs072501/), July 2025 | Findings |
| D14 | NIST AI 100-4, ["Reducing Risks Posed by Synthetic Content"](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-4.pdf), 2024-11 | §3.2, §3.2.2.4 |
| D15 | Suh et al., ["An Empirical Study on Automatically Detecting AI-Generated Source Code"](https://arxiv.org/html/2411.04299v1), ICSE 2025, v1 | Tables IV–VII |
| L1 | Regulation (EU) 2024/1689, [OJ L 2024/1689, 12.7.2024](https://publications.europa.eu/resource/cellar/dc8116a1-3fe6-11ef-865a-01aa75ed71a1.0006.01/DOC_1) (Publications Office copy; CELEX 32024R1689; EUR-Lex returned empty pages) | Art. 50(2), (4), (5); Recitals 133, 135; Art. 113 |
| L2 | Digital Omnibus on AI, [PE-CONS 30/26](https://data.consilium.europa.eu/doc/document/PE-30-2026-INIT/en/pdf), 18 June 2026 (signed text; OJ L 2026/1744 per the Commission's service desk, not opened) | Art. 1 points (20), (39); Recital 38 |
| L3 | European Commission, [Code of Practice on Transparency of AI-Generated Content](https://ec.europa.eu/newsroom/dae/redirection/document/129555), published 2026-06-10 (no version number in the PDF) | Measures 1.1, 1.1.2, 1.1.3, 1.2; 2.1.1–2.1.4; 2.2; 2.3; 3.2–3.4; Glossary |
| L4 | European Commission, ["Commission publishes Code of Practice on marking and labelling AI-generated content"](https://digital-strategy.ec.europa.eu/en/news/commission-publishes-code-practice-marking-and-labelling-ai-generated-content), 2026-06-10 | Publication date |
| L5 | European Commission, ["Strong backing for Code of Practice …"](https://digital-strategy.ec.europa.eu/en/news/strong-backing-code-practice-transparency-ai-generated-content), last update 2026-11-18 | Signatory list (fetch-tool extraction) |
| L6 | European Commission, [Guidelines on Article 50](https://ec.europa.eu/newsroom/dae/redirection/document/131215), C(2026) 7702 final, 5.11.2026 | Points 60, 63, 68, 70, 75–78, 90–92, 153–154 |

Searched and not found: a separate Anthropic FAQ of 2026-08-15 (the FAQ is part of A1); detector-specific terms, retention rules or prohibited-use lists for Anthropic and OpenAI text detectors; any sample size for the O1 figures; any independent evaluation of the deployed Claude or textGrain watermarks (searches on arXiv and the web for each name with "removal", "spoofing", "stealing", "evaluation", October–November 2026); any paper measuring NFKC alone on clean watermarked text; any Google statement on code surfaces.

## Validation and handoff

Run on the tree that adds this file, 2026-11-24: `tools/validate.py` PASS; `tools/validate.py --links-all` PASS (local Markdown links in every Markdown file); `tools/check_hygiene.py` PASS. External URLs were read on 2026-11-24 as recorded in the ledger; they were not re-requested by a link checker. **Needs the owner:** AIO.0, AIO.3 and AIO.4 (§8). Any contact with a provider detector, account or form; any download; anything paid.
