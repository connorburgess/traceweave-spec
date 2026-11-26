# Pinned offline synthetic demo — 0.1.0-draft.1

This is the designated native release demo: the existing Go and Rust `go-function-in-host` walkthroughs run extraction, catalogue building, comparison, stamped report emission and validation. The [original reproduction record](../../research/reviews/m5-3-offline-demo-review.md) records the tested revisions and results. M5.3 is now recorded met in the [roadmap](../../ROADMAP.md), following non-author review of this exact recipe at `24bb4b8483dc86966cb7c8277130bb816b0c6b3f` ([independent recipe review](../../research/reviews/m5-3-recipe-24bb4b8-review.md) `284ce4e`; [closure recount](../../research/reviews/m5-3-gate-closure-24bb4b8.md)). The executable recipe and its limitations are unchanged by closure; this is not release approval.

## Prerequisites and pins

Use a POSIX shell, Git, Python 3 (standard library), Rust **1.97.1** with Cargo, and Go **1.27.3**. Install toolchains before the offline phase; the recorded reproduction used preinstalled toolchains and Python 3.14.6. Rust's pin is also in `rust-toolchain.toml`, and Go's in `go/go.mod`.

Real OS network denial is required: macOS needs `sandbox-exec`; Linux needs an available network namespace through unprivileged `unshare`, or passwordless `sudo -n unshare --net` with `setpriv`. The recorded run used macOS; Linux execution of this recipe is unverified. The wrapper refuses to execute if confinement or its proof fails.

Implementation repository: `https://github.com/connorburgess/traceweave`, exact commit **`dcaa0d42e9de63d23aa113d9306134de9b28942c`**. Its `spec.lock` pins **`9cf78eec72d89c4a5383dc0ebf0fa98a4693d191`**, spec version `0.1.0-draft.1`. The implementation's historical README pin description is stale; use the lock and binary version output. The tested clone source was a local repository containing this commit; remote availability/access was not tested.

## Clone and fetch dependencies with network available

Set `IMPLEMENTATION_SOURCE` to the repository URL above, or to a local Git repository containing the exact commit. A local clone must include full history; an archive alone does not supply stamped-build metadata. Keep the temporary root outside any existing checkout. These commands use fresh temporary dependency/build caches and leave the source repository unchanged.

```sh
: "${IMPLEMENTATION_SOURCE:?Set the implementation Git URL or local repository path}"
DEMO_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/traceweave-release-demo.XXXXXX")
export DEMO_ROOT
mkdir "$DEMO_ROOT/tmp"
export TMPDIR="$DEMO_ROOT/tmp"
export CARGO_HOME="$DEMO_ROOT/cargo-home"
export GOMODCACHE="$DEMO_ROOT/go-mod-cache"
export GOCACHE="$DEMO_ROOT/go-build-cache"
export GOTOOLCHAIN=local
unset GOFLAGS CARGO_NET_OFFLINE GOPROXY TW_SPEC_DIR TRACEWEAVE_TEST_SPEC_DIR
git clone --no-hardlinks "$IMPLEMENTATION_SOURCE" "$DEMO_ROOT/implementation"
cd "$DEMO_ROOT/implementation"
git checkout --detach dcaa0d42e9de63d23aa113d9306134de9b28942c
git status --porcelain=v1
rustc --version
cargo --version
go version
python3 --version
scripts/ci-fetch
```

Require an empty Git status and exit 0 from the fetch. `scripts/ci-fetch` performs `cargo fetch --locked` for both Cargo lockfiles and verifies the two standard-library-only Go modules. This is the dependency-fetch phase; it is intentionally outside confinement. Network access is no longer needed after this step.

## Build and run under OS network denial

Continue in the same shell and clone. Run each command separately and stop on any nonzero exit.

