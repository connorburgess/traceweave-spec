# Registration record: design draft

Status: research draft, 2026-11-23. Not normative. No schema, profile, vector or roadmap file is changed by this draft. Nothing was submitted to any time-stamping authority, log, calendar or witness. Every time evidence in the [fixtures](registration-fixtures/README.md) is a labelled placeholder. Evidence for the mechanisms is in [lane 13](../lanes/13-timestamp-evidence-review.md) (cited as T1–T9, L1–L2). Context: the [roadmap](../../ROADMAP.md) finding of 2026-11-23 that a mark is a finding aid and not evidence of origin; M4; [attestations](../../spec/attestations.md); [core](../../spec/core.md); the [catalogue and report contract](../../spec/catalogue-report.md) §6.6–§8 (B10); [use cases](../../docs/use-cases.md) UC-3 and UC-4; the [C2PA mapping draft](c2pa-mapping.md); the [lane 11 audit](../lanes/11-report-audit.md) (signed reports are M4).

## 1. Summary

A **registration record** lets a creator later show: *these exact bytes existed, and my key signed a statement naming them, no later than time T.* It is a signed in-toto statement (DSSE), plus one or more **time evidences** attached as separate objects. Each time evidence countersigns the statement's signature under its own trust root. A verifier reports each part separately: digest, possession, signature, signer trust, each time evidence, and the combined time bound. There is never a single "authentic" verdict.

A registration does **not** show authorship, originality, ownership or permission. It does not show that the registrant created the content rather than copied it first. **First to register is not first to create.** §11 makes this text mandatory wherever a registration is shown to a person.

Recommended first mechanisms: **RFC 3161 time-stamp tokens** and **OpenTimestamps** (Bitcoin). They have unrelated trust roots, both are verifiable offline once complete, both send only a digest, and neither needs an account (§6, §16 RD1).

## 2. Terms

- **Claimed time:** a time written by the registrant (`claims.createdAt`), like core's `recordedAt` and the report's `generatedAt`. Anyone can write any value. It is never shown as proved.
- **Proved bound (`notAfter`):** an upper bound on when the signed statement existed, derived from a verified time evidence under the verifier's policy. Time evidence gives only an upper bound. Nothing here proves a lower bound or a creation time.
- **Root:** the trust anchor a time evidence depends on: a TSA certificate chain, Bitcoin proof of work, a log key, a witness key. Two evidences from the same root count once.

## 3. Objects

| Object | Version string | Content | Fixture |
| --- | --- | --- | --- |
| Registration statement | `traceweave-registration-draft-1`, predicate type `https://traceweave.org/predicate/registration/draft-1` (proposed, not published) | in-toto Statement v1 (§4) | `statement.json` |
| Bundle | `traceweave-registration-bundle-draft-1` | DSSE envelope, public keys, time evidences | `bundle-two-roots.json` |
| Time evidence | `traceweave-time-evidence-draft-1` | One evidence, standalone, naming its target signature and root (§6) | `evidence-*.json` |
| Verification result | `traceweave-registration-verification-draft-1` | The closed outcomes of §10 | `verification-result.json` |
| Report link | `traceweave-registration-link-draft-1` | Ties a comparison report to a registration without changing the report (§9) | `report-link.json` |
| Rendering | `traceweave-registration-rendering-draft-1` | User-facing text, with §11 sentences | `rendering.json` |
| Key event | `traceweave-key-event-draft-1`, predicate type `https://traceweave.org/predicate/key-event/draft-1` | Retire, rotate or report a key compromised (§8) | `key-event-rotation.json` |

All of these are proposals in the `traceweave.org` namespace, which the [C2PA draft](c2pa-mapping.md) D3 also leaves to the owner.

