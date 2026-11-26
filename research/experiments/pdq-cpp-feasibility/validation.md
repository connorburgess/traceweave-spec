# Validation scope for the curated package

The public inspector verifies the exact manifest inventory and SHA-256 values, six complete Git trees and their 17 declared subset leaves, consistency of the reported private object identity, and the stored comparison accounting (six inputs, eight variants each, 32/48 hash matches, 6/6 quality matches, four complete C++ input matches). Its output explicitly reports that commit-to-root binding is historical private verification and that PDQ was not executed.

The accompanying mutation tests refresh the package manifest after structural/accounting mutations, so passing the outer checksum alone cannot satisfy those tests. Other tests reject file injection and ordinary file tampering. These checks are packaging checks; they do not authenticate the reports, execute the adapted runner or localize numeric differences.

Original independent reproduction and review concerned the original package and privately available artifacts. The [review summary](../../reviews/pdq-cpp-curated-public-summary.md) records that distinction. This curated package requires its own independent review. No new numeric experiment, build, acquisition, service or held M3 evaluation is authorized or performed by this packaging change. Core and extension gate counts, criteria and holds are unchanged.

## Source preparation checks, 2026-11-26

Prepared from exact source base `ec2a4ddcfd0d4894ce369e6687bed67f2e023f6f`. The public inspector, its 10 tests, the repository validator and 29 existing unit tests passed under OS network denial, as did README claim mapping (77 units), requirement mapping (157 MUSTs), all local Markdown links and hygiene. The unchanged private rules reported zero working-tree scan hits. Whitespace checks passed. Ten copied files, including all seven JSON reports, were verified byte-identical to historical author revision `5e9eebdd2e365ed62911b25dc85c297f8b4ab5a1`; all previously tracked JSON/JSONL and frozen files remain unchanged.

An independent mechanical row recount during preparation gives core **34/47 met, 13 open** and extensions **28/55 met, 2 negative-result, 25 open**. No gate criteria or status rows changed. The raw-bearing private revisions are not ancestors of this curated source. These are preparation checks, not independent acceptance of the new package, sanitized-history validation or publication authorization.
