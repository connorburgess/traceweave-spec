# Extraction vector metadata map (M1.2)

Successor to [promotion-map.md](promotion-map.md) for `test-vectors/extraction/`, written 2026-11-23 on `roadmap-v2`. "Before" is each file at `437d619`, the last commit before this change. "After" is the file at the end of this series: the M1.2 metadata commit, then the M1.1/M1.5 commit, which added `requirement-map.json` and README text and changed no vector file.

## What changed, and what did not

**Only metadata was added, plus new vectors.**
- **Header fields:** `metadataRules`, `derivationRule`.
- **Per-vector fields:** `derivation`, `vectorClasses`, `pairedRejection`, `pairedPositive`, and on one vector `derivationNote`.
- **New vectors:** 60 rejection vectors, each the paired rejection of one positive vector.

**What did not change.** No existing vector's input, expected tokens, spans, k-grams, hashes, window selections, fingerprints, error code or offset changed, and no configuration entry's bytes or expected result changed. The configuration files and the Unicode table are byte-identical. This change modifies no file outside `test-vectors/extraction/` other than this note and one pointer line in the promotion map. In particular it modifies nothing under `test-vectors/matching/`, and `test-vectors/matching/check_matching.py` still passes.

**Proof:**

```
python3 -I test-vectors/extraction/harness/compare_outputs.py 437d619
```

The script compares every expected output at `437d619` with the working tree, and allows only the fields listed. It passed with 123 vectors and 31 configuration entries compared, 60 vectors added, and 6 files byte-identical.

**For the implementation repository.** A vector JSON digest change in the table below is a metadata change. Precedence checks that compare digests should take these new digests, because every previously vendored expected output is unchanged. Implementations should also reproduce the 60 new rejection vectors; M1.4 and M1.6 re-run on them.

## Revision after the non-author review (2026-11-23)

The core-gates review (`research/reviews/core-gates-m1-m2-review.md`) found two new rejection vectors with wrong expected results. Both were hand errors that missed the reserved-prefix rule of contract §5.3 step 3, and both were corrected by hand:

| Vector | Was | Now |
| --- | --- | --- |
| `rust-s1-string-digit-expr-rej` | `unterminated-literal`@8 | `reserved-token`@7 |
| `rust-q11-shebang-first-line-only-rej` | `unterminated-literal`@10 | `reserved-token`@8 |

**These are the only vector results that changed.** Each of the two vectors also gained a `derivationNote` and a new description.

The `derivationRule` header of every vector file now states the ROADMAP.md definition of hand-derived verbatim. That text is metadata only.

`harness/compare_outputs.py 488086f` lists exactly these differences: the two vectors' results and descriptions, the six `derivationRule` headers, and the requirement map. `harness/compare_outputs.py 437d619` still passes, because both vectors were added after `437d619`. Implementations re-vendoring from `488086f` must take the new `rust.json`, and should confirm their results for the two vectors. Both implementations at `af3af2b` already produce the corrected results.

## Wording revision (review section 11)

**What changed:**
- **`derivationRule`.** In the five vector files it is now the ROADMAP definition followed by how it applies to them. The arithmetic (spans, normalized values, k-gram hashes, windows and fingerprints) is computed by the specification's own builder, not by an implementation under test, and is independently confirmed. Spans are located by search, except in vectors marked `spanStarts: hand`.
- **`spanStarts: hand`.** One vector gained this metadata field: `rust-q11-shebang-first-line-only`.

**What did not change.** No vector output changed. `config-negative.json` is byte-identical. `harness/compare_outputs.py 34eea25` reports only the five `derivationRule` headers.

## Offset-derivation revision (confirmation pass)

**No vector file changed.** `harness/compare_outputs.py a625c97` reports 12 of 13 JSON files byte-identical; only `requirement-map.json` changed. So no expected output changed, and there is nothing to re-vendor except the checker and cross-check scripts, if they are vendored. Both now derive the error offset per code: every ±1 shift is rejected, 151 of 151. The requirement map now says "Go only" for the EX-22 and EX-23 timing tests.

## Files

"Before" is `437d619`; "previous" is `a625c97`; "after" is the current tree.

