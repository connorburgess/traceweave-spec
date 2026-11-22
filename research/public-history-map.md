# Public history map

This history was produced from the local branch `roadmap-v2` so that it can be published. The local branch keeps its original history, and the reviews and gate records in this repository cite its commit ids. Every commit between `origin/main` and the source tip was recreated with the same order, authors, author and committer dates, parents (mapped) and file modes. Only text content changed, by the fixed substitutions below, and the rewrite tool's own earlier versions were dropped (see below).

**The text of this repository, including its reviews and gate records, cites the old commit ids.** They do not exist in this history. Use the table below to translate an old id to the new id.

**Scope of this map.** It is a file in the source history, so it can only list the commits that come before the commit that adds it; that commit and later ones are not listed, and their new ids follow from rerunning the rewrite. The rewrite is append-stable: new source commits never change the ids of earlier public commits, so each published tip is an ancestor of the next one. Regenerating the map is a new source commit, and the map is not an input to the ids it lists.

## Reproducing

`python3 tools/public_history_scrub.py rewrite --branch NAME --source <source commit>` with the private rules file. The rules are not in this repository in any form. Rules file SHA-256: `974e52bf34051e1a0d5a11f33f68ef316a0c8c01dbbad61b61932cf6a1e067c0`.

## What was substituted, by category

The same fixed rules were applied to every text blob in every commit and to every commit message. The removed strings are not reproduced here. Counts are substitutions made, each counted once per distinct file version (and once per commit message).

| Category | What was replaced | Substitutions |
| --- | --- | --- |
| quotes | Verbatim quoted words of the owner, replaced by a neutral paraphrase of what the owner approved or delegated, with the date kept | 45 |
| privterms | A list of search terms specific to the private pilot applications, replaced by a generic phrase | 8 |
| coordination | Conversation thread identifiers and wording that only made sense inside the internal coordination setup; the technical content is kept and the role is called "the coordinator" | 46 |
| tooling | A sentence that named the supervision tooling as internal tooling | 17 |
| abspath | Absolute paths under the local home directory, replaced by repository-relative paths or placeholders; the image-run transcript carries a note that paths were replaced after the run | 44 |
| scratch | Scratch-directory paths of the agent harness, and the harness entry in the ignore file | 11 |

Unchanged on purpose: the git author identity (already public on `origin/main`), the GitHub repository URL, public third-party names, and every `.json` and `.jsonl` file (vectors, configurations, schemas, results, manifests). A substitution that would touch one of those files stops the rewrite; none did.

## Dropped file versions and commits

Every version of `tools/public_history_scrub.py` that held the rules was removed from every rewritten tree: 5 versions. A commit whose tree became equal to its parent's tree was dropped, and its old id maps to the id of its nearest surviving ancestor (listed below as `dropped`).

## Verification of the commits listed here

`python3 tools/public_history_scrub.py scan` over the 96 commits and 986 objects of the rewritten history before the map commit, in plain text, ROT13 and base64 decodings, over blobs, paths, messages and author and committer headers:

| Category | Hits |
| --- | --- |
| quotes | 0 |
| privterms | 0 |
| thread ids | 0 |
| coordination text | 0 |
| tooling name | 0 |
| absolute paths and user name | 0 |
| scratch paths | 0 |
| e-mail addresses | 0 |

## Commit ids cited by the roadmap and the work queue

| Cited as | Old id | New id |
| --- | --- | --- |
| `b13cb68` | `b13cb6877711` | `ea027ebe5a68` |
| `215145b` | `215145baaa79` | `7fb3d1ddb749` |
| `3a640b3` | `3a640b3af721` | `d0c959799be2` |
| `9c03c95` | `9c03c95103bf` | `bf6b7b9acc56` |
| `15a4b2d` | `15a4b2d93010` | `88128d114f26` |
| `2fa2b58` | `2fa2b58f14c7` | `8c6980ee0787` |
| `de9a5b7` | `de9a5b7131d9` | `863bca247a43` |
| `4d0288f` | `4d0288ffe05a` | `5e29802eb91f` |
| `95fb157` | `95fb157ec5bb` | `aebb49f51946` |
| `0bc4e23` | `0bc4e23432ac` | `0766f3a39235` |
| `6f39e50` | `6f39e50f3302` | `b47b8945b9d6` |
| `0c7523c` | `0c7523c23613` | `52049a8a0591` |
| `dbd109b` | `dbd109bce3cf` | `44179c47fe77` |
| `835f6c0` | `835f6c0df461` | `3ced88b0f2fc` |
| `ec0cf67` | `ec0cf67ca3c8` | `ee083b345a31` |
| `6f39e50f33026c9f1d9526c2a566d6a447219667` | `6f39e50f3302` | `b47b8945b9d6` |