## 4. The registration statement

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [{"name": "sum.go", "digest": {"sha256": "974c8d0a…697c"}}],
  "predicateType": "https://traceweave.org/predicate/registration/draft-1",
  "predicate": {
    "registrationVersion": "traceweave-registration-draft-1",
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

Each subject is the SHA-256 of the **original artifact bytes**, as in the catalogue (`sha256`, contract §3.2). One to 64 subjects; no two share a digest. `name` is an opaque label with the catalogue id pattern `^[a-z0-9][a-z0-9._-]{0,63}$`, so it cannot hold a path (`subject-name`). The existing statement schema allows one subject; this predicate needs its own restricted adapter, which is why it has its own predicate type.

### 4.2 Nonce

`nonce` is 32 fresh bytes from an operating-system random source, new for every registration. It has two jobs. It makes the statement bytes unguessable, so the digest sent to time services reveals nothing, even to someone holding the content (§5). It also salts the possession digest. An all-zero or malformed nonce is rejected (`nonce-invalid`).

### 4.3 Possession digest

`possession[i].sha256 = SHA256("Traceweave-Possession-v1" || 0x00 || nonce || L || A)`, where `A` is the artifact bytes and `L` its length as an unsigned 64-bit big-endian integer. This mirrors the core commitment framing.

*Why.* A time evidence over a plain artifact digest shows that *someone* knew that digest by T. A digest can be copied from anywhere it was published: a C2PA hard binding, a report body, a package index. The possession digest uses the registrant's own fresh nonce, so nobody could have computed it before the registration. Whoever made it held the bytes (or was given them) by T. When the record is disclosed, the verifier recomputes it from the supplied bytes (`possession-mismatch`). It does **not** exclude a copier: a person who copied the content also holds it.

### 4.4 Catalogue commitment (optional)

`catalogue` commits to the private catalogue with the existing salted scheme `sha256-salted-catalogue-v1` ([core](../../spec/core.md#private-catalogue-commitment)), plus the profile triple. It lets a later comparison report be tied to the registered catalogue (§9) without revealing fingerprints now. A plain catalogue digest is rejected (`catalogue-unsalted`; §5 explains why).

### 4.5 Implementation provenance (B10)

`implementation` and `specCommit` have the report provenance form (contract §6.6). The same rule applies: the commit is fixed at build time and only by a verified, clean build (§6.8 B10). An unstamped build refuses to write a registration, just as it refuses a report document (`provenance-shape` covers the form only). The fixtures carry placeholder all-zero commits, as `example-report.json` does. Provenance stays cooperative-build evidence; a registration signature attests who registered, not which code ran.

### 4.6 Claims, and what the statement must not hold

`claims.createdAt` is the only time in the statement, and it is claimed. A time-like field anywhere else (`provedAt`, `timestamp`, `notAfter`, `genTime`, `registeredAt` and others) is rejected (`time-in-statement`): a registrant cannot prove its own time. Content, fingerprints, tokens, catalogue bytes and openings are rejected (`forbidden-field`). Unknown fields are rejected (`statement-shape`), and so is a wrong predicate type (`predicate-type`).

## 5. What publishing each value reveals

A registration is **private by default**. The creator keeps the bundle; only the digest of the signature goes to time services (§6). The table assumes the item named is published, for example in a dispute or a public log.

| Published value | Reveals about unknown content | Guessing attack | Verdict |
| --- | --- | --- | --- |
| Digest of the DSSE signature (what time services see) | Nothing; the statement contains a fresh 256-bit nonce | None feasible: the attacker must guess the nonce | Safe to send. Links the evidences of one registration to each other and to the requester's IP and timing (T1 §4 item 5, T4) |
| Artifact digest (`subject`) | Nothing about content that is unknown to the attacker | **Confirmation:** anyone holding a candidate file confirms exact equality. Low-entropy content (a short snippet, a template with few variants, an image from a known set) can be enumerated. Links to every other place the digest appears | Disclose only with the bytes, in a dispute |
| Possession digest | Nothing without the nonce; once the statement is disclosed, the same as the artifact digest | As the artifact digest, after disclosure | Disclosed with the statement |
| Salted catalogue commitment | Nothing until opened (256-bit nonce) | None before opening. **Opening reveals the whole catalogue** (core) | Safe in the statement |
| Plain catalogue digest | Nothing directly | **Whole-set confirmation:** catalogues are deterministic in their artifacts, ids and configuration (contract §3.3). Anyone with candidate files, the public profile configuration and guessed ids rebuilds the bytes and confirms. Ids such as `sum.go` are easy to guess | Never (`catalogue-unsalted`) |
| Fingerprints | Structure, token positions and spans | **Fragment membership:** anyone can fingerprint any text and learn which fragments the creator's private content contains, without holding it. Short, low-entropy k-grams may be enumerable (I) | Never in a registration (`forbidden-field`) |
| Public key | Links all registrations under it | — | Published only if the creator chooses (§7) |
| OIDC identity (Fulcio certificate) in a public log | Identity, time, and the logged digest, **for ever** (T3) | — | Opt-in only, owner-gated |

## 6. Time evidence

### 6.1 What is time-stamped

Each evidence targets **the SHA-256 of one DSSE signature value** (`target: {kind: "dsse-signature", signatureIndex, sha256}`). This follows Sigstore's countersigning advice and C2PA's v2 payload (T3, T6). A signature can be produced only from the statement it verifies against. So a bound on the signature is a bound on the statement, including its subjects and possession digests. The bound also survives a later compromise of the registrant's key: a thief can sign new statements, but cannot obtain evidence dated before the theft (§8). Evidence over another digest, for example the statement bytes, is rejected (`evidence-wrong-target`). It could be moved between signatures.

### 6.2 Evidence types and their bounds

| Type | Root kind | `notAfter` | Notes |
| --- | --- | --- | --- |
| `rfc3161` | `tsa-certificate-chain` | `genTime + accuracy`. Without `accuracy` in the token, the verifier's policy must state the root's accuracy (EN 319 421: 1 s for its best-practice policy); otherwise the evidence is `unsupported` | Retain the TSA chain and revocation data as of `genTime`; renew before the TSA key or SHA-256 weakens (T1 §4 item 3, T9) |
| `opentimestamps` | `bitcoin-proof-of-work` | Attesting block header time **+ 7,200 s**. I: header times are miner-chosen within the median-time-past and two-hour rules (T4), so the margin is this draft's choice and needs review (RD6) | `status: pending` until upgraded; a pending proof has no time and must not state one (`pending-counted`) |
| `rekor-v2` | `log-key` | **None.** Rekor v2 has no time of its own (T3); stating one is rejected (`log-time-claimed`) | Inclusion and discoverability only. Pair with a TSA token |
| `cosigned-checkpoint` | `witness-key` | The checkpoint cosignature time, from the witness's clock (T5) | Only through a witnessed log; quorum of witnesses per the log's policy |

A placeholder that does not carry the exact placeholder notice, or whose token text does not start with `PLACEHOLDER`, is rejected (`placeholder-unlabelled`). A malformed evidence is `evidence-shape`.

### 6.3 Combining evidences

The verifier's policy lists accepted roots and a quorum `q` (default 2, RD5). For each accepted root, take the smallest valid `notAfter`, then sort those per-root bounds.
- `notAfterAnyRoot` is the smallest. One root alone vouches for it, so one dishonest or compromised root can backdate it (lane 13 finding 3).
- `notAfterQuorum` is the q-th smallest. At least q independent roots agree that the statement existed by then. With q = 2, backdating needs two unrelated roots to collude, for example a TSA and the Bitcoin chain.

Counting two evidences from the same root as two roots is rejected (`quorum-miscount`). The fixture shows the trade-off: the TSA bound is 10:00:01Z, but the two-root bound is 13:12:00Z, because the Bitcoin margin dominates.

## 7. Signer identity options

| Option | What a verifier learns | Cost to the creator | Privacy |
| --- | --- | --- | --- |
| I0 Self-managed Ed25519 key, public key only in the bundle (**default**) | "Whoever holds this key signed it." Nothing about who that is. Later, the creator can show control by signing a challenge | None. Must keep the key safe and backed up | Nothing published |
| I1 I0, plus the public key posted somewhere dated and third-party-observable (own website, a forge profile) | A weak link between key and a name or account, as strong as that site's history | None | The key is linkable to the name |
| I2 Sigstore Fulcio short-lived certificate (OIDC) | "Someone who authenticated as this identity at an OIDC provider signed it", under Sigstore's trust root (T3 threat model). Needs time evidence because the certificate lasts 10 minutes | An account at an identity provider | Identity and time go into public CT and Rekor logs **for ever** |
| I3 Organisation or qualified certificate (X.509, eIDAS qualified seal or signature) | The issuing CA's identity checks, under its policy | Paid; identity verification | Whatever the certificate contains |

The key id in an envelope is a lookup hint, not identity ([attestations](../../spec/attestations.md)). An unlisted key gives `unknown-key`. Signer trust is the verifier's policy decision, reported separately from signature validity.

## 8. Key loss, rotation and revocation

- **Loss.** Existing registrations stay verifiable: the bundle carries the public key, and the time evidence fixes when each signature existed. The creator can no longer sign new registrations or key events with that key. Recovery is a new key, linked through I1 or I2, not through the lost key.
- **Rotation.** The old key signs a key event (`event: rotated`, `successorPublicKeyHex`) and the creator time-stamps it like a registration. A verifier that trusts the old key may then trust the successor for statements whose bounds are after the rotation bound. A rotation that does not name its successor is rejected (`key-event-shape`).
- **Compromise.** The holder signs `event: compromised` with `compromisedNotBefore: Tc` and time-stamps it. A verifier keeps trusting signatures whose `notAfterQuorum` is before `Tc`; for later ones, signer trust becomes `untrusted`. A thief can also publish a compromise event, but that only reduces trust; it cannot backdate anything. There is no central revocation list for self-managed keys; with I2 or I3, the CA's revocation applies.
- **Retirement.** `event: retired`: no new signatures expected.

## 9. How a comparison report references a registration

The report body is closed (contract §6.2, §7) and must not carry signatures, trust or time results. A report therefore never embeds a registration. A separate **report link** object joins them:
- `report`: the report path and `bodySha256`, recomputed from the canonical body (`report-digest`).
- `registration`: the bundle and the SHA-256 of the statement payload bytes (`statement-digest`).
- `links`: for each pair, the role (`reference` or `candidate`), the subject index and the digest. The report pair's digest, the link digest and the registered subject digest must all be equal (`subject-mismatch`).
- `catalogueOpening` (optional): the catalogue bytes and nonce. They must open the registered commitment (`catalogue-does-not-open`), hash to the report's `referenceCatalogueSha256` (`catalogue-not-report-input`), and the registered profile must equal the report's (`profile-mismatch`). Opening reveals the whole catalogue to whoever receives the link.
- `notShown`: the §11 list.

What this shows: the reference artifact compared in the report is byte-identical to content registered no later than T, and (with the opening) the reference catalogue is the registered one. It shows nothing about the candidate's origin, about direction of copying, or about anything contract §8 forbids.

## 10. Verification procedure

Inputs: a bundle; optionally the artifact bytes, a catalogue opening and key events; and the verifier's policy (accepted roots, quorum, trusted keys, per-root accuracy). Every step reports its own outcome. A failure in one step does not change another step's outcome.

1. **Parse** the bundle strictly (no duplicate keys, `duplicate-key`; size limits as in the signing harness). Check the envelope form and payload type. Outcome `envelope`: `ok` | `malformed` (`envelope-shape`).
2. **Signatures.** For each signature, look up the key by hint among the bundle's keys and verify Ed25519 over `PAE(payloadType, payload)`, the exact payload bytes. Outcome per signature: `valid` | `invalid` | `unknown-key` (`signature-invalid`).
3. **Signer trust** under the policy, including key events (§8). Per signature: `trusted` | `untrusted` | `not-evaluated` (when the signature is not valid).
4. **Statement.** Decode and strictly parse the payload, then apply §4. Outcome `statement`: `ok` | `malformed` | `unsupported`.
5. **Subject digests.** Hash each supplied artifact. Per subject: `match` | `mismatch` | `not-supplied`.
6. **Possession digests.** Per subject: `match` | `mismatch` | `not-supplied`.
7. **Catalogue.** `opens` | `does-not-open` | `not-supplied` | `not-committed`.
8. **Each time evidence.** Check the target, then verify the evidence under its own root, offline from retained material. Per evidence: `valid` | `invalid` | `wrong-target` | `pending` | `untrusted-root` | `unsupported`, with `notAfter` when valid. (Fixtures only: `placeholder`, or `placeholder-assumed-valid` when the result says `simulated: true`.)
9. **Time bound** (§6.3). `quorum-met` | `below-quorum` | `none-valid`, with `notAfterAnyRoot`, `notAfterQuorum`, `quorum` and `distinctRoots`.
10. **Claimed time.** `absent` | `claimed-only` | `after-proved-bound`. The last flags a claim later than the proved bound, which is impossible and points at a wrong clock or a careless registrant.
11. **Output** all outcomes and the fixed `notShown` list: `authorship`, `originality`, `first-creation`, `ownership`, `permission`.

A result must not add a combined verdict (`authentic`, `verdict`, `overall` and similar: `single-verdict`). It must not report the claimed time as a proved bound (`claimed-as-proved`), count a pending proof (`pending-counted`), or add an authorship or ownership field (`authorship-claim`). Any other disagreement with the recomputed outcomes is `result-mismatch`.

## 11. What a registration does not show (required text)

A registration does not show **authorship**, **originality**, **ownership** or **permission**. It does not show that the registrant **created** the content rather than copied it, or that they were first: anyone who obtains a copy can register it, and an earlier creator may never have registered. **First to register is not first to create.** It also does not show a creation time; it gives an upper bound on when the statement existed.

Any user-facing text that presents a registration or its verification (command-line output, the WEB page, an agent skill under SK.3, a C2PA export) MUST include these three sentences verbatim (`notice-missing`):

> This record shows that the content existed, and that this key signed a statement naming it, no later than the time shown.
> It does not show who created the content, that it is original, that the registrant was first to create it, or who owns it.
> First to register is not first to create.

The same text MUST NOT claim proof of authorship, ownership, originality or creation (`authorship-claim`), call the record "authentic" or "verified" as a whole (`single-verdict`), or show the claimed time without the word "claimed" (`claimed-as-proved`). The fixture checker applies these rules to `rendering.json`. They are a floor for review, not a complete wording test.

## 12. Threat model

| Threat | Who | What stops it | What remains |
| --- | --- | --- | --- |
| Backdating a registration | Registrant | Time evidence binds the signature; the registrant cannot choose `genTime` or a block time. Quorum q = 2 over unrelated roots | A TSA that colludes or loses its key backdates `notAfterAnyRoot` (T1 §4 item 2). Bitcoin header times have slack (§6.2) |
| Registering someone else's work | Anyone with a copy | Nothing technical. The record says only "held no later than"; §11 text | A copier who registers first holds an earlier record than a creator who never registers. Disputes need evidence outside this design |
| Replay or transplant of evidence | Anyone | Evidence targets one signature; moving it to another statement fails `evidence-wrong-target`. Re-signing someone's statement with your own key gives a new signature without the old evidence | Copying a whole bundle proves only that the original key holder registered |
| Claiming a published digest without the content | Anyone | Possession digest (§4.3) | A collaborator of the content holder can compute it |
| Privacy leaks | Services, observers, recipients | Only a signature digest leaves; fresh nonce; salted commitments; no fingerprints; private by default (§5) | IP address and timing to TSAs and calendars (T1, T4); identity for ever if a public log is used (T3); opening a catalogue reveals all of it |
| Service shutdown | TSA, calendar, log | Two roots; evidence verifiable offline once complete; retained chains and headers | An OpenTimestamps proof is lost if every calendar disappears before upgrade (T4); a TSA token needs renewal before its key or algorithm ages (T9) |
| Key theft | Attacker | Bounds on old signatures stay valid; compromise events (§8) | Signatures after the theft and before the compromise event are ambiguous |
| Algorithm ageing | Time | SHA-256 and Ed25519 today; renewal by re-time-stamping the bundle (T9) | A renewal must happen before a break, not after |
| Fake or unlabelled evidence | Tool or registrant | Each evidence verified against its own root; placeholders must say so | A verifier with a careless policy (accepting any root) |

## 13. The two mechanisms to implement first, and why

1. **RFC 3161 tokens (T1).** This is the standard form: C2PA, Sigstore bundles, eIDAS qualified time stamps and RFC 4998 renewal all consume it. Precision is about a second. Verification is offline from retained chains. It costs nothing at public TSAs (whose terms the owner must read). It also allows a later qualified TSA for creators who want the eIDAS presumption (L1), without a format change.
2. **OpenTimestamps (T4).** Its root, Bitcoin proof of work, has no operator who can backdate. It needs no account and no fee, and it survives the shutdown of every calendar once upgraded. Its weaknesses (hours of precision, a pending window, LGPL-3.0 client code, a Bitcoin header source to verify) are acceptable for a second root, not for the only one.

Rekor and witness cosigning are deferred: they add discoverability and split-view protection that private registrations do not need. Rekor v2 also needs a TSA token for time anyway (T3).

## 14. What a creator would do in practice

1. Once: generate a signing key with the tool (stored in the private location of contract §6.8 B11) and back it up in two places. Optionally publish the public key somewhere dated (I1).
2. For each piece of work: run a local `register` command on the original files. It hashes them, draws a nonce, computes the possession digests (and, if wanted, builds the private catalogue and its commitment), writes and signs the statement, and sends **only the SHA-256 of the signature** to one or more TSAs and to OpenTimestamps calendars. No content and no identity leaves the machine. The command reports `pending` for the Bitcoin part.
3. A few hours later (the tool can do this on its next run): upgrade the OpenTimestamps proof and save the bundle again. From then on the bundle verifies offline.
4. Keep, unchanged and backed up: the original files' exact bytes, the bundle, the catalogue and its opening, and the TSA certificate chains. A changed file no longer matches; re-registering it is a new registration.
5. Within a few years, before a TSA key or algorithm ages: run `renew` to time-stamp the existing bundle again (T9).
6. In a dispute: hand over the original bytes and the bundle (and the catalogue opening only if needed). The other side runs the verification in §10 with their own policy and reads the §11 limits.

## 15. Roadmap mapping (proposed wording; ROADMAP.md is not changed here)

| Gate | Today | Proposed change |
| --- | --- | --- |
| M4 row, "What becomes possible" | A recipient checks a signed evidence record | Add: "A creator can show that registered bytes existed under their key no later than a time, from two independent roots; a registration never shows authorship or first creation." |
| M4.3 | Negative cryptographic vectors | Add registration reason codes: `evidence-wrong-target`, `possession-mismatch`, `subject-mismatch`, `signature-invalid`, `duplicate-key`, `pending-counted`, `log-time-claimed`, each distinct |
| M4.5 | "A recorded decision on the optional timestamp adapter" | **New wording needed:** "A recorded owner decision selecting the time-evidence types for registration records (proposed: RFC 3161 and OpenTimestamps), the default quorum, and which external services may be used for test tokens." Time evidence is no longer optional for a registration record |
| M4.6 | Commitment/disclosure design review | Extend the scope to the registration nonce, the possession digest and the §5 disclosure table |
| New REG.1 (E, S) | — | Registration fixtures (this directory, after review) checked by `validate`: every positive passes, every negative gives its one code |
| New REG.2 (E, I) | — | Two implementations produce identical outcomes (§10) on every REG.1 fixture |
| New REG.3 (E, I) | — | With owner approval for the services: one real RFC 3161 token and one upgraded OpenTimestamps proof over a synthetic registration, verified with the network denied, k/k, both directions of failure tested (wrong target, tampered token) |
| New REG.4 (E, S+I) | — | Every user-facing rendering contains the §11 sentences and none of the forbidden claims; a non-author checks it (feeds M5.2 and WEB.5) |
| UC-3 | Limit: "Signing alone proves neither ownership nor earlier existence" | Unchanged for signing alone. A new use case (for example UC-9, "Register content now, show possession later") needs owner wording; this draft supplies its limit text (§11) |
| SK.3 | A2A design: only digests on the wire | Consistent: only the signature digest leaves the machine |
| C2PA mapping | Time-stamp row "conflicting" | A C2PA manifest holds **one** RFC 3161 token over its claim signature (T6). The TSA evidence maps; the OpenTimestamps evidence and the quorum are unmapped |

## 16. Open decisions

| ID | Decision | Options | Recommendation |
| --- | --- | --- | --- |
| RD1 | First two mechanisms | (a) RFC 3161 + OpenTimestamps; (b) RFC 3161 from two unrelated TSAs; (c) Rekor v2 + TSA | (a): two unrelated roots, no accounts, nothing public (§13). (b) is the fallback if Bitcoin verification is unwanted |
| RD2 | Which TSAs | Free public TSAs listed by Sigstore (terms unread); a qualified eIDAS TSA (paid); none until approved | **Owner.** None until approved; then one free public TSA for tests, after reading its terms |
| RD3 | Public logs | Never; opt-in per registration; a project-run log | Never by default; opt-in only after RES.1 and an owner decision. A project-run log or witness is SK.5 |
| RD4 | Default identity | I0, I1, I2, I3 | I0, with I1 documented. I2 opt-in only, because it publishes identity for ever |
| RD5 | Default quorum | 1 or 2 | 2, and always report both bounds |
| RD6 | OpenTimestamps margin | 0, 7,200 s, the time of a later block | 7,200 s for now; needs a reviewer who knows Bitcoin consensus rules |
| RD7 | Possession digest | Mandatory or optional | Mandatory; it is cheap and it is the only possession evidence |
| RD8 | Time-stamp target | Signature digest; statement digest; artifact digest | Signature digest (§6.1) |
| RD9 | Many files | 64 subjects; a Merkle root over a file list | 64 now; a Merkle form later if creators need it |
| RD10 | Identifiers | Predicate URLs under `traceweave.org` | Proposed only; publish nothing (shared with C2PA D3) |
| RD11 | Renewal | Re-time-stamp the bundle; RFC 4998 evidence records | Re-time-stamping first; evidence records if a qualified archive is ever needed |

## 17. Needs the owner

- Using any external service at all, including requesting one test token from a TSA or an OpenTimestamps calendar (REG.3).
- Which TSAs, after reading their terms; any paid or qualified TSA.
- Whether anything is ever written to a public transparency log, and whether the project ever operates a log, witness or signer (SK.5).
- Identity choices: whether I2 (OIDC accounts) is offered at all.
- Publishing the predicate identifiers under `traceweave.org`.
- The ROADMAP wording of §15 (M4.5 in particular), new REG gates, and the new use case.
- Legal questions. Lane 13 quotes eIDAS and the US Federal Rules of Evidence only; nothing here is legal advice.

## 18. Fixtures and checker

See the [fixtures README](registration-fixtures/README.md). `check_registration.py` (standard library) verifies the fixtures' Ed25519 signatures with a public test-only key, recomputes digests, possession digests, the catalogue commitment and the expected verification result, and applies the rules above. It verifies no real time evidence. Failure codes: `authorship-claim`, `catalogue-does-not-open`, `catalogue-not-report-input`, `catalogue-unsalted`, `claimed-as-proved`, `duplicate-key`, `envelope-shape`, `evidence-shape`, `evidence-wrong-target`, `fixture-shape`, `forbidden-field`, `key-event-shape`, `log-time-claimed`, `nonce-invalid`, `notice-missing`, `pending-counted`, `placeholder-unlabelled`, `possession-mismatch`, `predicate-type`, `profile-mismatch`, `provenance-shape`, `quorum-miscount`, `report-digest`, `result-mismatch`, `signature-invalid`, `single-verdict`, `statement-digest`, `statement-shape`, `subject-mismatch`, `subject-name`, `time-in-statement`.

## 19. Verification of this draft

Run on 2026-11-23 on `roadmap-v2` (parent `0879905`), on this draft, lane 13 and the fixtures directory:

- `check_registration.py`: the Ed25519 and PAE self-tests pass. 11 positive fixtures give no code; each of the 27 negatives gives exactly its expected code; all 31 codes appear in this document; 27 codes are exercised by a negative.
- `build_fixtures.py` rerun: the rebuilt files are byte-identical to the committed ones (`git status` showed no change).
- `tools/validate.py`: PASS. `python -m unittest discover -s tests`: 9 tests, OK. `tools/validate.py --links-all`: PASS. `tools/check_hygiene.py`: PASS. `git diff --cached --check`: no whitespace errors.
- External URLs in this draft, lane 13 and the README: 28 requested, all answered. 25 returned 200 or 206 (one-byte range request) directly; the two EUR-Lex pages returned 202; RFC 5816 and RFC 9162 failed once on a timeout, then returned 301 to their `/info/` pages, which returned 200. The three predicate type and in-toto identifiers are names, not pages, and were not requested.
- Not done: no real time-stamp token, proof, log entry or cosignature was requested or verified; no implementation exists.
