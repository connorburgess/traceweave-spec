# Public history map

This history was produced from the local branch `publication-source/pdq-curated-20261126-5a212f1c` so that it can be published. The local branch keeps its original history, and the reviews and gate records in this repository cite its commit ids. Every commit between `origin/main` and the source tip was recreated with the same order, authors, author and committer dates, parents (mapped) and file modes. Only text content changed, by the fixed substitutions below, and the rewrite tool's own earlier versions were dropped (see below).

**The text of this repository, including its reviews and gate records, cites the old commit ids.** They do not exist in this history. Use the table below to translate an old id to the new id.

**Scope of this map.** It is a file in the source history, so it can only list the commits that come before the commit that adds it; that commit and later ones are not listed, and their new ids follow from rerunning the rewrite. The rewrite is append-stable: new source commits never change the ids of earlier public commits, so each published tip is an ancestor of the next one. Regenerating the map is a new source commit, and the map is not an input to the ids it lists.

## Curated publication-source boundary

This replay uses publication-source lineage based at `ec2a4ddcfd0d4894ce369e6687bed67f2e023f6f`, mapped exactly to published `a589a1bbb3d00009438376d2df40ae923317cacb`. It includes curated package `d6c09e05829ccd95159ea9e19ff7f71f8c239f4e` and independent review `0bd15f8e6cb3999045786c4977a67cbb9ed52849`. See the [durable source workflow](../docs/publication-source-workflow.md) and [independent review](reviews/pdq-cpp-curated-source-review.md).

Private `roadmap-v2` at `7a0fd5ac64a50eb5c3ef6d6f955c21e4f11cc41c` is intentionally not this replay's source. Its unpublished raw-bearing history, including original package `5e9eebdd2e365ed62911b25dc85c297f8b4ab5a1` and review `bab7b0f75353156daa0203b5c27fa66c88804d43`, is outside this map and has no translation claimed here. The raw object remains privately retained unchanged; it is omitted entirely from publication-source history. Historical private identifiers in the curated summary identify absent artifacts, not public proof. Published tree/subset consistency does not reproduce commit-to-root binding.

## Reproducing

`python3 tools/public_history_scrub.py rewrite --branch NAME --source <source commit>` with the private rules file. The rules are not in this repository in any form. Rules file SHA-256: `362950c0c62ec6549d270070b03d0b632b516423563163d1f44695d1c654ac2b`.

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

Every version of `tools/public_history_scrub.py` that held the rules was removed from every rewritten tree: 5 versions. A commit whose tree became equal to its parent's tree was dropped, and its old id maps to the id of its nearest surviving ancestor. 14 source commits were dropped: 3 changed the rewrite tool (their tool versions are among those removed), and 11 were scrub commits (removing or paraphrasing text) whose changes the rewrite already applies to every earlier version, so they became empty. The state column marks each as `dropped (tool)` or `dropped (empty)`.

## Verification of the commits listed here

