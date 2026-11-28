# Focused independent PDQ-D1 acceptance — labelled portable adaptation

Original SHA-256 `c39bd5d39cd166c9434be9622031340d9713a6631b03ae9a1cfb15c27a95b6cf`, 3038 bytes. Original retained unchanged privately. Markdown attachment/local-locator links are made inert; remaining body is unchanged. Inline artifact names describe the original package, not an assertion that every named file is published here. See the [retention manifest](../retention-manifest.json) and [package scope](../README.md). Historical pending/adverse statements keep their original date/scope; only the focused D1 addendum supersedes its report-correction condition. This adaptation is not an independent review of its own retention package.

---

# Focused PDQ-D1 re-review

**PDQ-D1 resolved. Accept the revised report/package for the previously reviewed bounded six-input numeric finding. No remaining blocker.** This addendum supersedes only the report-correction condition in the prior review (original attachment/locator; see retention manifest); it preserves that review and all numerical/scope limitations.

Exact accepted identities:

| Artifact | SHA-256 |
| --- | --- |
| Revised report | `2816c35b4ce7ace508170bb6f55a515fe4df60cec7a20d0d3603f66e30ebac95` |
| Revised package SHA256SUMS | `5b2db7762a4e7949b9ebb70fb1d40397bfff25a85a8af968ba7ea31541976b8e` |
| Revised generator | `43c0f84721b88f23776949392a9ce1ed7f2d8f9990ec9cfccf7727b684fbd9e8` |
| Added resolution note | `9fa0b752a3aeeda824b060b4c33c3bdcdb3335be0f1c9d3da795e80637f28557` |
| Supplied resolution identity record | `b0065d78730cf07576fdd5a0ca069a48cebf7089b2a90fafd06e796222dd1257` |
| Preserved prior independent review | `1abe8a7a08cffd5dde65b4653455c7d7167f58b746f2cf0add511903377526eb` |

The exact report diff changes only its two flip rows; the generator diff changes the same two literal rows. `flipx` now uses **row i: +B on odd, −B on even**. `flipy` uses **column j: +B on odd, −B on even**. Neither transposes. These match retained C++ `dct16OriginalToFlipX`/`dct16OriginalToFlipY` and frozen Python `np.where(i & 1, b, -b)` / `np.where(j & 1, b, -b)`. No implementation or numeric mapping was changed to accommodate the report.

Compared against the prior exhaustive snapshot: **409 other existing files are byte-identical**. Only `report.md`, `write-report.py` and `SHA256SUMS` changed among the original 412 files. One documented new file, `pdq-d1-resolution.md`, was added. The revised package therefore contains **413 files**, with **412 unique manifest entries**, all verified and exactly covering everything except the manifest itself. All numerical arrays, 1,606-decision CSVs, input declarations, diagnostic JSON, binaries, source, tests and logs retain their original identities.

For generator consistency, copied the revised package into a fresh temporary directory and ran **only the document generator** there under the existing network-denial sandbox. Its generated report is byte-identical to the accepted revised report above. The temporary copy was removed. No compiler, core, numeric diagnosis or arithmetic probe was rerun; no author file was written. Focused check evidence (original attachment/locator; see retention manifest) retains the exact accounting and identities. The prior review and its original evidence manifest remain untouched.

Baseline remains **32/48 exact hashes and 6/6 exact qualities**, with both low-quality mismatches retained. Acceptance is limited to the same six integer common-luma inputs, one host/compiler and the already independently reproduced arithmetic diagnosis. It establishes no generalized parity, full frozen-set agreement, upstream commit authentication, threshold/usefulness claim or IMGF.5 closure. M3 remains held. No acquisition, repository/gate change, publication or sublane occurred.
