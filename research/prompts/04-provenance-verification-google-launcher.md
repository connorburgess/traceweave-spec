# Google workflow: provenance verification

Use the existing full prompt 04-provenance-verification.md as a source titled “Deep research prompt: Private provenance and evidence verification”. It is task instructions, not evidence.

## Left-side Web / Deep Research query

Research private, offline-verifiable provenance for embedded Go/Rust code marks: DSSE PAE, in-toto Statement v1, Sigstore modes, RFC 3161 timestamps, salted exact-byte commitments, original/marked artifact binding, key compromise and replay/transplant attacks. Use primary specs and maintained libraries. Separate signature validity, trust, exact binding, time and detector evidence. Compare optional external services and disclosure; no mandatory public log, new cryptography or ownership guarantees.

## Center chat after importing research results

Use “Deep research prompt: Private provenance and evidence verification” as the full task instructions. Produce its complete eight-section standalone Markdown report, named 04-provenance-verification.md. Use the imported primary sources as evidence, not the prompt itself. Do not merely summarize the prompt.

Preserve local/private operation and the Go/Rust embedded-mark goal. Distinguish secret-assisted mark detection from public signature verification. Separate signature validity, signer trust, exact subject binding, commitment opening, trusted time, mark presence, similarity and fragment ancestry. None alone proves ownership or infringement.

Specify embedding, digest calculation, record creation and signing order without circular dependencies. Explain original versus final marked bytes, retained exact bytes, domain separation, nonce generation and commitment opening. Exact hashes do not authenticate arbitrary edited descendants; fingerprints are soft matches. Explain what a timestamp actually establishes about an imprint rather than assuming authorship or creation time.

Do not mandate C2PA, zero-knowledge proofs, public logs or new signature primitives. Evaluate existing libraries with pinned versions and licenses. Explain external-service disclosures and offline verification limits. Supply a verification decision table and positive/negative interoperability tests: changed payload/type/signature, malformed or duplicate-key JSON, wrong openings, untrusted/compromised keys, missing references and invalid timestamps. Preserve signed bytes and bound unsafe parsing/fetching behavior.

Label experiments unexecuted unless actually run and illustrative data clearly synthetic. Invent no private paths, commits or repository sections. Cite portable primary URLs, versions and sections; identify evidence gaps. Recommend the smallest implementable verification increment, alternatives and remaining assumptions.
