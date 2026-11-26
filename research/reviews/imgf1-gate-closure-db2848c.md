# Scoped IMGF.1 research specification closure

Recorded 2026-11-26 on the isolated image branch, at pre-closure HEAD **`5d0a8630d4a5cd55b1e7501766ab902c66d90c8f`**. The coordinator authorized recording this closure after independent review. The exact reviewed proposal is **`db2848c1e8ec7c8465c066f5bff26863a803d440`**; the original arithmetic review is committed as **`b3a3a2c99b52f7313a3e6b6a4ae10e5e96846755`**, and the follow-up review as **`5d0a8630d4a5cd55b1e7501766ab902c66d90c8f`**.

**IMGF.1 is met as a research specification completeness gate.** Its unchanged criterion requires an image extraction profile answering the enumerated twelve contract items with zero TBDs. It does not require normative promotion, a full image study, universal equivalence to a compiled library, natural-image performance, or closure of IMGF.5. Acceptance here adopts the reviewed draft-3 arithmetic as the research contract for this criterion; the document remains under `research/drafts/`.

## Committed basis

- The [draft-3 contract](../drafts/extraction-profile-image-draft3.md) defines integer grey conversion, full-box 32×32 resize, sample centres and support bounds, clipped-edge renormalization, binary64 elementary-operation rounding/order, signed 22-bit coefficient quantization, exact integer accumulation, floor/saturation, intermediate bytes, dimension-dependent pass order, skipped axes, identity and post-trim upscaling. Other extraction clauses are inherited from draft-2 at `24bb4b8483dc86966cb7c8277130bb816b0c6b3f`.
- The independent [arithmetic review and twelve-item recount](image-normalization-draft3-review.md#independent-imgf1-recount) locates all **12/12** explicitly enumerated ROADMAP answers, with no missing item or remaining grey/resize choice. Lane 10's additional vendor-vector phrase is separately located in draft-2 §7 and IMGF.2; it is not dropped or miscounted as a thirteenth enumerated item.
- The [follow-up review](image-normalization-draft3-review.md#follow-up-review-exact-grey-half-tie-fixture) confirms **15/15 finite single-host synthetic post-trim cases** against committed expectations, the ordinary implementation, software-binary64 rational oracle and the already provisioned pinned Pillow target. Both resize mutations retain five witnesses each. Exact RGB `(1,53,185)` gives `3440640/65536 = 52.5`, so half-up is 53; an independent exact-rational ties-to-even mutation yields 52 and is rejected on **1,024/1,024 first/final bytes**. All four checker self-tests passed, including unchanged in-memory fixture regeneration.
- Independence was inspected rather than inferred from agreement: the two author programs share the contract and author, but use separate binary64 arithmetic mechanisms and axis traversal. The pinned compiled target is a comparison, not the expected-output generator. Separate review anchors checked the grey half-tie and **224/224** coefficient rows via an expanded rational polynomial at bounded dyadic sizes. These are not a third complete implementation or evidence for IMGF.5.

The earlier nonblocking half-tie fixture gap is resolved at the exact reviewed follow-up commit. No blocking finding remains in the reviewed specification scope.

## Preservation and limits

The upstream C-source limitation is retained: no fresh independent reread/rehash of `Resample.c` or `Convert.c`, tag resolution or compiler-flag verification was possible from the retained local bytes. The recorded source-pin metadata agrees with the earlier proposal; the wheel wrapper hash and loaded wrapper/compiled-target bytes were checked locally. No upstream acquisition was performed. The explicit equations define the new research contract, so this provenance limit is not an unresolved arithmetic choice.

Draft-3 extraction configuration stays **`38b2dc7c534cc93e321160a9bba1f885e0106f8212760559d0c744f4ddb8654d`**. Draft-2 extraction stays **`c740e92de69a47904fa81bb3614c086194717be856fa6a44d89ad6fdba3bb927`**; matching stays **`fe3fa0395d3701fa5b1b55839063998eba528851d4f9e3dcaca62d3a0f6c97ac`**. The draft-2 profile, experiment protocol, whole `image-fingerprint/` tree and historical `e-img-f-2` results remain unchanged. They retain their old identities and are not relabelled draft-3. Finite normalization agreement does not establish historical universal output preservation.

The new suite does not validate decode, trim correctness/reachability, ISCC hash core, variants, matching, inherited PDQ, SDK parity, all dimensions, cross-host/compiler agreement, or natural-image usefulness. These boundaries remain explicit. There is no normative promotion or universal equivalence claim. IMGF.2–IMGF.4 retain their historical scope; IMGF.5 and IMGF.6 remain open. The 48-repository M3 evaluation remains held. No M3 work, other gate change, acquisition, full experiment, push, service or sublane is included.

## Branch-local count reconciliation

Independently parsed all **55** individual later-profile/EXT/RC rows, classifying only explicit `Status: met` or `Status: negative-result` as closed; prose such as “complete for review” stays open. Before this change, the parsed met-ID set exactly matches the progress table's 21 IDs; the negative-result set is `{TXT.4, TXT.8}`.

| Later-profile/EXT/RC status | Before | After |
| --- | ---: | ---: |
| Met | 21 | **22** |
| Negative-result | 2 | **2** |
| Open | 32 | **31** |
| Total | 55 | **55** |

The sole added met ID is **IMGF.1**. Its criterion and all other individual gate rows are unchanged. The ROADMAP progress paragraph, extension count and IMGF.1 status/evidence are updated together. The core M0–M5 summary remains byte-identical to this branch's existing **33/47 met, 14 open** baseline; no newer branch's M5 closure/count state is imported. Current integration counts must be reconciled by the coordinator when merging this branch. Historical closure/review count snapshots are preserved.

## Validation

For this status/evidence-only change, the relevant checks are local Markdown links, tree hygiene, staged whitespace, a scoped Git comparison and an independent row/status recount. The recount compares ID sets, not only totals: 55 total, 22 met, two negative-result, 31 open; the added met set is exactly `{IMGF.1}` and every other gate row and the core summary are unchanged from `5d0a863`.

No executable, fixture, configuration or contract change is included. The bounded pinned comparison and four self-tests were reproduced in the immediately preceding committed follow-up review; this closure relies on that committed evidence and performs no new image computation.
