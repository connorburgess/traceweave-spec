# Independent review of curated PDQ publication source

Reviewed 2026-11-26: exact **`d6c09e05829ccd95159ea9e19ff7f71f8c239f4e`**, base **`ec2a4ddcfd0d4894ce369e6687bed67f2e023f6f`**, on the clean isolated publication-source branch. This review assesses the **new curated representation**, its rewritten inspector/manifest/prose and divergence workflow. It does not inherit acceptance from the historical private package review. Only this new review record is added; all twenty author-changed paths remain as reviewed.

**Verdict: accept for evidence-only source integration and subsequent separately authorized sanitized preparation; no blocking finding.** The curated package truthfully preserves the bounded six-input result while omitting the raw upstream commit and explicitly relinquishing publicly recomputable commit-to-root binding. It does not establish interoperability, authorize replay/publication, or close IMGF.5. **IMGF.5 remains OPEN; M3 remains on HOLD.**

## Representation and scope independently checked

The sixteen-file curated directory contains the manifest plus fifteen listed files. The ten copied files are byte-identical to historical author revision `5e9eebdd2e365ed62911b25dc85c297f8b4ab5a1`: BSD licence, acquisition report, bridge, comparison, input declaration, original artifact identities, original provenance verification, frozen Python source identities, adapted runner and compact source-tree proof. Seven of those ten are JSON reports. No retained result JSON was edited to accommodate publication.

The new source adds eighteen paths and modifies only CONTRIBUTING and the work queue, for twenty author-changed paths overall. All **449 previously tracked JSON/JSONL paths** have the same Git blob IDs as the base. ROADMAP, root README, normative specifications/profiles/schemas, tools/hooks, test vectors, frozen draft-2 extraction/profile/protocol code and historical image experiment files are unchanged. No criterion, gate status or count is altered. The work queue preserves core **34/47 met, 13 open**, extensions **28/55 met, two negative-result, 25 open** and their existing holds; its PDQ row adds qualified evidence rather than a new assignment.

Raw upstream object bytes are omitted, not merely hidden at the latest tree:

- `upstream-commit.txt`, the original package manifest and its `.gitattributes` are absent from the curated package.
- The source range contains exactly one author commit; the raw file path has no history in `ec2a4dd..d6c09e0`.
- Raw blob **`a7abe43c1ce5e71a1bdb90384be29d5a2b6f1efc`** is absent both from the new range's reachable-object set and from the complete object set reachable from the curated source commit.
- Private tip **`7a0fd5ac64a50eb5c3ef6d6f955c21e4f11cc41c`**, the historical original package and its historical review are not ancestors. The approved base is an ancestor. The raw object may remain in shared private object storage; that is different from publication-source reachability, and no private object was deleted.
- Complete changed-file inspection and unchanged-rule scans found no encoded, relocated or alternative raw-object representation. The omitted object's public size/hash/name metadata is clearly identification of absent bytes, not an encoding of the object or replacement proof.

## Inspector and proof boundary

The [new inspector](../experiments/pdq-cpp-feasibility/inspect_evidence.py) was reviewed independently of its predecessor. It verifies the current [public manifest](../experiments/pdq-cpp-feasibility/public-package-sha256.json), not the omitted original package manifest. It requires the on-disk package inventory to equal the manifest plus the manifest itself, rejects extra directories/symlinks, unsafe manifest path names and the two named private-package files, and hashes each listed file. Thus a stale manifest, ordinary injection or file tampering fails; this is consistency relative to Git-pinned manifest bytes, **not a signature/authentication claim or protection against arbitrary coordinated rewriting of all evidence**.

It reconstructs six canonical Git tree objects, checks duplicate names, parent/child links and the seventeen declared subset leaves. Optional provisioned-source mode hashes the actual retained bytes; optional reference mode hashes the thirteen frozen Python exports. It explicitly treats the upstream pin/raw-object size/hash/root fields as consistency checks of a **historical private report**. Its result says commit-to-root binding is historically privately verified and **not recomputed from the public package**, with `pdqExecuted: false`.

