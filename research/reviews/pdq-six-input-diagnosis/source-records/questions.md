# Predeclared bounded diagnostic questions

Declared before any new core execution or instrumentation. Only the original black, constant127, low-contrast, asymmetric, wide and tall integer common-luma inputs are admitted. No 30-image/1400-input study, RGB/decoder experiment, quality waiver, threshold change or replacement parity implementation.

1. Do unchanged retained C++ binary and frozen Python port/vendor reproduce exactly 32/48 hashes, 6/6 quality and each original hash? Stop if not.
2. At which stage do common numeric arrays first differ: each Jarosz row/column pass, decimation, DCT coefficient matrix, first DCT product T, second DCT product B? Observational instrumentation must retain original outputs exactly or conclusions stop pending repair.
3. For each variant, do the recorded signed/transpose mappings, Torben median and strict greater-than bits reproduce its actual hash? Which bit positions flip, how far are their coefficients from the median, and how many ties/near-zero coefficients occur?
4. If DCT arithmetic is implicated, controlled diagnostic substitutions will hold the same six input arrays and operation order fixed while distinguishing coefficient-matrix precision/construction, product/accumulator precision and (only if necessary) accumulation ordering. First test a software NumPy binary32 sequence using the observed C++ DCT matrix versus rounded Python matrix; then double accumulation with C++ coefficients versus Python coefficients. Label every result diagnostic, never replacement conformance. Further probes require a stated observed justification and saved patch identity before execution.
5. Does a controlled substitution reproduce the affected bit decisions exactly, or only reduce error? Report causal attribution only to the intervention actually isolated; otherwise partial explanation/hypothesis.

Instrumentation design: copies only. Dump exact binary arrays at stage boundaries, DCT matrix, T/B and per-variant B/median; reconstruct bit selection independently. Compile with the original flags/compiler under network denial. Save exact patch/source/binary/input/output identities and commands. Retain all qualities/mismatches. Original source/acquisition metadata stays in thread storage, never public history. No acquire.py execution.

## Conditional follow-up, declared after stage traces and before mixed arithmetic runs

Observed cpp-D-f32 reproduces T, B and all hashes exactly, while changing either matrix construction or all arithmetic precision loses the 16 problematic variants. To separate product and accumulator rounding, run only the same six A arrays with observed C++ D: (a) binary32 products summed in binary64, storing each stage back to binary32; (b) binary64 products added to binary32 accumulators, rounding each addition to binary32. These diagnostic interventions do not modify any implementation or threshold. No accumulation-order probe is needed unless these leave the reproduction unexplained.
