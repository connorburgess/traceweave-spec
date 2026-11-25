# Registration record specification (`traceweave-registration-draft-5`)

Status: experimental draft, normative for conformance of this draft version (promoted 2026-11-25 from `research/drafts/registration-record.md`, aligned with [core](core.md), [attestations](attestations.md), and [trust-policy](trust-policy.md)).

Revision status (before promotion): draft-5 of 2026-11-24, with the follow-up `d74d0eb`, **§9.1, the text reference, frozen as normative on 2026-11-24** (no statement-format change), **§4.7, the optional self-declared AI-use claim, added on the owner's decision of 2026-11-24** (an optional field; version unchanged; no existing fixture changed), and `CD-B2` + `CD-A2`–`CD-A5` dispositions from [commitment-disclosure-review.md](../docs/reviews/commitment-disclosure-review.md). It resolves the "Draft-4 confirmation" section of the [draft-2 review](../research/reviews/registration-record-draft-2-review.md#draft-4-confirmation) (`2186523`), whose single blocking item is E1; §24 maps every item. Draft-4 (`dba683b`) resolved D1–D9 (§23), draft-3 (`5250eae`) B1–B3 and S1–S13 (§22), and draft-2 the first [review](../research/reviews/registration-record-review.md) (§21). **No external time-stamping service, calendar, log or witness was contacted.**

**What changed from draft-4:**
- **E1** (§8). Key events are now evaluated in two passes with no fixed point: standing first, then disputes, which never feed back. A compromise report never disputes the rotation that gives its own signer standing. The evaluation cannot oscillate, and a non-settling implementation is an error, never a verdict.
- **Event identity** is the SHA-256 of payload and signature (an enumeration finding).
- **Enumeration** (§8). It is widened: steps both shorter and longer than the look-back, three claimed starts, boundary and no-quorum probes, 13 invariants, and a sample run through real signed bundles. Its mutation check includes the draft-4 rule.
- **Policy** (§6.3, §10). `minConfirmations` (≥ 1), the checkpoint shape and `compromiseLookbackSeconds` (non-negative integer) are validated. An attested height must be at most the checkpoint height minus `minConfirmations`. A real `recoveryKeys` field replaces the unbacked RD18 claim.
- **RFC 3161** (§6.2). Unsupported algorithms (such as ECDSA) give the outcome `unsupported`, not a forgery code (D7). Path building backtracks past decoy certificates.
- **Text.** The threat row states that a report inside the window loses the successor chain permanently. REG.1 is tied to the widened enumeration.

**What changed from draft-3:**
- **Supersession** (§8; D1, D2):
  - After a key's first applied rotation or retirement, events it signs other than `compromised` are `ignored-superseded`, and so is any later rotation or retirement of it.
  - Two different supersessions of one key at the same proved time are both `disputed`.
  - Rotations are otherwise disputed only inside a compromise window.
  - Trust flows only through a rotation proved strictly after its signer became trusted (an enumeration finding).
  - An enumeration test covers 1,727,604 event sequences, with a mutation check showing that the invariants catch weakened rules.
- **OpenTimestamps** (§6.2; D3): the header source is trusted only up to a pinned **checkpoint** header, from the verifier's own node, at or above the attested height plus `minConfirmations`.
- **RFC 3161** (§6.2):
  - RFC 5280 path validation at `genTime`: basic constraints, key usage, validity, path length and critical extensions (D4). Every chain vector is cross-checked against `openssl ts -verify`.
  - The TSTInfo version and duplicate signed attributes are checked (D8).
  - The supported algorithms are stated (D7).
- **Revocation** names a certificate, not a root (§6.7; D5). The renewal basis is stated (§6.6; D9).
- **Renderings** (§11; D6): a rendering of a simulated result must start with the marker line. Keys are shown with 128 bits of their SHA-256, not the 64-bit hint.
- **Gate text** (§15): REG.1–REG.4 fixed as the review asked.
- Object version strings end in `draft-4`.

Earlier draft-3 summary, kept for the record:

**What changed from draft-2:**
- **Key handling** (§8):
  - Keys are identified by the SHA-256 of the full public key, never by the 64-bit `keyid` hint (B3).
  - Key events are evaluated in order of proved time, independent of input order (B2).
  - A compromise disputes later rotations and retirements of the key, no trust flows through a disputed rotation, and conflicting rotations are both disputed (B1).
  - With no quorum bound, a signature touched by a key event is `disputed` (S1).
- **Time evidence** (§6):
  - RFC 3161 token checks are specified and run on real-format vectors (S2, S9, S10).
  - Revocation data carries its source and date (S3).
  - A witness counts with the TSA its time comes from (S4).
  - `cosigned-checkpoint` is removed (S5).
  - Renewal is defined (S6).
  - Times are rounded up and the OpenTimestamps header source is pinned (N1, N2).
- **Verification and wording:**
  - URL-safe base64 is accepted (S7).
  - "Registrant", not "creator", throughout; renderings may not order two registrations (S8).
  - The claim is compared with trusted signatures only (S11).
- **C2PA and the roadmap:** the C2PA row is corrected (S12), and exact ROADMAP.md text is proposed for the gates (S13; ROADMAP.md is not edited here).
- Every object version string ends in `draft-3`.

## 1. Summary

A **registration record** lets a registrant later show: *these exact bytes existed, and my key signed a statement naming them, no later than time T.* It is a signed in-toto statement (DSSE), plus time evidences attached as separate objects. Each time evidence countersigns **one** signature under **one** trust anchor. A verifier reports each part separately:
- the digest and possession checks;
- each signature and its signer trust;
- each key event;
- each time evidence;
- **for each signature**, the earliest single-source bound and the bound agreed by a quorum of independent sources.

There is never a single "authentic" verdict.

A registration does **not** show authorship, originality, ownership or permission. It does not show that the registrant created the content rather than copied it first. **First to register is not first to create.** §11 makes this text mandatory wherever a registration is shown to a person, and allows only listed line templates.

A registration does not depend on the content's profile. Python source under `py-tokens` draft-1 is registered exactly like Go, Rust or any other bytes; the profile matters only for the optional catalogue commitment (§4.4).

Recommended first mechanisms: **RFC 3161 time-stamp tokens from two unrelated TSAs** and **OpenTimestamps** (Bitcoin), with quorum 2 (§13). That is three time sources, so losing one, for example to a TSA certificate revocation, still leaves two. Every result also states how current its revocation data is (§6.7): offline verification holds only as of that date.

## 2. Terms

- **Claimed time:** a time written by the registrant (`claims.createdAt`), like core's `recordedAt` and the report's `generatedAt`. Anyone can write any value. It is never shown as proved.
- **Bound (`notAfter`):** an upper bound on when one signature existed, from one verified time evidence under the verifier's policy. Time evidence gives only upper bounds. Nothing here proves a lower bound or a creation time.
- **Trust anchor:** what a time source's validity ultimately rests on, identified by a SHA-256 the verifier computes, never by a name the producer writes:
  - TSA: the DER root certificate of the token's chain;
  - Bitcoin: the chain as pinned by the verifier's own node or header file;
  - log or witness: the public key.
- **Independence group:** a label in the **verifier's** policy. Anchors in the same group count once. An evidence that rests on several anchors (a witness and its TSA) joins their groups (§6.3).
- **Key identity:** the SHA-256 of the raw 32-byte Ed25519 public key. The 16-hex `keyid` is only a lookup hint (B3).
- **Placeholder versus real format:** in placeholder fixtures the anchor digest and certificate dates are written by the producer and accepted as given. Only the real-format vectors (§6.5) test that the verifier computes them (S10).

## 3. Objects

All version strings and predicate URLs are proposals in the `traceweave.org` namespace, which [C2PA draft](../research/drafts/c2pa-mapping.md) D3 also leaves to the owner.

| Object | Version string | Content | Fixture |
| --- | --- | --- | --- |
| Registration statement | `traceweave-registration-draft-5`; predicate type `https://traceweave.org/predicate/registration/draft-5` | in-toto Statement v1 (§4) | `statement.json` |
| Bundle | `traceweave-registration-bundle-draft-5` | DSSE envelope with one or more signatures, public keys, time evidences | `bundle-three-roots.json`, `bundle-cosigned.json`, `bundle-second-work.json` |
| Time evidence | `traceweave-time-evidence-draft-5` | One evidence: target (a signature, or the token of an earlier evidence for renewal), trust anchor, type-specific fields or a real-format token (§6) | `evidence-*.json` |
| Witness statement | `traceweave-witness-draft-5`; predicate type `https://traceweave.org/predicate/witness/draft-5` | A hosted witness's signed statement, used as evidence type `traceweave-witness` (§6.2, §19) | `evidence-witness.json` |
| Key event | `traceweave-key-event-draft-5`; predicate type `https://traceweave.org/predicate/key-event/draft-5` | Retire, rotate or report a key compromised, time-stamped like a registration (§8) | `key-event-*.json` |
| Verification result | `traceweave-registration-verification-draft-5` | The closed outcomes of §10, with the policy used | `verification-result*.json` |
| Report link | `traceweave-registration-link-draft-5` | Ties a comparison report to a registration without changing the report (§9) | `report-link.json` |
| Registration set | `traceweave-registration-set-draft-5` | Several registrations by one producer, for the nonce-freshness check (§4.2) | `registration-set.json` |
| Rendering | `traceweave-registration-rendering-draft-5` | User-facing lines from the §11 templates | `rendering*.json` |

## 4. The registration statement

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [{"name": "sum.go", "digest": {"sha256": "974c8d0a…697c"}}],
  "predicateType": "https://traceweave.org/predicate/registration/draft-5",
  "predicate": {
    "registrationVersion": "traceweave-registration-draft-5",
    "contentKind": "source-code",
    "nonce": "<64 hex: 32 fresh random bytes>",
    "possession": [{"subjectIndex": 0, "scheme": "sha256-salted-possession-v1", "sha256": "…"}],
    "catalogue": {"scheme": "sha256-salted-catalogue-v1", "sha256": "…", "profile": {"configSha256": "…", "id": "go-tokens", "version": "draft-1"}},
    "implementation": {"name": "…", "version": "…", "commit": "<40 hex>"},
    "specCommit": "<40 hex>",
    "claims": {"createdAt": "2026-11-20T09:00:00Z"}
  }
}
```

### 4.1 Subjects

- Each subject is the SHA-256 of the **original artifact bytes**, exactly as stored, with no normalization (`sha256`, contract §3.2).
- There are one to 64 subjects, and no two share a digest.
- `name` is an opaque label with the catalogue id pattern `^[a-z0-9][a-z0-9._-]{0,63}$`, so it cannot hold a path (`subject-name`). in-toto matches subjects "purely by digest", so the name rule is a local one.
- **Selective disclosure (`CD-A2`):** Disclosing a multi-subject statement exposes every bundled `subject` digest and filename. Registrants requiring per-work selective disclosure SHOULD register one work/catalogue per statement rather than batching unrelated works (`v1` does not specify per-entry Merkle commitments).

**Producer obligation:** hash the original bytes. A verifier can check this only when the bytes are supplied (§10 step 5). Without them, the only correct outcome is `not-supplied`; reporting `match` is wrong (`neg-subject-unsupplied-match`).

### 4.2 Nonce

`nonce` is 32 fresh bytes from an operating-system cryptographic random source (OS CSPRNG APIs with no non-cryptographic fallback), new for every registration. It has two jobs:
- It makes the statement bytes unguessable, so the signature digest sent to time services reveals nothing, even to someone holding the content (§5).
- It salts the possession digest.

An all-zero or malformed nonce is rejected (`nonce-invalid`).

**Producer obligation:** never reuse a nonce. Reuse cannot be seen in one record. A verifier given several registrations by the same producer checks that their nonces differ (`registration-set`; `nonce-reused`).

### 4.3 Possession digest

`possession[i].sha256 = SHA256("Traceweave-Possession-v1" || 0x00 || nonce || L || A)`, where `A` is the artifact bytes and `L` its length as an unsigned 64-bit big-endian integer ([core](core.md#salted-possession-digest)). `possession[i]` binds to a signer key **only** through the enclosing verified DSSE signature over the statement (§6.1).

*What it adds.* A time evidence over a plain artifact digest shows that *someone* knew that digest by T, and a digest can be copied from anywhere it was published. The possession digest uses the registrant's own fresh nonce, so nobody could have computed it before the registration. Whoever made it held the bytes, or was given them, by T. The verifier recomputes it from the supplied bytes (`possession-mismatch`).

*What it does not add.* Anyone holding the bytes at registration time can compute it. So for content that was already public at T, it adds nothing, and it never excludes a copier. Once the statement is disclosed, the nonce is known, and the possession digest confirms guessed content just as the artifact digest does (§5).

### 4.4 Catalogue commitment (optional)

`catalogue` commits to the private catalogue with the existing salted scheme `sha256-salted-catalogue-v1` ([core](core.md#private-catalogue-commitment)), plus the profile triple. It lets a later comparison report be tied to the registered catalogue (§9) without revealing fingerprints now. A plain catalogue digest is rejected (`catalogue-unsalted`; §5 explains why). The catalogue bytes committed to and later opened MUST be retained as exact raw bytes (never re-serialized before opening), which for the fixtures are the RFC 8785 bytes of the catalogue object (contract §3.3). Verifiers MUST enforce a bounded memory/byte-length cap when checking `C` (`1 MiB` / `1,048,576` bytes in the M4 policy/harness) and stream/bound artifact hashing for `A`.

**Opening nonce `R` (`catalogueOpening.nonceHex`, §9).** The commitment nonce `R` must be 32 fresh random bytes from an operating-system cryptographic random source (`HEX64`: exact 64 lowercase hexadecimal characters, non-zero), drawn independently of `predicate.nonce`. Reusing `predicate.nonce` as `R` is forbidden: `predicate.nonce` is disclosed in plaintext whenever the registration statement is shared, so reusing it would prematurely reveal `R` before any `catalogueOpening` and collapse the salted commitment into an unsalted public-salt digest (`nonce-reused`).

### 4.5 Implementation provenance (B10)

`implementation` and `specCommit` have the report provenance form (contract §6.6), and the same rule applies: the commit is fixed at build time, and only by a verified, clean build (§6.8 B10). An unstamped build refuses to write a registration, as it refuses a report document (`provenance-shape` covers the form only). The fixtures carry placeholder all-zero commits, as `example-report.json` does. Provenance stays cooperative-build evidence: a registration signature attests who registered, not which code ran.

### 4.6 Claims, and the closed key lists

`claims.createdAt` is the only time in the statement, and it is claimed. The checker's lists are closed and are part of the rule:
- **Time keys** rejected anywhere in the predicate (`time-in-statement`): `provedAt`, `timestamp`, `notAfter`, `genTime`, `registeredAt`, `recordedAt`, `time`, `provedTime`.
- **Content keys** rejected anywhere in the predicate, and in hosted-route requests (`forbidden-field`): `fingerprints`, `tokens`, `source`, `text`, `content`, `catalogueBytes`, `opening`, `nonceHex`, `inputBase64`.
- Other unknown fields are rejected (`statement-shape`), and so is a wrong predicate type (`predicate-type`), including the types of earlier drafts.

### 4.7 Self-declared AI use (normative; owner decision 2026-11-24)

The first released predicate carries an **optional** claim, `claims.aiUse`: the registrant's own declaration about generative AI. It is signed with the rest of the statement and **never checked by Traceweave**.

The name is not `generator`. "Generator" reads as "who generated it", which is the authorship reading this design forbids. The sources speak of disclosing AI generation or modification, and `aiUse` follows them.

**Shape (closed).** `"aiUse": {"declared": <value>, "tool": <token, optional>}`. Any other key is `ai-use-shape`.

| `declared` | Meaning (registrant's words, not checked) | EU Code of Practice icon | IPTC digital source type |
| --- | --- | --- | --- |
| `generated` | The content was generated with an AI system | "AI + GENERATED" (Annex 1, Figure 1: "fully AI-generated deep fakes or published text") | `trainedAlgorithmicMedia` ("Created using Generative AI") |
| `modified` | The content was modified with an AI system | "AI + MODIFIED" (Annex 1, Figure 2: "AI-manipulated/partially modified") | `compositeWithTrainedAlgorithmicMedia` ("Edited using Generative AI") |
| `no-generative-ai` | No generative AI system was used | none; the Code labels AI content only | none (see below) |

**Absent means nothing was declared.** A statement without `aiUse` is never read, rendered or exported as "no AI" or "human-made". The verification result always carries `declaredAiUse`; when the claim is absent it is `{"status": "not-declared"}`, so a JSON consumer cannot read a gap as "none".

**Fixed at registration.** `aiUse` is inside the signed statement. Changing it changes the signature, every time evidence over that signature, `statementSha256` and the `tw1-` reference (§9.1). A declaration cannot be added or changed after registration without making a new registration, which gets its own, later time bounds.

**Sources, pinned.**
- **EU Code.** The [Code of Practice on Transparency of AI-Generated Content](https://ec.europa.eu/newsroom/dae/redirection/document/129555), 2026-06-10, the final text (38 pages, SHA-256 `7bd22c5a3c56eaefda27a5bf7a6118198ef2a9c9255241bd97abf7cdedf9bc28`).
  - **How it was obtained, so a third party can repeat it:** on 2026-11-24, one HTTPS GET of that URL with Python 3.14.6 `urllib.request` (header `User-Agent: Mozilla/5.0`; the redirect URL served the PDF directly, 1,213,943 bytes). `curl` from the same machine failed with "unable to get local issuer certificate", as it did for the reviewer, while Python's own CA store accepted the chain.
  - **What was read:** the text, extracted with `pdftotext -layout` (poppler 26.07.0), including Section 2 Measure 1.1 and the Annex 1 text on pages 37–38. The icon texts "AI + GENERATED" and "AI + MODIFIED" are quoted from that **text**. The Figure 1–3 **images** were not viewed, so the mapping to the icon artwork itself is unverified. Its labelling vocabulary is two icon texts in Annex 1, "AI + GENERATED" and "AI + MODIFIED", plus a basic "AI" icon, with Section 2 Measure 1.1 (b) encouraging "text indicating 'modified' or 'generated'". The Code has no finer taxonomy, so this list has exactly those two AI values.
- **IPTC.** The [IPTC Digital Source Type scheme](https://cv.iptc.org/newscodes/digitalsourcetype/) (`http://cv.iptc.org/newscodes/digitalsourcetype/`), `dateReleased` 2024-10-23, CC BY 4.0, SHA-256 `e9178aa2…99a6` of the JSON fetched 2026-11-24.
- **Why `modified` maps to `compositeWithTrainedAlgorithmicMedia`.** The Code's "AI + MODIFIED" is for content that is "AI-manipulated/partially modified". That is a change made to existing content, which matches IPTC's "Edited using Generative AI" ("Augmentation, correction or enhancement using a Generative AI model").
  - IPTC `compositeSynthetic` ("Mix or composite of several elements, at least one of which is Generative AI") describes assembling elements. That fits text into which AI-written passages were pasted, which the Code would also label MODIFIED.
  - One term per value keeps the mapping single-valued. A later version may add `compositeSynthetic` as a value of its own, if the owner wants that distinction; that is a value change and would need a version step.
