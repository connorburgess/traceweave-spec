# Attack research comparison

Reviewed 2026-11-18. Inputs: Perplexity (local input: `perplexity/02-robustness-attacks.md`; not distributed) and Google (local input: `gemini/02-robustness-attacks.md`; not distributed). These are research inputs, not adopted requirements or executed Traceweave measurements.

Google adds useful literature leads but does not justify immediately combining learned AST embedding, CodeT5 extraction and zero-knowledge proofs before establishing a useful Go/Rust carrier.

## Primary-source checks

- [RoSeMary v3](https://arxiv.org/html/2502.02068v3), sections 3 and 5: its proof hides a witness and verifies a defined extraction relation under setup/encoder assumptions. The paper separates cryptographic guarantees, empirical robustness, and operational defenses against adaptive queries. The public decision bit remains observable. Evaluations cover Python, Java and C++, not a demonstrated Go/Rust implementation. NIZK does not itself eliminate oracle exploitation, prove ownership, or preserve marks through rewriting.
- [PlaceMark v1](https://arxiv.org/html/2610.21031v1), section VI: module placement is a useful alternative carrier evaluated in Python. Carrier-aware relocation and identity-changing edits are explicit weaknesses; one tested marked Django tree has an additional failure. Repository placement does not supply a mark inside an isolated copied function. Retain as a research candidate, not a replacement for content embedding.
- [SrcMarker's license](https://github.com/YBRua/SrcMarker/blob/main/LICENSE) is MIT; the report's Apache/academic classification is incorrect.
- [gofmt](https://pkg.go.dev/cmd/gofmt) accepts file/directory paths; `gofmt -w ./...` incorrectly treats a package pattern as a path.

## Harness corrections

Preserve significant comments/directives: see [Go build constraints](https://pkg.go.dev/cmd/go#hdr-Build_constraints), [embed](https://pkg.go.dev/embed), and [Rust doc comments](https://doc.rust-lang.org/reference/comments.html). Separate source transformations from binary optimization: compilation does not remove a mark from the original source file. Compile success is only one validity gate; `go build -race` does not execute a race-detector workload. Tests provide bounded evidence, not general semantic equivalence.

Do not reject valid evasions merely for low CodeBLEU. Report similarity separately from functional validation. Do not import an arbitrary generation pass-rate regression allowance into a tool that marks existing applications.

A copied marked function may support fragment ancestry without establishing whole-repository origin. Exact repository hashes alone cannot authenticate arbitrarily edited descendants. Declare the scope of each claim.

Retain query budgets, failed attempts and best-output selection from both reports. Report attack validity and evasion separately with denominators and uncertainty. Do not automatically publish private artifacts or logs.

## Next experiment

Continue [Go/Rust carrier feasibility](02-carrier-feasibility.md): measure eligible sites and clean recovery before selecting payload size. Then test formatting, safe renaming, canonicalization and partial copying on synthetic/public fixtures. Include unmarked, wrong-key and transplant controls. Freeze thresholds using separate calibration data. Add adaptive queries when there is a detector to query. Keep ZK and repository placement as optional research branches.
