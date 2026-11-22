# Proposed UC-7: recognize a marked image

**Status: proposed, awaiting the owner's acceptance of this wording (roadmap gate IMG.0).** It follows the style of UC-6 and UC-8 in [use cases](../../docs/use-cases.md). It is a draft in `research/`. It changes nothing in `docs/`, and it is not counted in the capability index until the owner accepts it and the coordinator moves it. The weight download that IMG.0 also names was approved on 2026-11-23, subject to the licence check in [lane 12](../lanes/12-image-mark-licences.md), which cleared it.

| Case | Person and question | Inputs and workflow | Useful result | Important limit | Verification plan |
| --- | --- | --- | --- | --- | --- |
| UC-7 (proposed) — Recognize a marked image | A creator marks still images they publish and later asks whether a candidate image carries one of their marks | Keep a private key and a local catalogue; for each image, derive a payload from the key and a catalogue entry id, embed it with a pinned mark profile, refuse outputs below the quality floor, publish. Later, decode a local candidate's raw bits and test them against the expected payloads of the catalogue | A detection record: candidate digest, profile and model digests, statistic (agreement m of n) for the accepted entry or entries, threshold with its calibration basis, search scope, outcome or abstention reason | Removal (the authors' remover, deep crops, rotation, heavy recompression or regeneration) can erase the mark. A mark copied onto another image can be accepted, so a match is not proof that the candidate derives from the original. The payload is not signed. No result does not establish absence. Not ownership or permission | [UC-7 plan](#uc-7-verification-plan-proposed); gates IMG.0–IMG.5 |

**UC-7 (proposed) — Recognize a marked image.** A creator marks still images that they may modify, keeps the original, the marked artifact digest, the mark profile and a private catalogue, and publishes the marked image. Later, they check a candidate image they can read locally. The check never uploads the candidate.

- **What is embedded.** A payload of n transmitted bits: TrustMark-Q carries 61 data bits, BCH-coded into 100; PixelSeal carries 256. The payload is HMAC-SHA256(creator key, entry id), truncated. It is a keyed locator for a private catalogue entry. It is not an identity claim, a signature or a licence.
- **Key handling.** One secret random key per creator, stored outside any repository and never placed in a record. Records carry a key id and the payload-derivation rule id. Rotating keys multiplies the search scope (below).
- **Decision.** A decode by itself is not presence evidence ([lane 10](../lanes/10-evidence-review.md#after-the-report-audit): blind BCH success occurs on 5.9–15.3% of unmarked images in X1). The verifier counts agreement m between the decoded raw bits and each expected payload, and accepts an entry iff m ≥ k. k is the smallest value with P(Bin(n, ½) ≥ k) ≤ 10⁻⁶: 74 of 100 or 167 of 256. Over the key's randomness, that is the per-comparison false-accept bound, whatever the image. Searching N entries under N_K keys gives at most N × N_K × 10⁻⁶ per query. Outcomes: `match`, `ambiguous` (two or more entries accepted), `no-match`, or an abstention with a reason (`undecodable`, `unsupported-mode`, `too-small`).
- **Quality.** A marked output below the profile's PSNR floor (38 dB in the first protocol) is refused, not published.
- **Separate results.** Detection, record resolution, signature validity and trust stay separate. Mark evidence and fingerprint evidence are never multiplied.

Expected misses and false acceptances: deep crop, rotation, flip for some schemes, heavy recompression, model-based or author-supplied removal, and re-marking by another party. Expected false acceptance: a residual or mark transplanted from a marked image to an unrelated one. Synthetic-image results say nothing about photographs.

## UC-7 verification plan (proposed)

- **Checked:** marks embed and are recovered offline on CPU from pinned code and weights; the expected-payload test rejects unmarked images, wrong keys and wrong entries; survival under 12 edits and 5 removal attempts is counted; transplant and overwrite outcomes are counted; quality of the marked output is measured; records carry the fields the shared record needs.
- **By:** IMG.1 (pins and licences: [lane 12](../lanes/12-image-mark-licences.md), `weights.json`, `sources.json`, `requirements.txt`), IMG.2 and IMG.4 (the measured run of [protocol `e-img-m-1`](image-mark-protocol.md)), IMG.3 (that protocol frozen with its digest before running), IMG.5 (its §12 record mapping).
- **Pass:** each item is decided by an exit code or a count.
  - `fetch_weights.py --verify` and `fetch_sources.py --verify` exit 0 (6/6 and 84/84 files).
  - The unit tests exit 0.
  - `run_mark.py full` exits 0 twice under the network-deny sandbox, with the probe refused (W2).
  - `run_mark.py compare` exits 0 (W3).
  - `recordValidation.errors` has 0 entries (W4).
  - For TrustMark-Q and PixelSeal separately: clean marked images correctly matched ≥ 95/100 (P1); unmarked accepted 0 in 20,000 comparisons (P2); wrong key accepted 0 in 10,000 (P3); wrong entry accepted 0 in 9,900 (P4).
  - Every report-only count (edits, removal, transplant, overwrite, quality) appears with its denominator of 100.
- **Fail:** any of those commands exits non-zero; any record error; P1 below 95; any accept in P2–P4 (that scheme is recorded as negative-result); any count without a denominator. Transplant and removal successes are **not** failures of the plan. They are recorded limits of the use case.
- **Today:** pins and licences are recorded. The unit tests pass (20/20). Smoke dry runs on 3 smoke images per scheme run offline and are byte-identical across runs. They are not results. **Needs:** a non-author review of the frozen protocol, then the measured run; the owner's acceptance of this wording.
- **Unverifiable:** behaviour on natural photographs (synthetic images only; a real-image set needs the owner); a false-accept rate near 10⁻⁶ (analytic only; 0 of 200 unmarked bounds the per-source rate below about 1.5%); resistance to adaptive, learned or regeneration attacks not in the protocol; ownership, authorship or permission; any result across hosts.
