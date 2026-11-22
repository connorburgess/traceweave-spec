# Source-only Go census v1

This directory contains original scanner/acquisition/verification code, a pinned manifest and aggregate results. Upstream source, archives, per-file digests and function/run byte spans stay under ignored `.local/go-census/`. The scanner parses data only; it never imports, type-checks, builds or executes inspected packages. Its own standard-library-only executable/tests are built normally.

Frozen scanner SHA-256: `03c2e9343e8522324d8e203427fc952647dfae09d59bb4f3da4820a6cb6e2a5f`, frozen 2026-11-21T13:10:46Z before either snapshot was scanned. Rule inventory and provenance are in [manifest.json](manifest.json); per-file aggregate distribution is in the two `*-summary.json` files. [Results](../../lanes/go-census-results.md).

`ExactEligible=0` means this source-only study does not establish the required complete source/build/scope/type preconditions. It is not proof that a future implementation cannot mark these sources. Function shape is counted separately with fixed function/package names ignored only for structural measurement. Potential runs are maximal consecutive direct block statements `x := N`: one lower-case identifier and one nonnegative decimal literal fitting signed 32 bits. Singleton and length>=2 counts are separate. No dependency/use/freshness/effect proof, scope resolution or capacity follows from these syntactic counts. `fixture.go` was only a parser label in the earlier harness and is not an eligibility requirement.

All regular `.go` files are inventoried. Primary results exclude dependencies, testdata, generated files and tests, in that classification priority. A generated file inside vendor remains in the dependency class; independent verification records the overlap. Build constraints/filenames are not evaluated and mutually exclusive files are not treated as one valid build. `filename_configuration_unresolved` conservatively flags underscore-containing filenames without claiming they name actual GOOS/GOARCH targets. Filesystem/symlink/read/parser failures remain explicit.

From the project root, for a fresh acquisition (the acquisition script refuses overwrite):

```sh
cd <repository root>
git check-ignore -v .local/go-census/sources/hey .local/go-census/sources/go-spew
mkdir -p .local/go-census/licenses
curl --fail --location --silent --show-error https://raw.githubusercontent.com/davecgh/go-spew/8991bc29aa16c548c550c7ff78260e27b9ab7c73/LICENSE -o .local/go-census/licenses/go-spew-LICENSE
curl --fail --location --silent --show-error https://raw.githubusercontent.com/rakyll/hey/af177063f85bd935c55f1f2ee59c2898d9654f82/LICENSE -o .local/go-census/licenses/hey-LICENSE
shasum -a 256 .local/go-census/licenses/*
# Read/verify the pinned license texts and manifest hashes before collecting.
python3 research/experiments/go-census/acquire.py
```

The original acquisition script downloads exactly the two manifest commit archives, validates paths, writes regular files, skips special/link members and verifies root license hashes. No checkout hooks, generators or candidate commands run. License/notice headers and nested vendor licenses were reviewed after extraction; the first-party root licenses were checked before collection. The script records UTC acquisition times and archive hashes locally; those observations are also in the published manifest.

Reproduce scans with Go 1.27.3; these commands build only the original scanner:

```sh
cd research/experiments/go-census
shasum -a 256 main.go
env GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off go test -v -count=1 ./...
env GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off go run main.go -root ../../../.local/go-census/sources/go-spew -summary go-spew-summary.json -details ../../../.local/go-census/go-spew-details.json
env GOTOOLCHAIN=local GOWORK=off GOPROXY=off GOSUMDB=off go run main.go -root ../../../.local/go-census/sources/hey -summary hey-summary.json -details ../../../.local/go-census/hey-details.json
cd ../../..
python3 research/experiments/go-census/verify.py
```

The verifier checks frozen scanner identity, archive identity, independent archive file/size/content inventory, every local source digest and independent line-oriented declaration counts. Two vendored raw-string template lines explain a regex/AST discrepancy. It records the fixed audit coordinates in ignored storage and publishes aggregate verification counts. Manual audit covered the first two per observed primary shape-refusal reason in each repository and all five primary potential runs, including the non-ASCII-prefix case. No exact accepted unit was available to audit.
