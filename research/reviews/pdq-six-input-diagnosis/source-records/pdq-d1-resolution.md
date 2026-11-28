# PDQ-D1 documentation resolution

2026-11-27. Independent review `pdq-diagnosis-review/review.md` found that the report and generator reversed the flipx/flipy sign masks. Both table rows now say **+B on odd index, −B on even index**. Only these two lines changed in each file; the generator was edited as text, not executed.

Verified against retained Python `pdq_np.py` lines181/183 (`np.where(i & 1, b, -b)` / `np.where(j & 1, b, -b)`) and C++ `dct16OriginalToFlipX`/`dct16OriginalToFlipY`: odd branches copy A[i][j], even branches negate it, with B[i][j] unchanged coordinates (no transpose). Here i is the zero-based row index and j the zero-based column index. Thus flipx is the top/bottom reflection using row-frequency parity, and flipy is the left/right reflection using column-frequency parity; those axis labels remain correct.

No numeric rerun, build, new experiment, acquisition or generator execution. All pre-existing package files other than report.md, write-report.py and SHA256SUMS were verified byte-identical after this correction. All numerical arrays, CSV decisions, JSON outcomes, binaries, sources, questions and tests/logs are unchanged. Baseline remains32/48 exact hashes,6/6 qualities. Six-input/one-host limitations and all gate boundaries remain unchanged. No repository/publication changes.

## Exact before/after identities

- Report before: `a81e276273276d095c568a3bb5dfb9abec02c0ac81d629184b13bc00c53f78c4`
- Report after: `2816c35b4ce7ace508170bb6f55a515fe4df60cec7a20d0d3603f66e30ebac95`
- Generator before: `9e637c57950fe9d940a154f5e9b7736a0a99d97b14dc3385e3e0fb911b400a54`
- Generator after: `43c0f84721b88f23776949392a9ce1ed7f2d8f9990ec9cfccf7727b684fbd9e8`
- Package SHA256SUMS before: `7d27b104fe18fc4f1e8d2c75b85108160e0d8e97bf8ba4779b694e34e7d86f99`
- Independent review SHA256 (unchanged): `1abe8a7a08cffd5dde65b4653455c7d7167f58b746f2cf0add511903377526eb`

Original report/generator/manifest copies are retained in sibling `pdq-d1-before/`. The revised SHA256SUMS updates only report/generator entries and adds this resolution note. Its final hash and verified file accounting are in sibling `pdq-d1-resolution-identity.json`, outside the package to avoid a self-referential identity. No prior review was edited. Ready for a focused documentation/identity recheck only.