That weaker boundary is correct: tree/subset consistency relative to root `dbd86e307c396ab13c3d261126732be72163295e` does **not** prove that the root belongs to upstream commit `9f627fb1d6d2a4a26c9b5ee1d6ca5e5ccc8e06a2`. The absent 1,135-byte raw body cannot be reconstructed from its digest. The [provenance page](../experiments/pdq-cpp-feasibility/provenance.md), README, validation record and queue consistently retain this limitation. The original 207-tree report is historical; it is not presented as the public inspector's six-tree computation. No signer authentication, immutable acquisition chronology or parent-chain validation is inferred.

The ten packaging tests passed, including manifest-refreshed tree/leaf/report-identity/distance/quality/summary mutations. These exercise structural/accounting rejection beyond an outer checksum failure, while ordinary injection and tampering tests cover the file boundary. They execute no PDQ. The manifest is not a general authenticity oracle; externally supplied source/reference paths are caller-provisioned local inputs, not acquisition instructions executed by inspection.

## Retained numerical evidence and historical reviews

The copied comparison preserves all exact output strings, input hashes, quality values and variant distances. Stored XOR/popcount accounting gives **32/48 exact hashes, 6/6 quality matches, 4/6 complete C++ input agreements**. Python port/vendor agree on all six cases but share arithmetic; they are not an additional independent implementation.

| Input | Quality Python/C++ | Exact hashes / 8 | Retained qualification |
| --- | --- | --- | --- |
| black | 0/0 | 8 | Quality zero does not inherently imply disagreement |
| constant127 | 0/0 | 0 | All eight mismatches remain: 138,145,138,138,138,145,138,138 bits |
| low-contrast | 11/11 | 0 | All eight mismatches remain: 48,46,82,68,68,46,48,82 bits |
| asymmetric | 100/100 | 8 | Bounded common-luma result |
| wide | 100/100 | 8 | Bounded common-luma result |
| tall | 100/100 | 8 | Bounded common-luma result |

No post-hoc quality exclusion, tolerance substitution, criterion change or E-gate negative-result designation appears. These six arrays bypass RGB/decode/trim/ISCC and are neither the thirty vendor images nor the full frozen synthetic extraction set. Numeric cause remains unlocalized; precision sensitivity is a hypothesis. No universal/cross-host or natural-image usefulness claim follows.

The [historical summary](pdq-cpp-curated-public-summary.md) explicitly identifies its author-prepared status, private historical revision/artifact identifiers and absence of a current independent review at preparation time. I verified its historical review SHA-256 against the historical review commit. It does not present that earlier acceptance as acceptance of this inspector, manifest or prose. The present record supplies the independent assessment of this exact source representation; pending language in author documents remains a dated preparation statement.

The bridge, BSD licence and adapted runner are unchanged copied bytes. The prior bridge findings and original independent numeric reproduction remain historical evidence. The adapted runner is **statically checked and unexecuted** in this review and in curated packaging. No build or numerical rerun was performed. Source/binary/input files and the raw commit are not bundled; the package does not claim a self-contained offline rebuild or new runtime proof. Original predeclaration chronology remains filesystem-supported, not immutable preregistration.

## Durable divergence workflow assessment

[Publication-source workflow](../../docs/publication-source-workflow.md), linked from CONTRIBUTING and the active queue, explicitly changes the source lineage for future preparation. It prohibits merging the named raw-bearing private tip, original package or original review into it, and explains why deletion at a later tip would not remove the historical introduction. Before replay it requires clean source/base checks, forbidden ancestry/path/blob checks and complete changed-file inspection for alternate representations. It requires seven JSON identities, current manifest/inspector checks, preserved criteria/holds and honest omission language.

Future preparation must use the accepted publication-source tip, not a default private branch. It preserves the established full-range replay base, fixed critical mapping pair, stable previously published mappings and current-public-tip ancestry. It requires fresh candidate refs, truthful source naming, explicit accounting for excluded private revisions, preliminary/final replay and map review, protected JSON identity, unchanged-rule scans, candidate validation and the existing destination-aware pre-push hook. It authorizes no rule/scanner/hook exceptions and no publication by itself.

