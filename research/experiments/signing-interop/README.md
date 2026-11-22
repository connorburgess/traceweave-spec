# Synthetic offline DSSE interoperability experiment

Research only. Go and Rust use actual DSSE library APIs to sign and verify the exact bytes of the existing single-subject `examples/statement.json`. The public synthetic seeds (`[7; 32]` and `[9; 32]`) exist solely to make fixtures reproducible. They provide no production identity or secrecy. No private evidence, TSA, remote signer, transparency log or candidate execution is involved.

The drivers perform cryptographic verification and return authenticated raw bytes. The initial `run.py` supplies separate strict JSON/resource policy, existing schema validation, explicit local signer trust, exact candidate digest checks, and a Python commitment-opening check. That initial harness does not exercise Go/Rust commitments; the follow-up below adds that check. This is not a production verifier.

From the repository root, install/fetch dependencies online once:

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
cd research/experiments/signing-interop/go
go mod download
cd ../rust
cargo fetch --locked
```

Build from populated caches (run from repository root):

```sh
cd research/experiments/signing-interop/go
mkdir -p ../bin
GOPROXY=off GOSUMDB=off go build -mod=readonly -o ../bin/go-dsse .
cd ../rust
cargo build --release --locked --offline
```

Run verification from the repository root on macOS with an OS network-denial policy inherited by both binaries:

```sh
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  .venv/bin/python research/experiments/signing-interop/run.py --require-network-denied
```

The harness asserts that the policy denies binding a local socket; it does not contact a remote service to test denial. Dependency fetching is not offline verification. Other systems can run `.venv/bin/python research/experiments/signing-interop/run.py`; that alone does not establish network isolation. Use an OS network sandbox before claiming isolation on another platform.

The harness checks all four producer/consumer combinations, retains exact payload bytes, and writes ignored `last-results.json`. A checked-in measurement snapshot is [results.json](results.json). Limits are experiment policy: 16 KiB envelope, 8 KiB decoded payload, exactly one signature, ten-second subprocess timeout. They permit the full 8 KiB payload after base64 expansion. Synthetic regular files are assumed; the drivers are not hardened file servers or parsers for arbitrary streams. The strict outer preflight is in Python and must not be confused with native parser behavior. Native duplicate-key and key-hint probes intentionally expose the differences.

See [measured results and primary sources](../../lanes/signing-interop-results.md). Sources, `go.sum`, and `Cargo.lock` are retained; binaries, target directories, transient public keys and local run logs are excluded. No normative schema changes are proposed.

## Follow-up policy and independent commitment checks

The later `run_policy.py` experiment leaves `run.py` and its checked-in `results.json` unchanged. It adds a common strict parsing/key-hint policy around the same library APIs and independent catalogue commitment implementations in Go and Rust. The `commit catalogue-file nonce-file` operation accepts opaque catalogue bytes (up to 1 MiB) and exactly 32 raw nonce bytes. Go uses standard-library SHA-256; Rust adds pinned `sha2 =0.10.9` with updated transitive lockfile entries. Fetch that dependency online before the cached build commands above.

Run from repository root after rebuilding:

```sh
/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  .venv/bin/python research/experiments/signing-interop/run_policy.py --require-network-denied
```

This writes ignored `last-policy-results.json`; the measurement snapshot is [policy-results.json](policy-results.json). See the [follow-up report](../../lanes/signing-policy-results.md) for the exact application policy, observed cases and limitations. Hint normalization is shared Python experiment policy, not a new DSSE rule or two independent parser implementations.
