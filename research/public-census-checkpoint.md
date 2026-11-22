# Public-code eligibility checkpoint

Measured 2026-11-21 using the [frozen census protocol](public-census-plan.md). Four pinned public repositories were inspected as source only. No acquired program, build script, macro or dependency was executed. This small convenience sample measures the current narrow patterns, not the code ecosystem.

## Coordinator reruns

| Language/sample | Primary files | Observed units | Narrow potential patterns |
| --- | --- | --- | --- |
| Go: go-spew library | 8 | 63 parsed function declarations | 2 singleton literal assignments; no adjacent multi-assignment run |
| Go: hey application | 6 | 32 parsed function declarations | 3 singleton literal assignments; no adjacent multi-assignment run |
| Rust: itoa library | 2 | 16 lexical `fn` tokens; 138 numeric tokens | No current canonical suffixed-u32 spelling tokens or explicit u32 declaration runs |
| Rust: hexyl application | 5 | 75 lexical `fn` tokens; 312 numeric tokens | No current canonical suffixed-u32 spelling tokens or explicit u32 declaration runs |

Go excludes tests, testdata, generated files and dependencies from these primary totals; the scanner reports other classes separately. Rust primary means `src/` and can include inline tests and macro bodies. Its `fn` counts are lexical, not parsed functions. Do not pool these denominators or compare language performance from them.

No full synthetic shape matched. More importantly, no exact safe embedding eligibility was established: source/build/type/observer preconditions remain unestablished by this source-only study. The recorded zero eligibility is not proof that no implementation could mark these sources. Singleton assignments are not safe naming opportunities without scope and use analysis. Rust's absent suffixed patterns say nothing about broader unsuffixed or inferred integer literal opportunities.

The coordinator independently reran both Go scans and obtained exact equality with their aggregate JSON. The coordinator also reran both Rust scans with the frozen scanner and carrier hashes; their complete local scan records and published aggregate groups matched exactly. The coordinator manually checked all five primary Go singleton spans against source bytes. Scanner tests cover synthetic positive/negative cases and path/offset handling; detailed lane audits and reproduction commands accompany the results.

## Decision

Keep these carrier implementations as synthetic controls. Do not promote their function grammars to production profiles or add identity framing based on this census. We now have two distinct problems: the narrow patterns offer little observable opportunity in this sample, and earlier normalization experiments erase their nonzero raw states. More payload machinery resolves neither problem.

Continue the roadmap's extracted-fingerprint baseline as a complementary measurement tool. Embedded marking remains a first-class use case: any next carrier proposal must separately justify a useful source subset, capacity, behavior safety and a declared transformation target. Broader literal spelling might offer more sites, but should not be promoted without confronting cheap canonicalization. Acquisition beyond this four-repository study requires a new bounded protocol; retain this sample outside future held-out evaluations.

Next bounded implementation proposal: a synthetic, deterministic token-fingerprint comparison baseline with original UTF-8 spans, exact and normalized comparisons, partial copies, common-code negatives and explicit abstentions. Freeze its extraction/configuration description before choosing hash/window parameters. This establishes a comparison control, not a substitute for embedded marks or a calibrated detector. Normative schemas and identity/signature claims stay unchanged.

Detailed audits, pins, license provenance, exclusions and reproduction commands: [Go census](lanes/go-census-results.md) and [Rust census](lanes/rust-census-results.md).
