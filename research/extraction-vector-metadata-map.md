# Extraction vector metadata map (M1.2)

Successor to [promotion-map.md](promotion-map.md) for `test-vectors/extraction/`, written 2026-11-23 on `roadmap-v2`. "Before" is each file at `437d619`, the last commit before this change. "After" is the file in the tree that adds the M1.2 metadata.

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

## Files

| File | SHA-256 before (`437d619`) | SHA-256 after | Result |
| --- | --- | --- | --- |
| `test-vectors/extraction/README.md` | `00b8831c5fc24f16c6aaf3a379b1f9db8753a7724128179eaa0a80f7d8369cd3` | `a9a28dad954c05a694e09fc72aaab21b4994ecfb3347ef2742935de85cc769f9` | changed (tooling or documentation) |
| `test-vectors/extraction/check_vectors.py` | `9c3174976745a906f5214d52bd38cb5573d2465fb5ca02e06ceba1cb2d976be5` | `fb16cb25c5d8bc33fe8a29001262ed51606d6b547b89a380b598210d9718d15f` | changed (tooling or documentation) |
| `test-vectors/extraction/config-exclusion-test.json` | `65ae9f23f38b060edbb4aa294a68f289f4a286af3dd8b5e23b8b8f97784d2464` | `65ae9f23f38b060edbb4aa294a68f289f4a286af3dd8b5e23b8b8f97784d2464` | identical |
| `test-vectors/extraction/config-go-limit16.json` | `aa86722255afbf50dc4c4772a718ad00f842192f442266203164c60d6dbdeea8` | `aa86722255afbf50dc4c4772a718ad00f842192f442266203164c60d6dbdeea8` | identical |
| `test-vectors/extraction/config-go.json` | `dfbc5fe3517e9da65189cf2ef32c4655b5ec662441f2e71f508543a0a5c8f7b2` | `dfbc5fe3517e9da65189cf2ef32c4655b5ec662441f2e71f508543a0a5c8f7b2` | identical |
| `test-vectors/extraction/config-negative.json` | `413661ca3bf4d437099bd7828adc8582bd79ac8e467dc5c917dbc1c36a470d6c` | `2919909e3a3899db87bfb6ea8c2737310e0e21e40f141f7b3732abd63ad874ac` | metadata added (vector outputs unchanged; see compare_outputs.py) |
| `test-vectors/extraction/config-rust-limit16.json` | `71d5ed27bea011f65a939e9c885170c6db138c5ae41084f8d214c15357c88716` | `71d5ed27bea011f65a939e9c885170c6db138c5ae41084f8d214c15357c88716` | identical |
| `test-vectors/extraction/config-rust.json` | `64b34335e4a61383ada1403a2df97c2e45dba987bbf0c8ec21385e04104d1277` | `64b34335e4a61383ada1403a2df97c2e45dba987bbf0c8ec21385e04104d1277` | identical |
| `test-vectors/extraction/exclusion-rule.json` | `bc65be980d5590eccf9d17ddaa4cc37c9b9ba4c955407a2edd0ec49ff5234f31` | `a5777bc12af49974ff0d3d8de889856f73ff82191d3df31f3127537e2a831ddb` | metadata added (vector outputs unchanged; see compare_outputs.py) |
| `test-vectors/extraction/go.json` | `f81fede1bfc540d11d1f24fbaf661d4eaf19682c720d6bd796eaabc5caa9294b` | `984e0fa75d7db002b0fd6f66bd61c7818f0523bf082a2c661769a2f417b66c8c` | metadata added (vector outputs unchanged; see compare_outputs.py) |
| `test-vectors/extraction/harness/build_vectors.py` | `7c7ec53d0ff7397c1da9ad9cea8d68bf24491d124982750fd5d297d48b6a6e99` | `10fe49f0ea4537011988e0427ff7bf9381d2d67259bb8fae1ccd233ce448e5c3` | changed (tooling or documentation) |
| `test-vectors/extraction/harness/compare_outputs.py` | — | `a80c052eb560d937b51195ffc143a441c1618821e420529982da7505b783a51b` | new file |
| `test-vectors/extraction/harness/crosscheck.py` | `31acb142346f8d0a04b6699007fd32b266594de7266158af9046d7a9f1bce0b0` | `6df0798f6bdaa30ff8b174d47e3134b3e846697e44694fad21405da8d9522f2a` | changed (tooling or documentation) |
| `test-vectors/extraction/harness/gen_unicode_tables.py` | `4ca955fc1c2f770abbada54a7df55dbca78ae4eb59bbd890f82fcde99b729757` | `4ca955fc1c2f770abbada54a7df55dbca78ae4eb59bbd890f82fcde99b729757` | identical |
| `test-vectors/extraction/harness/go/go.mod` | `df45563c21ad076eebd24f730e6c753392c4f110b2572c397f8d5dcd1b5f4d0c` | `df45563c21ad076eebd24f730e6c753392c4f110b2572c397f8d5dcd1b5f4d0c` | identical |
| `test-vectors/extraction/harness/go/main.go` | `6b521d6fcc64753cc342e62e6a74697c34234e8c1312df55cfc39546bf9ca940` | `6b521d6fcc64753cc342e62e6a74697c34234e8c1312df55cfc39546bf9ca940` | identical |
| `test-vectors/extraction/harness/rust/Cargo.lock` | `02e4a1012b12a9e1c3d0d746850c1521f09a51df24719c9a52f917a9a9d7b201` | `02e4a1012b12a9e1c3d0d746850c1521f09a51df24719c9a52f917a9a9d7b201` | identical |
| `test-vectors/extraction/harness/rust/Cargo.toml` | `0092528d95419485b4923336043c8fa6503d10d7da5f8aedc9ceb83d47393e50` | `0092528d95419485b4923336043c8fa6503d10d7da5f8aedc9ceb83d47393e50` | identical |
| `test-vectors/extraction/harness/rust/src/main.rs` | `eb75e7341eba56f570798f4770adbf6b1bcce384017dcf0d251f4bc10ac974e6` | `eb75e7341eba56f570798f4770adbf6b1bcce384017dcf0d251f4bc10ac974e6` | identical |
| `test-vectors/extraction/limits-go.json` | `0d5d243ecb4605af934ef544027f0c6a7e88694be1a118fb32191874bfc95b94` | `9aa98d716d63a47f009aadf01edce330a6c4c7b11c6b0c893016bd9fa59e7388` | metadata added (vector outputs unchanged; see compare_outputs.py) |
| `test-vectors/extraction/limits-rust.json` | `61ad316e717aed92d077759255fde118cc7e272d476d754d4d7224f21e249c6b` | `deaf38d72dc31c869ec3d69ba390d2b48aa23efc945dff815111a56d8d229fd3` | metadata added (vector outputs unchanged; see compare_outputs.py) |
| `test-vectors/extraction/rust.json` | `21f3360c9e7c2394033e26548f35e8dddfdb723a35279c984c09967f96cc9590` | `420288aa27d67e1717430a0f28a8b9391b34af4b131728dcff7fa692fd6e7d73` | metadata added (vector outputs unchanged; see compare_outputs.py) |
| `test-vectors/extraction/unicode-17.0.0-tables.json` | `9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f` | `9363b97eb849cb236c786098f017728ad04688782f07c2969afddf93b03ac29f` | identical |
