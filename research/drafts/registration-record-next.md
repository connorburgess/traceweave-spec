# Registration record: next-increment proposal

Status: proposal, 2026-11-24. **Non-blocking.** The build proceeds from the confirmed [registration record](registration-record.md) draft-5 (`aab6717`, with the follow-up `d74d0eb`). This file changes none of its text, fixtures or checker. Read first: [lane 14](../lanes/14-ai-origin-signals.md) (`db3263f`), cited below as L14. No service was contacted and nothing was built.

Every item below is assessed on the same five points:
- what it adds;
- what it must never claim;
- what it costs;
- whether it changes the confirmed statement format (the aim is not to);
- the fixtures and gates it would need.

Gate IDs `NEXT.*` are proposals, like the REG gates in the design's §15.

## 1. A reference that travels with text

**The problem.** Pasted text cannot carry metadata ("free-form text cannot transport metadata", L14 §1.1, quoting the EU Code of Practice). A copy loses any link to its registration. Invisible Unicode carriers are no answer: one published fold erases them ([lane 09](../lanes/09-evidence-review.md)).

**What it adds.** A short reference a person can paste next to the text, derived from what the record already has.
- **Form:** `tw1-` + 26 characters of Crockford base32. That is the first 130 bits of the `statementSha256` the design already defines: the SHA-256 of the exact statement payload bytes, used by the report link in §9.
- **Check:** one more Crockford check character (mod 37) catches typing errors.
- **What it contains:** no content, no key and no identity. The statement holds a fresh 256-bit nonce, so the reference cannot be guessed from the content (design §5).
- **Why 130 bits:** finding a second statement whose digest begins with the same 130 bits takes about 2¹³⁰ work. That is comparable to the 128-bit key display the design already uses.

**Going from reference to record, with no project-run service.**
1. **Where the record is:** in a local file, or at **any URL the registrant chooses**, printed next to the reference by the registrant (for example "tw1-… · record at https://example.org/r/…").
2. **The check:** the verifier fetches or opens the bundle, recomputes `statementSha256`, and requires its first 130 bits to equal the reference. A wrong or substituted bundle fails this check, whatever its URL.
3. **The text:** the verifier then runs the normal procedure of design §10. The pasted text must equal the registered bytes for the digest outcome to be `match`. Re-typed, re-wrapped or edited text gives `mismatch`, and the honest rendering says so. Finding how much of the text survives is a separate comparison (UC-8), never part of the registration result.

**Privacy and abuse.**
- **Fetching a URL** tells its host the verifier's IP address and time.
- **Publishing the bundle at a URL** is a disclosure decision (design §5): it reveals the artifact digest, which confirms a guessed file, and the public key, which links registrations. A registrant who wants neither publishes nothing and hands the bundle over only in a dispute.
- **Squatting.** Anyone who copies the text can register it and paste *their* reference. Design §11 already says first to register is not first to create. A reference adds nothing to that, and must say so.
- **Phishing.** A reference next to a link invites "verify here" pages that show a fake result. Defence: a reference is verified only by a local verifier, never by trusting the page it came from. Renderings never show a URL as verified, only the outcome of the local check.

**Must never claim:** that the text "is registered" or "is verified" when the bytes differ; that a reference identifies who wrote anything; that a project service vouches for it.

**Cost:** about 20 lines of code; no service, account or key.

**Format change:** **none.** The reference is derived from `statementSha256`. It adds one rendering template (`Reference: tw1-…`) to the §11 allow-list, which is text, not format.

**Fixtures and gates — NEXT.1 (E, S):**
- reference vectors from the committed fixtures: encode, decode and check character;
- negatives: a wrong check character; a bundle whose digest does not match the reference; a reference rendered as "verified" for mismatching bytes; a reference rendered next to an authorship word;
- the rule that a URL never appears in a rendering's outcome line.

## 2. Self-declared AI use (`claims.generator`)

**What it adds.** An optional statement by the registrant about whether, and which, AI tools were used, signed with the rest of the statement (L14 §4.2 floats this). It answers a question people ask, the way C2PA's `digitalSourceType` does, without Traceweave inferring anything.

**Shape (proposal).**

```json
"claims": {"createdAt": "…",
           "generator": {"declaration": "ai-tool-used", "tools": [{"name": "…", "version": "…"}],
                         "digitalSourceType": "http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"}}
```