`python3 tools/public_history_scrub.py scan` over the 242 commits and 3570 objects of the rewritten history before the map commit, in plain text, ROT13 and base64 decodings, over blobs, paths, messages and author and committer headers:

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
| `58c25a9` | `58c25a9e13a9` | `62294bdd0ae5` |
| `b13cb68` | `b13cb6877711` | `ea027ebe5a68` |
| `215145b` | `215145baaa79` | `7fb3d1ddb749` |
| `3a640b3` | `3a640b3af721` | `d0c959799be2` |
| `3b6e9f3` | `3b6e9f3f6922` | `1ce99d635839` |
| `f84343b` | `f84343b19e68` | `6807cb9d96ca` |
| `be51871` | `be51871217c3` | `c8b053ae1fb4` |
| `34eea25` | `34eea2587916` | `da719106e7a9` |
| `a625c97` | `a625c97d17b7` | `b4b5471f4ff5` |
| `6f787a0` | `6f787a0630eb` | `5a3465ecb793` |
| `a77c657` | `a77c65745a3d` | `5ddc71120540` |
| `28f5b6d` | `28f5b6d88351` | `2211862b7172` |
| `16ebc94` | `16ebc94f5c9a` | `4fd94d44cba9` |
| `c512550` | `c512550ffd57` | `db8e60dbcae7` |
| `f42156d` | `f42156dc5ba8` | `e397e59fa78e` |
| `de9a5b7` | `de9a5b7131d9` | `863bca247a43` |
| `4d0288f` | `4d0288ffe05a` | `5e29802eb91f` |
| `95fb157` | `95fb157ec5bb` | `aebb49f51946` |
| `0bc4e23` | `0bc4e23432ac` | `0766f3a39235` |
| `5facdd4` | `5facdd4e9274` | `54d49bf9843c` |
| `51033c9` | `51033c911163` | `688e37093883` |
| `1b51807` | `1b51807301f0` | `9696d4569eba` |
| `07c98cad440e3797d0ddc0c4b8c2bfb06a36dbd7` | `07c98cad440e` | `185aaf367a92` |
| `e7e7149` | `e7e714987ace` | `037aa20d6fb6` |
| `1df04f9` | `1df04f922161` | `856016afeb17` |
| `07c98ca` | `07c98cad440e` | `185aaf367a92` |
| `6ded8a3` | `6ded8a3d6923` | `4cb75f5f3c56` |
| `24bb4b8483dc86966cb7c8277130bb816b0c6b3f` | `24bb4b8483dc` | `f024316078fd` |
| `24bb4b8` | `24bb4b8483dc` | `f024316078fd` |
| `284ce4e` | `284ce4e1f3b2` | `8c703bbcff24` |
| `409d486` | `409d486cc02c` | `dec460e84334` |
| `4fa00c7` | `4fa00c7d00eb` | `f4bd1095b048` |
| `12a1459` | `12a1459c62e3` | `3d3a5e7ed0f6` |
| `73b6d5c` | `73b6d5cfd116` | `a68bfd46ad0f` |
| `ca8fb4f` | `ca8fb4f51df7` | `a8445ef0d431` |
| `db2848c` | `db2848c1e8ec` | `b210a142d331` |
| `0db8b44` | `0db8b44097b6` | `c87655a88151` |
| `3b5f24e` | `3b5f24ecd756` | `548394878bff` |
| `73b6d5cfd116a1d13a2463638e4e2448280db958` | `73b6d5cfd116` | `a68bfd46ad0f` |
| `db2848c1e8ec7c8465c066f5bff26863a803d440` | `db2848c1e8ec` | `b210a142d331` |
| `b3a3a2c` | `b3a3a2c99b52` | `1a4cbea6c987` |
| `5d0a863` | `5d0a8630d4a5` | `6476a51e6de2` |
| `6f39e50` | `6f39e50f3302` | `b47b8945b9d6` |
| `0c7523c` | `0c7523c23613` | `52049a8a0591` |
| `dbd109b` | `dbd109bce3cf` | `44179c47fe77` |
| `835f6c0` | `835f6c0df461` | `3ced88b0f2fc` |
| `3147237` | `31472373d24c` | `7f1ec2fb48f5` |
| `a78aace` | `a78aace574a6` | `d9c4efa5a883` |
| `d3d4788` | `d3d4788ffe83` | `e95339bc4e48` |
| `d3af1ee` | `d3af1ee07595` | `b91606abb533` |
| `c708b20` | `c708b203165f` | `5de16269a9bf` |
| `76afd60` | `76afd6006786` | `89ad40c9c310` |
| `62b81eb` | `62b81ebf6621` | `3ea5aa2980b0` |
| `9f50798` | `9f50798d8de8` | `f68bacfb8b64` |
| `4fa00c7d00eb24c5a39866b05e8b6aeca27174b2` | `4fa00c7d00eb` | `f4bd1095b048` |
| `12a1459c62e3539e02ef174e0fbf6d909b199eb4` | `12a1459c62e3` | `3d3a5e7ed0f6` |
| `11e975e34720235543ae9a22ff5a199e9be10d56` | `11e975e34720` | `a170a47b8d84` |
| `0075c8f394b31a946d279a358e2c71a47a7f60d9` | `0075c8f394b3` | `639cb855bd1b` |
| `afca82c` | `afca82c41d54` | `d66e4b942c8c` |
| `41628be` | `41628be879a8` | `f396a4133b56` |
| `a4ea8d4` | `a4ea8d46fa7c` | `d61f45c9c203` |
| `0823f1d` | `0823f1d91143` | `cae4883ee992` |
| `c402191` | `c402191166e9` | `f9ced808fa54` |
| `11e975e` | `11e975e34720` | `a170a47b8d84` |
| `631e71e` | `631e71e22994` | `4d9c9173dfde` |
| `7dccedd` | `7dccedd63897` | `a8f6c47798af` |
| `4d4e98d` | `4d4e98d68bef` | `6883ebe512be` |
| `67f7b5d` | `67f7b5dbcec0` | `3a29ca30f228` |
| `284ce4e1f3b2daf9eabd7700cabdc4b10865310d` | `284ce4e1f3b2` | `8c703bbcff24` |
| `6ded8a3d6923b310f6b0abfab2a4037abfc3e467` | `6ded8a3d6923` | `4cb75f5f3c56` |
| `e7e714987aced74569294bfe6aa11a072ed43372` | `e7e714987ace` | `037aa20d6fb6` |
| `7dccedd6389762ea038b4b132a8479436a30f23d` | `7dccedd63897` | `a8f6c47798af` |
| `fce78938e9fd7d80a7ddd2d06686a857bfc458d5` | `fce78938e9fd` | `726b333a2ee0` |
| `fce7893` | `fce78938e9fd` | `726b333a2ee0` |
| `5d0a8630d4a5cd55b1e7501766ab902c66d90c8f` | `5d0a8630d4a5` | `6476a51e6de2` |
| `b3a3a2c99b52f7313a3e6b6a4ae10e5e96846755` | `b3a3a2c99b52` | `1a4cbea6c987` |
| `303b966fe20f03e346b00732f0fd05ed17ede4b9` | `303b966fe20f` | `8517c53c2284` |
| `4c7c61bab7c2faf250401b9ccc3c3d7000021d34` | `4c7c61bab7c2` | `ece5f3bd4e05` |
| `1c8f09a62faabfa2304b14315ee80d1b324304d7` | `1c8f09a62faa` | `e2863bd5a657` |
| `9eab88fe34eb36606c9d958446fda26eb8649b3f` | `9eab88fe34eb` | `182dba97718a` |
| `ca8fb4f51df75250cd82ea4e6a86b0f3e48aa9ae` | `ca8fb4f51df7` | `a8445ef0d431` |
| `631e71e22994dc5a8e16f2f6eee73ed94b1e54cd` | `631e71e22994` | `4d9c9173dfde` |
| `c402191166e9224d54d819433112b8ff68bc579d` | `c402191166e9` | `f9ced808fa54` |
| `303b966` | `303b966fe20f` | `8517c53c2284` |
| `1c8f09a` | `1c8f09a62faa` | `e2863bd5a657` |
| `afca82c41d54d363c28a49fff76a99718e7bb996` | `afca82c41d54` | `d66e4b942c8c` |
| `0823f1d91143` | `0823f1d91143` | `cae4883ee992` |
| `09359ac` | `09359acc2dd5` | `25acdad361ef` |
| `09359acc2dd53022963b1e2046368dff49cf7fe3` | `09359acc2dd5` | `25acdad361ef` |
| `0075c8f` | `0075c8f394b3` | `639cb855bd1b` |
| `ec2a4ddcfd0d4894ce369e6687bed67f2e023f6f` | `ec2a4ddcfd0d` | `a589a1bbb3d0` |
| `aba26b5797c82e53d7190db9f618f287afa8d280` | `aba26b5797c8` | `7e30cb703484` |
| `d6c09e05829ccd95159ea9e19ff7f71f8c239f4e` | `d6c09e05829c` | `3d89d451eb12` |
| `ec2a4dd` | `ec2a4ddcfd0d` | `a589a1bbb3d0` |
| `d6c09e0` | `d6c09e05829c` | `3d89d451eb12` |
| `6f39e50f33026c9f1d9526c2a566d6a447219667` | `6f39e50f3302` | `b47b8945b9d6` |