- **No IPTC term for `no-generative-ai`.** IPTC's nearest non-AI terms (`digitalCreation`, "Media created by a human using non-generative tools", and `humanEdits`) assert human creation. Mapping to them would turn a declaration into an authorship statement, so `no-generative-ai` maps to no IPTC term and is never exported as one.
- Both sources are recorded in the [source register](../docs/sources.md).

**Tool identifier (optional).**
- **Where allowed:** only with `generated` or `modified`.
- **Pattern:** `[A-Za-z0-9][A-Za-z0-9._+-]{0,63}`, matched against the **whole** value (a trailing newline does not match), one token. It cannot hold a space, `/`, `:`, `@` or `\`, so URLs, paths, e-mail addresses and names written with a space are `ai-use-shape`.
- **No origin statements inside the token (A1).** The token is split at `.`, `_`, `+` and `-` and at case changes (`Penned-by-Bob` → penned, by, bob; `NoAIUsed` → no, ai, used). It is `ai-origin-claim` if any part is on one of these lists, or if the parts read as the §11 never-shown wording:
  - **human origin and attribution:** `human`, `humans`, `humanly`, `person`, `people`, `handwritten`, `handmade`, `hand`, `manual`, `manually`, `penned`, `pen`, `written`, `wrote`, `typed`, `authored`, `author`, `by`, `me`, `myself`, `self`, `mine`, `organic`, `natural`, `real`, `genuine`, `original`;
  - **negation:** `no`, `not`, `non`, `none`, `never`, `without`, `zero`, `free`, `nil`, `null`, `only`.

  The review's examples are all rejected, with mixed-case and separator variants: `human-made`, `Human-Only`, `Handwritten`, `not-AI`, `no-ai-used`, `by-Alice`, `Penned-by-Bob`, `HUMAN_MADE`, `humanMade`, `Not.AI`, `NoAIUsed`, `penned+by+bob`, `AI-free`, `100pct-Human` (`neg-ai-use-tool-*`). The rule is deliberately broad: a real product name containing such a word (for example "…Free…") is refused, and the registrant leaves the tool out.
- **Rendering frame.** The tool is shown only as a quoted identifier in a fixed frame: `Tool identifier given by the registrant: "<token>". Traceweave did not check this.` It cannot read as a sentence about the content.
- **Residual risk.** A single-word personal name ("Alice") cannot be excluded mechanically. The frame names it only as an identifier the registrant gave, never as the subject of a sentence about a person.

**How the authorship rule stays intact.**
- **Key rule.** A key in `authorship`, `author`, `owner`, `ownership`, `creator`, `original` or `originality` (case-insensitive), **anywhere inside `aiUse`**, is `authorship-claim`.
- **Value rule.** A tool token that, with `-`, `_` and `.` read as spaces, matches the §11 authorship deny-list (`author…`, `wrote`, `written`, `belongs`, `creator`, `created`, `own…`, `original…` and the rest) is `authorship-claim`.
- **Origin rule.** The token rule above (`ai-origin-claim`). The never-shown check also runs on **every** rendered line, template or not, so a template-matching line cannot carry origin wording through its token.
- **Why this keeps the rejection whole.** The claim's own names (`aiUse`, `declared`, `tool`, `generated`, `modified`, `no-generative-ai`) are on neither list, so the existing rejection is unchanged.

**What it never affects.** A declaration changes **no** trust, time, key-event, digest or possession outcome. The verification result always carries `declaredAiUse`: `{declared, tool, euCodeIcon, iptcDigitalSourceType, status: "declared-not-checked"}` when the statement carries the claim, and `{status: "not-declared"}` when it does not. A result whose other outcomes differ because of the claim is `ai-use-affected-outcome`.

**Format and fixtures.**
- **Change log.** Draft-5, amended 2026-11-24: optional `claims.aiUse` added (owner decision). Addendum fixes, the same day: the A1 token rule, the quoted tool frame, full-value matching, and `declaredAiUse` always present.
- **Format impact.** The predicate version stays `traceweave-registration-draft-5`. The field is optional, every existing draft-5 statement remains valid and byte-identical, and draft-5 is unreleased. A verifier built before this section rejects a statement carrying `aiUse` as `statement-shape`, which is the correct behaviour for an unknown field. **No existing fixture changed.**
- **Positives:** `bundle-ai-use-*`, `verification-result-ai-use-*` and `rendering-ai-use-*` for each value, plus `rendering-ai-use-absent`.
- **Negatives:** `neg-ai-use-*` for:
  - an unknown value, an extra key, a missing value;
  - a URL, path, e-mail or spaced name as tool, and a tool alongside `no-generative-ai`;
  - an authorship word in the tool, and an authorship key;
  - a dropped not-checked sentence;
  - "AI-generated" and "human-written" as properties;
  - an absent claim rendered as "no AI";
  - a declaration that changes trust.
- **Self-test:** six wrong-implementation cases.

## 5. What publishing each value reveals

A registration is **private by default**. The registrant keeps the bundle; only digests of signatures go to time services (§6). The table assumes the item named is published, for example in a dispute.

| Published value | Reveals about unknown content | Guessing attack | Verdict |
| --- | --- | --- | --- |
| Digest of a DSSE signature (what time services see) | Nothing; the statement contains a fresh 256-bit nonce | None feasible | Safe to send. Links the evidences of one registration to each other and to the requester's IP address and timing (T1 §4 item 5, T4) |
| Artifact digest (`subject`) | Nothing about content the attacker lacks | **Confirmation:** anyone holding a candidate file confirms exact equality. Low-entropy content (a short snippet, a template with few variants) can be enumerated | Disclose only with the bytes, in a dispute |
| Possession digest | Nothing without the nonce. After disclosure, the same as the artifact digest, so short snippets are not protected by it either | As the artifact digest, after disclosure | Disclosed with the statement |
| Salted catalogue commitment | Nothing until opened | None before opening. **Opening reveals the whole catalogue** (core) | Safe in the statement |
| Plain catalogue digest | Nothing directly | **Whole-set confirmation:** catalogues are deterministic in their artifacts, ids and configuration (contract §3.3), so anyone with candidate files and guessed ids rebuilds and confirms | Never (`catalogue-unsalted`) |
| Fingerprints | Structure, positions and spans | **Fragment membership:** anyone can fingerprint any text and learn which fragments the private content contains | Never in a registration (`forbidden-field`) |
| Public key | Links every registration made under it | — | One key per registrant (I0) links all disclosed registrations and all time-service requests under it. A per-work key avoids that, at the cost of identity continuity (§7) |
| OIDC identity in a public log | Identity, time and the logged digest, **for ever** (T3) | — | Opt-in only, owner-gated |

## 6. Time evidence

### 6.1 What is time-stamped (A1)

Each evidence targets **one** object:
- **A signature:** `target: {kind: "dsse-signature", signatureIndex, sha256}`. `sha256` is the SHA-256 of the **raw decoded signature bytes** (64 bytes for Ed25519), not of the base64 text in the envelope (`neg-evidence-target-base64`). This follows Sigstore's countersigning advice and C2PA's v2 payload (T3, T6).
- **An earlier evidence's token**, for renewal only (§6.6): `target: {kind: "evidence-token", evidenceIndex, sha256}`.

A signature exists only after its statement does, so a bound on the signature bounds the statement, including its subjects and possession digests. The bound also survives a later theft of the key: a thief can sign new statements but cannot obtain evidence dated before the theft. Evidence over another digest, such as the statement bytes, is rejected (`evidence-wrong-target`). So is an index the envelope does not have (`evidence-shape`; `neg-signature-index-out-of-range`).

### 6.2 Evidence types: fields, checks and bounds

Every evidence has `evidenceVersion`, `type`, `placeholder`, `notice`, `target`, `root: {kind, anchorSha256}` and `token`.
- **Placeholder evidence** (`placeholder: true`) adds one type-specific object, and its `token` text starts with `PLACEHOLDER`.
- **Real-format evidence** (`placeholder: false`, §6.5) carries the real token (and, for RFC 3161, the request) as base64, and every field is read from it.

A root identified by anything other than an anchor digest is rejected (`root-not-anchored`). Wrong labelling is rejected (`placeholder-unlabelled`). Malformed evidence is `evidence-shape`.

**`rfc3161`**, root kind `tsa-certificate-chain`. Placeholder fields: `rfc3161: {genTime, accuracySeconds (optional), policyOid, nonce, requestNonce, signerCertificate: {notBefore, notAfter}}`. The checks below run in this order, and the real-format vectors exercise every one (S2):
1. **Imprint.** `messageImprint.hashAlgorithm` is `id-sha256` and `hashedMessage` equals `target.sha256` (RFC 3161 §2.4.1–§2.4.2); otherwise `tsa-imprint-mismatch`.
2. **Request nonce.** The producer sends a fresh nonce in the request (§2.4.1) and checks that the token echoes it with the same imprint. That is what detects a replayed response at request time; otherwise `tsa-nonce-mismatch`.
3. **Signing certificate.** The SigningCertificate attribute, ESSCertIDv2 (RFC 5816 §2, "MUST be included") or ESSCertID, identifies the certificate named by the SignerInfo; otherwise `tsa-signing-cert-mismatch`.
4. **Key usage.** That certificate carries exactly one extended key usage, `id-kp-timeStamping`, marked critical (RFC 3161 §2.3); otherwise `tsa-eku-invalid`.
5. **Signature.** There is exactly one SignerInfo; signed attributes appear at most once each; the TSTInfo `version` is 1; the `messageDigest` attribute equals the SHA-256 of the TSTInfo; and the signature over the signed attributes verifies; otherwise `tsa-signature-invalid` (`evidence-shape` for the version, D8).
6. **Path validation** (RFC 5280, at `genTime`; D4). The verifier builds the path from the TSA certificate through the token's certificates to the **pinned root certificate** whose SHA-256 is the anchor (otherwise `untrusted-root`). On that path:
   - every signature verifies;
   - every certificate, the root included, is valid at `genTime`;
   - every issuer has basicConstraints `cA=TRUE` and, if keyUsage is present, `keyCertSign`;
   - no `pathLenConstraint` is exceeded;
   - no certificate carries a critical extension the verifier does not understand;
   - the TSA certificate's keyUsage, if present, asserts digitalSignature or nonRepudiation.

   Path building tries every candidate issuer and backtracks, because the SignedData `certificates` field is unsigned. A decoy inserted first must not turn a valid token into `path-invalid` (`verification-result-real-decoy-first`). Any failure is the outcome `path-invalid`. The leaf keyUsage check has no openssl cross-check, because openssl refuses to issue such a token. A signatures-only chain check is **not** enough: it accepts a TSA certificate issued by an end-entity certificate, and one under an expired intermediate, both of which `openssl ts -verify` rejects (`real-format/MANIFEST.json`; `verification-result-real-issued-by-end-entity`, `-expired-intermediate`).
7. **Policy OID.** The token's `policy` must be one the verifier's policy lists for that anchor (outcome `wrong-policy`).
8. **Certificate validity.** `genTime` must lie within the TSA certificate's validity (outcome `invalid`).
9. **Revocation** (RFC 3161 §4 items 1–2; §6.7). An entry applies only to the certificate it names, the TSA certificate or an intermediate on the path (D5). Revocation **without** a reasonCode, or with `keyCompromise`, invalidates **every** token whose path includes that certificate, including past ones (outcome `revoked`). With reasonCode `unspecified`, `affiliationChanged`, `superseded` or `cessationOfOperation`, tokens before the revocation time stay valid (`verification-result-revoked-retaining`). Missing revocation data gives `no-revocation-data`.
10. **Expiry.** If the verification time is after the TSA certificate's expiry, the token counts only through a renewal (§6.6); otherwise `expired-unrenewed`.
**Supported algorithms (D7).**
- **The checker:** RSA PKCS #1 v1.5 signatures with SHA-256 (`rsaEncryption` or `sha256WithRSAEncryption`), SHA-256 message digests, and ESSCertID (SHA-1) or ESSCertIDv2 with SHA-256, SHA-384 or SHA-512.
- **Reported as the outcome `unsupported`, never as a forgery code:** ECDSA, RSA-PSS and SHA-384/512 signatures (`verification-result-real-ecdsa`; openssl verifies that token). An implementation for REG.3 must support what the chosen TSAs actually issue, and state it.
- **Not built:** high tag numbers, `subjectKeyIdentifier` signer identifiers, name constraints, policy mappings and revocation fetching.

11. **Bound.** `notAfter = genTime + accuracy`, **rounded up to the whole second** when `genTime` or the accuracy has fractional parts (N1). Accuracy comes from the token, else from the verifier's policy for that anchor (RFC 3161 §2.4.2); with neither, the outcome is `unsupported` (A3).

**`opentimestamps`**, root kind `bitcoin-proof-of-work`. Placeholder fields: `opentimestamps: {status: "pending"}` or `{status: "complete", blockTime}`.
- **Pending.** A pending proof has no time, and stating one is rejected (`pending-counted`).
- **Real-format proofs:**
  - The checker applies the proof's operations to the target digest (python-opentimestamps serialization, pinned at `8c3dc6fb`). The proof's file digest must equal the target (`evidence-wrong-target`).
  - The attested block header is read from the verifier's **own** header source, never from a bundle. Its first header's SHA-256 is the anchor. The policy also pins a **checkpoint**: the SHA-256 of the raw header at a height of at least the attested height plus `minConfirmations`, taken from the verifier's own node (D3).
  - The checker verifies that the header's Merkle root equals the commitment, checks proof of work up to that height, and **links back from the checkpoint** through the previous-header hashes to the attested header.
  - Pinning the first header is not enough. Proof of work against each header's own `nBits` lets anyone re-mine an easy fork on top of it, with any attested time (`neg-real-ots-forked-headers`: 2001-01-01).
  - Without a checkpoint the outcome is `unsupported`. The attested height must satisfy `height ≤ checkpoint.height − minConfirmations`, with `minConfirmations ≥ 1` validated in the policy; otherwise the outcome is `insufficient-confirmations`. Without that rule, a header file kept real up to the checkpoint and forged above it would pass, for an attested height above the checkpoint (draft-4 review; `neg-policy-min-confirmations-zero`).
  - It takes `blockTime` **from that header, never from the evidence** (N2).
- **Offline.** "Verifiable offline" holds only with such a header source (T4: "a local Bitcoin Core node (a pruned node is fine)").
- **Margin and its assumption.** `notAfter = blockTime + 7,200 s`. An upper bound on existence needs a header time that cannot lag the real mining time by much. Consensus gives only that a header time must exceed the median of the previous 11 blocks. That keeps the lag to roughly an hour **only under an honest-majority assumption**: most recent blocks were mined by honest miners with roughly correct clocks. The 7,200 s margin covers that with slack. The two-hour future rule bounds the other direction and does not justify the margin (draft-1 had this backwards). See RD6 for the alternative.

**`rekor-v2`**, root kind `log-key`. Fields: `rekorV2: {logIndex}`. **No bound**: Rekor v2 has no time of its own (T3), and stating one is rejected (`log-time-claimed`). Inclusion and discoverability only.

**`traceweave-witness`**, root kind `witness-service-key`. Fields: `witness: {bundle}`. The bundle holds the witness's signed statement over the presented signature digest (§19), with the witness's own RFC 3161 evidence over the witness signature.
- The anchor is the SHA-256 of the witness public key, computed from the bundle.
- The bound is the witness's TSA bound, not the witness's clock.
- It rests on **two** anchors, the witness key and that TSA, and counts in both groups (§6.3, S4).

**`cosigned-checkpoint` is removed in draft-3** (S5). A cosignature bounds a checkpoint, not our digest. Without an inclusion proof of the signature digest at that checkpoint, it shows nothing about the registration. If needed later, it returns with an inclusion proof and the checkpoint body. The old type is `evidence-shape` (`neg-checkpoint-type-removed`).

### 6.3 Roots, independence and the policy (F2, S4)

The verifier's policy lists accepted anchors:

```json
"timeRoots": [{"anchorSha256": "…", "kind": "tsa-certificate-chain", "independenceGroup": "tsa-operator-a",
               "policyOids": ["…"], "accuracySeconds": 1, "rootCertificate": "…"},
              {"anchorSha256": "…", "kind": "bitcoin-proof-of-work", "independenceGroup": "bitcoin",
               "headerFile": "…", "minConfirmations": 6, "checkpoint": {"height": 12, "headerSha256": "…"}}, …]