- **`declaration`:** `no-ai-tool` or `ai-tool-used`.
- **`digitalSourceType`:** optional, from a closed list of IPTC/C2PA URIs. C2PA 2.5 itself uses:
  - `http://cv.iptc.org/newscodes/digitalsourcetype/` with `trainedAlgorithmicMedia`, `compositeSynthetic`, `digitalCapture` and `humanEdits`;
  - `http://c2pa.org/digitalsourcetype/` with `trainedAlgorithmicData` and `empty`.

  The full IPTC vocabulary must be pinned by version before use.
- **Labelling vocabulary.** The EU Code of Practice's own labelling vocabulary was **not read** for lane 14 or for this proposal. It must be pinned from the primary text before any label wording follows it.

**Must never claim:**
- that Traceweave checked the declaration;
- that `no-ai-tool` means "human-written" (L14 §7 never-shown list);
- authorship of any kind.

The rendering is a fixed template: "The registrant declares that {no AI tool / the tools listed} were used in making this content. Traceweave has not checked this." The record already gives the time as claimed, and nothing about the declaration is "proved".

**Compatibility with `authorship-claim`.** The design rejects authorship keys (`author`, `creator`, `owner`, `original` and others) in results and witness statements, and authorship words in unlisted rendering lines.
- **No collision:** `generator`, `declaration`, `tools` and `digitalSourceType` are not on those lists, and the template uses none of the denied words ("making", not "created by").
- **New negatives keep the line:** a `generator` value carrying a person's name; a rendering that turns `no-ai-tool` into "written by a human"; and any combination of the declaration with a provider signal in one sentence.

**Cost:** small in code. The real cost is honesty: a declaration is only as good as the registrant, and it can be wrong or false. That limit must be on screen, not only in the documentation.

**Format change: yes.** `claims` is closed (design §4.6), so an unknown key is `statement-shape` today. Adding the field means a new predicate version (`registration/draft-6`, or the first released version). Old records stay valid under their own version.

**Fixtures and gates — NEXT.2 (E, S):**
- positive statements with each declaration and each pinned `digitalSourceType`;
- negatives: an unknown URI; a free-text declaration; a person as tool name; the template violations above;
- an owner decision on whether to offer it at all (NEXT.2-O), because an "AI-use" field invites the very verdicts L14 §7 forbids.

## 3. C2PA export for containers that can carry it

**What it adds.** For PDFs and images, the registration travels inside the file. It becomes a C2PA manifest whose custom assertion `org.traceweave.registration` holds the statement bytes and the bundle digest.
- **Time-stamp:** the manifest gets its **own** RFC 3161 token over the C2PA claim signature (`sigTst2`), as corrected in design §15. A registration's token over its DSSE signature does not map.
- **Assertion store:** a registrant exporting their own registration puts the assertion in `created_assertions`. Anyone else puts it in `gathered_assertions` ([C2PA mapping](c2pa-mapping.md) rules).

**What interoperates today: nothing that this project has verified.** C2PA.2 (round-tripping through a pinned C2PA tool) is still open. What a C2PA validator would show, from the C2PA 2.5 text and the mapping draft:
- the hard binding valid for the file's bytes;
- the claim signature valid, but **not trusted**, unless the signer's certificate is on the validator's trust list;
- the time-stamp valid if the TSA is trusted;
- `org.traceweave.registration` listed as an assertion it **does not interpret**.

It would not show the Traceweave outcomes. Those need this project's verifier. **Text inside a C2PA text container** (C2PA A.8) is hashed after NFC normalization, so it is not a digest of the stored bytes (mapping draft §4). Item 1 serves pasted text; this item does not.

**Must never claim:** C2PA compatibility before C2PA.2 and C2PA.3 pass; that a C2PA "valid" means the registration's outcomes were checked; any `digitalSourceType` the registrant did not declare (item 2).

**Cost:**
- a C2PA tool build (mapping D7, owner);
- an X.509 signing certificate, because C2PA's COSE signatures need X.509 while the registration uses raw Ed25519 keys (mapping: "conflicting"). A self-signed certificate validates as untrusted; a trusted one costs money and an identity check (owner);
- the second RFC 3161 token, which falls under REG.3's external-service decision.

**Format change:** none to the statement; the export is a container around it.

**Fixtures and gates — NEXT.3 (E, I), after C2PA.2:**
- one PDF and one image fixture, exported and read back by the pinned C2PA tool, giving the same `statementSha256` and the same §10 outcomes;
- negatives: the assertion in `created_assertions` signed by someone else; a registration DSSE token reused as `sigTst2`; a compatibility claim in any rendering.

