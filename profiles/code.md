# Code profile research plan

Status: experimental; extraction algorithm and thresholds are not yet standardized.

Start with a local catalogue of overlapping token regions and source spans. Use separate literal-preserving and scope-aware identifier-normalized channels. Do not erase every identifier and literal in the sole representation: this can collapse unrelated code into the same features.

Before registering a profile, specify language and grammar revision, tokenizer rules, scope resolution, encodings, parser error behavior, comments/docstrings, significant whitespace, macro/generated code, token serialization, hash parameters, window sizes, minimum-selection tie-breaking, and coordinate units. Tree-sitter by itself does not provide complete semantic scope resolution.

Winnowing offers a locality guarantee for an unchanged normalized substring of at least `k + w - 1` tokens under a consistent extraction procedure. It does not guarantee unique ancestry, resilience to edits within that substring, or a false-positive rate. Winnowing selection and MinHash estimation are distinct algorithms. [Original paper](https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf).

Use local alignment and directional containment for fragments; report whole-file Jaccard separately. A 30-feature excerpt inside 3,000 distinct host features has Jaccard 0.01 despite complete containment of the excerpt. Similarity denominators and duplicate handling must be explicit.

Exact normalized subtree hashes can survive moving an unchanged subtree. Loop inversion or changed subtree structure generally requires another method. AST similarity is not automatically semantic equivalence. Compare structural methods only after a token baseline is measured.

Store region origins and historical license evidence independently of detection scores. Include mixed-history files, imports from older branches, dependencies, templates, and third-party contributions. No universal token/subtree count establishes copying or legality.

The synthetic `exact-bytes-fixture` profile in examples is a format demonstration only. It is not this code profile and makes no transformation-resilience claim.
