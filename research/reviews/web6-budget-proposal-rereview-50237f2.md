# Focused independent WEB.6 proposal rereview

2026-11-27. Final exact reviewed author tip: `50237f26360290102f60ff293c81d91aaef774ad`, tree `5d55bbfa7fe7789dda3305c2ac459310e0397f0e`. This addendum follows [review 82899da](web6-budget-proposal-review-a2f867d.md), which reviewed `a2f867d5204695b13c84b632d7a8b2d97cef1576`. The historical review remains unchanged. Scope is the author's two-file revision to the [proposal](../drafts/web6-budget-amendment-proposal.md) and [source-validation ledger](../drafts/web6-budget-source-validation.md), plus affected cross-references. Unaffected primary-source checks from the earlier review were not duplicated. No new external source claims or runtime evidence are introduced here.

**Verdict: R1 and R2 closed as proposal-design findings; eligible as a PROPOSED owner-decision document. No remaining blocker within this focused rereview.** This does not adopt an amendment or budgets, freeze a protocol, approve an implementation, establish numerical feasibility, or close WEB.6. Gate status/counts and M3 hold are unchanged.

## R1 — registration commit boundaries: closed for this proposal

Section 4b now explicitly separates R from P7 disposable core termination. It covers before key acquisition, key generation/write, pre-sign, in-flight signing, completed signature/pre-card-save including verification, and entered/completed card callback. Accepted cancellation stops future steps; it cannot retroactively prevent a synchronous commit or undo a saved key/card or completed signature. Queued clicks are ordered by actual host acceptance and commit guards, not backdated to imply prevention. UI state alone is not persistence acknowledgement.

