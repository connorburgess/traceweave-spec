# Non-author check: promotion of the reviewed drafts, and push hygiene for `roadmap-v2`

Checked 2026-11-23 on `roadmap-v2` at `f42156d`. The promotion is `c512550..f42156d`, with parent `04849f9`. The push scope is the 79 commits in `origin/main..roadmap-v2`, compared with the local `origin/main` ref `8d5e6a7`; I fetched nothing. I wrote none of the promoted files. My scripts are in `$TMPDIR/pp/`.

## 1. Promotion

**Digests.** I parsed all 84 rows of [promotion-map.md](../promotion-map.md) and recomputed SHA-256 from `git show 04849f9:<old>` and `HEAD:<new>`. All 84 match, the working copy equals HEAD, and every old path is gone at HEAD. That gives 57 identical files and 27 changed, as stated.

**The 8 changed JSON files.** I reversed the substitutions myself.
- `../extraction/` → `../extraction-vectors/` and `../extraction-text/` → `../extraction-vectors-text/` restore the old bytes exactly in all 5 matching-vector files.
- In the 3 schemas, the parsed trees differ only in `$id` and `description`. Restoring those two strings restores the old bytes, and the digests (`9370770f…`, `5ce5eebb…`, `ed81db7e…`) equal the map.

**The 19 Markdown and script files.** I word-diffed each one against its draft. All changes are status lines, link targets, path strings and the schema directory in `check_matching.py` (`SCHEMAS = HERE.parent.parent / "schemas"`), **with one exception**:
- **P1.** [profiles/text.md:122](../../profiles/text.md) changed rule text. The code-span example `` `[x](y)` `` became `` `[x](../research/drafts/y)` ``: the path rewrite treated a literal example as a link. **Fix:** restore `` `[x](y)` ``, and note the one-line correction in the promotion map.

**Status wording.**
- `ts-tokens` is frozen and `tsx-tokens` is a deferred draft marked not normative ([profiles/typescript.md:5](../../profiles/typescript.md)).
- `text-plain` is frozen for stage 1 and `text-markdown` is marked not normative ([profiles/text.md:5](../../profiles/text.md)).
- The vector READMEs say the same.
- The image profile is still "draft for review". The evaluation protocol is `m3-eval-draft-4`, "ready to freeze … Not run", still under `research/drafts/`.

All of this is accurate, with one exception:
- **P2.** [image-experiment-protocol.md:3](../drafts/image-experiment-protocol.md) still says "not yet run", but it ran (`0c7523c`). The file is digest-frozen, so do not edit it. Add a one-line note to `research/experiments/image-fingerprint/README.md` pointing at `results/e-img-f-2/`.

**Checks I ran.** All exit 0:
- `.venv/bin/python tools/validate.py`: PASS, including "promoted schemas and vector checkers".
- `-m unittest discover -s tests`: 9 tests, OK.
- `test-vectors/extraction/check_vectors.py`.
- `test-vectors/matching/check_matching.py` (record self-test 55/55).
- `test-vectors/extraction-typescript/check_vectors.py` (28/28 mutations, 15/15 wrong lexers).
- `test-vectors/extraction-text/check_text_vectors.py` (12/12; 60/60 records).

**spec/conformance.md.** Level 4 now lists the four vector sets and the two contracts, and says checkers are not extractors. That is accurate, except:
- **P3.** [spec/conformance.md:11](../../spec/conformance.md) says "the vector checkers … do not lex or match". In fact `extraction-typescript/check_vectors.py` re-lexes every input with `tslex.py`, and `check_text_vectors.py` tokenizes. **Fix:** "the checkers validate recorded outputs; the TypeScript and text checkers also re-lex with reference lexers written from the profile; none is a production extractor".

**Approval scope.**
- **P4.** [ROADMAP.md:167](../../ROADMAP.md) records the promotion as approved "into `test-vectors/`, `schemas/` and `profiles/`", and L312 repeats that list. The two contracts went into `spec/` (`spec/extraction.md`, `spec/catalogue-report.md`). **Fix:** the coordinator confirms that `spec/` was intended and adds it to both lines.
- **P5.** [ROADMAP.md:87](../../ROADMAP.md): M2.10 still says OD-C5 is "pending owner confirmation", but L170 records it as confirmed. Align them.

## 2. Push hygiene