```

- An evidence whose anchor is not listed for its kind is `untrusted-root`.
- Independence is decided **only** by the policy's groups. A producer-written label never counts (`root-not-anchored`). Two TSAs under one CA share an anchor, so they count once (`neg-quorum-same-anchor`).
- **An evidence that rests on several anchors joins their groups.** Groups that co-occur in one evidence are merged (union-find over all evidence of the bundle), and each merged class counts once. So a witness whose time comes from TSA A, plus a direct TSA A token, is **one** source (`verification-result-witness-shared-tsa`: `below-quorum`). With the witness on TSA B, they are two (`verification-result-witness-independent`).

### 6.4 Per-signature bounds and quorum (F1)

For **each signature** i, only evidence whose target is signature i counts; renewals never do.
1. Take the smallest valid `notAfter` in each independence class.
2. Sort those values.
3. `notAfterAnyRoot` is the smallest. One source vouches for it, so one dishonest or compromised source can backdate it.
4. `notAfterQuorum` is the q-th smallest (default q = 2).

Both bounds are always reported, with `distinctRoots`. A signature with no evidence of its own has **no** bound, and a later co-signature never inherits an earlier bound (`key-bound-misattributed`). Removing an evidence from a bundle can only make bounds later or remove them (N3; `verification-result-stripped`).

### 6.5 Real-format vectors (S9, S10)

`test-vectors/registration/real-format/` holds real-format vectors made by `make_real_vectors.py`. No external service was contacted. **Their anchors must never be trusted.**
- **TSA tokens.** A local `openssl` (version in `MANIFEST.json`) creates a test-only root CA and a TSA certificate with a critical `id-kp-timeStamping` EKU, then issues RFC 3161 tokens over the fixture signature's digest.
- **openssl cross-check.** `MANIFEST.json` records `openssl ts -verify` for **every** token, and the checker agrees with it on every one:
  - OK for the good token, and for the token over another digest when checked against its own request;
  - FAILED for the tampered (digest failure), non-critical-EKU (unsuitable purpose), wrong-ESS (ESS cert id not found), end-entity-issued (invalid CA certificate) and expired-intermediate (certificate has expired) tokens.
- **Negative variants:**
  - a token over another digest;
  - a token whose `genTime` was edited after signing;
  - a token re-signed under a certificate whose EKU is not critical;
  - a token whose ESSCertIDv2 names another certificate.

  The last two were re-signed with `openssl pkeyutl`.
- **OpenTimestamps.** A proof in the python-opentimestamps format commits the digest through append, SHA-256 and prepend operations into the Merkle root of header 4 of a 13-header chain. The chain was mined locally at regtest difficulty (`nBits` 0x207fffff), so its proof of work is real but trivial. There is also a pending proof, a proof for another digest, an unrelated chain, and a **forked** chain. The fork is re-mined on the same first header, with the commitment at height 4 and time 2001-01-01; it passes per-header proof of work and fails only the checkpoint (D3). The checkpoint (height 12) is recorded in the manifest.
- **What the checker does with them.** It verifies them with `realformat.py`, standard library only: DER, X.509, CMS, RSA PKCS #1 v1.5, and the OpenTimestamps operations and headers. It computes the anchors itself from the pinned root certificate and the header file (S10).
- **What it is not.** `realformat.py` is not a general path validator: no name constraints, policy mappings or revocation fetching.
- **Not reproducible.** The tokens carry their issuing time and a random nonce, so the build does not regenerate them. Rerun `make_real_vectors.py` after any change to the statement, because the tokens are bound to its signature. The private keys exist only in a temporary directory during that run.
- **Placeholder fixtures still trust producer-written anchors and dates.** Only the real-format vectors test the anchor computation, and REG.1 must name them (S10).

### 6.6 Renewal (S6)

A **renewal** is an `rfc3161` evidence whose target is `{kind: "evidence-token", evidenceIndex: j, sha256}`, the SHA-256 of evidence j's token bytes (for placeholders, the UTF-8 token text). This is RFC 4998's timestamp renewal: a new token over the old one.

**Rule:** at verification time V, if V is after the expiry of evidence j's TSA certificate, evidence j counts only if some valid renewal of it has `notAfter` no later than that expiry. A renewal is itself an RFC 3161 evidence and may need renewing in turn. A renewal never adds to any signature's bounds.

**What the renewal covers (D9).** It hashes only the earlier token's bytes. It therefore relies on the policy's `revocationData` for that token's path (§6.7): the revocation data, retained with the bundle, must show the certificate unrevoked. RFC 3161 §4 item 3 asks for "authentic copies of old CRLs", and RFC 4998 covers verification data too. Including the chain and revocation data in the renewed bytes is the stronger form, and it is left for when renewal is implemented (RD11).

**Not covered:**
- Renewal does **not** rescue a token whose TSA key was revoked without a retaining reasonCode or for `keyCompromise`. RFC 3161 §4 item 2 says such tokens "cannot be trusted anymore". RFC 4998 renewal guards against expiry and algorithm ageing, not compromise.
- Hash-tree renewal over the original data (RFC 4998 §1.2), needed if SHA-256 weakens, is outside this draft. It needs a new statement over a new digest, so it is a new registration that references the old one.

Fixtures: `bundle-renewed`, `evidence-renewal`, `verification-result-renewed` (V = 2032; TSA A survives through a 2030 renewal, TSA B does not), `verification-result-expired`, `neg-expired-accepted`, `neg-renewal-wrong-target`.

### 6.7 Revocation data and "as of" (S3)

The policy's `revocationData` lists, for each TSA anchor, the `source` of the revocation data used (a CRL or OCSP response, retained with the bundle), its date `asOf`, and the revocations found. Each revocation is `{certificateSha256, revokedAt, reasonCode}` and names one certificate, the TSA certificate or an intermediate, never the whole root (D5). Revoking signing certificate 1 under TSA A's root leaves certificate 2's token valid (`verification-result-revoked-one-unit`; `neg-revocation-by-root`).
- A token whose anchor has no revocation data is `no-revocation-data`.
- Each RFC 3161 evidence in the result reports `revocationDataAsOf`.
- **An offline result holds only as of that date.** A later `keyCompromise` revocation can still invalidate the token retroactively (§6.2, RFC 3161 §4 item 2).

## 7. Signer identity options

| Option | What a verifier learns | Cost to the registrant | Privacy |
| --- | --- | --- | --- |
| I0 Self-managed Ed25519 key, public key only in the bundle (**default**) | "Whoever holds this key signed it." Nothing about who that is. Later, the key holder can show control by signing a challenge | None. Must keep the key safe and backed up | Nothing published. One key links all disclosed registrations |
| I0′ A fresh key per work, optionally linked later by a signed key list | As I0, per work | Key management per work | Disclosing one registration does not link the others. Proving that two works share a creator needs the key list |
| I1 I0 with the public key posted somewhere dated and third-party-observable | A weak link between key and a name, as strong as that site's history | None | Key linkable to the name |
| I2 Sigstore Fulcio short-lived certificate (OIDC) | "Someone who authenticated as this identity at an OIDC provider signed it" (T3). Needs time evidence: the certificate lasts 10 minutes | An identity-provider account | Identity and time in public CT and Rekor logs **for ever** |
| I3 Organisation or qualified certificate | The CA's identity checks, under its policy | Paid; identity verification | Whatever the certificate contains |

The key id is a lookup hint, not identity ([attestations](attestations.md)). Signer trust is the verifier's policy decision, listed by SHA-256 of the full public key (`trustedKeys`; B3), and reported separately from signature validity.

## 8. Key identity, rotation, compromise and revocation (F3, B1–B3, S1)

**Key identity (B3).** Every decision about a key uses the SHA-256 of its raw 32-byte public key:
- the policy's `trustedKeys`;
- a key event's target, which is its subject digest;
- a rotation's successor, from `successorPublicKeyHex`;
- the signer of an event.

`keyid` (16 hex digits) is only a lookup hint. A policy that lists 16-hex keyids, or the draft-2 field `trustedKeyids`, is `key-identity-by-hint`. An event whose `keyid` does not equal the first 16 hex digits of its subject digest is `key-event-shape` (`neg-key-event-subject-mismatch`).

**Key events are statements too.** A key event is an in-toto statement whose single subject is the target key (digest = SHA-256 of the public key), with predicate `{eventVersion, keyid, event, successorPublicKeyHex (rotated only), compromisedNotBefore (compromised only)}`. It is signed and time-stamped like a registration. Its **proved time E** is its own quorum bound (§6.4); without one it is `ignored-no-proved-time`.

**The procedure: two passes, no fixed point (draft-5, E1).** Key events are evaluated by a terminating procedure that cannot oscillate, by construction:
1. **Identity and signature count.** A key-event envelope carries **exactly one** signature. Any other number is the named rejection `key-event-signatures`. Envelope signatures are not signed, so without this rule anyone carrying a K-signed event file could prepend their own signature and make it load as an `ignored-unauthorized` event by that key, a silent mask (draft-5 review F1; `neg-key-event-two-signatures`, `neg-result-with-foreign-signature`; the enumeration's loading sample includes the case). Each event is identified by the SHA-256 of its payload **and** signature. One statement signed by two keys is two events; the same signed statement supplied twice is one event with its earliest proved time. (An enumeration finding: draft-4 used the payload alone, so a thief's re-signing of the owner's statement collided with it; `verification-result-same-statement-two-signers`, `neg-event-identity-collision`.)
2. **Pass 1, standing,** in order of proved time E, with ties broken by the event identity. "Earlier" always means a smaller E, never a position in the input. Each event's status is decided once, from events with a smaller E:
   - **Authorization.** It is authorized if signed by its target key, or by the successor named in an applied rotation of that key with a smaller E. The rotation may be disputed or not: a disputed rotation passes on no trust, but its successor may still speak about the old key, which can only restrict. Otherwise the event is `ignored-unauthorized`.
   - **Supersession (D1, D2).** The first applied `rotated` or `retired` event for key K supersedes K. After it, events signed by K other than `compromised`, and later rotations or retirements of K by anyone, are `ignored-superseded`. A retired or rotated-away key cannot rotate again (`verification-result-retired-then-rotated`; `neg-retired-key-rotates`). A much later second rotation cannot erase the honest successor chain (`verification-result-late-second-rotation`; `neg-late-rotation-erases-chain`).
   - **Pass 1 never consults disputes,** so nothing computed later can withdraw the standing of the event that caused it.
3. **Pass 2, disputes,** over the events applied in pass 1:
   - **Equal-time supersessions.** Two different supersessions of K at the same E are both `disputed`. An equal-time tie must not be won by grinding the identity that breaks ties (`verification-result-retired-and-rotated-same-time`).
   - **Compromise windows.** An applied `compromised` event for K, with claimed start Tc and proved time E, defines `start = max(Tc, E − lookback)`. It disputes every applied rotation or retirement of K with proved time ≥ `start`, **except the rotation that gives the report's own signer standing**: a successor's report never disputes its own appointment. Every rotation of the target **to the report's signer** counts as that one appointment. Two different statements of K→S (for example, re-serialized) proved at the same time are twins, not a conflict, and the report disputes neither. Without this, S stayed trusted through one twin while the result listed the other as `disputed`, a cosmetic edge case (draft-5 review note; `verification-result-e1-twin-rotation`).
   - Disputes never feed back into pass 1. There is no iteration, so there is no pass limit, and no state in which the evaluation has "not settled". An implementation that iterates and fails to settle is wrong, and must report an error, never a verdict.

**Why the own-standing exemption is the right answer (E1).**
- **The honest flow.** K leaks, so the owner rotates K→S at T and then, with S, reports K compromised at T+10 d from T−5 d.
  - **Draft-4** let that report dispute K→S, which removed S's standing to make the report, which removed the dispute, and so on. The result depended on the parity of the number of events supplied: adding one rejected event flipped S to `untrusted`, two flipped it back.
  - **Draft-5:** K→S stays applied, the report is applied, S is **trusted**, and K's own signatures bounded in [T−5 d, T) are `disputed`. Adding 0, 1 or 2 rejected events gives byte-identical outcomes (`verification-result-e1`, `-e1-extra-1`, `-e1-extra-2`, checked by `result-equivalence-e1`; the draft-4 behaviour is the review case `neg-extra-event-changed-result`).
- **Why this is right.** A successor's report is a statement by S that its own predecessor leaked. S has no reason to undercut the rotation that appointed it, and a report that could undo its own authority is self-defeating.
- **The other case.** If the rotation itself was made by a thief, the owner reports with K, as the target's own key. That report has no appointment to protect, and it does dispute the thief's rotation (`verification-result-rotation-hijack`).
- **One level down.** S2 reporting S within 30 days of S→S2 behaves the same (`verification-result-e1-second-level`).

**Trust flows forward only.** A successor is trusted only through an applied, undisputed rotation proved **strictly after** its signer became trusted. The draft-4 enumeration found that equal-time K→S and S→S2 let S2 become trusted (`verification-result-chain-same-time`; `neg-chain-same-time`).

**Recovery keys (RD18).** The policy field `recoveryKeys: [{keySha256, recovers, notBefore}]` lists, in advance, a key that replaces a trusted key `recovers`. It is trusted only for bounds at or after `notBefore`, never retroactively. It does not sign events for the key it recovers; it is a new trust root with a start time (`verification-result-recovery-key`). Without such a field, the only in-band form would have been an extra `trustedKeys` entry, trusted for every bound. The draft-4 review rightly said that was not a recovery mechanism.

**Enumeration test (widened for draft-5).** `test-vectors/registration/enumerate_key_events.py` has two parts.
- **Dictionary enumeration.**
  - **Alphabet:** {rotate, retire} × {signed by the current honest key, the old key, the successor, an attacker} × 5 proved-time steps, plus {compromise} × the same four signers × 5 steps × 3 claimed starts: 100 symbols.
  - **Steps and claims:** steps of −40, −10, 0, +10 and +40 days, so both shorter and longer than the 30-day look-back. Claimed starts 2, 20 and 60 days before the report.
  - **Coverage:** every sequence of length 1 to 3 (1,010,100), and a seeded random sample of 200,000 sequences of length 4.
  - **Probes:** each key at the final time, far before, at E − 1 s and E of every event, at start − 1 s and start of every compromise window, and without quorum.
- **Loading sample.** 300 sampled sequences are rebuilt as **real signed key-event bundles** with the builder, and evaluated through `load_event_bundles`. Some events are tampered (bad signature), some left without a proved time (one source), and some given a subject that disagrees with the keyid. Outcomes must equal the dictionary path's.
- **Invariants:**
  - **I1** order independence;
  - **I2** removing rejected events changes nothing (the draft-4 "attacker-signed events" form was wrong, because an attacker key gains standing legitimately once the old key rotates to it);
  - **I3** supersession;
  - **I4** no trust at or after a key's own supersession or compromise start;
  - **I5** trust only through undisputed rotations from a trusted key;
  - **I6** the honest chain is final after the window, against late events signed by the old key **or the successor**;
  - **I7** the thief window;
  - **I8** inside a compromise window the key is never trusted, and just below its start trust is as without the report;
  - **I9** no-quorum signatures of touched keys are never trusted;
  - **I10** adding a rejected event (a retirement, report or rotation by a key without standing) changes nothing;
  - **I11** who may sign;
  - **I12** equal-time supersessions are both disputed;
  - **I13** a report never disputes its own appointment.
- **Mutation check.** The same invariants are run on length ≤ 2 against three weakened rule sets: no supersession or disputes; trust through disputed rotations; and **the draft-4 fixed point**, which catches E1. Counts are in §20.

**RD18 re-examined: what an honest owner sees.**
- **Owner rotates first** (K→S), and K leaks later.
  - Everything the thief signs with K is ignored, except a compromise report.
  - A report filed within the look-back window after the owner's rotation disputes it **permanently**: S never regains trust, and K cannot be rotated again. The owner must then recover through a pre-listed recovery key or out of band (I1, I2).
  - After the window, the honest chain is final, whoever signs the late report (I6).
  - **The owner's own successor-signed report never harms the owner's chain** (E1).
- **Thief rotates first** (K→A), and the owner reports with K, from before the thief's rotation, within the window: the thief's rotation is disputed and A gains nothing. The owner's later rotation of K is ignored as superseded, so the owner continues with a recovery key or out of band.
- **Owner retires K.** Nothing signed with K afterwards counts, except a compromise report, which can only reduce trust.

**Effect on a signature by key D**, where B is that signature's **quorum bound** (S1):
1. **Trusted set.** D is in the trusted set if it is in `trustedKeys`, or is the successor of an applied, undisputed rotation of a trusted key that was proved strictly after that key became trusted. A successor is trusted only for signatures with B ≥ the rotation's E. Otherwise the signer is `untrusted`.
2. **No quorum (S1).** If any applied or disputed event targets D, or names D as successor, and the signature has **no quorum bound**, the signer is **`disputed`**, never `trusted`. One source could have moved the bound across the event (`verification-result-single-source-event`; `neg-trust-without-quorum`).
3. **`compromised` (applied):** B < `start`: trust unchanged; `start` ≤ B < E: `disputed`; B ≥ E: `untrusted`.
4. **`retired` or `rotated` (applied, disputed or not):** B ≥ E: `untrusted`; earlier signatures are unchanged.

**Why an early-dated false claim cannot erase honest history.** The event's effect starts no earlier than E − lookback. Inside that window the outcome is `disputed`, shown with both times, not silently `untrusted`. Registrations bounded before the window keep their trust (`verification-result-compromise-early`). The trade-off: an honest owner who discovers a theft later than the look-back window cannot dispute registrations made before it (RD15).

**Key loss.** Existing registrations stay verifiable, because the bundle carries the public key and each signature's bound. Recovery is a new key, linked through I1 or I2.

**TSA revocation** is a separate input: the policy's `revocationData` (§6.7).

## 9. How a comparison report references a registration

The report body is closed (contract §6.2, §7). A report never embeds a registration. A separate **report link** joins them:
- `report`: the report path and `bodySha256`, recomputed from the canonical body (`report-digest`).
- `registration`: the bundle, and the SHA-256 of the statement payload bytes (`statement-digest`).
- `links`: for each pair, the role, the subject index and the digest. The report pair's digest, the link digest and the registered subject digest must be equal (`subject-mismatch`).
- `catalogueOpening` (optional): the catalogue bytes (the exact stored bytes; RFC 8785 bytes of the catalogue object in the fixtures) and `nonceHex`.
  - `nonceHex` must be exact 32-byte lowercase hex (`HEX64`) and non-zero (`nonce-invalid`).
  - `nonceHex` must be distinct from the registration statement's `predicate.nonce` (`nonce-reused`).
  - They must open the registered commitment (`catalogue-does-not-open`).
  - They must hash to the report's `referenceCatalogueSha256` (or `candidateCatalogueSha256` when every linked entry has `role: "candidate"`, `catalogue-not-report-input`).
  - The registered profile must equal the report's (`profile-mismatch`).

  Opening reveals the whole catalogue to whoever receives the link.
- `notShown`: the §11 list.

This shows that the reference artifact compared in the report is byte-identical to content registered under the named key no later than that signature's bound. It shows nothing about the candidate's origin, about direction of copying, or about anything contract §8 forbids.

### 9.1 Text reference (normative; frozen 2026-11-24)

Pasted text cannot carry metadata, so a registrant can paste a short reference next to it. The format is frozen before any registration is shared, because a reference already printed next to someone's text cannot be re-derived later. This section changes **no** statement field: the reference is computed from `statementSha256`, the SHA-256 of the exact statement payload bytes (§9).

**Format.** `tw1-` followed by 27 characters:
1. **Prefix.** `tw1-`, in lower case. `tw` names the scheme and `1` its version. Any other prefix, version or separator is `reference-shape`.
2. **Body.** 26 characters encoding the **first 130 bits** of `statementSha256`, most significant bit first, 5 bits per character.
3. **Check.** One **Luhn mod 32** check character over the body, computed with the same alphabet (factor 2 on the rightmost body character, alternating).
4. **Example.** For a `statementSha256` of `abab…ab` (32 bytes of `0xab`), the reference is `tw1-NENTQAXBNENTQAXBNENTQAXBNE4`.

**Alphabet: Crockford base32, upper case only:** `0123456789ABCDEFGHJKMNPQRSTVWXYZ`.
- **Why this alphabet.** It leaves out `I`, `L` and `O`, which are easily confused with `1` and `0`, and `U`, which avoids accidental words. It has no punctuation that Markdown, URLs or auto-linkers might change.
- **Why not Crockford's own check.** Crockford's mod-37 check symbols (`*~$=U`) would bring such punctuation back, so the check character uses Luhn mod 32 over the same 32 symbols.
- **Strict parsing.** A verifier accepts **only** the canonical upper-case form. Lower case, look-alike letters, missing or extra characters are `reference-shape`. An input tool may offer to upper-case and to map `I`/`L` to `1` and `O` to `0`, but only as a suggestion the person confirms, never silently before verification.

**Error detection** (measured by the checker's self-test, exhaustively over 64 references):
- all 53,568 single-character substitutions are detected;
- of 1,595 adjacent transpositions, all but 3 are detected. All three swap an adjacent `0` and `Z`, the values 0 and 31: the known Luhn mod N blind spot.
- **jump transpositions (positions two apart) are never detected:** 1,545 of 1,545 were missed, because positions two apart carry the same Luhn weight. The check character catches typing slips, not deliberate edits.
- The pattern is matched against the whole string, so a trailing newline is `reference-shape`, not `reference-check`.
- A wrong check character is `reference-check`.

**Margins at 130 bits.** Collision resistance here is a property of the reference, not of the record.
- **Second preimage: about 2¹³⁰ work.** Finding another statement whose reference equals a given reference is out of reach. A verifier who fetches a bundle and finds its statement's first 130 bits equal to the reference has the statement the reference names.
- **Collision: about 2⁶⁵ work, by birthday search.** That is not protection against a registrant who deliberately makes **two** statements with the same reference, in order to show different records to different people. Such equivocation costs about 2⁶⁵ SHA-256 evaluations. That is expensive for an individual but within reach of a large adversary. A verifier who must bind to exactly one record keeps the full `statementSha256`, as the report link does (§9), not only the reference.

**What the reference carries.** **No content and no identity.**
- **Content:** the statement contains a fresh 256-bit nonce (§4.2), so the reference cannot be computed from the content, and the content cannot be recovered from it.
- **Identity:** no key, name or account is in it. Two references from one registrant are not linkable through the references themselves.
- **Same statement, same reference:** a statement co-signed later by another key keeps its reference (`text-reference-cosigned` equals `text-reference-three-roots`). The reference names the statement, not a bundle or a signer. Changing any statement field — including adding, changing or removing `claims.aiUse` (§4.7) — makes a different statement, signature, time evidence, `statementSha256` and `tw1-` reference.

**Lookup, with no project-run service.**
- **Where:** the verifier gets the bundle from a local file, or from a URL the registrant chose and printed next to the reference.
- **Check:** the verifier recomputes the reference from the bundle's statement payload and requires equality of the **whole** reference; otherwise `reference-mismatch`. It then runs §10 against the pasted bytes. A verifier that must bind to exactly one record keeps the full `statementSha256`, not only the reference (the 2⁶⁵ equivocation margin above).
- **Look-alikes.** People tend to compare the first and last few characters. A reference matching another in its first four and last four characters (40 bits) costs only about 2⁴⁰ work to make. Tools must compare the whole reference, and renderings must not abbreviate it.
- **Exposure:**
  - Fetching tells the host the verifier's IP address.
  - Publishing a bundle discloses what §5 says.
  - Anyone who copies the text can register it and paste their own reference (§11).
  - A page that "verifies" a reference proves nothing; only the local check counts.

**Rendering.** A `Reference: tw1-….` line is in the §11 allow-list. It must equal the reference of the bundle the result was computed from (`reference-mismatch`).

**Fixtures:**
- **Positives:** `text-reference-three-roots`, `-cosigned` and `-second-work`.
- **Negatives:**
  - `neg-reference-wrong-check`, `-transposed` (`reference-check`);
  - `-too-short`, `-too-long`, `-wrong-prefix`, `-no-prefix`, `-lower-case`, `-trailing-newline`, `-look-alike-I`, `-look-alike-L`, `-look-alike-O`, `-letter-U` (`reference-shape`);
  - `-jump-transposed`, `-other-statement`, `neg-rendering-reference-mismatch` (`reference-mismatch`).

## 10. Verification procedure

**Inputs:**
- a bundle;
- optionally, the artifact bytes, a catalogue opening and key-event bundles;
- the verifier's **policy**: `{quorum, timeRoots, trustedKeys, recoveryKeys, revocationData, compromiseLookbackSeconds, verificationTime}`. The checker refuses a policy with a quorum below 1, a negative or non-integer look-back, `minConfirmations` below 1, a malformed checkpoint, or malformed recovery keys. A result carries the policy it used, so its revocation date and verification time are on record (S3).

Every step reports its own outcome, and a failure in one step does not change another step's outcome.

1. **Parse** strictly: no duplicate keys (`duplicate-key`); size limits as in the signing harness. Base64 fields may be standard or URL-safe, because DSSE says verifiers "MUST accept either" (S7; `bundle-url-safe`). Outcome `envelope`: `ok` | `malformed` (`envelope-shape`, which also covers one key signing twice: `neg-duplicate-signer`).
2. **Signatures.** Look up each key by its `keyid` hint among the bundle's keys. A missing or unmatched hint gives `unknown-key`; there is no trial verification (A7). Verify under §10.1 over `PAE(payloadType, payload)` of the exact payload bytes. Per signature: `valid` | `invalid` | `unknown-key`, with `keySha256` (`signature-invalid`).
3. **Key events,** evaluated by the two-pass procedure of §8 (standing in order of proved time, then disputes). Per event: `applied` | `disputed` | `ignored-superseded` | `ignored-unauthorized` | `ignored-no-proved-time` | `invalid-signature`.
4. **Signer trust**, from the policy's `trustedKeys` (by full key digest) and the events, using quorum bounds only (§8). Per signature: `trusted` | `untrusted` | `disputed` | `not-evaluated`.
5. **Statement.** Strictly parse the payload and apply §4. Outcome `statement`: `ok` | `malformed` | `unsupported`.
6. **Subject digests.** Per subject: `match` | `mismatch` | `not-supplied`.
7. **Possession digests.** Per subject: `match` | `mismatch` | `not-supplied`.
8. **Catalogue.** `opens` | `does-not-open` | `not-supplied` | `not-committed`.
9. **Each time evidence** (§6.2), offline from retained material, as of the policy's revocation dates. Per evidence: `valid` | `invalid` | `wrong-target` | `pending` | `untrusted-root` | `unsupported` | `wrong-policy` | `revoked` | `no-revocation-data` | `expired-unrenewed` | `insufficient-confirmations` | `path-invalid`, with its target, `notAfter` and `revocationDataAsOf`. In fixtures only, `placeholder`, or `placeholder-assumed-valid` when the result says `simulated: true`.
10. **Bounds, per signature** (§6.4): `quorum-met` | `below-quorum` | `none-valid`, with `keyid`, `keySha256`, `quorum`, `distinctRoots`, `notAfterAnyRoot` and `notAfterQuorum`.
11. **Claimed time.** `absent` | `claimed-only` | `after-proved-bound` | `not-compared`. The comparison is with the earliest `notAfterAnyRoot` over signatures whose signer is **`trusted`** (S11). An untrusted co-signer with one early source cannot change the registrant's outcome (`verification-result-claim-trusted-only`). With no trusted signature, the outcome is `not-compared`. The value compared with is reported as `comparedWith`.
12. **Declared AI use** (§4.7): if the statement carries `aiUse`, echo it as `declaredAiUse` with status `declared-not-checked`. It changes no other outcome (`ai-use-affected-outcome`).
13. **Output** all outcomes, and the fixed `notShown` list: `authorship`, `originality`, `first-creation`, `ownership`, `permission`.

A result must not:
- add a combined verdict (`single-verdict`);
- report the claimed time as a bound (`claimed-as-proved`);
- count a pending proof (`pending-counted`);
- give a signature a bound it has no evidence for (`key-bound-misattributed`);
- count one class twice (`quorum-miscount`);
- ignore an applicable key event (`key-event-ignored`);
- trust a signature on one source after a key event (`trust-without-quorum`);
- match keys by hint (`key-identity-by-hint`);
- add an authorship or ownership field (`authorship-claim`).

Any other disagreement with the recomputed outcomes is `result-mismatch`.

### 10.1 Ed25519 verification rule set (A4)

Verification follows RFC 8032 §5.1.7 with the **cofactorless** equation `[S]B = R + [k]A`, plus these rejections:
- a signature that is not 64 bytes, or a key that is not 32 bytes;
- `S ≥ L`;
- a non-canonical encoding of A or R (y ≥ p, or x = 0 encoded with the sign bit set);
- a public key A of small order (`[8]A` is the identity).

R of small order is not rejected separately. Implementations must reject exactly these, so two verifiers (REG.2) agree on edge cases. The checker's self-test shows two lenient verifiers that this rule set rejects:
- one that reduces S modulo L accepts a malleated signature;
- one without the small-order check accepts R = identity, S = 0 under the identity key, for **any** message.

It also shows that a non-canonical point is refused.

**Side-channel boundary (`CD-A5`).** Comparing public commitment digests during `catalogueOpening` verification operates on values supplied by the opener (`R` and `C`) rather than secret material, whereas private Ed25519 signing and OS CSPRNG nonce generation operate on secret material and MUST use constant-time / side-channel-safe primitives and OS CSPRNG APIs.

## 11. What a registration does not show (required text, F4)

A registration does not show **authorship**, **originality**, **ownership** or **permission**. It does not show that the registrant **created** the content rather than copied it, or that they were first: anyone who obtains a copy can register it, and an earlier creator may never have registered. **First to register is not first to create.** It gives upper bounds on when each signature existed, not a creation time.

**Renderings use an allow-list.** Every line of user-facing text that presents a registration (command-line output, the WEB page, an agent skill under SK.3, a C2PA export) is one of the following lines, filled from the verification result. `<key>` is the first **32 hex digits (128 bits) of the key's SHA-256**, never the 16-hex `keyid` hint, so two keys with colliding hints cannot render identically (B3 note).

| Template | Filled from |
| --- | --- |
| `Simulated: time evidence is placeholder only.` | **Required as the first line** when the result says `simulated: true`, and forbidden otherwise (D6; `simulated-unmarked`) |
| `Registration of <name> (SHA-256 <first 8 hex>…<last 4 hex>).` | subject |
| `Reference: <tw1-reference>.` | §9.1; must equal the reference of the result's bundle |
| `The registrant declared that this content was generated with an AI system ("AI + GENERATED" in the EU Code of Practice).` / `… was modified with an AI system ("AI + MODIFIED" in the EU Code of Practice).` / `The registrant declared that no generative AI system was used.` | §4.7 `declaredAiUse.declared`; must match it |
| `Tool identifier given by the registrant: "<tool>". Traceweave did not check this.` | §4.7 `declaredAiUse.tool`, if any; the token must also pass the A1 rule |
| `Traceweave did not check this declaration.` | **Required** with every declaration line (`notice-missing`) |
| `The registrant made no declaration about AI use.` | Optional, only when nothing was declared; any declaration line without a declaration is `result-mismatch` |
| `Content digest: matches the file you supplied.` / `does not match the file you supplied.` / `not checked, because no file was supplied.` | step 6 |
| `Signature by key <key>: <valid/invalid/unknown key>; signer <trusted/not trusted/disputed by a key event/not evaluated> under your policy.` | steps 2, 4 |
| `This record shows that the content existed, and that key <key> signed a statement naming it, no later than <T>.`, where T is that signature's `notAfterQuorum`; if quorum was not met, T is its `notAfterAnyRoot` and the line ends `… no later than <T> (according to one time source only).` | step 10, **one line per signature with a bound** |
| `Time sources for key <key>: <distinctRoots> independent, <quorum> required; the earliest single source says <notAfterAnyRoot>.` | step 10 |
| `No proved time for key <key>.` | step 10, for a signature with no bound |
| `Creation time claimed by the registrant, not proved: <T>.` | step 11 |
| `Witnessed: the caller <subject> presented the signature digest no later than <T>, according to the witness's time-stamp authority.` | §19 witness; T is the witness's TSA bound, not its clock (S8) |