| File | SHA-256 before (`437d619`) | SHA-256 previous (`a625c97`) | SHA-256 after | Result in this revision |
| --- | --- | --- | --- | --- |
| `test-vectors/extraction/README.md` | `00b8831c5fc24f16c6aaf3a379b1f9db8753a7724128179eaa0a80f7d8369cd3` | `62cd477e9ea7008111b351a1f9e7ebfacbe9119d5e384e6a48bbbf2d0007298a` | `464c55008141d3c268eeaf62606f1cd5e679f7cbc46eaf0e0beecb5b0e99e37a` | changed (checker, cross-check, map or documentation) |
| `test-vectors/extraction/check_vectors.py` | `9c3174976745a906f5214d52bd38cb5573d2465fb5ca02e06ceba1cb2d976be5` | `eda26f3a413642c41c2162101e50848b6d20da34c2cfc889dc365d22082760c9` | `370c8e95e5f78f2f8c738614bf5c024bc7b632c11e823f9a640bcf28523ca1bc` | changed (checker, cross-check, map or documentation) |
| `test-vectors/extraction/config-exclusion-test.json` | `65ae9f23f38b060edbb4aa294a68f289f4a286af3dd8b5e23b8b8f97784d2464` | `65ae9f23f38b060edbb4aa294a68f289f4a286af3dd8b5e23b8b8f97784d2464` | `65ae9f23f38b060edbb4aa294a68f289f4a286af3dd8b5e23b8b8f97784d2464` | unchanged in this revision |
| `test-vectors/extraction/config-go-limit16.json` | `aa86722255afbf50dc4c4772a718ad00f842192f442266203164c60d6dbdeea8` | `aa86722255afbf50dc4c4772a718ad00f842192f442266203164c60d6dbdeea8` | `aa86722255afbf50dc4c4772a718ad00f842192f442266203164c60d6dbdeea8` | unchanged in this revision |
| `test-vectors/extraction/config-go.json` | `dfbc5fe3517e9da65189cf2ef32c4655b5ec662441f2e71f508543a0a5c8f7b2` | `dfbc5fe3517e9da65189cf2ef32c4655b5ec662441f2e71f508543a0a5c8f7b2` | `dfbc5fe3517e9da65189cf2ef32c4655b5ec662441f2e71f508543a0a5c8f7b2` | unchanged in this revision |
| `test-vectors/extraction/config-negative.json` | `413661ca3bf4d437099bd7828adc8582bd79ac8e467dc5c917dbc1c36a470d6c` | `e4212a74136d79ef65f617f08e3d19bf51997c19030f9cb29619553e2ec855dd` | `e4212a74136d79ef65f617f08e3d19bf51997c19030f9cb29619553e2ec855dd` | unchanged in this revision |
| `test-vectors/extraction/config-rust-limit16.json` | `71d5ed27bea011f65a939e9c885170c6db138c5ae41084f8d214c15357c88716` | `71d5ed27bea011f65a939e9c885170c6db138c5ae41084f8d214c15357c88716` | `71d5ed27bea011f65a939e9c885170c6db138c5ae41084f8d214c15357c88716` | unchanged in this revision |
| `test-vectors/extraction/config-rust.json` | `64b34335e4a61383ada1403a2df97c2e45dba987bbf0c8ec21385e04104d1277` | `64b34335e4a61383ada1403a2df97c2e45dba987bbf0c8ec21385e04104d1277` | `64b34335e4a61383ada1403a2df97c2e45dba987bbf0c8ec21385e04104d1277` | unchanged in this revision |
| `test-vectors/extraction/exclusion-rule.json` | `bc65be980d5590eccf9d17ddaa4cc37c9b9ba4c955407a2edd0ec49ff5234f31` | `8d5cb7943e77f6c8db75c42b4e20a3c60f379418d0b5949f2b37927eb08f2585` | `8d5cb7943e77f6c8db75c42b4e20a3c60f379418d0b5949f2b37927eb08f2585` | unchanged in this revision |
| `test-vectors/extraction/go.json` | `f81fede1bfc540d11d1f24fbaf661d4eaf19682c720d6bd796eaabc5caa9294b` | `5eb7c2e24553196ca7725712d6b7df5d8e4125e71d284124f825da59ace03d55` | `5eb7c2e24553196ca7725712d6b7df5d8e4125e71d284124f825da59ace03d55` | unchanged in this revision |
| `test-vectors/extraction/harness/build_vectors.py` | `7c7ec53d0ff7397c1da9ad9cea8d68bf24491d124982750fd5d297d48b6a6e99` | `e459288163ceaa575decffb9c6b3ae95ec9560264ce1eed979a9720f365e8225` | `e459288163ceaa575decffb9c6b3ae95ec9560264ce1eed979a9720f365e8225` | unchanged in this revision |
| `test-vectors/extraction/harness/compare_outputs.py` | — | `1445f52cf4fd8a80dc0687a7ae0b584fde5b1d08a11e758ac467721436fd4c75` | `1445f52cf4fd8a80dc0687a7ae0b584fde5b1d08a11e758ac467721436fd4c75` | unchanged in this revision |
| `test-vectors/extraction/harness/crosscheck.py` | `31acb142346f8d0a04b6699007fd32b266594de7266158af9046d7a9f1bce0b0` | `7ac22da687a8cd75776e2d8a8830970bfbb7310324cb26cb5df3ef1d77e436fa` | `ffad9808edd51a316d87c2137d23a484769d6884113d10b0741df46415b9b65e` | changed (checker, cross-check, map or documentation) |
| `test-vectors/extraction/harness/gen_unicode_tables.py` | `4ca955fc1c2f770abbada54a7df55dbca78ae4eb59bbd890f82fcde99b729757` | `4ca955fc1c2f770abbada54a7df55dbca78ae4eb59bbd890f82fcde99b729757` | `4ca955fc1c2f770abbada54a7df55dbca78ae4eb59bbd890f82fcde99b729757` | unchanged in this revision |
| `test-vectors/extraction/harness/go/go.mod` | `df45563c21ad076eebd24f730e6c753392c4f110b2572c397f8d5dcd1b5f4d0c` | `df45563c21ad076eebd24f730e6c753392c4f110b2572c397f8d5dcd1b5f4d0c` | `df45563c21ad076eebd24f730e6c753392c4f110b2572c397f8d5dcd1b5f4d0c` | unchanged in this revision |
| `test-vectors/extraction/harness/go/main.go` | `6b521d6fcc64753cc342e62e6a74697c34234e8c1312df55cfc39546bf9ca940` | `6b521d6fcc64753cc342e62e6a74697c34234e8c1312df55cfc39546bf9ca940` | `6b521d6fcc64753cc342e62e6a74697c34234e8c1312df55cfc39546bf9ca940` | unchanged in this revision |
| `test-vectors/extraction/harness/rust/Cargo.lock` | `02e4a1012b12a9e1c3d0d746850c1521f09a51df24719c9a52f917a9a9d7b201` | `02e4a1012b12a9e1c3d0d746850c1521f09a51df24719c9a52f917a9a9d7b201` | `02e4a1012b12a9e1c3d0d746850c1521f09a51df24719c9a52f917a9a9d7b201` | unchanged in this revision |
| `test-vectors/extraction/harness/rust/Cargo.toml` | `0092528d95419485b4923336043c8fa6503d10d7da5f8aedc9ceb83d47393e50` | `0092528d95419485b4923336043c8fa6503d10d7da5f8aedc9ceb83d47393e50` | `0092528d95419485b4923336043c8fa6503d10d7da5f8aedc9ceb83d47393e50` | unchanged in this revision |
| `test-vectors/extraction/harness/rust/src/main.rs` | `eb75e7341eba56f570798f4770adbf6b1bcce384017dcf0d251f4bc10ac974e6` | `eb75e7341eba56f570798f4770adbf6b1bcce384017dcf0d251f4bc10ac974e6` | `eb75e7341eba56f570798f4770adbf6b1bcce384017dcf0d251f4bc10ac974e6` | unchanged in this revision |
| `test-vectors/extraction/limits-go.json` | `0d5d243ecb4605af934ef544027f0c6a7e88694be1a118fb32191874bfc95b94` | `c70c60a1d79cc74d8bb3ec1df19b1da9e44f95c6c1d7f171581a7a9419636de0` | `c70c60a1d79cc74d8bb3ec1df19b1da9e44f95c6c1d7f171581a7a9419636de0` | unchanged in this revision |
| `test-vectors/extraction/limits-rust.json` | `61ad316e717aed92d077759255fde118cc7e272d476d754d4d7224f21e249c6b` | `b1f43876398fe11455ea9f40f5e0e55c5521d289389c3e3f750b3711bdc6274c` | `b1f43876398fe11455ea9f40f5e0e55c5521d289389c3e3f750b3711bdc6274c` | unchanged in this revision |
| `test-vectors/extraction/requirement-map.json` | — | `11d9c6737c2782b379a88a02a7942837321bddbe38f8f9bbae8a58e231d2e761` | `8ab82342deb619e13e59cfe649181d57098d39fd6439354cfe529fd9b02c61d1` | changed (checker, cross-check, map or documentation) |
| `test-vectors/extraction/rust.json` | `21f3360c9e7c2394033e26548f35e8dddfdb723a35279c984c09967f96cc9590` | `7d53e9e6dde548d86b9bcd84175c7f59e6db03539f57bebefe1ff28578e32c72` | `7d53e9e6dde548d86b9bcd84175c7f59e6db03539f57bebefe1ff28578e32c72` | unchanged in this revision |
| `test-vectors/extraction/unicode-17.0.0-tables.json` | `9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f` | `9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f` | `9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f` | unchanged in this revision |