**Important.** Fixes committed at the tip do **not** remove anything from the 79 commits being pushed. Removing an item from history means rewriting `roadmap-v2`. That would change commit ids that the reviews, ROADMAP and the frozen image protocol cite (`6f39e50`, `0c7523c`, `835f6c0` …) and break the ancestry evidence. So each item below either stays public as it stands or forces a rewrite. I give my view on each.

**Nothing found:**
- **Secrets:** no private keys, tokens, `ghp_`/`github_pat_`/`AKIA`/`sk-` strings or passwords. The 12 pattern hits are prose, topic names (`secret`, `password-sniffer` in the manifest) and a test fixture named `secret.go`. The signing seeds are the documented public test seeds.
- **Attribution:** no AI attribution or co-author trailer in any of the 79 commit messages, and none in the files.
- **Raw reports:** no raw external reports; `.local/`, `research/gemini/` and `research/perplexity/` are git-ignored.
- **Census outputs:** no third-party source text (the summaries carry counts and offsets only).

**Findings.** None is a secret. Fix each at the tip unless noted; history keeps the original.

| # | Where | What | Fix |
| --- | --- | --- | --- |
| H1 | [ROADMAP.md:162](../../ROADMAP.md), :228, :235 | **Owner words quoted verbatim**, including typed replies | Coordinator to decide. I recommend paraphrasing ("the owner delegated the four decisions to the coordinator on 2026-11-23") and dropping the typo transcription. History keeps the quotes, so decide before pushing |
| H2 | [implementation-merge-i1-review.md:59](implementation-merge-i1-review.md) | Lists the categories searched for as "terms specific to the private pilot applications" | Replace with "no private-application material" |
| H3 | [research/work-queue.md:12](../work-queue.md) | A sentence naming the supervision tooling as internal tooling | Delete the sentence. [02-carrier-feasibility.md:7](../02-carrier-feasibility.md), already on `main`, names the pilot applications; that is acceptable context |
| H4 | [research/lanes/06-evidence-review.md:3](../lanes/06-evidence-review.md) (also 07:3) | thread identifiers and internal coordination text | Replace with "the coordinator" or remove |
| H5 | ROADMAP.md:223; docs/implementation-repo-plan.md:7, :17; research/work-queue.md:16; go-census/README.md:14, :29; lanes/go-fragment-results.md:59; reviews: merge-i1 :3, merge-i2 :3, roadmap-v2 :168, evaluation-protocol :5; image `results/e-img-f-2/RESULTS.md:3` and `transcript.txt` (10 lines, including `~/Library/Caches/pip`) | **Absolute local paths** showing the user name and directory layout | Use repo-relative paths or `<implementation repo>` / `<run worktree>`. The transcript is evidence: leave the bytes and add a note, or accept. The user name equals the public GitHub handle prefix, so I rate this low |
| H6 | merge-i2 review :97, :130; [.gitignore](../../.gitignore) `.claude/` | `<scratch>/…` scratch paths and an agent-harness ignore entry. Not attribution, but they reveal tooling | Replace with "scratch scripts"; the `.gitignore` line is optional |
| H7 | all 79 commits | Author e-mail `connorburgesscodes@gmail.com` | Already public through the 6 commits on `origin/main`; no new exposure |

**Third-party content.**

| Item | Licence | Redistribution |
| --- | --- | --- |
| `image-fingerprint/vendor/threatexchange_pdq/` (11 files, unmodified, blob ids in PROVENANCE.md) | BSD (Meta ThreatExchange), LICENSE kept | Fine with the notice, which is present |
| `vendor/iscc-sdk-LICENSE.txt` (the normalization is re-implemented, not copied) | Apache-2.0; upstream has no NOTICE | Fine |
| `vectors/pdq-reference.json` (published hashes, file digests); the images are git-ignored | BSD source | Fine |
| `test-vectors/extraction/unicode-17.0.0-tables.json`, `test-vectors/extraction-text/text-tables-17.0.0.json` (derived from the Unicode Character Database) | Unicode License v3 / Unicode terms of use | Permitted with notice, but **no Unicode notice is in the repository**. [extraction-text/README.md:162](../../test-vectors/extraction-text/README.md) itself says this is "not settled" and the owner should confirm (**U1**) |
| Evaluation manifest (GitHub API metadata, licence-file digests, short classifier phrases; no licence texts) | — | Fine |
| Census manifests and summaries (metadata, counts) | — | Fine |
| `Cargo.lock`, `go.sum` | — | Fine |

**U1 fix:** add `LICENSES/Unicode-3.0.txt`, a line in [LICENSE.md](../../LICENSE.md) under third-party materials, and a sentence in both vector READMEs naming the UCD 17.0.0 source files. Then replace the "not settled" sentence.