The text must also contain the three fixed sentences, and for agent-made registrations the §19.5 sentence:

> It does not show who created the content, that it is original, that the registrant was first to create it, who owns it, or that its use is permitted.
> First to register is not first to create.
> Comparing the times of two registrations does not show which was made first.

The third sentence is new in draft-3 (S8). Each bound is an upper bound, so an earlier bound on A than on B does not show that A was registered first: B's registrant may simply have obtained evidence later.

**What the checker rejects:**
- A line outside the templates is `rendering-unlisted-line`, even a harmless one.
- An unlisted line that also uses an authorship or ownership word is additionally `authorship-claim`. The words are `author…`, `wrote`, `written`, `belongs`, `your`, `claim to`, `registered to you`, `first to create`, `priority`, `created`, `creator`, `own…`, `original…`, `copyright`, `proves`, `proof`, `establish…`, `authentic…`, `verified`, `genuine`, `legitimate`. This rejects the four renderings the review's checker accepted (`neg-authorship-claim-1` to `-4`).
- An unlisted line that orders registrations or times (`before`, `after`, `earlier`, `later`, `first`, `sooner`, `precede`, `predate`, `older`, `newer`) is additionally `ordering-claim` (`neg-ordering-claim`).
- A bound sentence for a key without that bound is `key-bound-misattributed`.
- A bound sentence carrying the claimed time is `claimed-as-proved`.
- A missing fixed sentence, or a missing bound sentence for a key that has a bound, is `notice-missing`.
- **Never shown** (§4.7): "AI-generated", "AI-written" or "made by AI" as a property of the content; "human-written", "human-made", "written by a human" or "not AI"; any sentence with a person as subject. An unlisted line with such words is `ai-origin-claim`.
- A rendering of a simulated result without the marker as its first line is `simulated-unmarked` (D6; review case `neg-simulated-unmarked`). A production renderer refuses simulated results outright (REG.4).