## 4. Importing a provider's signed detection result (shape only)

**What it adds.** EU Code Sub-measure 2.1.2 requires providers to offer "a digitally signed format, including at least a hash of the content submitted for detection, a URL or other identifier of the detection solution, and a timestamp" (L14 §1.2). Lane 14 §6 drafts the record that holds it: `traceweave-provider-signal-draft-1`.
- It is stored **beside** a registration, keyed by the same SHA-256 of the exact bytes, and **never inside it**. The registration predicate rejects it (`statement-shape`), and a comparison report never contains it.
- The import keeps the provider's signed bytes verbatim, maps `result` to `present`, `absent` or `inconclusive`, and defaults to `unknown`.

**Must never claim:** anything on L14's never-shown list ("AI-generated" or "human-written" as a verdict, percentages, any sentence about a person), or any combination with a registration or match outcome in one sentence. The §7 sentences of L14 are the only renderings.

**Cost:**
- **Now:** a schema and vectors.
- **Later:** a provider account, approved access and terms that allow storing and showing results. None of these exists today (L14 AIO.4, AIO.7; owner).
- **Nothing is connected.**

**Format change:** none. It is a separate record.

**Fixtures and gates:** L14's AIO.1 and AIO.5 cover it. Add one cross-record vector: a provider signal and a registration for the same bytes, each verified alone, with neither changing the other's outcomes.

## 5. Other provider practice, and what is not adopted

**Worth adopting:**
- **Re-association by fingerprint, locally.** Providers pair signed metadata with a soft binding so that a stripped copy can find its manifest again. The equivalent here needs no service: a registrant's own fingerprint catalogue (design §4.4) finds which registration a stripped or edited copy came from, as a **comparison** result (UC-1, UC-8), with the registration then verified separately.
  - **Adds:** recovery when item 1's reference was dropped.
  - **Must never claim:** that a match proves the copy is the registered work.
  - **Cost:** none new.
  - **Format change:** none.
  - **Gate:** a walkthrough fixture under NEXT.1.
- **Disclosure levels in renderings** (C2PA Appendix B, "Disclosure Levels"): a one-line summary, with the full outcome list one step away. That fits the §11 allow-list, as an ordering of the same templates.
  - **Format change:** none.
  - **Gate:** under REG.4.

**Not adopting, with reasons:**
- **Keyed statistical watermarks for existing text.** They are applied at generation by the model's operator. They cannot mark text a person already wrote, and their detection needs the operator's secret key (L14 §1, Decision). Lane 09 found no text mark that survives the cheapest fold.
- **Unkeyed "AI text detectors".** They have measured false positives that fall disproportionately on non-native writers, and no defensible error unit (L14 §5, §7 "accusation risk"). Never ship one.
- **Anything that needs a provider secret, account or approved access.** That includes running a provider's detector on the user's behalf. It breaks "content never leaves the machine", and it waits on AIO.4 and AIO.7.
- **Invisible-character reference carriers in text.** They are erased by folding (lane 09) and look like tampering. Item 1's visible reference replaces them.
- **A hosted lookup or registry by default** ("is this text registered?"). It is an enumeration oracle and an accusation tool, and it needs an operator (SK.5). Item 1 keeps lookup on the registrant's chosen location.
- **An "AI-generated" label as a property of content.** Only declarations (item 2) and provider signals (item 4) exist, each attributed to whoever made it.

## 6. Recommended order, and what to decide before the first build

**Order:**
1. Item 1, the reference: no format change, cheap, and it answers the pasted-text gap directly.
2. Item 4's shape, the AIO.5 vectors: no format change, nothing connected.
3. Item 2, after the owner decides NEXT.2-O.
4. Item 3, after C2PA.2.

**Before the first build.** Only two things would break compatibility if retrofitted:
- **The reference derivation (item 1).** Freeze it (`tw1-`, 130 bits of `statementSha256`, the check character) before any registration is shared. A reference already printed next to someone's text cannot be re-derived later. This is a rendering and tooling choice, not a statement change, so it does not touch the confirmed draft.
- **Whether `claims.generator` exists (item 2).** `claims` is a closed list, so adding the field after release means a new predicate version. That is not breaking, because old records stay valid, but it is a version step. **The owner should decide before the first release** whether the first released predicate carries this optional field. If the decision is "not now", nothing needs to change: build draft-5 as it stands.

Items 3 and 4 can follow at any time without affecting existing records.