I re-read the existing pinned Shelf source, without executing it: exact `86036c43394e94c1431ca335195a86e7754da6df` (also that checkout's current HEAD). `src/components/RegisterTab.tsx:201–245` orders key acquisition, signed bundle creation, verification, and card callback; `src/components/ShelfApp.tsx:84–87,122–125` delegates key acquisition and saves the card; `src/lib/storage.ts:32–34,49–51,116–126` writes localStorage and persists a missing key before returning it; `src/lib/crypto.ts:130–149` imports a signing key then awaits `crypto.subtle.sign`, with no application abort path. The proposed guard/receipt design is a future addition, correctly not attributed to that code. No current cancellation support, observed race, deployed identity or exactly-once transaction is certified.

The concrete old failure scenario is now accounted for: cancellation during verification after a key save and completed signature preserves both known effects and the signed-result receipt, skips an unentered card-save callback, and may terminate only disposable verification. If the save callback already ran, the result is completed/saved or a truthful failed/unknown outcome; discarding a worker message cannot report no effects. The existing code updates React state before the storage write; the proposal explicitly prevents interpreting that update as successful persistence.

Session-local receipts retain operation/digest/key/sign/verification/card/cancel status. Recovery is read-only; it cannot delete records, retry signing, generate another key, re-enter saving, change trust/policy, add persistent journals or transmit externally. A later deliberate action remains under existing consent and a new operation ID; this text grants no new consent. Transient bundle retention is distinguished from automatic export/save. Read-back establishes only session-visible content, and reload receipt loss, concurrent changes, storage uncertainty and late completion stay explicit.

R acknowledgement/status targets are distinct from cessation: ≤200 ms acknowledgement, within 1,000 ms reconciled status or truthful pending, with separate baseline-dependent 30/60-second settlement targets. Exceeding settlement is a failed target with pending/unknown state, not a passed cancellation. An in-flight sign/store is not promised to stop within one second. Later R manifests must enumerate boundary/error/reused-key/new-key/reload cases and per-device counts; R's 2/2 keyboard count and core probe counts cannot substitute. This is adequate design disposition, while implementation guards, instrumentation, exact R counts and feasibility remain prerequisites to later testing.

## R2 — cancellation allocation and validity: closed

P7 and §4a now unambiguously select ten active probes in each of three real processing phases per core subpath/profile-config tuple/required physical cell. Independent arithmetic: `10 × 3 × 4 × 2 = 240` minimum, 120 per physical device, 30 per subpath/tuple/device. For nonuniform tuple counts the physical total is `60 × Σ p_s`; a uniform p gives `240 × p`. D3's separate diagnostic minimum is 120 (`30 × Σ p_s`), and D/R do not enter the core denominator. More real phases require an explicit formula expansion.

Early read/decode, mid engine work and late actual copy/serialization/finalization are named work phases, not elapsed-time percentages. Completed work merely awaiting download is invalid as an active probe. Workload/trigger/phase evidence and a shared or calibrated timeline must be fixed before collection. Missing or unobservable phases retain unavailable buckets; artificial idle barriers cannot provide the only activity evidence. These requirements may be difficult on fast bounded inputs, but the draft now honestly requires feasibility resolution or reviewed protocol change before a conformance run, with no claim that it has happened.

Each bucket must independently pass 10/10. All attempts, invalid reasons and planned/valid-measured/passed counts remain visible. Predeclared replacement of an invalid attempt cannot erase a valid deadline failure; completed/inactive attempts cannot count as successes. P4 observations may be cross-referenced only when satisfying P7's additional phase conditions, without double-counting. P2/P3 now also state their five-run allocations per required physical cell. No pooled device result or small lab sample is represented as field reliability.

## Cross-references, checks and preserved limits

Read affected §2 R scope, P7, the core-worker explanation, §§4a/4b, §5 same-matrix R scope, §6 baseline dependencies/owner choices and per-cell P2/P3 allocation, §7 author dispositions, ledger L9 and its registration-boundary addendum. They consistently separate core disposal from committed R effects and distinguish proposed engineering requirements from existing source behavior. The general research-disposition shorthand for the one-second cancellation deadline is bounded by those explicit core/R sections. The author requests re-review rather than claiming independent resolution itself.

The retained observer/fallback restrictions remain: unavailable metrics stay unmeasured; heartbeat/rAF/shell-ready/buffer ledgers cannot substitute for paint/LCP/interaction/whole-context-memory evidence. The original three keyboard/input-boundary sentences remain verbatim; timing replacement remains proposed and prospective, not historical compliance. No telemetry, new storage/consent, service worker, hosting/header authority, broader device support, runtime testing or acquisition is inferred.

Exact author-file SHA-256:

| File under research/drafts | SHA-256 |
| --- | --- |
| web6-budget-amendment-proposal.md | `2ae32eb4c47ec5d38600189d6575a1013eb9e254b094e811472b7221a3c870a9` |
| web6-budget-source-validation.md | `07d5f19528ed78e8e47aa536d39d65e0036751550fe2725889c98e2fdd12b9c8` |

Bounded offline checks performed:

```sh
git rev-parse HEAD '50237f2^{tree}'
git diff a2f867d 50237f2 -- research/drafts
git diff --name-only 82899da 50237f2
git diff --quiet 82899da 50237f2 -- research/reviews ROADMAP.md spec profiles schemas tools
git diff --check 82899da 50237f2
shasum -a 256 research/drafts/web6-budget-amendment-proposal.md research/drafts/web6-budget-source-validation.md
python tools/validate.py --links-all
python3 -I tools/check_hygiene.py --messages 82899da..HEAD
```

The link command used the existing local Python environment; no dependencies were acquired. All listed checks pass, including links/hygiene with this addendum included. Additional standard-library assertions verified the allocation formulas, exact retained criterion, author-file byte identity to the reviewed commit, and unchanged historical review. The author revision changes only the two draft files; this review adds only this record. Source inspection is reproducible with `git -C <existing-shelf-checkout> show 86036c43394e94c1431ca335195a86e7754da6df:<path>` for the paths above. No builds, browser runs, numerical experiments, services, gate edits, acquisition, push or subagents were used.

Remaining owner decisions are the prospective timing amendment; candidate caps, numerical targets and physical device/AT envelope; core worker design and separate D/R release scope including commit-aware recovery; and offline-reload/privacy scope plus defensible memory instrumentation. Baselines, exact future manifests, instrumentation availability, implementation review and runtime authorization remain separate. This review permits no adoption or gate closure; M3 remains held.