The allow-list is a floor, not a wording review: REG.4 still needs a non-author to read every template.

## 12. Threat model

| Threat | Who | What stops it | What remains |
| --- | --- | --- | --- |
| Backdating a registration | Registrant | Evidence binds one signature; the registrant cannot choose `genTime` or a block time. q = 2 over independent anchors | One colluding or compromised source moves `notAfterAnyRoot` only. Bitcoin's bound rests on the honest-majority assumption (§6.2) |
| Retroactive loss of one source | Time | RFC 3161 revocation without a retaining reasonCode kills every token of that key (§6.2). Three sources and q = 2 survive one loss (`verification-result-revoked`) | Losing two sources leaves `below-quorum` |
| Counting one source twice | Producer or careless verifier | Anchors, not labels; groups set by the verifier (§6.3) | A policy that groups badly |
| Registering someone else's work | Anyone with a copy | Nothing technical; §11 text | First to register is not first to create |
| Replay or transplant of evidence | Anyone | Evidence targets one signature's raw bytes (`evidence-wrong-target`); co-signers get no inherited bound (§6.4); the TSA request nonce catches replayed responses at request time (`tsa-nonce-mismatch`) | Copying a whole bundle proves only that the original key holder registered |
| Claiming a published digest without the content | Anyone | Possession digest (§4.3) | Useless for content already public at T, and for short guessable content after disclosure |
| Key theft | Attacker | Bounds on earlier signatures; compromise events (§8) | Signatures between theft and the event's proved time are `disputed`: indistinguishable from the owner's |
| Hostile or early-dated compromise claim | Thief or former collaborator | Authorized signers only; proved time required; look-back clamp; `disputed`, not `untrusted` (§8) | Registrations inside the look-back window can be disputed |
| Nonce reuse | Careless producer | Producer obligation; cross-record check (§4.2) | Not detectable from one record |
| Linkage | Observers of disclosed records or time-service traffic | Per-work keys (I0′); one signature digest per registration | Timing and IP address at time services |
| Privacy leaks | Services, recipients | Only signature digests leave; fresh nonce; salted commitments; no fingerprints (§5) | Opening a catalogue reveals all of it; low-entropy content is confirmable after disclosure |
| Service shutdown | TSA, calendar, log | Three sources; complete evidence verifiable offline from retained chains, retained revocation data and a pinned header source, **as of the revocation data's date** (§6.7) | An OpenTimestamps proof is lost if every calendar disappears before upgrade (T4) |
| Algorithm ageing and certificate expiry | Time | Renewal evidence over the earlier token (§6.6), made before the TSA certificate expires; triggers: expiry approaching, any non-compromise revocation notice, reported weakness in SHA-256 or Ed25519 | A renewal must happen before the expiry or break. Hash-tree renewal for SHA-256 is outside this draft (§6.6). Renewal does not rescue a compromised TSA key |
| Retired or rotated-away key used again | Whoever later holds the old key | Supersession: later events signed by it are ignored, except a compromise report; later rotations of it are ignored; equal-time conflicts are both disputed (§8; D1, D2) | A compromise report signed with the old key within the look-back window after the honest rotation disputes it **permanently**: the successor chain is lost and the key cannot be rotated again, so recovery needs a pre-listed recovery key or an out-of-band link |
| A successor's report used against its own appointment | Anyone adding rejected events | Two passes, no fixed point; a report never disputes its own signer's appointment (§8; E1) | — |
| Forked OpenTimestamps headers | Anyone supplying headers | Checkpoint pinned from the verifier's own node; linkage back from it (§6.2; D3) | A verifier without a checkpoint gets `unsupported` |
| A TSA certificate minted under a CA by a non-CA certificate, or under an expired intermediate | Holder of any certificate under the root | RFC 5280 path validation at `genTime` (§6.2; D4) | Path checks this validator does not implement: name constraints, policies |
| Stolen key rotated to the thief | Thief | A later compromise disputes rotations inside its window; no trust through a disputed rotation; conflicting rotations both disputed (§8; `verification-result-rotation-hijack`, `-rotation-conflict`) | Until the owner's compromise event is proved, a verifier without it sees the rotation as applied |
| Events supplied in a convenient order | Anyone | Order-independent evaluation by proved time (§8; `-event-order-a`, `-b`) | — |
| Keys matched by hint | Implementations | Full-key SHA-256 everywhere (§8; `neg-trust-by-hint`, `neg-key-event-subject-mismatch`) | — |
| One backdating source deciding trust | Thief plus one source | Quorum bound only for event decisions; otherwise `disputed` (S1) | — |
| A witness and its TSA counted twice | Producer | Union of groups per evidence (§6.3; `verification-result-witness-shared-tsa`) | A policy that does not list the witness's TSA anchor |
| Evidence stripped in transit | Anyone handling a bundle | Bounds can only become later or disappear (N3; `verification-result-stripped`) | A record can be made to look later than it is |
| Lenient signature verifiers | Implementations | §10.1 rule set, self-tested | — |

## 13. The two mechanisms to implement first, and why

1. **RFC 3161 tokens (T1), from two unrelated TSAs.** Implement this first. It is the standard form consumed by C2PA, Sigstore bundles, eIDAS qualified time-stamps and RFC 4998 renewal. Precision is about a second. Verification needs only the retained chain and revocation data, and no header source, and holds as of that revocation data's date (§6.7). The real-format vectors (§6.5) exercise every token check locally. Public TSAs need no account, but the owner must read their terms. A qualified TSA can be added later for registrants who want the eIDAS presumption (L1), without a format change.
2. **OpenTimestamps (T4).** Its root, Bitcoin proof of work, has no operator who can backdate. It needs no account and no fee. Once upgraded, it survives the shutdown of every calendar. Its costs are acceptable for the third source: hours of precision, a pending window, LGPL-3.0 client code, and a trusted Bitcoin header source to verify.

Two TSAs plus OpenTimestamps give **three independent sources with q = 2**, so one retroactive TSA revocation still leaves a quorum. Rekor and witness cosigning are deferred: they add discoverability and split-view protection that private registrations do not need, and Rekor v2 needs a TSA token for time anyway (T3).

## 14. What a registrant would do in practice

1. **Once:** generate a signing key with the tool, stored in the private location of contract §6.8 B11, and back it up in two places. Optionally publish the public key somewhere dated (I1), or choose per-work keys (I0′).
2. **For each piece of work:** run a local `register` command on the original files. It hashes them, draws a nonce, computes the possession digests, and optionally builds the private catalogue and its commitment. It then signs the statement and sends **only the SHA-256 of the signature bytes** to two TSAs, each with a fresh request nonce that it checks, and to OpenTimestamps calendars. No content and no identity leaves the machine. It reports `pending` for the Bitcoin part.
3. **A few hours later:** upgrade the OpenTimestamps proof and save the bundle again. The tool can do this on its next run.
4. **Keep, unchanged and backed up:** the original bytes, the bundle, the catalogue and its opening (retained as exact raw bytes `C` without re-serialization), the TSA certificate chains, and access to a Bitcoin header source.
5. **Renew** before a TSA certificate expires, on any non-compromise revocation notice, or on reported weakness in SHA-256 or Ed25519: run `renew` to add renewal evidence over the existing tokens (§6.6). Also keep the revocation data fetched at each check, with its date (§6.7).
6. **In a dispute:** hand over the original bytes and the bundle, and the catalogue opening only if needed. The other side runs §10 with their own policy and reads the §11 limits.

## 15. Roadmap mapping and proposed ROADMAP.md text (S13; ROADMAP.md is not changed here)

ROADMAP.md M4.3–M4.6 are unchanged. M4.5 still asks for a decision on "the optional timestamp adapter", and REG gates exist only as proposals here. **Until the owner adopts text like the following, no M4 gate tests a registration, and M4 cannot be evidenced from this draft.** The text below is written to drop into the M4 table and to be checkable as written.

| ID | Type | Proposed verifiable criterion | Owner |
| --- | --- | --- | --- |
| M4 row, "What becomes possible" | — | "A registrant can show that registered bytes existed under a named key no later than a time agreed by two independent time sources. A registration never shows authorship, first creation, or which of two registrations was made first." | — |
| M4.3 (amended) | E | "Negative cryptographic vectors (tampered payload, type or signature; untrusted key; malformed or duplicate-key payload; subject mismatch; and, for registrations, `evidence-wrong-target`, `tsa-imprint-mismatch`, `tsa-signature-invalid`, `tsa-eku-invalid`, `tsa-signing-cert-mismatch`, `tsa-nonce-mismatch`, `key-event-shape`, and the §10.1 Ed25519 edge vectors), each with a distinct reason code. `validate` checks them." | S |
| M4.5 (replaced) | O+E | "A recorded owner decision selecting the time-evidence types for registration records (proposed: RFC 3161 from two unrelated TSAs, and OpenTimestamps), the default quorum (2), the compromise look-back (RD15), and whether any external service may be contacted for test tokens. In-toto adapter accept/reject fixtures and a trust-policy document, checked by `validate`." | S |
| M4.6 (amended) | E | "Commitment, disclosure and key-event design (`spec/registration-record.md` §4, §5, §8) reviewed by a named non-author. Report in `docs/reviews/`; every finding has a disposition." | S |
| REG.1 | E | "`check_registration.py` exits 0 under `validate`: every positive fixture gives no code, every negative gives exactly its codes, every code has a negative, and the wrong-implementation self-test passes. The real-format vectors in `real-format/` verify with anchors computed from the pinned root certificate and from the header file plus pinned checkpoint. The §4.7 AI-use fixtures (each value, absent, and the 15 `neg-ai-use-*` negatives) behave as stated. The real-format negatives are rejected: four token negatives (imprint, tampered, non-critical EKU, wrong ESS); two path negatives (TSA certificate issued by an end-entity certificate, and under an expired intermediate), each also rejected by `openssl ts -verify`; three OpenTimestamps negatives (other digest, unrelated chain, forked headers); and a pinned-root negative (the root file does not hash to the anchor). The gate fails if any of these is accepted. `enumerate_key_events.py` reports 0 violations: exhaustively at length ≤ 3 and on a seeded sample of 200,000 at length 4, over its 100-symbol alphabet with steps of ±10 and ±40 days and claimed starts of 2, 20 and 60 days, on all 13 invariants, and with 0 mismatches on its loading sample. Its mutation check finds violations in all three weakened rule sets, including the draft-4 fixed point." | S |
| REG.2 | E | "Two implementations, each with its own parser, produce verification results (§10) whose RFC 8785 canonical bytes are identical on every REG.1 fixture, including the §10.1 edge vectors and the two event orders. The comparison is over those canonical bytes, never over the implementations' own serializations." | I |
| REG.3 | E | "After the owner approves the services: one RFC 3161 token from each of two unrelated TSAs, and one upgraded OpenTimestamps proof, over one synthetic registration (k = 3 evidences). Each is verified with the network denied, from retained chains and revocation data, and with the verifier's own header source and checkpoint (§6.2); 3/3 must be valid. Failure directions, each 1/1: wrong target, tampered token, wrong policy OID, wrong request nonce, and a forked header file. The revoked-certificate direction uses the local test TSA of §6.5, because a revocation cannot be produced on demand at a real TSA." | I |
| REG.4 | E | "Every user-facing rendering uses only the §11 templates and the three fixed sentences, and shows keys with at least 128 bits of their SHA-256. A §4.7 declaration is shown only through its fixed sentence, always followed by "Traceweave did not check this declaration."; an absent claim is never shown as "no AI"; and no rendering presents AI or human origin as a property of the content or makes a sentence about a person. A production renderer refuses to render a result with `simulated: true`. Fixture renderings of simulated results carry the marker line. A named non-author reviews the templates. Feeds M5.2 and WEB.5." | S+I |
| REG.5 | E | "The §19 agent fixtures are checked by `validate`: 0 `raw` or `url` parts and 0 fingerprints in hosted-route fixtures; every skill description and agent rendering carries the required sentences." | S |
| UC-9 (proposed) | — | Owner wording. This draft supplies the limit text (§11); UC-3's "Signing alone proves neither ownership nor earlier existence" stays for signing alone | — |

