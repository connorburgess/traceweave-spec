# Security and private evidence

This is an experimental specification, not a security-reviewed detector.

Keep actual keys, catalogues, nonce values, and investigation material outside public repositories and public CI. The ignore rules are a convenience, not an access-control boundary. Check staged files before sharing.

For non-sensitive design concerns, open a minimal issue. For vulnerabilities involving confidential material, use GitHub private vulnerability reporting if enabled. If that channel is unavailable, ask the maintainer for a private channel without posting the exploit or sensitive content. Do not assume a private channel is configured.

Local implementations must treat ingested files as hostile data: do not execute source code, fetch arbitrary URLs from records, follow uncontrolled symlinks, or trust paths in a supplied manifest. Define parser, memory, file-size, and recursion limits before deploying ingestion services.

The development validator accepts trusted repository fixtures only. It is not a hardened validator for arbitrary external evidence bundles.
