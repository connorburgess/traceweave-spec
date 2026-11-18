# Threat model

Assume the adversary has the specification, reference implementation, all public releases, and any content being distributed. Owner-specific keys and reference catalogues can remain private. The adversary need not recover a key to erase observable code or media features.

| Threat | Required response or open limitation |
| --- | --- |
| Formatting, renaming, refactoring, recompression | Measure each supported profile; never infer robustness from algorithm names |
| Partial extraction and insertion into a large host | Localize evidence and test containment; whole-file similarity can hide small copies |
| Repeated regeneration and cross-language ports | Allow abstention; arbitrary rewriting has no detection guarantee |
| Same-spec independent implementation | Include hard negative controls; semantics alone are not ancestry |
| Shared dependencies and lawful historical copies | Preserve origin and rights separately from similarity |
| Transplanted markers and repeated fragments | Do not attribute an entire asset from a small copied span or correlated matches |
| Signed false claims | Authenticate the signer separately; signatures do not prove the signed claim |
| Key or catalogue compromise | Document loss of privacy and trust; preserve old evidence with compromise context |
| Adaptive detector queries | Avoid public scoring oracles by default; rate limiting alone is not a security proof |
| Prefix queries and shared HMAC secrets | No claimed k-anonymity or zero knowledge; combinations, frequency and dictionary attacks can leak features |
| Malicious evidence files | Isolated parsing, bounded resources, no execution, no automatic remote fetching |
| Public transparency and identity | Explicit disclosure choice; record which metadata becomes public |

Conformance must not be described as prevention of copying. Private storage protects the detector's records, not public content against broad rewriting. Content inaccessible to the investigator remains outside source-matching coverage.

No planted defects, callbacks, telemetry, behavior changes, or secret collection are part of the design. Embedded watermark experiments require separate equivalence analysis and application-specific tests.