**C2PA (S12).** A C2PA v2 time-stamp countersigns the **C2PA claim signature** (`sigTst2`; T6), not the DSSE signature. A registration's RFC 3161 token over its DSSE signature therefore **cannot be reused** in a C2PA manifest. A C2PA export obtains its own RFC 3161 token over the claim signature, and **registration time evidence does not map**. The [C2PA mapping draft](../research/drafts/c2pa-mapping.md) correctly keeps the time-stamp row `conflicting`; this draft no longer says otherwise.

## 16. Open decisions

| ID | Decision | Options | Recommendation |
| --- | --- | --- | --- |
| RD1 | First mechanisms | (a) RFC 3161 from two TSAs + OpenTimestamps; (b) RFC 3161 from two TSAs only; (c) Rekor v2 + TSA | (a); implement RFC 3161 first, because OpenTimestamps verification needs a header source. (b) if Bitcoin verification is unwanted, accepting that one more revocation drops quorum |
| RD2 | Which TSAs | Free public TSAs listed by Sigstore (terms unread); a qualified eIDAS TSA (paid); none until approved | **Owner.** None until approved; then two unrelated public TSAs for tests, after reading their terms |
| RD3 | Public logs | Never; opt-in per registration; a project-run log | Never by default; opt-in only after RES.1 and an owner decision (SK.5) |
| RD4 | Default identity | I0, I0′, I1, I2, I3 | I0, with I0′ and I1 documented. I2 opt-in only |
| RD5 | Default quorum | 1 or 2 | 2 over three sources; always report both bounds; count by policy group |
| RD6 | OpenTimestamps margin | 7,200 s under the honest-majority assumption; use the median-time-past of a later block; no OpenTimestamps bound | 7,200 s with the assumption stated (§6.2); revisit with a reviewer who knows Bitcoin consensus |
| RD7 | Possession digest | Mandatory or optional | Mandatory |
| RD8 | Time-stamp target | Raw signature bytes; statement digest; artifact digest | Raw signature bytes, with per-signature bounds (§6.1, §6.4) |
| RD9 | Many files | 64 subjects; a Merkle root | 64 now |
| RD10 | Identifiers | Predicate URLs under `traceweave.org` | Proposed only; publish nothing (shared with C2PA D3) |
| RD11 | Renewal | Re-time-stamp the bundle; RFC 4998 evidence records | Re-time-stamping on the §12 triggers; evidence records if a qualified archive is ever needed |
| RD12 | Architecture for registration at creation (§19) | Local-first; hosted witness; custodial hosting | Local-first first; witness only as an optional extra source after SK.5; never custodial |
| RD13 | Agent identity in the statement | None; claimed `claims.generator`; delegated-identity field | None in this draft (§19.5) |
| RD14 | Local agent route | MCP over stdio; A2A on loopback; command line only | MCP over stdio first |
| RD15 | Compromise look-back (validated as a non-negative integer; 30 days is a placeholder for the owner, not derived from any expected discovery time) | 30 days; 90 days; no clamp | 30 days as the fixture default. **Owner/policy choice:** longer protects owners who discover theft late, shorter protects honest history from hostile claims |
| RD16 | Ed25519 rule set (§10.1) | As specified; also reject small-order R; cofactored equation | As specified; record it with REG.2 vectors |
| RD17 | Who may assert key events | The key itself; the successor named in an applied rotation of it with a smaller proved time, **disputed or not** (§8 pass 1); recovery keys | The key and the successor named in an applied rotation with a smaller proved time, disputed or not: a disputed rotation passes on no trust, but its successor may still restrict. Recovery keys (`recoveryKeys`, RD18) are trust roots from their `notBefore` and **do not** sign events for the key they recover. There is no other policy field for adding event signers. Each key event carries exactly one signature (§8; `key-event-signatures`) |
| RD18 | Recovery after reporting a compromise (re-examined in draft-4; policy field in draft-5) | Rotation by the compromised key (now ignored as superseded, or disputed); out-of-band link (I1 or I2); policy-listed recovery keys | Out of band, or a recovery key listed in advance in the verifier's policy field `recoveryKeys`, trusted from its `notBefore` only. Under the draft-4 and draft-5 rules (§8), an honest owner who rotated first keeps the chain unless a compromise report lands within the look-back window; after that the chain is final. An owner whose key was rotated by a thief first must recover out of band |
| RD21 | Bitcoin header source for verification | Verifier's own node with a checkpoint; a header file shipped with a bundle | The verifier's own node and checkpoint only (D3) |
| RD22 | Algorithms for real TSAs | RSA PKCS #1 v1.5 with SHA-256 only; add ECDSA, RSA-PSS, SHA-384/512 | Decide with REG.3 from the TSAs chosen (D7) |
| RD19 | Witnessed checkpoints | Removed (draft-3); restore with an inclusion proof and checkpoint body | Removed until a log is in scope (S5, RD3) |
| RD20 | Hash-tree renewal for SHA-256 | Outside this draft; define with RFC 4998 evidence records | Outside this draft; a new registration referencing the old one if SHA-256 weakens (§6.6) |

## 17. Needs the owner

- **Using any external service at all**, including one test token (REG.3). The reviewer's answer on what one test submission discloses, recorded for this decision:
  - **RFC 3161:** the TSA sees the SHA-256 imprint of a signature over a synthetic statement, the hash OID, the request nonce, the client IP address, the time, the user agent and TLS metadata, and may log them under its terms. Nothing is published.
  - **OpenTimestamps:** each calendar sees the digest (further hashed with a nonce), the IP address and the time. The calendar's Merkle root is placed in a Bitcoin transaction **permanently**. The digest itself is not revealed unless the proof is shown.
  - **Neither** reveals content or identity beyond network metadata. Both reveal that this address used a time-stamping service at that time.
  - The reviewer suggests one TSA and one calendar (`--calendar`) for the test, over a synthetic statement.
- Which TSAs, after reading their terms; any paid or qualified TSA.
- Whether anything is ever written to a public transparency log, and whether the project ever operates a log, witness or signer (SK.5).
- Identity choices: whether I2 is offered; the default between I0 and I0′.
- The compromise look-back default (RD15).
- Publishing the predicate identifiers under `traceweave.org`.
- Adopting the ROADMAP.md text proposed in §15 (M4.3, M4.5, M4.6, REG.1–REG.5). Until it is adopted, no M4 gate tests a registration (S13). Also the new use case.
- Everything listed at the end of §19.7.
- Legal questions. Lane 13 quotes eIDAS and the US Federal Rules of Evidence only; nothing here is legal advice.

## 18. Fixtures and checker

See the [fixtures README](../test-vectors/registration/README.md). `check_registration.py` (standard library, with `realformat.py`) does four things:
- **It checks the fixtures.** It verifies Ed25519 signatures under §10.1 with public test-only keys. It recomputes digests, possession digests, the catalogue commitment and the full expected verification result: per-signature bounds; independence classes; revocation data; renewal; key events in proved-time order with full-key identities; trust from quorum bounds only. It applies the §11 allow-list.
- **It verifies the real-format vectors for real** (§6.5): the RFC 3161 structure, signature, ESSCertIDv2, EKU, chain and imprint, and the OpenTimestamps operations, proof of work, linkage and Merkle root, with anchors it computes itself.
- **It runs a wrong-implementation self-test.** Thirty-three plausible wrong verifiers, renderings and decoders are built in memory, and each must be rejected or shown to misbehave. Among them: B1 hijack and conflict, B2 list-order evaluation, B3 hint trust, S1 one-source trust, S4 witness double counting, S6 expiry ignored, S7 standard-only base64, S11 any-signer claim comparison, S2 an imprint-blind token check, two lenient Ed25519 verifiers, and for draft-4 the D1 and D2 cases, D3 a forked header file without a checkpoint, D4 a signatures-only chain check on both bad paths, and D6 an unmarked rendering.
- **It runs a drift check.** Every failure code must appear here and have a negative fixture.

`enumerate_key_events.py` is the key-event enumeration test (§8). It runs separately: about a minute on the machine used here, with one process per core. A `result-equivalence` fixture kind checks that results differing only by rejected events agree byte for byte (`extra-event-changed-result`).

Placeholder time evidence is never verified (§6.5, S10).

Failure codes: `authorship-claim`, `catalogue-does-not-open`, `catalogue-not-report-input`, `catalogue-unsalted`, `claimed-as-proved`, `duplicate-key`, `envelope-shape`, `evidence-shape`, `evidence-wrong-target`, `fixture-shape`, `forbidden-field`, `key-bound-misattributed`, `key-event-ignored`, `key-event-shape`, `key-identity-by-hint`, `log-time-claimed`, `nonce-invalid`, `nonce-reused`, `notice-missing`, `ordering-claim`, `pending-counted`, `placeholder-unlabelled`, `possession-mismatch`, `predicate-type`, `profile-mismatch`, `provenance-shape`, `quorum-miscount`, `rendering-unlisted-line`, `report-digest`, `result-mismatch`, `root-not-anchored`, `signature-invalid`, `single-verdict`, `statement-digest`, `statement-shape`, `subject-mismatch`, `subject-name`, `time-in-statement`, `trust-without-quorum`, `tsa-eku-invalid`, `tsa-imprint-mismatch`, `tsa-nonce-mismatch`, `tsa-signature-invalid`, `tsa-signing-cert-mismatch`, `simulated-unmarked`, `extra-event-changed-result`, `key-event-signatures`, `reference-shape`, `reference-check`, `reference-mismatch`, `ai-use-shape`, `ai-origin-claim`, `ai-use-affected-outcome`; for §19: `content-on-wire`, `a2a-shape`, `mcp-tool-shape`, `witness-shape`.

## 19. Registration at creation time and agent interoperability

The owner wants content registered at the moment it is created, including by AI agents, over A2A. This section designs that from the protocol texts. Nothing was run against any agent, server or service.