**Size.** The diff is +217,877 lines across 231 files. The largest files are two byte-identical 2.0 MB `queries.jsonl` files (image runs 1 and 2) and `matching.json` (1.3 MB). There are no binaries and no build outputs. The duplicate run file is evidence for V2; keeping it is fine.

**Claims.** README keeps "not a universal guarantee" and "detecting a mark does not establish ownership"; spec/core.md says it "is not a stable standard". I found no ownership, accuracy or security overclaim. The README's contract rows say "experimental draft, normative for this draft version", which is accurate.

## Verdict

**Push after listed fixes.**

Blocking, before the push:
1. **H1 decision:** whether the owner statements may be published as written. If not, history must be rewritten before pushing, with every cited commit id re-recorded. My recommendation is to accept and paraphrase at the tip.
2. **P1:** restore `` `[x](y)` `` in `profiles/text.md:122`, so the promotion really changed paths and status only.
3. **U1:** add the Unicode licence notice for the two derived tables before they are published as normative vectors.

Non-blocking, at the tip: H2–H6, P2–P5.

## Public branch verification

Checked 2026-11-23: `roadmap-v2-public` at `651451c` against `roadmap-v2` at `3346d55` and `origin/main` at `8d5e6a7`. My scripts are in `$TMPDIR/pub/`; I did not use the lane scanner. Nothing was pushed or fetched; GitHub's API was used read-only for the action pins.

**1. Scan of everything new.** That is 104 commits (messages, author and committer fields) and 975 new objects, of which 495 are distinct text blobs. **Zero hits:** owner quotes, thread ids, coordination text, e-mail addresses other than the already-public identity, raw reports. **Paths and user name:** no blob version contains `/Users/<name>` or the bare user name. The remaining hits are the generic `/Users/…` and `~/Library/…` in two reviews and the transcript. **Benign hits:** "private" terms are corpus GitHub topics (`interview-questions`) and "resume point" in the text profile. "AI" terms are corpus topics, hygiene-checker patterns and review prose. `traceweave.local` is a Go module path. `github_pat_` occurs only in this review's prose. **Exception (B1 below):** `tools/public_history_scrub.py`, in every version from map row 84, stores its rules ROT13-encoded. Decoded locally, they contain the verbatim owner quotes with their typos (48 hits), the private-application search terms and both pilot-application names (85 hits), the home path including the user name, and the agent's scratch path.

**2. Trees and JSON.** The tip trees differ only in `research/public-history-map.md`. Pairing all 103 commits in order: author, committer, dates and subjects are equal; all 6,073 `.json`/`.jsonl` blob versions are byte-identical; 23 text paths differ somewhere in history, all of them scrubbed documents; the frozen image protocol and its harness never differ.

**3. Reproducibility.** **Deterministic:** in a scratch clone, `rewrite` run twice gives `74c0329` both times, with identical id maps. That equals `651451c^`. **Append-stable:** after one appended source commit, the first 103 ids are unchanged and the new tip descends from `74c0329`. **But not a fast-forward from the pushed tip (B2):** the map commit `651451c` exists only on the public branch, so the next rewrite will not descend from it.

**4. Fresh clone of `651451c`.** All exit 0: `tools/validate.py`, and `--links-all`; the unit tests; the extraction, matching, TypeScript and text checkers; `tools/check_hygiene.py`.

The workflow has `contents: read`, `persist-credentials: false` and no `secrets.` references. Its pins resolve on GitHub: `actions/checkout@3d3c42e5…` = tag v7.0.1, and `actions/setup-python@6d4fd22b…` = tag v7.1.0.

**5. Earlier findings: all resolved at the public tip.** **P1–P5:** P1 restored at `profiles/text.md:122`. P2 has a results pointer at image README:5. P3 is reworded at `spec/conformance.md:11`. P4 now names `spec/` at ROADMAP:166 and :312. P5 reads "OD-C5 … confirmed". **U1:** `LICENSES/Unicode-3.0.txt` is the Unicode License v3 text, and its SHA-256 `e7a93b00…` equals the digest recorded in `LICENSE.md:11`. Both vector READMEs carry a notice naming the UCD 17.0.0 source files. **H1–H6:** no clear-text hits remain (§1), and `.claude/` is gone from `.gitignore`.