This is a **durable procedural safeguard**, not a new automatic Git merge prohibition. The existing tool still requires an explicitly correct source and operators must perform the documented preflight. It is sufficient as a clearly stated workflow for later authorized preparation; it is not proof that a future candidate or push has already passed those checks. The current review performed no replay, map regeneration, history rewrite, hook edit, integration or push. Private `roadmap-v2` still resolves to **`7a0fd5ac64a50eb5c3ef6d6f955c21e4f11cc41c`**.

## Finding dispositions and checks

No blocking or correction-required finding was found in this exact representation. Material limitations are retained rather than dismissed:

| Item | Disposition |
| --- | --- |
| Public upstream commit binding | **Not reproducible from published package; explicitly disclosed.** Private historical verification is reported, not promoted to public proof. |
| Original versus current package review | **Separated correctly.** Historical review supplies scoped prior evidence; this record reviews the rewritten public package. |
| Adapted runner | **Unexecuted.** Static source/AST evidence only; no new numerical result. |
| Future raw-bearing merges/replays | **Explicitly prohibited by documented preflight.** Not an automatic hook claim; future candidate must independently pass the prescribed checks. |
| 32/48 mismatches and IMGF.5 | **Preserved.** Full required agreement remains unestablished; OPEN, not waived or relabelled. |
| Chronology, platform and causation | **Limits retained.** No immutable input preregistration, universal equivalence or localized numerical explanation. |

Bounded offline checks reproduced in this review:

- Stdlib inspector: six trees, seventeen declared leaves, 32/48 hashes, 6/6 quality; PDQ not executed. Optional provisioned source/reference verification also passed.
- All **10** new packaging tests and **29** existing repository unit tests passed under OS network denial.
- Repository validator, all-Markdown links and hygiene passed; full whitespace check passed with no raw-commit exception needed.
- README claim checker: **77 mapped, zero unmapped**; requirement checker: **157 MUST occurrences, zero unmapped**, using the existing implementation checkout only for source locators, not native execution.
- All three package Python scripts parsed without executing the adapted runner. Ten copied files/seven JSON compared byte-for-byte with the original private package. The seventeen source/licence bytes and thirteen Python export bytes matched their reports; no fetching or importing those sources.
- The unchanged private rules produced **zero hits** for the working tree and exact one-author-commit range, scanning blobs, paths, messages and headers with existing plain/ROT13/reversal/base64/hex rules. Rules/tool/hook bytes were not edited; private-rules SHA-256 was recorded in a separate local audit and checked unchanged. No detector result or rule contents are embedded here.
- Reachability/ancestry/path checks above passed. Existing protected files and all 449 prior JSON/JSONL blobs equal the base. No gate row, count, rule, hook, map or frozen file changed.

Reproducible check forms (paths refer to existing local provisioning, never acquisition):

```sh
python3 -B research/experiments/pdq-cpp-feasibility/inspect_evidence.py
python3 -B research/experiments/pdq-cpp-feasibility/inspect_evidence.py \
  --source "$RETAINED_SOURCE" --reference "$RETAINED_REFERENCE"
python3 -B -m unittest discover -s research/experiments/pdq-cpp-feasibility -p 'test_*.py'
"$REPOSITORY_PYTHON" -B -m unittest discover -s tests
"$REPOSITORY_PYTHON" -B tools/validate.py
"$REPOSITORY_PYTHON" -B tools/validate.py --links-all
"$REPOSITORY_PYTHON" -B tools/check_hygiene.py
python3 -B tools/public_history_scrub.py --rules "$UNCHANGED_PRIVATE_RULES" scan --tree
python3 -B tools/public_history_scrub.py --rules "$UNCHANGED_PRIVATE_RULES" \
  scan d6c09e05829ccd95159ea9e19ff7f71f8c239f4e --base ec2a4ddcfd0d4894ce369e6687bed67f2e023f6f
git diff ec2a4dd d6c09e0 --check
```

The review-only commit adds this record without altering author files. Final record links, whitespace, hygiene and unchanged-rule tree/range scans also pass. No candidate generation/publication approval is supplied. M3 remains held and IMGF.5 remains open.