```sh
export CARGO_NET_OFFLINE=true GOPROXY=off
scripts/offline scripts/check-spec-pin
scripts/offline python3 -I tools/stamped-build/stamped-build \
  --out "$DEMO_ROOT/traceweave-rust"
scripts/offline sh -c \
  'cd go && GOENV=off GOFLAGS= GOTOOLCHAIN=local go run ./tools/stampbuild -o "$1"' \
  sh "$DEMO_ROOT/traceweave-go"
scripts/offline cargo run -q --locked --offline -p tw-conformance -- \
  walkthrough --bin "$DEMO_ROOT/traceweave-rust" --work "$DEMO_ROOT/rust-walkthrough"
scripts/offline sh -c \
  'cd go && go run ./tools/walkthrough -bin "$1" -keep' \
  sh "$DEMO_ROOT/traceweave-go"
scripts/offline "$DEMO_ROOT/traceweave-rust" --version-json
scripts/offline "$DEMO_ROOT/traceweave-go" --version-json
git status --porcelain=v1
```

Before every command, `scripts/offline` proves that an unconfined client can connect to its temporary loopback listener and that confined clients cannot connect to that listener or `1.1.1.1:443`. On the tested macOS host it printed:

```text
scripts/offline: confinement: sandbox
scripts/offline: probe outside: loopback connected
scripts/offline: probe inside:  loopback refused:Operation_not_permitted, public refused:Operation_not_permitted
scripts/offline: network denial proven; running: ...
```

macOS uses `(version 1)(allow default)(deny network*)` through `sandbox-exec`; Linux uses a network namespace. Application offline flags supplement this OS boundary. A failed proof is a failed reproduction: do not bypass the wrapper. OS denial does not establish zero attempted network syscalls; no packet trace was taken.

## Expected results and retained outputs

Every command must exit 0. The pin check must report **356** vendored files matching `spec.lock`. Both version outputs must say `stamp: "stamped"`, implementation commit `dcaa0d42e9de63d23aa113d9306134de9b28942c` and spec commit `9cf78eec72d89c4a5383dc0ebf0fa98a4693d191`.

Both walkthroughs must report this canonical body SHA-256:

```text
081d860084af229d77137e32dedd9f40f7d0bbeca6b18424b6d51cc1d89ed3be
```

Rust must report `spans: 4/4`, a valid report document with the pinned provenance and matching body/config digests, a valid candidate-generation record, and `walkthrough: passed`. Go must pass every step, including `report document (stamped build)`, and print `all steps passed` with the expected digest. The final Git status must remain empty.

Rust retains outputs in `$DEMO_ROOT/rust-walkthrough`; Go prints its retained scratch directory under `$TMPDIR`. Each contains synthetic source, extraction records, catalogues, `body.json`, `report.json` and a candidate-generation record. Compare the two `body.json` files byte-for-byte (`cmp`) and hash them with an available SHA-256 tool; both must equal the digest above. Report wrappers have different implementation names/versions and need not be identical. Preserve the temporary tree until review is complete.

The default Go walkthrough without `-bin` builds an unstamped binary and correctly refuses report emission. That expected refusal is tested separately in the reproduction record; it does not replace the stamped report step above. There is no `scripts/walkthrough` wrapper at this revision; use these documented native entry points.

## Scope and limitations

This demo uses one synthetic Go-source fixture in two native implementations. It does not reproduce every profile, full `scripts/check`, registration/signing, browser/Shelf flows, held-out detection evaluation or production evidence. No corpus acquisition, paid services or live timestamp/registration service is involved. Similarity does not establish authorship, ownership, infringement or copying direction.

The recorded strict pin check also compared all **356/356** vendored files with `git show` bytes at the pinned spec commit in a separate local spec clone. To repeat that optional check, make a local spec mirror containing `9cf78eec72d89c4a5383dc0ebf0fa98a4693d191` available before denial and run `scripts/offline scripts/check-spec-pin --strict --mirror MIRROR_DIR`. The ordinary check above verifies local lock digests only. Neither check proves remote publication/access. The implementation's locked spec revision is older than the release-documentation revision; this is not a claim of conformance to every subsequent spec change.