**6. What should not be public.** **B1 (blocking).** ROT13 is not protection: anyone can decode it in one line, so the encoded rule list publishes exactly the strings the rewrite removed. That covers every historical version of the tool, not just the tip. An encoded rule list is not acceptable in any form that allows replacement. Keep the rules out of the public branch entirely: exclude `tools/public_history_scrub.py` from every rewritten commit, with a deterministic rule for the commits that become empty; keep the rules on `roadmap-v2` only; record in the map the SHA-256 of the tool file used, so it can be reproduced privately. **B2 (blocking for fast-forward pushes).** Commit the map on `roadmap-v2`, so it flows through the rewrite, and regenerate. **Id map:** acceptable. Its commit subjects ("Remove the supervision tooling name…", "Fix the escaping of the rule tables…") say that something was removed, not what. After B1, the tool commits stay listed only by subject.

**Verdict: blocking items B1 and B2; do not push `651451c`.**
- After B1 (tool and rules dropped from all public commits) and B2 (map committed on the source branch), regenerate the public branch. Re-run the scan with ROT13 decoding, plus the determinism check. Then push the new tip as `origin roadmap-v2`.

Everything else is ready.

## Public branch verification 2

Checked 2026-11-23: `roadmap-v2-public` at `dec460e` (97 commits over `origin/main` `8d5e6a7`). It was generated from `roadmap-v2` at **`409d486`**; `dec460e^{tree}` = `409d486^{tree}` = `d7fa29ad…`. My scripts are in `$TMPDIR/pub2/`. The private rules file was read locally only to load its patterns; none of its content appears here. Nothing was pushed to or fetched from `origin`.

**1. Scan.** The scan covered 97 commits (messages, author and committer headers), 505 new blobs and every path. Each was matched in plain text, ROT13, reversed, base64-decoded and hex-decoded form against the 44 private substitution patterns, the 8 private detectors and my own categories (owner quotes, private terms, thread ids, coordination text, home paths and user name, AI trailers, secrets, foreign e-mails).
- **Real hits: 0.** All five residual matches are false positives: "the parent commit" (git sense) in `test-vectors/extraction/README.md`, the ROT13 of an identifier in the matching scripts, and the allowed git identity in this review.
- **The tool:** 3 versions of `tools/public_history_scrub.py` remain, none is a listed rule-bearing blob, and none carries the removed strings in any encoding.

**2. Reproducibility.**
- **Deterministic:** in a scratch clone, `rewrite --source 409d486` run twice gives `dec460e` both times, with identical id maps.
- **Append-stable:** after one appended source commit, the earlier ids are unchanged, `dec460e` is an ancestor of the new tip, and later pushes are fast-forwards.

**3. Trees and dropped commits.**
- **JSON:** pairing all 97 kept commits through the id map, all 5,635 `.json`/`.jsonl` blob versions are byte-identical, and no path other than the tool is missing.
- **Correction to the brief:** the 14 dropped commits are **not** only tool-version commits. Three are (`4d5d203`, `6a9b81e`, and `584cbda`, whose lane edits also become no-ops). The other 11 are the scrub commits themselves (owner quotes, thread ids, paths, scratch paths, private terms, tooling sentence), whose edits are exactly the substitutions already applied to every earlier version. All 14 have a rewritten tree equal to their parent's, so dropping them loses no content.

**4. Fresh clone of `dec460e`.** Everything exits 0: `tools/validate.py`, `--links-all`, the unit tests, the four vector checkers and `tools/check_hygiene.py`. `.github/workflows/validate.yml` is byte-identical to the version verified at `651451c`, with SHA pins and no secrets.

**5. Pre-push hook** (local bare remote under `$TMPDIR`). It refuses `roadmap-v2` ("contains a rule-bearing version of the rewrite tool") and accepts `roadmap-v2-public`.
- **Gap (non-blocking for this push):** the hook checks only the listed tool blobs. It **accepted** `f42156d`, an older `roadmap-v2` commit that predates the tool but still contains an owner quote and a thread id.
- **Fix before routine use:** have the hook run `tools/public_history_scrub.py scan` on the pushed range with the private rules, or accept only refs whose tip descends from the current public tip.

**6. Map and subjects.** Acceptable. The map names categories and counts, the rules-file SHA-256 and the old→new ids with subjects. Subjects such as "Replace verbatim owner quotes with neutral paraphrase" say that something was removed, not what. No subject contains removed content.

**Verdict: safe to push `dec460e` to `origin` as branch `roadmap-v2`.** Widen the hook (point 5) before any later push from this clone. Correct the dropped-commit description in the map or brief (point 3) at the next regeneration.