Ancestry was checked for all 4560 pairs of these 96 ids in both directions: the relation is the same before and after the rewrite (0 mismatches).

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
| 84 | `4d5d20303d96` | `1206af664d8b` | dropped (tool) | Add the deterministic scrub tool used to prepare a publishable history |
| 85 | `6aaa983f95f3` | `1206af664d8b` | dropped (empty) | Replace verbatim owner quotes with neutral paraphrase |
| 86 | `d6183608dc31` | `1206af664d8b` | dropped (empty) | Remove thread identifiers and internal coordination text |
| 87 | `27b6cb73b287` | `1206af664d8b` | dropped (empty) | Remove the supervision tooling sentence from the review |
| 88 | `6a18e9d4ee62` | `1206af664d8b` | dropped (empty) | Replace absolute local paths with repository-relative paths and placeholders |
| 89 | `8aef3c9a1346` | `1206af664d8b` | dropped (empty) | Remove agent-harness scratch paths |
| 90 | `6a9b81ece2db` | `1206af664d8b` | dropped (tool) | Fix the escaping of the rule tables in the scrub tool |
| 91 | `95f0ad0b1145` | `1206af664d8b` | dropped (empty) | Replace the remaining verbatim owner quotes with neutral paraphrase |
| 92 | `f29346c31ffd` | `1206af664d8b` | dropped (empty) | Remove search terms specific to the private pilot applications |
| 93 | `1a1392444d70` | `1206af664d8b` | dropped (empty) | Remove the remaining internal coordination text and thread identifiers |
| 94 | `9d799c777e9a` | `1206af664d8b` | dropped (empty) | Remove the supervision tooling name used as internal tooling |
| 95 | `645beb4b1f64` | `28fa469c19b1` | kept | Remove agent-harness scratch paths and the harness ignore entry |
| 96 | `584cbda1c130` | `28fa469c19b1` | dropped (tool) | Scrub the remaining tip residuals; refine the scanner |
| 97 | `1d1f73f697f6` | `28fa469c19b1` | dropped (empty) | Replace the last quoted owner reply in the image experiment record |
| 98 | `bcd649eceaae` | `9690537b5550` | kept | Confirm post-i2 at e5933a3: flips closed; private export edited mid-build forges in both lanes |
| 99 | `a0a8a1e60479` | `9690537b5550` | dropped (empty) | Replace a scratch path in the post-i2 confirmation |
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
| 111 | `409d486cc02c` | `dec460e84334` | kept | Add the public history map |
| 112 | `93c258107462` | `7f83889c0e96` | kept | Draft C2PA 2.5 mapping with illustrative fixtures and checker |
| 113 | `2c5c4386a9f5` | `a51725031259` | kept | Add public branch verification 2 to the promotion and push review |
| 114 | `26bb992de276` | `fcfed2858f42` | kept | Record the public roadmap-v2 push at dec460e; keep pin-dependent gates open until the implementation re-vendors |
| 115 | `9165f198bcd3` | `b83ca671c11c` | kept | Freeze image mark protocol e-img-m-1 with licence check, proposed UC-7 and harness |
| 116 | `ef0aa0c01a98` | `30ccc550e893` | kept | Add non-author review of the image mark protocol e-img-m-1 and proposed UC-7 |
| 117 | `d3af1ee07595` | `b91606abb533` | kept | Freeze image mark protocol e-img-m-2; retire e-img-m-1 unrun after its review |
| 118 | `2f584360c435` | `8b6713dac736` | kept | Add e-img-m-2 confirmation pass to the image mark protocol review |
| 119 | `6ff7c835162c` | `bad6b5a1af1f` | kept | Accept sandbox-exec network denial with the harness probe in IMG.2 |
| 120 | `992c4c98e534` | `c5f6c3f05093` | kept | Strengthen the pre-push guard and the scanner |
| 121 | `83af8b7a1f01` | `d4ce66756004` | kept | Update the public history map |
| 122 | `d16b5ac0228a` | `c06b2149e8e3` | kept | Pre-push hook: decide by the destination ref and keep the leak-free test |
| 123 | `c5bedc137955` | `7f4d9072d6dc` | kept | Pre-push hook: pass the rules path to the scanner and tell hits from errors |
| 124 | `20162a80ac05` | `33f252fda754` | kept | Add non-author review of the M3 evaluation harness |
| 125 | `a17fc22d6db0` | `986d9bb4992b` | kept | Rule the 40 harness ambiguities and the harness review in m3-eval-draft-6 |
| 126 | `a78aace574a6` | `d9c4efa5a883` | kept | Record the measured image mark run e-img-m-2: two identical full runs, counts per scheme |
| 127 | `d3d4788ffe83` | `e95339bc4e48` | kept | Add e-img-m-2 results recheck to the image mark protocol review |
| 128 | `31472373d24c` | `7f1ec2fb48f5` | kept | Accept UC-7 (recognize a marked image) with its verification plan |
| 129 | `084369b752e5` | `a8e6f64b66da` | kept | Mark IMG.0-IMG.4 met from the e-img-m-2 recheck; record the image-mark finding and the synthetic-set decision |
| 130 | `7f8d95382b16` | `cc264b65d4ed` | kept | Add the planned WEB milestone (browser tool and testing page) to the roadmap |
| 131 | `4337924a59d9` | `6dd2fef9c8ee` | kept | State the project's non-commercial nature, record the traceweave.org domain, and add the WEB purpose |
| 132 | `024e508ab1c5` | `b06c555eec18` | kept | C2PA mapping: use the org.traceweave namespace for proposed identifiers |
| 133 | `087990589504` | `fb78e2e840bf` | kept | Record the registration-over-marks direction and add planned A2A gates SK.3-SK.5 |
| 134 | `e3bac866fe52` | `1aa520e384d0` | kept | Rule harness open points O1-O8 in m3-eval-draft-7 |
| 135 | `3d3197487a8e` | `efc42b1f33e5` | kept | Add lane 13 time-evidence review, registration record design draft and illustrative fixtures with checker |
| 136 | `7271715ea71b` | `867fb306457b` | kept | Registration draft: correct the URL count in the verification record |
| 137 | `5c3d9c545d5f` | `dfe65e31dc7b` | kept | Review the registration record draft, fixtures and lane 13 |
| 138 | `1c5c06ad13ca` | `500771130564` | kept | Draft the Python token profile (py-tokens draft-1) with hand-derived vectors, checker and CPython 3.14.6 cross-check |
| 139 | `1dd9c1fbb256` | `5499a00b4715` | kept | Registration draft: add registration at creation time and agent interoperability (A2A 1.0, MCP 2026-07-28), with agent fixtures and checks |
| 140 | `e44f31583ada` | `0f9d642824e1` | kept | Add confirmation pass to the evaluation harness review |
| 141 | `0db8b44097b6` | `c87655a88151` | kept | Add clean-room review of the Python token profile py-tokens draft-1 |
| 142 | `de486c94f4e1` | `2befafa71d5f` | kept | Re-evaluate M1/M2 gates and implementation exits against the published pin; record live sites and the new project statement |
| 143 | `58c25a9e13a9` | `62294bdd0ae5` | kept | Resolve the py-tokens draft-1 clean-room review and freeze it for stage-1 implementation |
| 144 | `c4848c16bf39` | `e290f735b5ac` | kept | Registration record draft-2: resolve the non-author review (5c3d9c5) |
| 145 | `a405f679adf5` | `035e9c6cc3d5` | kept | Rule the direct-check shape, the unbatched caching check and the disk margin in m3-eval-draft-8 |
| 146 | `ff907ac47435` | `1ef9251b6a67` | kept | Add second confirmation pass to the evaluation harness review |
| 147 | `85b16907d25d` | `c71073b6244b` | kept | Require pair completeness for every batched comparison in m3-eval-draft-9 |
| 148 | `fc7b91baae3c` | `488ddf23da12` | kept | Record Linux CI, the frozen py-tokens profile, registration draft-2, m3-eval-draft-9, the visual identity and open name clearance |
| 149 | `437d6195f804` | `65981d7ecd92` | kept | Update the public history map |
| 150 | `9ce62c2fe4c8` | `7237c4367b99` | kept | Add M1.2 derivation metadata and one-to-one paired rejections to the extraction vectors |
| 151 | `a9a5f7ee3a7f` | `725f01fcc25f` | kept | Add the vendor control class, py-tokens registration and M2.2 vectors |
| 152 | `8dd65c3c3301` | `3e66916bbfbf` | kept | Add review packets, candidate-generation records and the M2.2 manifest |
| 153 | `488086f6fd7f` | `8452135e2ff7` | kept | Add the M1.1 registration item map and the M1.5 requirement map for extraction |
| 154 | `98e2fc487946` | `1555655777b5` | kept | Define hand-derived vectors and reference the definition from the vector gates |
| 155 | `3b6e9f3f6922` | `1ce99d635839` | kept | Add non-author review of core gates M1.1, M1.2, M1.5, M2.2, M2.3, M2.6, M2.7 and M2.9 |
| 156 | `41628be879a8` | `f396a4133b56` | kept | Fix the byte form of the pair-id digest in m3-eval-draft-10 |
| 157 | `f84343b19e68` | `6807cb9d96ca` | kept | Apply the hand-derivation definition to M1.2 and M2.6 in the core gates review |
| 158 | `34eea2587916` | `da719106e7a9` | kept | Apply the core-gates review to the extraction vectors and maps |
| 159 | `a77c65745a3d` | `5ddc71120540` | kept | Apply the core-gates review to the catalogue and report contract |
| 160 | `a625c97d17b7` | `b4b5471f4ff5` | kept | State how the hand-derivation rule applies to the extraction vectors |
| 161 | `28f5b6d88351` | `2211862b7172` | kept | Write the matching inputs' token streams by hand and state the derivation rule |
| 162 | `be51871217c3` | `c8b053ae1fb4` | kept | Add confirmation pass to the core gates review |
| 163 | `16ebc94f5c9a` | `4fd94d44cba9` | kept | Require the derivation rule in every labelled matching file |
| 164 | `6f787a0630eb` | `5a3465ecb793` | kept | Derive extraction error offsets per code and reject shifted offsets |
| 165 | `1e322afb554a` | `84a1db071bcb` | kept | Mark M1.1, M1.2, M1.5, M2.6 and M2.7 met from the core gates review; record implementation work, confirmed draft items and the evaluation status |
| 166 | `5b6b1efe255e` | `1b10ba301175` | kept | Update the public history map |
| 167 | `38fb2febd4a4` | `577f9ed36a27` | kept | Make the extraction checker run on Python 3.11 |
| 168 | `be5fde3025df` | `ec3c8a8f794f` | kept | Add final pass to the evaluation harness review |
| 169 | `c86eb022dd5a` | `bc25f8210275` | kept | Rule on the questions from the core-gates differential |
| 170 | `a6851dd3b75c` | `5901aeff236a` | kept | Update the public history map |
| 171 | `66aec94e47f3` | `c5808d69a8e9` | kept | Review registration record draft-2 (confirmation) |
| 172 | `4cc2cc53c62b` | `60d645a44336` | kept | Rule on the text-plain implementations' questions (TXT.3): check order, boundary configurations, rejections, table conventions, reordering; wording only |
| 173 | `5250eae2b4aa` | `f4286095482e` | kept | Registration record draft-3: resolve the draft-2 confirmation review (66aec94) |
| 174 | `1c7043fef8a2` | `82c9bca0d4c3` | kept | Registration record draft-3 confirmation: key-event and real-format verification findings |
| 175 | `dba683b29d9d` | `094b349513a9` | kept | Registration record draft-4: resolve the draft-3 confirmation (1c7043f) |
| 176 | `21865235e8b0` | `3b3bd3337ca2` | kept | Registration record draft-4 confirmation: successor-signed compromise reports do not converge (E1) |
| 177 | `aab67171571e` | `98ddb15d86df` | kept | Registration record draft-5: resolve the draft-4 confirmation (2186523), E1 |
| 178 | `8b4a01943d5d` | `a3edac3f52cf` | kept | Registration record draft-5 confirmation: E1 resolved; confirmed with two should-fix items |
| 179 | `d74d0eb0bdad` | `1a6a7ae55810` | kept | Registration record draft-5 follow-up: resolve F1 and F2 of the draft-5 confirmation (8b4a019) |
| 180 | `545c51668d58` | `101a037efa32` | kept | Restore the M1.4 criterion and keep the M1.4, M2.4 and IMG.4 rows on one line each |
| 181 | `3e9cf189b5d1` | `ae1a7f76d813` | kept | Rule on candidate-generation records over any body |
| 182 | `21ae62b01007` | `6437c26528ff` | kept | Update the public history map |
| 183 | `db3263fffd48` | `99db4617d71b` | kept | Lane 14: AI-origin signals in text, evidence review and design note |
| 184 | `c29841fab57e` | `a3a56008d98f` | kept | Registration record: next-increment proposal (reference for pasted text, self-declared AI use, C2PA export, provider-signal import, adoption and non-adoption list) |
| 185 | `a726ab2d61c4` | `a9c302d8f739` | kept | Registration record: freeze the text reference format as normative design 9.1 |
| 186 | `e6444c9c9458` | `e47e49938e18` | kept | Registration record: add the optional self-declared AI-use claim (design 4.7, owner decision 2026-11-24) |
| 187 | `5852c3d5002b` | `c06e2650a55e` | kept | Addendum review of registration design 4.7 (AI-use claim) and 9.1 (text reference) |
| 188 | `d0bf632ae5cf` | `ec03eddcdf06` | kept | Address addendum review of registration design 4.7 and 9.1 |
| 189 | `3b5f24ecd756` | `548394878bff` | kept | Confirmation pass on addendum fixes (d0bf632) |
| 190 | `b376f591ab3f` | `0ca309175470` | kept | ROADMAP: mark M1/M2 implementation gates met, update M4 registration & planned CI catalogue |
| 191 | `7941c473d9a2` | `ca1347bdfd01` | kept | ROADMAP: mark TS.3 and TXT.3 implementation gates met |
| 192 | `c708b203165f` | `5de16269a9bf` | kept | Freeze TXT.4 Stage 1 prose evaluation protocol (e-txt-1) and dry-run harness |
| 193 | `acebacb59c19` | `ae7efac313b3` | kept | Review frozen TXT.4 Stage 1 prose evaluation protocol (e-txt-1) |
| 194 | `76afd6006786` | `89ad40c9c310` | kept | Record TXT.4 Stage 1 prose evaluation results (e-txt-1, negative-result) |
| 195 | `62b81ebf6621` | `3ea5aa2980b0` | kept | Recheck e-txt-1 Stage 1 prose evaluation results (76afd60) |
| 196 | `96698e332409` | `8a1150bec529` | kept | ROADMAP: mark PY.3 met, TXT.4 negative-result, record M4 REG.1/REG.2 |
| 197 | `5a224bdd3693` | `3371480e653a` | kept | Media tracks: IMG.5 finding-aid schema, C2PA registration link, AV scoping |
| 198 | `9d346b617d4f` | `de114a39cc47` | kept | Review media-c2pa-av (5a224bd): IMG.5, C2PA.1-3, Lane 15 |
| 199 | `a4ea8d46fa7c` | `d61f45c9c203` | kept | Address review blocking items B1 and B2 on media-c2pa-av |
| 200 | `66d276b47cd5` | `2e637b09cb53` | kept | Confirmation pass on media-c2pa-av (a4ea8d4) |
| 201 | `52b0702644b3` | `a72e4a3f8e65` | kept | Merge branch 'media-c2pa-av' into roadmap-v2 |
| 202 | `b193376b9835` | `a8f1d0857c37` | kept | TXT.7/TXT.8: cite e-txt-1 and Lane 09 limits in profiles/text.md; close TXT.8 Unicode-carrier review |
| 203 | `5a8ece2d269d` | `c1d566e9fa26` | kept | Add TXT.7 non-author recount and M4.6 commitment/disclosure review |
| 204 | `bd2f7031b452` | `3f75f3b2e4f4` | kept | Fix M4.6 CD-B2 catalogue opening nonce validation and record review dispositions |
| 205 | `1b51807301f0` | `9696d4569eba` | kept | Confirm M4.6 CD-B2 fix in commitment-disclosure review |
| 206 | `0476cec34ac4` | `44b88cf69d0f` | kept | Draft M4.5 trust policy, in-toto adapter fixtures, and timestamp decision |
| 207 | `c2bd946fcc16` | `3f6779697e4c` | kept | Review M4.5 deliverables on m4-5-intoto (0476cec) |
| 208 | `290530087574` | `5ef7ff302f42` | kept | Address M4.5 review B1/B2 findings and add regression fixtures |
| 209 | `51033c911163` | `688e37093883` | kept | Confirmation pass on m4-5-intoto (2905300) |
| 210 | `c8d8f5150642` | `d527c70e0d31` | kept | Merge branch 'm4-5-intoto' into roadmap-v2 |
| 211 | `50c5641ae498` | `aae74d66f203` | kept | ROADMAP: mark M4.5 met from m4-5-intoto (51033c9) |
| 212 | `19cc1cae9d75` | `d144bd0cd73d` | kept | RES.1: draft resolver threat model and link from ROADMAP |
| 213 | `eb4da68b9c96` | `49b4383f4914` | kept | RES.3: independent review of resolver-threat-model (19cc1ca) |
| 214 | `9f50798d8de8` | `f68bacfb8b64` | kept | RES.1: address review B1-B3 and A1-A5 in resolver threat model |
| 215 | `f6fa840d5935` | `cd91c1d0c089` | kept | RES.1: confirm resolver threat model (9f50798) and mark met |
| 216 | `81a47e1f33a2` | `6add4cef6a5d` | kept | ROADMAP: mark SK.1 and SK.2 met, update main to c3c17a8 |
| 217 | `5facdd4e9274` | `54d49bf9843c` | kept | Promote M4 registration, in-toto adapter, and py-tokens profile |
| 218 | `550a7b5e5fc9` | `5561ae3b00dd` | kept | Review promotion 5facdd4 and mark M4.3, M4.6, PY.1, PY.2 met |
| 219 | `ff1c8c4edd82` | `9cf78eec72d8` | kept | ROADMAP: mark WEB.1 and WEB.2 met, update main to 51f29d7 |
| 220 | `85a673c30484` | `5b9dbb519181` | kept | README: refresh layout with Evidence Ledger light/dark SVG visuals and section index |
| 221 | `c52ea2362eda` | `2354d5d6d77b` | kept | ROADMAP & README: mark M4.4 met (6/6 M4, 28/47 core) and clarify site/docs links |
| 222 | `abcbfad3827c` | `0869ebd792b9` | kept | README: restyle Figure 3 embedded-mark workflow in Evidence Ledger light/dark SVG |
| 223 | `aba26b5797c8` | `7e30cb703484` | kept | M2E.0: record decision to omit source-code embedding from next release |
| 224 | `7dccedd63897` | `a8f6c47798af` | kept | Add candidate release requirement and claim inventories |
| 225 | `4d4e98d68bef` | `6883ebe512be` | kept | Record independent M5 readiness review of 7dccedd |
| 226 | `67f7b5dbcec0` | `3a29ca30f228` | kept | Defer CI signing integration until existing research is supported |
| 227 | `e7e714987ace` | `037aa20d6fb6` | kept | Resolve M5 review findings with executable evidence |
| 228 | `1df04f922161` | `856016afeb17` | kept | Record independent M5 re-review of e7e7149 |
| 229 | `07c98cad440e` | `185aaf367a92` | kept | Reject ambiguous display evidence and minimum labels |
| 230 | `6ded8a3d6923` | `4cb75f5f3c56` | kept | Confirm M5 display oracle fix at 07c98ca |
| 231 | `70f70d43ae1a` | `44852c4d9ae1` | kept | Record independently reviewed M5 gate closures |
| 232 | `24bb4b8483dc` | `f024316078fd` | kept | Document pinned offline synthetic release demo |
| 233 | `284ce4e1f3b2` | `8c703bbcff24` | kept | Review pinned M5.3 offline demo recipe at 24bb4b8 |
| 234 | `1c8f09a62faa` | `e2863bd5a657` | kept | Record independently reviewed M5.3 closure |
| 235 | `4c7c61bab7c2` | `ece5f3bd4e05` | kept | Update public history map for reviewed M5 closure |
| 236 | `fce78938e9fd` | `726b333a2ee0` | kept | Propose explicit image normalization draft with synthetic conformance |
| 237 | `b3a3a2c99b52` | `1a4cbea6c987` | kept | Record independent review of image normalization draft-3 |
| 238 | `db2848c1e8ec` | `b210a142d331` | kept | Add exact grey half-tie normalization fixture |
| 239 | `5d0a8630d4a5` | `6476a51e6de2` | kept | Review exact grey half-tie fixture follow-up |
| 240 | `303b966fe20f` | `8517c53c2284` | kept | Record scoped IMGF.1 research contract closure |
| 241 | `c402191166e9` | `f9ced808fa54` | kept | Merge reviewed IMGF.1 contract closure into roadmap-v2 |
| 242 | `9eab88fe34eb` | `182dba97718a` | kept | Record scoped IMG TS and text criterion recount |
| 243 | `73b6d5cfd116` | `a68bfd46ad0f` | kept | Add TS exclusion decisions and stage-one rejection partners |
| 244 | `ca8fb4f51df7` | `a8445ef0d431` | kept | Record independent review of TS selection and rejection evidence |
| 245 | `631e71e22994` | `4d9c9173dfde` | kept | Record five scoped IMG TS and text gate closures |
| 246 | `0823f1d91143` | `cae4883ee992` | kept | Merge reviewed TS and text evidence with scoped profile closures |
| 247 | `afca82c41d54` | `d66e4b942c8c` | kept | Update public history map for reviewed profile closures |
| 248 | `09359acc2dd5` | `25acdad361ef` | kept | Reconcile research queue with reviewed closures and current holds |
| 249 | `0075c8f394b3` | `639cb855bd1b` | kept | Review queue reconciliation against current gates and holds |
| 250 | `4fa00c7d00eb` | `f4bd1095b048` | kept | Propose local-first agent registration design for review |
| 251 | `12a1459c62e3` | `3d3a5e7ed0f6` | kept | Review local-first agent registration design at 4fa00c7 |
| 252 | `11e975e34720` | `a170a47b8d84` | kept | Record bounded SK.3 local-first design closure |
| 253 | `18657390ee1c` | `30c80b24418e` | kept | Merge accepted SK.3 design closure and reconcile current queue |
| 254 | `ec2a4ddcfd0d` | `a589a1bbb3d0` | kept | Update public history map for reviewed SK.3 design closure |
| 255 | `d6c09e05829c` | `3d89d451eb12` | kept | Prepare curated PDQ publication source with explicit proof limits |
| 256 | `0bd15f8e6cb3` | `2abda2c39334` | kept | Review curated PDQ publication source and proof boundary |