**Sources, read 2026-11-23 over read-only HTTP.**
- **A1:** A2A at tag `v1.0.1`, commit `3303592588e388e62e0f69f701af531d2f4e3991`: [specification.md](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/docs/specification.md) (its banner names `1.0.0` as the latest released version; the protocol version on the wire is `1.0`, §3.6), [a2a.proto](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/specification/a2a.proto), [extensions](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/docs/topics/extensions.md), [GOVERNANCE.md](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/GOVERNANCE.md), [README](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/README.md), [JSON artifact README](https://github.com/a2aproject/A2A/blob/3303592588e388e62e0f69f701af531d2f4e3991/specification/json/README.md). Apache-2.0.
- **A1 governance:** "an open source project under the Linux Foundation, contributed by Google" (README). It is "governed by the Technical Steering Committee", with eight seats held by Google, Microsoft, Cisco, Amazon Web Services, Salesforce, ServiceNow, SAP and IBM Research, in a "Startup Phase" composition (GOVERNANCE.md).
- **M1:** Model Context Protocol at commit `862397cec702e8f828713071da501cf56158e8fc`, revision `2026-07-28`, labelled "(latest)" in the [docs navigation](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/docs/docs.json): [tools](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/docs/specification/2026-07-28/server/tools.mdx), [stdio](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/docs/specification/2026-07-28/basic/transports/stdio.mdx), [authorization](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/docs/specification/2026-07-28/basic/authorization/index.mdx), [overview](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/docs/specification/2026-07-28/index.mdx), [schema.ts](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/schema/2026-07-28/schema.ts), [schema.json](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/schema/2026-07-28/schema.json), [GOVERNANCE.md](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/862397cec702e8f828713071da501cf56158e8fc/GOVERNANCE.md). MCP "has been established as Model Context Protocol a Series of LF Projects, LLC"; specifications are Apache-2.0 (GOVERNANCE.md).

### 19.1 What the protocols give, and what they do not

| Feature | What the text says (A1 unless marked) | Consequence for registration |
| --- | --- | --- |
| Normative source | "`spec/a2a.proto` is the single authoritative normative definition"; `a2a.json` is "a non-normative build artifact", "generated during builds and intentionally **not** committed" (§1.4; JSON README) | No published A2A JSON Schema could be validated against offline. The fixtures are checked against the proto field lists (§19.4) |
| Agent Card | "A2A Servers **MUST** make an Agent Card available"; discovery at `https://{server_domain}/.well-known/agent-card.json` (§8.1, §8.2). Required fields in the proto: `name`, `description`, `supportedInterfaces`, `version`, `capabilities`, `defaultInputModes`, `defaultOutputModes`, `skills` | A card describes a service. It is not evidence about content |
| Skills | `AgentSkill` requires `id`, `name`, `description`, `tags`; a skill "is largely a descriptive concept" (proto comment on `skills`) | Skill descriptions are where the §11 limit text must appear |
| Tasks | `TaskState`: `SUBMITTED`, `WORKING`, `COMPLETED`, `FAILED`, `CANCELED`, `INPUT_REQUIRED`, `REJECTED`, `AUTH_REQUIRED` (proto) | §19.4 lifecycle |
| Messages and artifacts | "Results SHOULD BE returned using Artifacts"; "Messages MUST NOT be considered a reliable delivery mechanism for critical information" (§3.7) | The witness statement is returned as an artifact, never only as a message |
| Parts | A `Part` holds exactly one of `text`, `raw` (bytes), `url` or `data` (JSON), plus `metadata`, `filename`, `mediaType` (proto) | `raw` and `url` are how content would leave; the profile forbids them (§19.3) |
| Transports | `protocolBinding` values `JSONRPC`, `GRPC`, `HTTP+JSON` (proto); "Production deployments **MUST** use encrypted communication" (§7.1) | A hosted witness is HTTPS only |
| Authentication | "Identity information is handled at the protocol layer, not within A2A semantics" (§7); credentials are obtained "out-of-band" (§7.3); the server "**MUST** authenticate every incoming request" (§7.4). Schemes: API key, HTTP, OAuth 2.0, OpenID Connect, mutual TLS (proto `SecurityScheme`) | The witness can say which authenticated caller presented a digest. That caller identity is whatever the identity provider asserts |
| Idempotency | "**Send Message** operations MAY be idempotent. Agents may utilize the messageId to detect duplicate messages" (§3.3.1) | §19.4 defines it for the witness |
| Errors | Authentication, authorization, validation, resource and system categories, plus A2A errors such as `ContentTypeNotSupportedError`, `ExtensionSupportRequiredError`, `VersionNotSupportedError` (§3.3.2); "rate limit exceeded" is an example system error | §19.4 error mapping |
| Signing and provenance | The only signing in the core is of the **Agent Card**, by JWS over the RFC 8785 canonical card (§8.4, §8.4.1). Nothing signs messages, tasks or artifacts, and the proto has no provenance field | A2A cannot carry evidence by itself. Registration evidence travels as Traceweave's own signed objects inside a `data` part |
| Time | Timestamps are ISO 8601 UTC strings (§5.6.1). The extensions page lists a sample "Timestamp Extension" that adds timestamps to `metadata` (not read further) | Any A2A time is a claimed time, never time evidence |
| Extensions | Declared in the card with `uri`, `description`, `required`, `params` (proto `AgentExtension`); "Anyone is able to define, publish, and implement an extension" (extensions page) | A Traceweave profile extension, proposed URI `https://traceweave.org/a2a/ext/registration/draft-1` (not published), declares `wire: digests-only` or `local-only` |
| Versioning | Major.Minor only; patch numbers "SHOULD NOT be used in requests, responses and Agent Cards" (§3.6) | `protocolVersion: "1.0"`; `"1.0.1"` is rejected (`a2a-shape`) |
| Discrepancy | The sample card in §8.5 uses a `security` field; the proto names it `security_requirements` (`securityRequirements` in JSON), holding `{"schemes": {…}}` | The fixtures follow the proto, which §1.4 makes normative |
| MCP tools (M1) | Tools are "model-controlled"; "there **SHOULD** always be a human in the loop with the ability to deny tool invocations"; clients "**MUST** consider tool annotations to be untrusted unless they come from trusted servers"; servers "**MUST** … Rate limit tool invocations" (tools.mdx). Annotations: `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` (schema.ts) | The local route is an MCP tool whose annotations say it writes and reaches the network |
| MCP stdio (M1) | "the client launches the MCP server as a subprocess"; implementations using stdio "**SHOULD NOT** follow this [authorization] specification, and instead retrieve credentials from the environment" | A local stdio tool needs no listener, no network authentication and no account |

### 19.2 Two architectures and what each means

**(a) Local-first (recommended first).** The creating tool or agent calls a local Traceweave tool when it writes a file. The local tool may be an MCP tool over stdio, a local A2A agent on loopback, or the command line. It does everything in §14 step 2 on the machine: digests, nonce, possession digests, optional catalogue and commitment. It signs with the **creator's** key and requests evidence over the raw signature bytes from two TSAs (each with a checked request nonce) and OpenTimestamps (§13). The trust meaning is exactly §1: this key signed a statement naming these bytes no later than T. Registering at creation time can make T close to creation, if the registrant registers promptly; the record does not show that they did (S8). It never proves the creation moment, and the bound is still an upper bound.

**(b) Hosted Traceweave witness over A2A.** A remote agent receives **only the SHA-256 of a registrant's DSSE signature**, after (a) has signed. It authenticates the caller and signs a **witness statement** (predicate type `https://traceweave.org/predicate/witness/draft-1`, proposed). The statement says: *this digest was presented at `receivedAt` by the witness's clock, by the caller authenticated as {scheme, issuer, subject}, in request `requestMessageId`*. The witness attaches its own RFC 3161 token over its signature, so its time does not rest on its own clock. The result returns as an A2A artifact. The creator adds it to the bundle as one more time evidence (proposed type `traceweave-witness`, root kind `witness-service-key`). Its root is identified by the anchor of the witness key (§6.3), and the verifier's policy decides which independence group it belongs to. Its bound is per signature, like every other bound (§6.4).

"Signed by Traceweave" would mean only that: a presented digest, a time, an authenticated caller. It would **not** mean authorship or originality. It would not even mean that the caller held the content: the witness never sees content, and possession is shown by the creator's own possession digest (§4.3). A custodial variant, where the hosted service holds creators' keys and signs registrations for them, is **not recommended**. It would make the operator able to sign as any creator.

**What operating (b) requires.**
- **Key custody:** a hardware or cloud key service, rotation, a published key history, and a compromise procedure (§8 applies to the witness key too).
- **Availability:** a stated service level. Registration must still succeed without the witness, because it is an extra root, never a required one.
- **Abuse handling:** quotas, rate limits and refusal policies (§19.6).
- **An accountable operator:** someone who answers for the key, the logs and incidents, and who can contract with a TSA.
- **Cost:** hosting, the key service, monitoring, and any paid TSA.
- **A retention and privacy policy:** caller identity, digest, time and IP address together are personal data about creative activity. This is not legal advice; the owner would need advice for any jurisdiction.

**What the project's status implies.** Traceweave is an independent, non-commercial specification and "not a legal entity" (roadmap). It has no body that can be the accountable operator, sign a TSA contract, or promise availability. A witness run by volunteers that later stops leaves its past statements verifiable, because the bundle carries the witness key and its TSA token, but no new ones can be made. A hosted signer would turn the project into a trust anchor it cannot currently back. **Recommendation: build (a) first. Specify (b) as an optional evidence type, and operate nothing until SK.5 is decided.** The roadmap already says "Until then, nothing is hosted".

### 19.3 What crosses the wire, and the privacy exposure

| Hop | Architecture | What is sent | What the receiver learns |
| --- | --- | --- | --- |
| Creating agent → local Traceweave | (a) | File paths or bytes over stdio or loopback; **never leaves the machine** | — |
| Local Traceweave → TSA | (a), (b) | An RFC 3161 request whose imprint is the SHA-256 of the signature, plus an optional request nonce | The digest, the requester's IP address and the time (lane 13, T1) |
| Local Traceweave → OpenTimestamps calendars | (a), (b) | The same digest | The same; the client adds its own nonce (T4) |
| Creator → hosted witness | (b) | TLS; the `A2A-Version` header; a credential (§7.3); a `SendMessageRequest` whose message has one `data` part `{"requestVersion": "traceweave-witness-request-draft-1", "presented": {"kind": "dsse-signature-sha256", "sha256": "…"}}` and the extension URI | Caller identity from the credential, the digest, the time, the IP address, the message id |
| Hosted witness → registrant | (b) | A `Task` with one artifact: the signed witness statement and its TSA evidence | — |

**Neither source code nor fingerprints need to leave the machine.** The statement, possession digests and catalogue are built locally (§4). The only value any remote party needs is a 32-byte digest of a signature over a statement that contains a fresh 256-bit nonce. That digest reveals nothing about the content, even to someone holding a guessed file (§5). The fixtures enforce this. A `raw` or `url` part sent to the witness is rejected (`content-on-wire`), and so is a digests-only card served over plain HTTP. Fingerprints in a request are `forbidden-field`. Presenting the artifact digest instead of the signature digest is `evidence-wrong-target`: it would let the witness confirm guessed files.

**Residual exposure.** The witness operator learns who registers, when, and how often. Repeated requests link a caller's registrations. If the operator ever publishes its records, that becomes a public activity log of identities. The witness statement given to the creator contains the caller identity, so disclosing that statement in a dispute discloses the identity too.

### 19.4 Agent cards, skills, lifecycle, errors, idempotency and caller authentication

Illustrative fixtures (labelled illustrative; no service exists):
- `a2a-card-hosted-witness.json`: an OpenID Connect security scheme with a security requirement, HTTPS, one skill `witness-digest`, and the profile extension with `required: true` and `wire: digests-only`.
- `a2a-card-local-registrar.json`: loopback interface, skills `register` and `verify`, `wire: local-only`.
- `a2a-request-witness.json` and `a2a-task-witness.json`: the request and the completed task. The witness statement is really signed with a second public test-only key; its RFC 3161 evidence is a placeholder.
- `mcp-tool-register.json`: the local MCP tool. Its inputs are paths. Its output is an opaque bundle id, never a path (SK.2). Its annotations are `readOnlyHint: false`, `destructiveHint: false`, `idempotentHint: false` (each call makes a new registration) and `openWorldHint: true` (it contacts time services).
- `rendering-agent.json`: user-facing text for an agent-made registration.

**Validation.** No A2A JSON Schema is published in the repository (§19.1), so the A2A fixtures were **not validated against a published schema**. The checker compares them with the field lists of `a2a.proto` at `v1.0.1`: required and allowed fields, bindings, Major.Minor version, part one-of, task states. The MCP tool fixture **was** validated against `$defs/Tool` of MCP `schema.json` at `862397ce` (SHA-256 `907dcebc…b551`), with the repository's pinned `jsonschema` 4.23.0: 0 errors. The negative `neg-mcp-tool-shape` is also schema-valid: it fails only a Traceweave rule.

**Lifecycle.** `SUBMITTED` → `WORKING` (obtaining the TSA token) → `COMPLETED`, with exactly one artifact holding the witness bundle. `REJECTED` covers a policy refusal: quota exhausted, or a caller barred for abuse. `FAILED` covers a witness that could not obtain its TSA token; it gives no partial statement. `INPUT_REQUIRED` and `AUTH_REQUIRED` are not used: authentication happens up front (§7.4), and the request is complete or invalid.

**Errors** (categories from A1 §3.3.2):

| Condition | Error |
| --- | --- |
| Missing or invalid credential | Authentication error (HTTP 401) |
| Malformed data part, wrong `requestVersion`, digest not 64 hex | Validation error (JSON-RPC `-32602`) |
| A `raw`, `url` or `text` part | `ContentTypeNotSupportedError` |
| Request without the profile extension | `ExtensionSupportRequiredError` |
| `A2A-Version` not `1.0` | `VersionNotSupportedError` |
| Rate limit or TSA outage | System error, with `Retry-After` |

**Idempotency.** The witness keys requests on (authenticated caller, `messageId`). A retry with the same pair returns the same task and the same artifact. A new `messageId` for the same digest creates a second witness statement. That is correct, because each statement records one presentation.

**Caller authentication.** Use OpenID Connect or OAuth 2.0 client credentials for agents, and mutual TLS for organisations. The witness records `{scheme, issuer, subject}` as authenticated by that issuer, nothing more. A hosted card should be signed with JWS (§8.4) and its key pinned in verifier policy, so a fake witness card is detectable.

**Local route.** A2A §7.1 requires encryption for production deployments, so a loopback A2A listener is a development convenience. The preferred local route is MCP over stdio. It opens no listener, and its credentials come from the environment (M1 authorization).

### 19.5 What an agent-made registration can and cannot evidence

It **can** show that a particular key signed a statement naming these bytes no later than T. With (b), it also shows that a caller authenticated by a named issuer presented the signature digest at the witness's receipt time.

It **cannot** show:
- whether a person or an agent created the content;
- whether the agent acted on a person's instruction;
- on whose behalf it acted. An OAuth token held "on behalf of" a user shows delegated **authorization** to call the witness, not creation;
- that the content came from that agent rather than being copied into its output.

A key held by an agent runtime says nothing about the human. A key held by a person but used by their agent says nothing about which of them wrote the bytes.

**Design choices.** The statement gets **no** creator or agent field in this draft (`authorship-claim` covers attempts). If the owner wants the generating tool recorded, add it later only as a claim (`claims.generator`), shown as claimed. By default, the creator key belongs to the person or organisation, and an agent uses it only through the local tool with the person's consent. MCP's "human in the loop" SHOULD applies.

**Required wording.** Every rendering of an agent-made registration uses only the §11 templates, includes the per-key bound sentence and the two fixed §11 sentences, and adds this one (`notice-missing`):

> A registration made by or through an agent shows which key signed it and, for a hosted witness, which authenticated caller presented the digest; it does not show whether a person or an agent created the content, or on whose behalf.

### 19.6 Abuse and mitigations

| Abuse | Mitigation | What remains |
| --- | --- | --- |
| Registering content one did not create, including mass registration of scraped content by agents to manufacture earlier records | None technical. §11 and §19.5 wording everywhere. The hosted witness offers **no** public lookup by digest, so it is not a registry that answers "who registered this?". Per-caller quotas | Anyone with a copy can register it. First to register is not first to create |
| Flooding the hosted witness | Authentication on every request; per-caller rate limits and quotas (MCP servers "**MUST** … Rate limit tool invocations"); one 64-hex digest per request; refusal as `REJECTED` | Cost to the operator, which is why SK.5 must decide |
| Flooding public TSAs and calendars from the local tool | One signature covers up to 64 subjects (§4.1); batch per work session | Each service's own limits apply |
| Backdating through the witness | The caller cannot set `receivedAt`. The witness's own TSA token bounds its statement. The witness counts as one independence group under the verifier's policy, so q = 2 still needs an unrelated root | A compromised witness backdates its own statements only |
| Claimed agent times presented as proof | A2A timestamps, timestamp-extension metadata and `claims.createdAt` are claimed only (§2) | — |
| Replaying a witness response onto another registration | The statement names the exact signature digest (`evidence-wrong-target`) | — |
| Prompt injection that makes an agent register or disclose | Only digests leave the machine; the tool's paths and outputs stay local; human confirmation; annotations treated as untrusted (M1) | An agent can still be induced to register something; that registration shows only what §19.5 allows |
| A fake witness | JWS-signed card (A1 §8.4); witness key pinned in verifier policy | — |

### 19.7 Roadmap mapping (proposed wording for the roadmap author)

- **SK.1** (wraps stable I2 commands): the MCP tool and the local A2A registrar wrap `register` and `verify` once those commands exist and are stable. Diagnostics pass through unchanged.
- **SK.2** (canaries): add "registration tools return opaque bundle ids; seeded paths, key material and nonces appear 0 times in model-visible output".
- **SK.3** (A2A design): proposed addition: "Registration is local-first with the registrant's key; a hosted witness, if any, receives only the SHA-256 of a DSSE signature and returns a signed witness statement as an A2A artifact. Design: `spec/registration-record.md` §19." The non-author review stays required.
- **SK.4** (A2A interoperability): A2A publishes no committed JSON Schema; `a2a.json` is generated from `a2a.proto`. **New wording needed:** "the agent card and skill descriptions validate against the JSON Schema generated from `specification/a2a.proto` at a pinned A2A tag, with the generator and its version recorded (0 errors)".
- **SK.5** (hosted service, owner): add the operating requirements of §19.2 as the decision's checklist: key custody, accountable operator, availability, cost, retention and privacy policy, accepted identity providers, abuse policy.
- **M4:** the witness becomes one more time-evidence type (`traceweave-witness`), counted as one independence group by the verifier's policy. The M4.5 decision record should say whether that type exists.
- **New REG.5 (E, S):** the agent fixtures (cards, request, task, tool, renderings) are checked by `validate`; 0 `raw` or `url` parts and 0 fingerprints in any hosted-route fixture; every card skill and agent rendering carries the required sentences.

**Needs the owner:**
- running any hosted witness or signer (SK.5), and who operates it;
- its keys, custody and costs;
- which identity providers callers may use;
- whether agents may hold their own registration keys by default;
- publishing the extension URI and the witness predicate under `traceweave.org`;
- the SK.3–SK.5 and REG wording above.

## 20. Verification of this draft

Run on 2026-11-24 on `roadmap-v2` (parent `2186523`), over this draft, lane 13 and the fixtures directory:

- **`make_real_vectors.py`,** run once. It wrote 19 files to `real-format/`. `MANIFEST.json` records `openssl ts -verify` for every token:
  - OK: the good, valid-intermediate, decoy-first and ECDSA tokens, and the other-digest token against its own request;
  - FAILED: the tampered, non-critical-EKU, wrong-ESS, end-entity-issued and expired-intermediate tokens.

  Only the local `openssl` was used; no external service was contacted.
- **`check_registration.py`** (draft-5):
  - the Ed25519 and PAE self-tests pass;
  - 86 positive fixtures give no code, and each of the 147 negative fixtures gives exactly its expected codes (after the draft-5 follow-up, §9.1, §4.7, addendum fixes and CD-B2);
  - all 46 wrong-implementation cases behave as required;
  - all 57 codes appear in this document and have a negative fixture;
  - the §9.1 check character detects every one of 53,568 single-character substitutions (the self-test asserts it).
- **`enumerate_key_events.py`** (60 s, after the follow-up):
  - 1,010,100 sequences of length 1–3 exhaustively, and 200,000 sampled sequences of length 4, over 100 symbols: **0 violations** of the 13 invariants;
  - the loading sample, 300 sequences as signed bundles, now also with prepended foreign signatures: 0 mismatches;
  - the mutation check at length ≤ 2: 345 violating sequences with no supersession or disputes, 430 with trust through disputed rotations, and **40 with the draft-4 fixed point**.
- **Rebuild.** `build_fixtures.py` rerun gives byte-identical files.
- **Repository checks:** `tools/validate.py`, `python -m unittest discover -s tests`, `tools/validate.py --links-all`, `tools/check_hygiene.py --messages` and `git diff --cached --check`. Results are in the commit message of this change.
- **MCP.** The tool fixture still validates against MCP `schema.json` `$defs/Tool` (0 errors).
- **Not done:** no token, proof, log entry or cosignature from any real service was requested or verified, and no implementation exists.

## 21. Review dispositions (draft-2)

Every finding of the [non-author review](../research/reviews/registration-record-review.md) (`5c3d9c5`), with what changed. "Fixture" names the evidence in [test-vectors/registration](../test-vectors/registration/README.md).

| Finding | Disposition | Where |
| --- | --- | --- |
| F1 bounds per signature, not per statement | Fixed. Bounds are computed per signature from evidence targeting it. Each names its key. A later co-signature inherits nothing. The bound sentence is generated per key | §6.4, §10 step 10, §11; `bundle-cosigned`, `verification-result-cosigned`, `rendering-cosigned`, `neg-key-bound-misattributed`, `neg-key-bound-misattributed-rendering` |
| F2 roots by trust anchor; independence by policy; three sources | Fixed. `root: {kind, anchorSha256}` replaces labels. The policy lists anchors and independence groups. Three sources (two TSAs and Bitcoin) with q = 2 are recommended, and both bounds are always reported | §2, §6.3, §13, RD1, RD5; `neg-root-not-anchored`, `neg-quorum-same-anchor`, `verification-result-revoked` |
| F3 key events as verification input; hostile early compromise claims | Fixed. Who may assert an event; events need their own quorum bound; a look-back clamp; `disputed` instead of silent `untrusted`; event outcomes in the result | §8, §10 steps 3–4, RD15, RD17; `verification-result-compromise-recent`, `-compromise-early`, `-event-unauthorized`, `neg-key-event-ignored` |
| F4 rendering rules; "permission" in sentence 2 | Fixed. The allow-list of templates rejects all four accepted renderings. Sentence 2 now ends "…who owns it, or that its use is permitted." | §11; `neg-authorship-claim-0`…`-4`, `neg-rendering-unlisted-line` |
| A1 which bytes the target covers | The raw decoded signature bytes | §6.1; `neg-evidence-target-base64` |
| A2 which bound `after-proved-bound` compares | The earliest `notAfterAnyRoot` over valid signatures, reported as `comparedWith` | §10 step 11 |
| A3 accuracy contradiction | The policy gives `accuracySeconds` per anchor. A token without accuracy and with none in policy is the outcome `unsupported`, not a failure code. `neg-evidence-shape` now tests a malformed `genTime` | §6.2; `verification-result-no-accuracy`, `neg-accuracy-assumed` |
| A4 Ed25519 strictness | Pinned to RFC 8032 §5.1.7, cofactorless, with S < L, canonical A and R, and A not of small order; self-tested against two lenient verifiers | §10.1, RD16 |
| A5 field names only in fixtures | Named in §6.2 | §6.2 |
| A6 "and others" key lists | Closed lists, stated | §4.6 |
| A7 key lookup with absent or unmatched hint | `unknown-key`; no trial verification | §10 step 2 |
| A8 opening catalogue bytes | The exact stored bytes; RFC 8785 bytes in the fixtures | §4.4, §9 |
| W3 two TSAs under one CA as two roots | Rejected by anchors and policy groups | `neg-quorum-same-anchor`, `neg-root-not-anchored` |
| W4 nonce reused | Producer obligation; cross-record check | §4.2; `neg-nonce-reused` |
| W6b subject over normalized bytes, bytes not supplied | Producer obligation; a verifier without the bytes must say `not-supplied` | §4.1; `neg-subject-unsupplied-match` |
| W8 co-signer reported with the earlier bound | Rejected | as F1 |
| W9 TSA certificate validity at `genTime` | Placeholders now carry `signerCertificate`; outside validity gives `invalid` | §6.2; `neg-cert-validity-ignored` |
| W10 compromised key still `trusted` | Rejected | as F3 |
| W12 four authorship renderings | Rejected | as F4 |
| Four codes with no negative fixture | `report-digest`, `profile-mismatch`, `catalogue-not-report-input` and `fixture-shape` now have one each. The checker now fails if any code lacks one | §18 |
| Wrong-implementation self-test | Added: 14 in-memory cases (W3, W8, W10, the four W12 lines, the margin dropped, the earliest taken as quorum, revocation ignored, the base64 target, two lenient Ed25519 verifiers, a non-canonical point) | §18 |
| RFC 3161 revocation and reason codes; request nonce; policy OID | Added, with outcomes `revoked` and `wrong-policy`, and code `tsa-nonce-mismatch` | §6.2; `verification-result-revoked`, `neg-tsa-nonce-mismatch` |
| OpenTimestamps "offline" needs a header source | Stated: a trusted node or retained header file | §6.2, §13, §14 |
| RD6 margin rationale pointed the wrong way | Corrected; the honest-majority assumption is stated | §6.2, RD6 |
| Retroactive loss of one source | Threat added; three sources recommended | §12, §13 |
| Key-theft window; linkage; low-entropy content; algorithm ageing triggers | Added | §5, §7 (I0′), §12 |
| Possession digest adds nothing for content public at T | Stated | §4.3, §12 |
| Published commitment nonce reused in fixtures | Stated in the README and in the builder | README |
| Lane 13 RFC 3161 §4.1 claim incomplete; "offline once complete" | Corrected in lane 13 | lane 13 T1 row, Decision |
| §7 test-submission disclosure | Recorded for the owner decision | §17 |

## 22. Resolution table (draft-3)

Every item of the [draft-2 confirmation review](../research/reviews/registration-record-draft-2-review.md) (`66aec94`). Fixtures are in [test-vectors/registration](../test-vectors/registration/README.md); "self-test" means a case in the checker's wrong-implementation self-test.

| Item | Resolution | Section | Fixtures |
| --- | --- | --- | --- |
| **B1** stolen key rotates to the thief; successor stays trusted | Compromise disputes rotations and retirements of the key with proved time ≥ `start`; no trust through a disputed rotation; conflicting rotations both disputed | §8 | `verification-result-rotation-hijack`, `verification-result-rotation-conflict`, `neg-rotation-hijack`, `neg-rotation-conflict`; self-test ×2 |
| **B2** event outcomes depend on input order | Evaluation by proved time E (ties by payload digest), authorization only from smaller E, iterated to a fixed point; output sorted | §8, §10 step 3 | `verification-result-event-order-a` and `-b` (identical objects), `neg-event-order-dependent`; self-test |
| **B3** trust and events keyed on the 64-bit keyid | `trustedKeys` and event targets and successors by SHA-256 of the full key; `keyid` must agree with the subject digest | §7, §8 | `neg-trust-by-hint` (`key-identity-by-hint`), `neg-key-event-subject-mismatch`; self-test |
| **S1** trust decided on one source | With no quorum bound, a signature touched by an event is `disputed` | §8, §10 step 4 | `verification-result-single-source-event`, `neg-trust-without-quorum`; self-test |
| **S2** RFC 3161 token checks missing | Imprint, request nonce, ESSCertID or ESSCertIDv2, critical timeStamping EKU, single SignerInfo and signature, chain to the pinned root; each with a code or outcome | §6.2 | real-format: `evidence-real-rfc3161`, `neg-tsa-imprint-mismatch`, `neg-tsa-signature-invalid`, `neg-tsa-eku-invalid`, `neg-tsa-signing-cert-mismatch`, `neg-real-root-not-pinned`; self-test |
| **S3** offline result without revocation date | `revocationData` with `source` and `asOf` per anchor; `no-revocation-data`; `revocationDataAsOf` per evidence; "as of" in §12 and §13 | §6.7, §12, §13 | `verification-result-no-revocation-data` |
| **S4** witness and its TSA counted twice | A witness evidence rests on two anchors; groups merged per evidence (union-find) | §6.2, §6.3, §19.2 | `verification-result-witness-shared-tsa` (`below-quorum`), `-witness-independent`, `neg-witness-shared-tsa`, `evidence-witness`; self-test |
| **S5** cosigned checkpoint without inclusion proof | Type removed in draft-3 | §6.2, RD19 | `neg-checkpoint-type-removed` |
| **S6** renewal undefined | Renewal evidence over the earlier token's bytes; rule at verification time; limits stated | §6.6, §12, §14 | `bundle-renewed`, `evidence-renewal`, `verification-result-renewed`, `-expired`, `neg-expired-accepted`, `neg-renewal-wrong-target`; self-test |
| **S7** URL-safe base64 rejected | Accepted, as DSSE requires | §10 step 1 | `bundle-url-safe`; self-test |
| **S8** claims discipline | Third fixed sentence on ordering; `ordering-claim`; "registrant" throughout; §19.2 (a) reworded; the witness template names its TSA | §1, §11, §14, §15, §19 | `neg-ordering-claim`, `rendering-agent`; self-test |
| **S9** missing vectors | Added: `wrong-policy`; `keyCompromise` and retaining-reason revocations; a result that applies a rotation; B1–B3; two orders; subject mismatch; S1; S4; URL-safe; duplicate signer; out-of-range index; stripped evidence; real-format TSA and OpenTimestamps vectors made locally | §6.5 | `verification-result-wrong-policy`, `-revoked-key-compromise`, `-revoked-retaining`, `-rotation-applied`, `-stripped`, `neg-duplicate-signer`, `neg-signature-index-out-of-range`, `bundle-real`, `verification-result-real`, `evidence-real-*`, `neg-real-ots-*` |
| **S10** anchors written by the producer | Real-format vectors compute anchors from the pinned root certificate and header file; README and REG.1 say placeholders do not test this | §2, §6.5, §15 | `verification-result-real`, `neg-real-root-not-pinned`, `neg-real-ots-other-chain` |
| **S11** untrusted co-signer changes the claim outcome | Compare only with trusted signatures; `not-compared` when none | §10 step 11 | `verification-result-claim-trusted-only`, `neg-claim-any-signer`; self-test |
| **S12** C2PA claim in §15 | Corrected: a C2PA export needs its own token over the claim signature; registration evidence does not map | §15 | — (text) |
| **S13** roadmap gates cannot be evidenced | Exact ROADMAP.md text proposed for M4.3, M4.5, M4.6 and REG.1–REG.5; adoption is the owner's | §15, §17 | — (text) |
| **N1** fractional seconds | `notAfter` rounded up to the whole second | §6.2 | `realformat.py` (`gtime`, accuracy) |
| **N2** `blockTime` from the evidence | Read from the pinned header; minimum confirmations | §6.2 | `verification-result-real`, `neg-real-ots-other-chain` |
| **N3** evidence can be stripped | Stated: bounds only get later | §6.4, §12 | `verification-result-stripped` |
| **N4** in-toto, DSSE, Ed25519 conformance | No change needed | §10.1 | — |

## 23. Resolution table (draft-4)

Every item of the "Draft-3 confirmation" section of the [review](../research/reviews/registration-record-draft-2-review.md#draft-3-confirmation) (`1c7043f`). "Review case" is the reviewer's reproducing case, kept as a negative fixture.

| Item | Resolution | Section | Fixtures |
| --- | --- | --- | --- |
| **D1** retired or rotated-away key still rotates (also at equal times) | First supersession of a key ends it: later events it signs, other than `compromised`, are `ignored-superseded`; equal-time different supersessions are both `disputed` | §8 | `verification-result-retired-then-rotated`, `-retired-and-rotated-same-time`; review cases `neg-retired-key-rotates`, `neg-retired-key-rotates-same-time`; self-test ×2 |
| **D2** later second rotation erases the honest chain | Later rotations of a superseded key are ignored; conflicting rotations disputed only at equal times or inside a compromise window; RD18 re-examined | §8, RD18 | `verification-result-late-second-rotation`, `-late-compromise-claim`, `-rotation-conflict`; review case `neg-late-rotation-erases-chain`; self-test ×3 |
| **D3** OpenTimestamps headers can be forked | Policy pins a checkpoint at or above the attested height plus `minConfirmations`; linkage back from it; the verifier's own node only | §6.2, §6.3, RD21 | `real-format/headers-forked.bin`; review case `neg-real-ots-forked-headers`; self-test |
| **D4** chain check is signatures only | RFC 5280 path validation at `genTime` (basicConstraints, keyUsage, validity, path length, critical extensions); every token cross-checked against `openssl ts -verify` | §6.2, §6.5 | `verification-result-real-issued-by-end-entity`, `-real-expired-intermediate`; review cases `neg-real-issued-by-end-entity-accepted`, `neg-real-expired-intermediate-accepted`; `MANIFEST.json`; self-test ×2 |
| **D5** revocation keyed by root | Each revocation names a certificate by SHA-256; it applies only to paths through it | §6.2 step 9, §6.7 | `verification-result-revoked-one-unit`; review case `neg-revocation-by-root` |
| **D6** simulated results rendered as real | Marker line required first; production renderers refuse (REG.4) | §11, §15 | review case `neg-simulated-unmarked`; self-test |
| **D7** algorithms | Supported algorithms stated; others are future work for REG.3 | §6.2, RD22 | — (text) |
| **D8** TSTInfo version; duplicate attributes | Both checked | §6.2 step 5 | `realformat.py` |
| **D9** renewal bytes | Stated: the renewal relies on the policy's retained revocation data; the stronger form is left to RD11 | §6.6 | — (text) |
| B3 note: 64-bit keys in renderings | Renderings show 128 bits of the key's SHA-256 | §11 | `rendering*.json` |
| REG.1 gate text | Counts corrected (three OpenTimestamps negatives, plus the pinned-root and two path negatives); fails if the D3 or D4 vectors are accepted; includes the enumeration | §15 | — |
| REG.2 gate text | RFC 8785 canonical bytes of results | §15 | — |
| REG.3 gate text | k = 3 named; revoked-certificate direction uses the local test TSA; checkpoint pin | §15 | — |
| REG.4 gate text | No rendering from a simulated result; 128-bit keys | §15 | — |
| Own sweep: equal-time onward rotation | Trust flows only through a rotation proved strictly after its signer became trusted | §8 | `verification-result-chain-same-time`, `neg-chain-same-time`; `enumerate_key_events.py` |

## 24. Resolution table (draft-5)

Every item of the "Draft-4 confirmation" section of the [review](../research/reviews/registration-record-draft-2-review.md#draft-4-confirmation) (`2186523`).

| Item | Resolution | Section | Fixtures and tests |
| --- | --- | --- | --- |
| **E1** a successor's compromise report does not converge; the result depends on the number of unrelated events | Two passes, no fixed point: standing decided once in proved-time order without consulting disputes; disputes never feed back; a report never disputes its own signer's appointment; no pass limit, and a non-settling implementation is an error | §8 | `verification-result-e1`, `-e1-extra-1`, `-e1-extra-2`, `result-equivalence-e1` (byte-identical), `-e1-second-level`; review cases `neg-e1-report-disputes-own-appointment`, `neg-extra-event-changed-result`; enumeration I2, I10, I13; mutation "draft-4 fixed point": 40 |
| Enumeration misses E1 | Steps ±10 and ±40 days (shorter and longer than the look-back); claimed starts of 2, 20 and 60 days; probes at start − 1 s, start, E − 1 s, E and without quorum | §8 | `enumerate_key_events.py` |
| Trust claims without an invariant | I8 window, I9 no quorum, I10 an added rejected event, I11 who may sign, I12 equal times, I6 widened to successor-signed late reports, I13 own standing | §8 | `enumerate_key_events.py` |
| Enumeration bypasses event loading | A loading sample of 300 sequences as real signed bundles, with tampered, single-source and subject-mismatch events | §8 | `enumerate_key_events.py`; it found the identity defect (`verification-result-same-statement-two-signers`, `neg-event-identity-collision`, `-same-statement-twice`) |
| `minConfirmations` unvalidated; forging above the checkpoint | `minConfirmations ≥ 1` and the checkpoint shape validated; attested height ≤ checkpoint − `minConfirmations` | §6.2, §10 | `neg-policy-min-confirmations-zero`; `realformat.linked_to_checkpoint` |
| `compromiseLookbackSeconds` unvalidated | Non-negative integer; 30 days stated as a placeholder | §10, RD15 | `neg-policy-negative-lookback` |
| Recovery keys have no field | `recoveryKeys: [{keySha256, recovers, notBefore}]`, trusted from `notBefore` only | §8, RD18 | `verification-result-recovery-key` |
| Threat row omits the lost successor chain | Stated: a report within the window disputes the honest rotation permanently | §12, §8 | — |
| D7 ECDSA reported as a forgery | Outcome `unsupported` | §6.2 | `verification-result-real-ecdsa` |
| Path building does not backtrack | Every candidate issuer tried | §6.2 | `verification-result-real-decoy-first` |
| Leaf keyUsage has no openssl cross-check | Stated (openssl refuses to issue such a token) | §6.2 | — |
| REG.1 passes with E1 present | Tied to the widened enumeration, its loading sample and its three mutations | §15 | — |
| Draft-5 confirmation **F1**: a key event is read from its first signature only | Exactly one signature per key event; otherwise `key-event-signatures` | §8 step 1, RD17 | `neg-key-event-two-signatures`, `neg-result-with-foreign-signature`; enumeration loading sample |
| Draft-5 confirmation **F2**: RD17 contradicts §8 | RD17 now states the two-pass rule (standing through a rotation disputed or not), that recovery keys do not sign events, and that there is no other signer field | RD17 | — (text) |
| Draft-5 confirmation note: twin statements of one appointment | Every rotation of the target to the report's signer counts as its one appointment | §8 pass 2 | `verification-result-e1-twin-rotation` |