Ancestry was checked for all 120 pairs of these 16 ids in both directions: the relation is the same before and after the rewrite (0 mismatches).

## All commits, oldest first

| # | Old id | New id | State | Subject |
| --- | --- | --- | --- | --- |
| 1 | `4d0288ffe05a` | `5e29802eb91f` | kept | Add fragment and transplant carrier experiments for Go and Rust |
| 2 | `0bc4e23432ac` | `0766f3a39235` | kept | Add Go/Rust signing interoperability and policy experiments |
| 3 | `95fb157ec5bb` | `aebb49f51946` | kept | Add public-code census plan, Go and Rust census harnesses and results |
| 4 | `80895af2eb4d` | `31d058beba69` | kept | Add lane 06-08 prompts, evidence reviews and report audits |
| 5 | `cb5cf78521fa` | `202f51c861ee` | kept | Add work queue and update status text for experimental checkpoints |
| 6 | `6f75d55eabfa` | `0fe249355375` | kept | Add reviewed drafts: roadmap v2, repository plan, checkpoint, use-case verification plans, extraction and catalogue/report contracts |
| 7 | `e16863f6c547` | `6c25dc16821e` | kept | Adopt roadmap v2 as ROADMAP.md |
| 8 | `fb50eac947bb` | `7e9ea60ef4e6` | kept | Adopt the implementation repository plan as docs/implementation-repo-plan.md |
| 9 | `53483b47fcb6` | `abf4fdf2387c` | kept | Adopt the lane 06-08 reconciliation checkpoint as a research checkpoint |
| 10 | `b13cb6877711` | `ea027ebe5a68` | kept | Merge verification plans into the use-case and implementation-pattern documents |
| 11 | `9f780418ffcf` | `9ac3026f1d53` | kept | Move contract review files to research/reviews and fix cross-links |
| 12 | `00815d55320f` | `55adffd024f8` | kept | Update the work queue and research indexes to gate IDs, current assignments and the loop rule |
| 13 | `80de67481761` | `f26d9519d6d6` | kept | Update gate statuses for evidence now committed |
| 14 | `85d8d7b2deb4` | `a2b1cec3750d` | kept | Add adoption check to the roadmap v2 review |
| 15 | `215145baaa79` | `7fb3d1ddb749` | kept | Make the UC-6, W-1, H-1, H-3 and H-5 verification plans decidable |
| 16 | `e821bd8343c4` | `7f704b2e41d9` | kept | Apply roadmap adoption-check fixes |
| 17 | `3a640b3af721` | `d0c959799be2` | kept | Add second M0.1 recount to the roadmap v2 review |
| 18 | `7fa20fe6cff7` | `e0ce1a086358` | kept | Mark M0.1 met after the second non-author recount |
| 19 | `c57fc2262302` | `6d4d0421c162` | kept | Add text and image profile research briefs for lanes 09 and 10 |
| 20 | `e0427d26a48a` | `a906d478902d` | kept | Add lane 10 still-image evidence review |
| 21 | `2fa2b58f14c7` | `8c6980ee0787` | kept | Rule on extraction contract questions from the two-implementation cross-check |
| 22 | `1c085b3fe522` | `eeb903d7aaa3` | kept | Add lane 09 text and document profile evidence review |
| 23 | `9625cd6e8ceb` | `51feb6ea296c` | kept | Record owner override for TS, image and text profiles; add text gates and fingerprint-first image gates |
| 24 | `c09634a7ca78` | `fb135cecd610` | kept | Add lane 09 report audit and post-audit note |
| 25 | `3dd35238752e` | `7ece02c01128` | kept | Add lane 10 report audit and post-audit note |
| 26 | `fb09039ef229` | `dd4d1457228f` | kept | Add draft TypeScript/JavaScript token profile with hand-derived vectors, checker and TypeScript cross-check |
| 27 | `074fd9c6b7bb` | `3e65170a956c` | kept | Specify the canonical extraction record and catalogue building from records |
| 28 | `5c210b8fdc17` | `093a161761dc` | kept | Add independent review of the draft TypeScript/JavaScript token profile |
| 29 | `38e8b2597b29` | `ef3799242281` | kept | Name the extraction configuration in every record vector |
| 30 | `bdbc19dbe3bb` | `15c529844de6` | kept | Revise TypeScript profile to draft-2 after review: stage ts-tokens, drop ; from normalized, complete exprEnd departures, pin rule choices with vectors and wrong-lexer self-test |
| 31 | `6fbf11b2db24` | `f7d772662f4a` | kept | Draft text extraction profile with hand-derived vectors, checker and cross-check (TXT.1, TXT.2) |
| 32 | `c81be10bc817` | `f329c5760aaa` | kept | Allow profiles to exclude tokens from the normalized stream |
| 33 | `47147356a817` | `45c031196a05` | kept | Add draft still-image fingerprint profile and frozen E-IMG-F protocol with dry-tested harness |
| 34 | `d955ee658817` | `108e61d3d115` | kept | Align TypeScript profile with contract OD-23: declare normalizedExclusions, verify tokenIndices placement, close TSOD-13 |
| 35 | `45e426120ac4` | `bc4cd2a2a638` | kept | Align the record and catalogue with normalized-stream exclusions |
| 36 | `b622509b868d` | `149d1d276f13` | kept | Add confirmation pass for TypeScript profile draft-2 to its review |
| 37 | `5d610d3585cc` | `26bcbc85da98` | kept | Extend profile versioning to channel-byte changes and state locality per channel stream |
| 38 | `c6e8f2a03e4c` | `abe6b81c48de` | kept | Review text extraction profile draft-1: clean-room reproduction, wrong-implementation runs, Markdown masks, contract fit and insertion evasion |
| 39 | `5d69b484c7d9` | `1ce92da55358` | kept | Freeze ts-tokens draft-2 for stage-1 implementation after confirmation pass: CR/LS/PS prefix vector and wrong lexer, stale text fixes, JSX-in-.js deferral rule, freeze record |
| 40 | `bd7f0944ef96` | `402ab112f550` | kept | Add non-author review of the image fingerprint profile and E-IMG-F protocol |
| 41 | `f8e24644c7b7` | `b8d0a5e65ce7` | kept | Correct periodic-insertion removal claim in lane 09 files |
| 42 | `fe14421554a8` | `0cf430723234` | kept | Reword IMGF.2 and IMGF.4 from the image protocol review; record the e-img-f-2 design choice |
| 43 | `0a3ee6c604bc` | `236aba469286` | kept | Rewrite IMGF.3 and IMGF.4 for design e-img-f-2; add owner-gated IMGF.6 |
| 44 | `e239cc20d09b` | `5e744aec9e50` | kept | Revise text profile after clean-room review: text-plain draft-1 frozen, text-markdown draft-2 (list-item fences, BOM before front matter), 8 vectors, wrong-implementation self-test, provisional record layout |
| 45 | `51ba163e6156` | `b6f321af3071` | kept | Define records, catalogues, comparison and reports over declared channel lists |
| 46 | `a5ccf59292fc` | `d9774866e527` | kept | Bind extraction channels to the profile's declared channel list |
| 47 | `794f1fe433a9` | `6795cd265388` | kept | Align text profile with catalogue/report contract A3: declared channels exact, folded, skeleton; section 2a record results; 60 canonical text-plain records with digests; record self-tests (no hash or version change) |
| 48 | `6f39e50f3302` | `b47b8945b9d6` | kept | Freeze E-IMG-F protocol e-img-f-2 (200-image contract check) and profile draft-2 |
| 49 | `835f6c0df461` | `3ced88b0f2fc` | kept | Add e-img-f-2 confirmation pass to the image protocol review |
| 50 | `bc8b234b44eb` | `b4ab83bcbcb2` | kept | Cite protocol V4 of e-img-f-2 in IMGF.2 |
| 51 | `33324f33115f` | `6daf45ee9a9d` | kept | Register text-plain and ts-tokens and validate the text-plain records |
| 52 | `9c03c95103bf` | `bf6b7b9acc56` | kept | Add non-author review of the traceweave merge-i1 integration |
| 53 | `0c7523c23613` | `52049a8a0591` | kept | Record e-img-f-2 measured run: validity V1, V2, V4, V5 pass, V3 not tested; counts without pass line |
| 54 | `dbd109bce3cf` | `44179c47fe77` | kept | Add e-img-f-2 results recheck to the image protocol review |
| 55 | `ec0cf67ca3c8` | `ee083b345a31` | kept | Record owner approval of the image experiment; mark IMGF.2-IMGF.4 met from the e-img-f-2 recheck |
| 56 | `15a4b2d93010` | `88128d114f26` | kept | Rule the I2 cross-check questions and bound the comparison |
| 57 | `55e190ac250b` | `02a47093042e` | kept | Rule the behavioural questions and add a conformance checklist |
| 58 | `de9a5b7131d9` | `863bca247a43` | kept | Review implementation merge-i2 at 82b02ab: checks, sabotages, clean-room and differential runs, M2.8, privacy, gate readings |
| 59 | `cd229a503cc7` | `291cab48cce5` | kept | Rule the behavioural follow-up questions and extend the checklist |
| 60 | `10c1b889bb3b` | `31637ceb36a9` | kept | Update M1/M2 gate statuses from the I1 and I2 reviews; mark M2.5 and M2.8 met; record implementation-track status and current assignments |
| 61 | `fae2db3c75e4` | `b3375996eb9f` | kept | Require a verified build-time stamp for provenance commits |
| 62 | `067be17e3261` | `1e39a6adc947` | kept | Draft the M3 evaluation protocol and a proposed Go/Rust corpus manifest with its checker |
| 63 | `f0da1f0aebdd` | `e33f85e43324` | kept | Fix the fault-injection values shared by both implementations |
| 64 | `b7282bf79aab` | `44daa2b028ac` | kept | Add non-author review of the M3 evaluation protocol and corpus proposal |
| 65 | `14809b8f9b84` | `016d7667b16f` | kept | Revise the M3 evaluation protocol to m3-eval-draft-2 after the non-author review |
| 66 | `1df11d3e2311` | `a47cc329c087` | kept | Add m3-eval-draft-2 confirmation pass to the evaluation protocol review |
| 67 | `ffbea0da3a32` | `5ee076849f9e` | kept | Revise the M3 evaluation protocol to m3-eval-draft-3 after the confirmation pass |
| 68 | `fad444d220e3` | `a54685b97d40` | kept | Confirm implementation post-i2 at f955fc1: offline check, checklist items, M2.4 rebuild, provenance forging routes |
| 69 | `33e12f8166be` | `6116ab74f4c4` | kept | Define a clean build by content for provenance commits |
| 70 | `f9a71a6643e6` | `7c3e69e8c5b4` | kept | Confirm post-i2 at c05fe64: P1/P2 closed, forgery self-test, new Go HEAD-race route |
| 71 | `3319a3c5d016` | `657d1f44a28d` | kept | Resolve the provenance commit once per build |
| 72 | `7b7eb6413424` | `788274d81a2e` | kept | Record the owner decisions of 2026-11-23; mark M3.0, M2.10 and M2.11 met |
| 73 | `04849f9328e0` | `ae9e7ea84d97` | kept | Record the M3 owner decisions in m3-eval-draft-4 and add the harness implementer brief |
| 74 | `c512550ffd57` | `db8e60dbcae7` | kept | Promote the extraction contract and vectors: move to spec/extraction.md and test-vectors/extraction/ |
| 75 | `cb2dae9c76a8` | `10db6e20b314` | kept | Promote the catalogue/report contract and matching vectors: move to spec/catalogue-report.md, test-vectors/matching/ and schemas/ |
| 76 | `d86a8b7ac74a` | `d00671e8d72a` | kept | Promote the TypeScript and text stage-1 profiles and their vectors |
| 77 | `1d880cab61cb` | `bdff68e692e9` | kept | Mark the promoted documents with their normative status |
| 78 | `b9d7839c9c92` | `d2a1fcb695b6` | kept | Update references to the promoted paths; validate the promoted schemas, vectors and checkers |
| 79 | `f42156dc5ba8` | `e397e59fa78e` | kept | Add the promotion map with SHA-256 digests before and after for every moved file |
| 80 | `3d2b069f073b` | `4cef0fd06b38` | kept | Add non-author check of the promotion and push hygiene for roadmap-v2 |
| 81 | `beb8b10886d2` | `1e8136cbb1ce` | kept | Restore the literal code-span example in the text profile |
| 82 | `b262ec44ca9d` | `15e256fcbb5c` | kept | Add the Unicode License v3 notice for the two Unicode-derived tables |
| 83 | `51871d4b393c` | `1206af664d8b` | kept | Correct the conformance level-4 wording, the approval scope and the OD-C5 status; point the image README at the results |
| 84 | `4d5d20303d96` | `1206af664d8b` | dropped | Add the deterministic scrub tool used to prepare a publishable history |
| 85 | `6aaa983f95f3` | `1206af664d8b` | dropped | Replace verbatim owner quotes with neutral paraphrase |
| 86 | `d6183608dc31` | `1206af664d8b` | dropped | Remove thread identifiers and internal coordination text |
| 87 | `27b6cb73b287` | `1206af664d8b` | dropped | Remove the supervision tooling sentence from the review |
| 88 | `6a18e9d4ee62` | `1206af664d8b` | dropped | Replace absolute local paths with repository-relative paths and placeholders |
| 89 | `8aef3c9a1346` | `1206af664d8b` | dropped | Remove agent-harness scratch paths |
| 90 | `6a9b81ece2db` | `1206af664d8b` | dropped | Fix the escaping of the rule tables in the scrub tool |
| 91 | `95f0ad0b1145` | `1206af664d8b` | dropped | Replace the remaining verbatim owner quotes with neutral paraphrase |
| 92 | `f29346c31ffd` | `1206af664d8b` | dropped | Remove search terms specific to the private pilot applications |
| 93 | `1a1392444d70` | `1206af664d8b` | dropped | Remove the remaining internal coordination text and thread identifiers |
| 94 | `9d799c777e9a` | `1206af664d8b` | dropped | Remove the supervision tooling name used as internal tooling |
| 95 | `645beb4b1f64` | `28fa469c19b1` | kept | Remove agent-harness scratch paths and the harness ignore entry |
| 96 | `584cbda1c130` | `28fa469c19b1` | dropped | Scrub the remaining tip residuals; refine the scanner |
| 97 | `1d1f73f697f6` | `28fa469c19b1` | dropped | Replace the last quoted owner reply in the image experiment record |
| 98 | `bcd649eceaae` | `9690537b5550` | kept | Confirm post-i2 at e5933a3: flips closed; private export edited mid-build forges in both lanes |
| 99 | `a0a8a1e60479` | `9690537b5550` | dropped | Replace a scratch path in the post-i2 confirmation |
| 100 | `968e9f075fc6` | `731d565648c0` | kept | Scrub tool: optionally write the old-to-new commit id map |
| 101 | `9e24e4d3a2cc` | `2f1234fa70fb` | kept | Remove the blank line left at the end of .gitignore; scrub rule no longer leaves one |
| 102 | `86562e9f1802` | `55d003815579` | kept | Make the validation workflow reproducible for the first push |
| 103 | `3346d5549a41` | `2b04b0c3bb6a` | kept | Make the matching checker run on Python 3.11 |
| 104 | `d32b25c1709d` | `c7efb8b1c6b2` | kept | Lane 11: audit the Perplexity and Google design-feedback reports and the third opinion; add the lane 11 brief |
| 105 | `f651658e43a7` | `50d093d6e4df` | kept | Add public branch verification to the promotion and push review |
| 106 | `c8fcaa3e6ac6` | `ff732437ad26` | kept | Record the 2026-11-23 owner decision opening the image mark study and C2PA mapping; update owner-blocked list and work queue |
| 107 | `e2a64b1e827b` | `cfb7017e20b9` | kept | Make the scrub tool generic: rules live in a private file outside the repository |
| 108 | `02e3ebba68d5` | `b61ad707bab0` | kept | Revise the M3 evaluation protocol to m3-eval-draft-5 after the lane 11 audit |
| 109 | `dbb157921388` | `8ce35aa2292c` | kept | Scrub tool: allow the ROT13 form of an allowed address; word-boundary thread-id check |
| 110 | `5c5fc5cea1b4` | `d1fe0ac1977f` | kept | Scrub tool: scan base64 payloads in one batch per blob |
