#!/usr/bin/env python3
"""Stage 1 prose evaluation harness for gate TXT.4 (protocol e-txt-1).

Standard library only (python3 -I). Invokes both stamped CLIs (Rust `traceweave`
and Go `traceweave-go`) under offline/network-denied mode and verifies TXT.4
failure criteria (i)-(iii) from ROADMAP.md and research/lanes/09-evidence-review.md.

Modes:
  smoke       Dry-run smoke check on TXT.2 vectors + synthetic smoke prose ONLY.
              Does NOT evaluate the 11 repo prose files; tagged SMOKE RUN - NOT A RESULT.
  full        Frozen Stage 1 evaluation on the 11 CC BY 4.0 files, 13 lane-09
              transformations, 110 ordered negative pairs, and 6 boilerplate files.
              Requires clean git tree descending from --frozen-commit, pinned
              digests, stamped CLIs, and active OS network denial.
  compare     Verify byte-identical determinism between two full/smoke run dirs.
  self-test   Unit tests for transformations, protocol digest, and failure detectors.
"""

from __future__ import annotations

import argparse
import base64
import bisect
from concurrent.futures import ThreadPoolExecutor
import errno
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unicodedata

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
PROTOCOL_PATH = HERE / "PROTOCOL.md"
PROTOCOL_VERSION = "e-txt-1"
EXTRACTION_TEXT_DIR = REPO_ROOT / "test-vectors" / "extraction-text"
TABLES_PATH = EXTRACTION_TEXT_DIR / "text-tables-17.0.0.json"

K = 8
WINDOW = 8
KW1 = K + WINDOW - 1  # 15
KW2 = K + WINDOW - 2  # 14
K_MINUS_1 = K - 1     # 7

PINNED_SOURCE_COMMIT = "7941c473d9a245c0c1023b29eccd61aa36ecdc1d"

PINNED_PROSE_FILES: dict[str, tuple[int, str]] = {
    "docs/evaluation.md": (2122, "7b659397c555b033ce7e28314ec7f2f1571f36c5e8ce2d27615c4b7a56d71b20"),
    "docs/implementation-patterns.md": (11894, "2fe9e3d08737eb19d2ab23bf0886bdb78bac74bf5571bb495fe41089232d746a"),
    "docs/implementation-repo-plan.md": (15368, "45cdb901c7daa70f8e8f4ce6e14658e66b3c3365b3587cb2b57eb01e77a1c0ef"),
    "docs/sources.md": (10239, "f00e86568b3d8b009e20c409a67084e586e5229aa5a9d44258e7b539c553ab9f"),
    "docs/use-cases.md": (33324, "0920225ec819bb3c58b81908e972792d16e6f7fad4abf28edd14dd2e7399f4ef"),
    "profiles/README.md": (1702, "a85c9b69e2e7a222eb213a7ff215d88af4c24cd907515c39ad5314536b9d9f08"),
    "profiles/code.md": (12763, "83b5eca2f12916b2cfb889e9247d2d99836bbd32633b99e318213bb9022ea6b7"),
    "spec/attestations.md": (3141, "56dc82ffbf21d049635ca68c523d334f8642c9911b4fe1b50a4455669ed49aff"),
    "spec/conformance.md": (2650, "4e3249938643e8209dc3227f8c82b5035e427f3d278c4e5eaf543b730423af77"),
    "spec/core.md": (4773, "2cdec134b60fefc136899f78f75bf73f04de178514d7759a2701f3640d31b449"),
    "spec/threat-model.md": (2237, "136e81ebf9b719876c3bf4d85ee27936ec253dc3bffa265ced41517f7038322b"),
}

PINNED_BOILERPLATE_FILES: dict[str, tuple[int, str]] = {
    "CONTRIBUTING.md": (4453, "3d55f9a0c56bd2c91372cd0e988edb444474062874de3b8773289df9df09e1f5"),
    "LICENSE.md": (1698, "a04847c3339a695fd97bb2de12fbac881a400a7c8d25bcafb36d728e23337ebd"),
    "LICENSES/Apache-2.0.txt": (11358, "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"),
    "LICENSES/CC-BY-4.0.txt": (18656, "9e5f1b3c610b9c2da5c313bf81d577a7d1acec686bdb0384edefa6df0f90cd94"),
    "LICENSES/Unicode-3.0.txt": (1995, "e7a93b009565cfce55919a381437ac4db883e9da2126fa28b91d12732bc53d96"),
    "SECURITY.md": (1091, "b2b255af6659a3a65e26c6ee17410e26fcebe932023fd9f690dff0b7818cdaec"),
}

PINNED_VECTOR_FILES: dict[str, tuple[int, str]] = {
    "test-vectors/extraction-text/config-negative-text.json": (9409, "dbe0347d83c185966ed9b3b2989a4a58d0e0033ccaa779911ea9c2be8d78da59"),
    "test-vectors/extraction-text/config-text-markdown.json": (210, "3bf7760a91297a5077f9fb0de3c119cb0a5d14b163190d640814a8735de23203"),
    "test-vectors/extraction-text/config-text-plain-limit16.json": (202, "16d15b33a3b0a117a155d1919f4331e94fce37af7cfbf285952f20fc22f4ac2a"),
    "test-vectors/extraction-text/config-text-plain.json": (207, "35c1f63cc2f669a54acb5f9792614721431943b2fd626ffb88982e53bd37323e"),
    "test-vectors/extraction-text/limits-text.json": (2249, "cb869b751ec98c4269fb517433e8f53dad665e6f40b09b541cdd9949dc99500e"),
    "test-vectors/extraction-text/records-text-plain.json": (211182, "4b58fba3ceaa8234e50db50a1a1bdcec2bfe2e7f465ed395fc3e638a77a78208"),
    "test-vectors/extraction-text/rejections.json": (61225, "f806d5e092a659ee07728b04a9fc601fa258aa481654477a6878b2c9b45ab97e"),
    "test-vectors/extraction-text/text-markdown.json": (114894, "26c76d7a2572f2a33c277e0820fbfb4ddb62269895d1638d5d6a39c45f6df47b"),
    "test-vectors/extraction-text/text-plain.json": (318505, "8690f5aea12a26e37ba3aa944107671075edf0103cd72db640b437042e195cb8"),
    "test-vectors/extraction-text/text-tables-17.0.0.json": (378149, "49eb0304ece1f9351f4db79ddf853fdc3bce353d4a833f7c4f9424bf80ae53f4"),
}

TRANSFORMS = (
    "reflow",
    "crlf",
    "nfc",
    "nfkc",
    "case-change",
    "zero-width-10",
    "confusable",
    "markdown-strip",
    "smart-quotes",
    "host-20x",
    "excerpt-kw1",
    "distractor-kw2",
    "distractor-k1",
)

# Transformations expected by construction to keep >= 1 unchanged folded run >= k+w-1
# (checked dynamically too; recorded limits distractor-kw2 and distractor-k1, plus
# confusable on folded where skeleton is the preserved channel, are documented separately).
LIMIT_TRANSFORMS = frozenset({"distractor-kw2", "distractor-k1"})

CONFUSABLE_MAP = {
    "a": "\u0430",  # Cyrillic small a -> skeleton 'a'
    "c": "\u0441",  # Cyrillic small es -> skeleton 'c'
    "e": "\u0435",  # Cyrillic small ie -> skeleton 'e'
    "o": "\u043e",  # Cyrillic small o -> skeleton 'o'
    "p": "\u0440",  # Cyrillic small er -> skeleton 'p'
    "x": "\u0445",  # Cyrillic small ha -> skeleton 'x'
}

COMPARISON_CONFIG_MIN1_SHA256 = "91b3b2039a7ec3015a6d2f79c8207e4a95b0beab602bb81deb6c3b9c02b51e64"
COMPARISON_CONFIG_MIN2_SHA256 = "4bbfe685752022a6e5b7120af2b78381197f903eefc62b44210a66bd1992beb4"

FROZEN_TRACKED_PATHS = (
    "research/experiments/text-stage1/PROTOCOL.md",
    "research/experiments/text-stage1/harness.py",
    "profiles/text.md",
    "test-vectors/extraction-text/",
    *PINNED_PROSE_FILES.keys(),
    *PINNED_BOILERPLATE_FILES.keys(),
)


class PreconditionError(Exception):
    """Raised when environment, identity, or confinement checks fail (exit 2)."""


def artifact_id(rel_path: str, suffix: str = "") -> str:
    """Map a repo path to a valid catalogue artifact ID (^[a-z0-9][a-z0-9._-]{0,63}$)."""
    base = rel_path.lower().replace("/", "__")
    aid = f"{base}--{suffix}" if suffix else base
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", aid):
        raise ValueError(f"Invalid artifact ID {aid!r} from {rel_path!r}")
    return aid


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_comparison_config(
    min_distinct: int = 1,
    merge_gap: int = WINDOW,
    max_seeds: int = 100_000,
    max_regions: int = 1_000,
    suppression_sha256: str = "none",
) -> bytes:
    """Return canonical traceweave-seed-merge-draft-2 configuration bytes."""
    obj = {
        "comparison": "traceweave-seed-merge-draft-2",
        "modes": ["exact", "folded", "skeleton"],
        "minRegionDistinctHashes": min_distinct,
        "mergeGap": merge_gap,
        "maxSeedsPerMode": max_seeds,
        "maxRegionsPerMode": max_regions,
        "suppressionCatalogueSha256": suppression_sha256,
    }
    return (json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


# --------------------------------------------------------------------------- protocol & pins


def protocol_digest(path: Path = PROTOCOL_PATH) -> tuple[str | None, str]:
    """Return (recorded_hex, computed_hex) for PROTOCOL.md self-excluding SHA-256."""
    raw = path.read_bytes()
    m = re.search(rb"Protocol digest \(SHA-256, self-excluding\): `([0-9a-f]{64})`", raw)
    recorded = m.group(1).decode("ascii") if m else None
    zeroed = re.sub(
        rb"(Protocol digest \(SHA-256, self-excluding\): `)[0-9a-f]{64}(`)",
        rb"\g<1>" + b"0" * 64 + rb"\g<2>",
        raw,
    )
    return recorded, sha256_bytes(zeroed)


def verify_pinned_files(check_protocol: bool = True) -> dict[str, str]:
    """Verify SHA-256 and byte lengths of all pinned corpus, boilerplate, and vector files."""
    if check_protocol:
        recorded, computed = protocol_digest()
        if recorded is None or recorded != computed:
            raise PreconditionError(
                f"PROTOCOL.md digest mismatch: recorded={recorded} computed={computed}"
            )
    digests: dict[str, str] = {}
    for group in (PINNED_PROSE_FILES, PINNED_BOILERPLATE_FILES, PINNED_VECTOR_FILES):
        for rel, (exp_len, exp_sha) in group.items():
            p = REPO_ROOT / rel
            if not p.is_file():
                raise PreconditionError(f"Missing pinned file: {rel}")
            raw = p.read_bytes()
            actual_sha = sha256_bytes(raw)
            if len(raw) != exp_len or actual_sha != exp_sha:
                raise PreconditionError(
                    f"Pinned file drifted: {rel} len={len(raw)} (expected {exp_len}) "
                    f"sha256={actual_sha} (expected {exp_sha})"
                )
            digests[rel] = actual_sha
    return digests


def check_git_identity(frozen_commit: str) -> dict[str, object]:
    """Verify clean tree, ancestor relationship, and frozen paths unchanged."""
    if not re.fullmatch(r"[0-9a-f]{40}", frozen_commit):
        raise PreconditionError(f"--frozen-commit must be 40 lowercase hex chars: {frozen_commit!r}")

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
        )

    head_p = git("rev-parse", "HEAD")
    if head_p.returncode != 0:
        raise PreconditionError("git rev-parse HEAD failed")
    head = head_p.stdout.strip()
    status_p = git("status", "--porcelain", "--untracked-files=all")
    porcelain = [ln for ln in status_p.stdout.splitlines() if ln.strip()]
    if porcelain:
        raise PreconditionError(f"Working tree is not clean ({len(porcelain)} entries)")
    anc_p = git("merge-base", "--is-ancestor", frozen_commit, "HEAD")
    if anc_p.returncode != 0:
        raise PreconditionError(f"HEAD {head} does not descend from frozen commit {frozen_commit}")
    diff_p = git("diff", "--quiet", frozen_commit, "HEAD", "--", *FROZEN_TRACKED_PATHS)
    if diff_p.returncode != 0:
        raise PreconditionError(f"Frozen paths changed between {frozen_commit} and HEAD")
    return {
        "head": head,
        "frozenCommit": frozen_commit,
        "cleanTree": True,
        "frozenPathsUnchanged": True,
    }


def check_network_denied() -> tuple[bool, str]:
    """Probe bind + loopback connect + public connect; True iff OS denies network."""
    notes: list[str] = []
    denied_bind = False
    denied_loopback = False
    denied_public = False
    denied_errnos = {errno.EPERM, errno.EACCES, errno.ENETUNREACH, errno.EHOSTUNREACH}

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 0))
        notes.append("bind:allowed")
    except OSError as exc:
        denied_bind = exc.errno in (errno.EPERM, errno.EACCES)
        notes.append(f"bind:errno={exc.errno}")
    finally:
        s.close()

    for label, target in (("loopback", ("127.0.0.1", 1)), ("public", ("1.1.1.1", 443))):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        try:
            s.connect(target)
            notes.append(f"{label}:connected")
        except OSError as exc:
            is_denied = exc.errno in denied_errnos
            if label == "loopback":
                denied_loopback = is_denied and exc.errno in (errno.EPERM, errno.EACCES)
            else:
                denied_public = is_denied
            notes.append(f"{label}:errno={exc.errno}({errno.errorcode.get(exc.errno, '?')})")
        finally:
            s.close()

    return (denied_bind and denied_loopback and denied_public), "; ".join(notes)


# --------------------------------------------------------------------------- pinned Unicode 17.0.0 NFC


class Unicode17Tables:
    """Minimal pinned Unicode 17.0.0 tables loaded from text-tables-17.0.0.json."""

    SBASE, LBASE, VBASE, TBASE = 0xAC00, 0x1100, 0x1161, 0x11A7
    LCOUNT, VCOUNT, TCOUNT = 19, 21, 28
    NCOUNT = VCOUNT * TCOUNT
    SCOUNT = LCOUNT * NCOUNT

    def __init__(self, path: Path = TABLES_PATH) -> None:
        raw = path.read_bytes()
        expected_sha = PINNED_VECTOR_FILES["test-vectors/extraction-text/text-tables-17.0.0.json"][1]
        if sha256_bytes(raw) != expected_sha:
            raise PreconditionError("text-tables-17.0.0.json digest mismatch")
        t = json.loads(raw)
        self.word_ranges = t["classes"]["word"]
        self.word_lo = [r[0] for r in self.word_ranges]
        self.ccc = t["ccc"]
        self.ccc_lo = [r[0] for r in self.ccc]
        self.decomp = {cp: m for cp, m in t["canonicalDecomposition"]}
        self.fce = t["fullCompositionExclusion"]
        self.fce_lo = [r[0] for r in self.fce]
        self.compose: dict[tuple[int, int], int] = {}
        for cp, m in self.decomp.items():
            if len(m) == 2 and not self._in_ranges(cp, self.fce, self.fce_lo):
                self.compose[(m[0], m[1])] = cp

    @staticmethod
    def _in_ranges(cp: int, ranges: list[list[int]], lo: list[int]) -> bool:
        idx = bisect.bisect_right(lo, cp) - 1
        return idx >= 0 and ranges[idx][0] <= cp <= ranges[idx][1]

    def is_word(self, cp: int) -> bool:
        return self._in_ranges(cp, self.word_ranges, self.word_lo)

    def combining_class(self, cp: int) -> int:
        idx = bisect.bisect_right(self.ccc_lo, cp) - 1
        if idx >= 0 and self.ccc[idx][0] <= cp <= self.ccc[idx][1]:
            return self.ccc[idx][2]
        return 0

    def _decompose(self, cp: int, out: list[int]) -> None:
        if self.SBASE <= cp < self.SBASE + self.SCOUNT:
            s = cp - self.SBASE
            out.append(self.LBASE + s // self.NCOUNT)
            out.append(self.VBASE + (s % self.NCOUNT) // self.TCOUNT)
            if s % self.TCOUNT:
                out.append(self.TBASE + s % self.TCOUNT)
            return
        m = self.decomp.get(cp)
        if m is None:
            out.append(cp)
        else:
            for child in m:
                self._decompose(child, out)

    def nfd(self, text: str) -> list[int]:
        out: list[int] = []
        for ch in text:
            self._decompose(ord(ch), out)
        i = 0
        while i < len(out):
            if self.combining_class(out[i]) == 0:
                i += 1
                continue
            j = i
            while j < len(out) and self.combining_class(out[j]) != 0:
                j += 1
            out[i:j] = sorted(out[i:j], key=self.combining_class)
            i = j
        return out

    def _compose_pair(self, s: int, c: int) -> int | None:
        if self.LBASE <= s < self.LBASE + self.LCOUNT and self.VBASE <= c < self.VBASE + self.VCOUNT:
            return self.SBASE + ((s - self.LBASE) * self.VCOUNT + (c - self.VBASE)) * self.TCOUNT
        if self.SBASE <= s < self.SBASE + self.SCOUNT and (s - self.SBASE) % self.TCOUNT == 0 and self.TBASE < c < self.TBASE + self.TCOUNT:
            return s + (c - self.TBASE)
        return self.compose.get((s, c))

    def nfc(self, text: str) -> str:
        out: list[int] = []
        starter: int | None = None
        last = 0
        for cp in self.nfd(text):
            cc = self.combining_class(cp)
            if starter is not None and (len(out) - 1 == starter or last < cc):
                comp = self._compose_pair(out[starter], cp)
                if comp is not None:
                    out[starter] = comp
                    continue
            if cc == 0:
                starter = len(out)
                last = 0
            else:
                last = cc
            out.append(cp)
        return "".join(chr(cp) for cp in out)


# --------------------------------------------------------------------------- CLI runner


class ScratchFiles:
    """Content-addressed scratch file store inside a private temp directory."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, data: bytes, suffix: str = ".bin") -> Path:
        digest = sha256_bytes(data)[:24]
        p = self.root / f"{digest}{suffix}"
        if not p.exists():
            tmp = self.root / f".{digest}.{os.getpid()}.{random.getrandbits(32):08x}"
            tmp.write_bytes(data)
            os.replace(tmp, p)
        return p


class CliPair:
    """Wrapper invoking Rust `traceweave` and Go `traceweave-go` side by side."""

    def __init__(
        self,
        rust_cli: Path,
        go_cli: Path,
        work_dir: Path,
        allow_unstamped: bool = False,
        jobs: int = 4,
    ) -> None:
        self.rust_cli = rust_cli
        self.go_cli = go_cli
        self.work_dir = work_dir
        self.private_dir = work_dir / "private"
        self.out_dir = work_dir / "out"
        self.private_dir.mkdir(parents=True, exist_ok=True)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.files = ScratchFiles(work_dir / "inputs")
        self.env = dict(os.environ, TRACEWEAVE_PRIVATE_DIR=str(self.private_dir))
        self.pool = ThreadPoolExecutor(max_workers=max(2, 2 * jobs))
        self.versions = self._check_versions(allow_unstamped)

    def close(self) -> None:
        self.pool.shutdown(wait=True)

    def _run(self, cmd: list[str], timeout: int = 120) -> tuple[int, bytes, str]:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, env=self.env
        )
        return proc.returncode, proc.stdout, proc.stderr.decode("utf-8", "replace")

    def _check_versions(self, allow_unstamped: bool) -> dict[str, dict[str, object]]:
        versions: dict[str, dict[str, object]] = {}
        for lane, cli in (("rust", self.rust_cli), ("go", self.go_cli)):
            if not cli.is_file():
                raise PreconditionError(f"Missing {lane} CLI: {cli}")
            rc, so, se = self._run([str(cli), "--version-json"])
            if rc != 0:
                raise PreconditionError(f"{lane} --version-json failed (rc={rc}): {se.strip()}")
            try:
                info = json.loads(so.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise PreconditionError(f"{lane} invalid --version-json: {exc}") from exc
            if not allow_unstamped:
                if info.get("stamp") != "stamped":
                    raise PreconditionError(f"{lane} CLI is not stamped: {info}")
                commit = info.get("implementation", {}).get("commit")
                if not (isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit)):
                    raise PreconditionError(f"{lane} stamped CLI missing 40-hex commit: {info}")
            versions[lane] = info
        if not allow_unstamped:
            r_commit = versions["rust"]["implementation"]["commit"]
            g_commit = versions["go"]["implementation"]["commit"]
            r_spec = versions["rust"].get("specCommit")
            g_spec = versions["go"].get("specCommit")
            if r_commit != g_commit or r_spec != g_spec:
                raise PreconditionError(
                    f"Stamped CLI commit mismatch: rust=({r_commit},{r_spec}) go=({g_commit},{g_spec})"
                )
        return versions

    def extract_both(self, cfg_path: Path, inp_path: Path) -> tuple[bytes, list[str]]:
        """Run extract on both CLIs; return (agreed_bytes, criterion_i_failures)."""
        fr = self.pool.submit(self._run, [str(self.rust_cli), "extract", "--config", str(cfg_path), "--input", str(inp_path)])
        fg = self.pool.submit(self._run, [str(self.go_cli), "extract", "-config", str(cfg_path), str(inp_path)])
        rrc, rso, rse = fr.result()
        grc, gso, gse = fg.result()
        errs: list[str] = []
        if rrc != 0 or grc != 0:
            errs.append(f"extract nonzero exit: rust={rrc} ({rse[:120]}) go={grc} ({gse[:120]})")
        if rso != gso:
            errs.append(f"extract byte divergence: rust_len={len(rso)} go_len={len(gso)}")
        return rso, errs

    def _build_one(self, lane: str, cfg_path: Path, items: list[tuple[str, Path]]) -> tuple[int, bytes | None, str]:
        out = self.out_dir / f"cat-{lane}-{random.getrandbits(64):016x}.json"
        if lane == "rust":
            cmd = [str(self.rust_cli), "build-catalogue", "--config", str(cfg_path)]
            for item_id, path in items:
                cmd += ["--source", f"{item_id}={path}"]
            cmd += ["--out", str(out)]
        else:
            cmd = [str(self.go_cli), "build-catalogue", "-config", str(cfg_path), "-out", str(out)]
            cmd += [f"{item_id}={path}" for item_id, path in items]
        rc, _, se = self._run(cmd)
        data = out.read_bytes() if (rc == 0 and out.exists()) else None
        if out.exists():
            out.unlink()
        return rc, data, se

    def _validate_one(self, lane: str, kind: str, path: Path) -> tuple[int, str]:
        cmd = (
            [str(self.rust_cli), "validate", kind, str(path)]
            if lane == "rust"
            else [str(self.go_cli), "validate", "-" + kind, str(path)]
        )
        rc, so, se = self._run(cmd)
        return rc, (so.decode("utf-8", "replace") + se).strip()

    def build_catalogue_both(self, cfg_path: Path, items: list[tuple[str, Path]]) -> tuple[bytes, Path, list[str]]:
        """Build and validate a catalogue in both CLIs; return (cat_bytes, cat_path, failures)."""
        fr = self.pool.submit(self._build_one, "rust", cfg_path, items)
        fg = self.pool.submit(self._build_one, "go", cfg_path, items)
        rrc, rcat, rse = fr.result()
        grc, gcat, gse = fg.result()
        errs: list[str] = []
        if rrc != 0 or grc != 0 or rcat is None or gcat is None:
            errs.append(f"build-catalogue failed: rust=({rrc},{rse[:120]}) go=({grc},{gse[:120]})")
            return b"", Path(), errs
        if rcat != gcat:
            errs.append(f"build-catalogue byte divergence: rust_len={len(rcat)} go_len={len(gcat)}")
        cat_path = self.files.put(rcat, ".cat.json")
        vr = self.pool.submit(self._validate_one, "rust", "catalogue", cat_path)
        vg = self.pool.submit(self._validate_one, "go", "catalogue", cat_path)
        vrr, vr_msg = vr.result()
        vgr, vg_msg = vg.result()
        if vrr != 0 or vgr != 0:
            errs.append(f"validate catalogue failed: rust=({vrr},{vr_msg[:120]}) go=({vgr},{vg_msg[:120]})")
        return rcat, cat_path, errs

    def _compare_one(
        self, lane: str, cc_path: Path, ref_cat: Path, cand_cat: Path, supp_cat: Path | None
    ) -> tuple[int, bytes | None, str]:
        out = self.out_dir / f"body-{lane}-{random.getrandbits(64):016x}.json"
        if lane == "rust":
            cmd = [
                str(self.rust_cli), "compare", "--config", str(cc_path),
                "--reference", str(ref_cat), "--candidate", str(cand_cat),
            ]
            if supp_cat is not None:
                cmd += ["--suppression", str(supp_cat)]
            cmd += ["--body-only", "--out", str(out)]
        else:
            cmd = [
                str(self.go_cli), "compare", "-comparison-config", str(cc_path),
                "-reference", str(ref_cat), "-candidate", str(cand_cat),
            ]
            if supp_cat is not None:
                cmd += ["-suppression", str(supp_cat)]
            cmd += ["-body-only", "-out", str(out)]
        rc, _, se = self._run(cmd, timeout=300)
        data = out.read_bytes() if (rc == 0 and out.exists()) else None
        if out.exists():
            out.unlink()
        return rc, data, se

    def compare_both(
        self, cc_path: Path, ref_cat: Path, cand_cat: Path, supp_cat: Path | None = None
    ) -> tuple[dict, bytes, list[str]]:
        """Compare catalogues in both CLIs, validate body, return (parsed_body, raw_bytes, failures)."""
        fr = self.pool.submit(self._compare_one, "rust", cc_path, ref_cat, cand_cat, supp_cat)
        fg = self.pool.submit(self._compare_one, "go", cc_path, ref_cat, cand_cat, supp_cat)
        rrc, rbody, rse = fr.result()
        grc, gbody, gse = fg.result()
        errs: list[str] = []
        if rrc != 0 or grc != 0 or rbody is None or gbody is None:
            errs.append(f"compare failed: rust=({rrc},{rse[:120]}) go=({grc},{gse[:120]})")
            return {}, b"", errs
        if rbody != gbody:
            errs.append(f"compare body byte divergence: rust_len={len(rbody)} go_len={len(gbody)}")
        body_path = self.files.put(rbody, ".body.json")
        vr = self.pool.submit(self._validate_one, "rust", "body", body_path)
        vg = self.pool.submit(self._validate_one, "go", "body", body_path)
        vrr, vr_msg = vr.result()
        vgr, vg_msg = vg.result()
        if vrr != 0 or vgr != 0:
            errs.append(f"validate body failed: rust=({vrr},{vr_msg[:120]}) go=({vgr},{vg_msg[:120]})")
        return json.loads(rbody.decode("utf-8")), rbody, errs


# --------------------------------------------------------------------------- deterministic transformations


def tx_reflow(text: str) -> str:
    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = re.split(r"\n[ \t]*\n+", norm.strip())
    wrapped_paras: list[str] = []
    for para in paragraphs:
        words = para.split()
        if not words:
            continue
        lines: list[str] = []
        cur = words[0]
        for w in words[1:]:
            if len(cur) + 1 + len(w) <= 60:
                cur += " " + w
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        wrapped_paras.append("\n".join(lines))
    return ("\n\n".join(wrapped_paras) + "\n") if wrapped_paras else ""


def tx_crlf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\n", "\r\n")


def tx_nfc(text: str, tables: Unicode17Tables) -> str:
    return tables.nfc(text)


def tx_nfkc(text: str) -> str:
    # Used strictly as a deterministic input transform (simulating external NFKC).
    return unicodedata.normalize("NFKC", text)


def tx_case_change(text: str) -> str:
    return text.upper()


def tx_zero_width_10(text: str, tables: Unicode17Tables) -> str:
    out: list[str] = []
    gap_count = 0
    prev_word = False
    for ch in text:
        cur_word = tables.is_word(ord(ch))
        if prev_word and cur_word:
            gap_count += 1
            if gap_count % 10 == 0:
                out.append("\u200b")
        out.append(ch)
        prev_word = cur_word
    return "".join(out)


def tx_confusable(text: str) -> str:
    return "".join(CONFUSABLE_MAP.get(ch, ch) for ch in text)


def _strip_link_or_image(text: str) -> str:
    """Replace [label](dest) and ![alt](dest) with label/alt, supporting 1-level nested parens."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        is_img = text.startswith("![", i)
        if is_img or text[i] == "[":
            j = i + (2 if is_img else 1)
            close_br = text.find("]", j)
            if close_br != -1 and close_br + 1 < n and text[close_br + 1] == "(":
                depth = 1
                k = close_br + 2
                while k < n and depth > 0 and text[k] != "\n":
                    if text[k] == "(":
                        depth += 1
                    elif text[k] == ")":
                        depth -= 1
                    k += 1
                if depth == 0:
                    out.append(text[j:close_br])
                    i = k
                    continue
        out.append(text[i])
        i += 1
    return "".join(out)


def tx_markdown_strip(text: str) -> str:
    s = text.replace("\r\n", "\n")
    if s.startswith("\ufeff"):
        s = s[1:]
    # Strip YAML front matter if present on line 1.
    s = re.sub(r"\A---\n.*?\n(?:---|\.\.\.)(?:\n|\Z)", "", s, flags=re.S)
    # Strip HTML comments.
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    out_lines: list[str] = []
    in_fence: tuple[str, int] | None = None
    for line in s.split("\n"):
        if in_fence is not None:
            fc, fn = in_fence
            if re.match(rf"^ {{0,3}}{re.escape(fc)}{{{fn},}}[ \t]*$", line):
                in_fence = None
            else:
                out_lines.append(line)
            continue
        m_fence = re.match(r"^ {0,3}(`{3,}|~{3,})([^`]*)$", line)
        if m_fence and not (m_fence.group(1)[0] == "`" and "`" in m_fence.group(2)):
            in_fence = (m_fence.group(1)[0], len(m_fence.group(1)))
            continue
        if re.match(r"^ {0,3}\[[^\]^\n][^\]]*\]:", line):
            continue
        if re.match(r"^\|?[\s:|-]+\|[\s:|-]*$", line):
            continue
        line = re.sub(r"^ {0,3}#{1,6}[ \t]+", "", line)
        line = re.sub(r"^ {0,3}(?:>[ \t]?)+", "", line)
        line = re.sub(r"^ {0,3}(?:[-*+]|[0-9]{1,9}[.)])[ \t]+", "", line)
        out_lines.append(line)
    s = "\n".join(out_lines)
    s = _strip_link_or_image(s)
    s = re.sub(r"</?[A-Za-z][^>\n]*>", "", s)
    s = re.sub(r"`+", "", s)
    s = re.sub(r"\*\*|__|~~|\*", "", s)
    s = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|>~])", r"\1", s)
    return s


def tx_smart_quotes(text: str) -> str:
    out: list[str] = []
    in_double = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            out.append("\u201d" if in_double else "\u201c")
            in_double = not in_double
            i += 1
        elif ch == "'":
            out.append("\u2019")
            i += 1
        elif ch == "-" and i + 1 < n and text[i + 1] == "-":
            # Avoid corrupting 3+ hyphen thematic breaks or table separators; replace '--'.
            out.append("\u2014")
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _synth_host_word(idx: int) -> str:
    """Bijective base-26 synthetic token with disjoint 'hst' prefix."""
    letters = []
    x = idx
    for _ in range(5):
        letters.append(chr(ord("a") + (x % 26)))
        x //= 26
    return "hst" + "".join(reversed(letters))


def tx_host_20x(raw_bytes: bytes, file_index: int) -> bytes:
    """Embed raw_bytes at midpoint of an unrelated synthetic host >= 20x size."""
    target_padding = max(20 * len(raw_bytes), 4096)
    half_target = target_padding // 2
    seed_offset = (0x54585434 ^ (file_index * 100_003)) % 10_000_000
    parts: list[str] = []
    total_len = 0
    idx = seed_offset
    while total_len < half_target * 2 + 128:
        words = [_synth_host_word(idx + j) for j in range(12)]
        idx += 12
        sent = " ".join(words) + ".\n"
        parts.append(sent)
        total_len += len(sent)
    prefix_parts: list[str] = []
    prefix_len = 0
    cursor = 0
    while prefix_len < half_target and cursor < len(parts):
        prefix_parts.append(parts[cursor])
        prefix_len += len(parts[cursor])
        cursor += 1
    suffix = "".join(parts[cursor:]).encode("utf-8")
    prefix = "".join(prefix_parts).encode("utf-8")
    return prefix + b"\n" + raw_bytes + b"\n" + suffix


def tx_excerpt_kw1(raw_bytes: bytes, orig_record: dict) -> bytes:
    tokens = orig_record["result"]["tokens"]
    if len(tokens) < KW1:
        raise ValueError(f"Input has only {len(tokens)} tokens (< {KW1})")
    start = tokens[0]["span"][0]
    end = tokens[KW1 - 1]["span"][1]
    return raw_bytes[start:end]


def tx_distractor(raw_bytes: bytes, orig_record: dict, interval: int) -> bytes:
    """Insert distractor token 'zq' after every `interval` original tokens."""
    tokens = orig_record["result"]["tokens"]
    if not tokens:
        return raw_bytes
    chunks: list[bytes] = []
    cursor = 0
    for idx, tok in enumerate(tokens):
        end = tok["span"][1]
        chunks.append(raw_bytes[cursor:end])
        if (idx + 1) % interval == 0:
            chunks.append(b" zq")
        cursor = end
    chunks.append(raw_bytes[cursor:])
    return b"".join(chunks)


def apply_transform(
    name: str, raw_bytes: bytes, orig_record: dict, tables: Unicode17Tables, file_index: int
) -> bytes:
    text = raw_bytes.decode("utf-8")
    if name == "reflow":
        return tx_reflow(text).encode("utf-8")
    if name == "crlf":
        return tx_crlf(text).encode("utf-8")
    if name == "nfc":
        return tx_nfc(text, tables).encode("utf-8")
    if name == "nfkc":
        return tx_nfkc(text).encode("utf-8")
    if name == "case-change":
        return tx_case_change(text).encode("utf-8")
    if name == "zero-width-10":
        return tx_zero_width_10(text, tables).encode("utf-8")
    if name == "confusable":
        return tx_confusable(text).encode("utf-8")
    if name == "markdown-strip":
        return tx_markdown_strip(text).encode("utf-8")
    if name == "smart-quotes":
        return tx_smart_quotes(text).encode("utf-8")
    if name == "host-20x":
        return tx_host_20x(raw_bytes, file_index)
    if name == "excerpt-kw1":
        return tx_excerpt_kw1(raw_bytes, orig_record)
    if name == "distractor-kw2":
        return tx_distractor(raw_bytes, orig_record, KW2)
    if name == "distractor-k1":
        return tx_distractor(raw_bytes, orig_record, K_MINUS_1)
    raise ValueError(f"Unknown transformation: {name}")


# --------------------------------------------------------------------------- failure criteria checks (ii) & (iii)


def verify_extraction_spans(raw_bytes: bytes, record: dict, label: str) -> list[str]:
    """Criterion (ii) at extraction level: every token/kgram/fp span == original bytes."""
    errs: list[str] = []
    res = record.get("result", {})
    if res.get("status") not in ("ok", "insufficient-tokens"):
        return errs
    tokens = res["tokens"]
    for idx, tok in enumerate(tokens):
        s, e = tok["span"]
        if not (0 <= s < e <= len(raw_bytes)):
            errs.append(f"{label}: token[{idx}] span [{s},{e}) out of bounds (len={len(raw_bytes)})")
            continue
        actual_text = raw_bytes[s:e].decode("utf-8", "strict")
        if actual_text != tok["text"]:
            errs.append(f"{label}: token[{idx}] bytes != token.text ({actual_text!r} vs {tok['text']!r})")
    for ch_name, ch_obj in res["channels"].items():
        for kind in ("kgrams", "fingerprints"):
            for entry in ch_obj[kind]:
                pos = entry["position"]
                ks, ke = entry["span"]
                exp_s = tokens[pos]["span"][0]
                exp_e = tokens[pos + K - 1]["span"][1]
                if ks != exp_s or ke != exp_e:
                    errs.append(
                        f"{label}: {ch_name}.{kind}[pos={pos}] span [{ks},{ke}) != [{exp_s},{exp_e})"
                    )
                    continue
                slice_bytes = raw_bytes[ks:ke]
                first_b = tokens[pos]["text"].encode("utf-8")
                last_b = tokens[pos + K - 1]["text"].encode("utf-8")
                if not (slice_bytes.startswith(first_b) and slice_bytes.endswith(last_b)):
                    errs.append(f"{label}: {ch_name}.{kind}[pos={pos}] boundary bytes mismatch")
    return errs


def verify_report_spans(
    body: dict,
    bytes_by_id: dict[str, bytes],
    records_by_id: dict[str, dict],
    label: str,
) -> list[str]:
    """Criterion (ii) at comparison report level: every region & seed span == original bytes."""
    errs: list[str] = []
    for pair in body.get("pairs", []):
        if pair.get("status") != "compared":
            continue
        ref_id = pair["reference"]["id"]
        cand_id = pair["candidate"]["id"]
        ref_b = bytes_by_id[ref_id]
        cand_b = bytes_by_id[cand_id]
        ref_res = records_by_id[ref_id]["result"]
        cand_res = records_by_id[cand_id]["result"]
        ref_toks = ref_res["tokens"]
        cand_toks = cand_res["tokens"]

        for mode_name, mode_obj in pair["modes"].items():
            ref_fps = {fp["position"]: fp for fp in ref_res["channels"][mode_name]["fingerprints"]}
            cand_fps = {fp["position"]: fp for fp in cand_res["channels"][mode_name]["fingerprints"]}
            ref_vals = ref_toks if mode_name == "exact" else ref_res["channels"][mode_name]["values"]
            cand_vals = cand_toks if mode_name == "exact" else cand_res["channels"][mode_name]["values"]

            for r_idx, reg in enumerate(mode_obj.get("regions", [])):
                seeds = reg["seeds"]
                if not seeds:
                    errs.append(f"{label} ({ref_id}->{cand_id} {mode_name}): region {r_idx} empty seeds")
                    continue
                r_starts, r_ends, c_starts, c_ends = [], [], [], []
                for p, q in seeds:
                    rfp = ref_fps.get(p)
                    cfp = cand_fps.get(q)
                    if rfp is None or cfp is None:
                        errs.append(f"{label} ({ref_id}->{cand_id} {mode_name}): missing fp ({p},{q})")
                        continue
                    if rfp["hash"] != cfp["hash"]:
                        errs.append(f"{label} ({ref_id}->{cand_id} {mode_name}): seed hash mismatch ({p},{q})")
                    # Check underlying k-gram token values match!
                    r_slice = [t["text"] for t in ref_vals[p:p + K]] if mode_name == "exact" else ref_vals[p:p + K]
                    c_slice = [t["text"] for t in cand_vals[q:q + K]] if mode_name == "exact" else cand_vals[q:q + K]
                    if r_slice != c_slice:
                        errs.append(f"{label} ({ref_id}->{cand_id} {mode_name}): token values mismatch at ({p},{q})")
                    r_starts.append(rfp["span"][0])
                    r_ends.append(rfp["span"][1])
                    c_starts.append(cfp["span"][0])
                    c_ends.append(cfp["span"][1])
                if not r_starts or not c_starts:
                    continue
                rs, re_ = reg["referenceSpan"]
                cs, ce = reg["candidateSpan"]
                if (rs, re_) != (min(r_starts), max(r_ends)):
                    errs.append(
                        f"{label} ({ref_id}->{cand_id} {mode_name}): referenceSpan [{rs},{re_}) != [{min(r_starts)},{max(r_ends)})"
                    )
                if (cs, ce) != (min(c_starts), max(c_ends)):
                    errs.append(
                        f"{label} ({ref_id}->{cand_id} {mode_name}): candidateSpan [{cs},{ce}) != [{min(c_starts)},{max(c_ends)})"
                    )
                p_min = min(p for p, _ in seeds)
                p_max = max(p for p, _ in seeds)
                q_min = min(q for _, q in seeds)
                q_max = max(q for _, q in seeds)
                r_first_b = ref_toks[p_min]["text"].encode("utf-8")
                r_last_b = ref_toks[p_max + K - 1]["text"].encode("utf-8")
                c_first_b = cand_toks[q_min]["text"].encode("utf-8")
                c_last_b = cand_toks[q_max + K - 1]["text"].encode("utf-8")
                if not (ref_b[rs:re_].startswith(r_first_b) and ref_b[rs:re_].endswith(r_last_b)):
                    errs.append(f"{label} ({ref_id}->{cand_id} {mode_name}): ref_bytes[span] token boundary mismatch")
                if not (cand_b[cs:ce].startswith(c_first_b) and cand_b[cs:ce].endswith(c_last_b)):
                    errs.append(f"{label} ({ref_id}->{cand_id} {mode_name}): cand_bytes[span] token boundary mismatch")
    return errs


def has_unchanged_run(seq_a: list[str], seq_b: list[str], run_len: int = KW1) -> bool:
    """Return True iff seq_a and seq_b share at least one contiguous slice of length run_len."""
    if len(seq_a) < run_len or len(seq_b) < run_len:
        return False
    seen = {tuple(seq_a[i:i + run_len]) for i in range(len(seq_a) - run_len + 1)}
    return any(tuple(seq_b[j:j + run_len]) in seen for j in range(len(seq_b) - run_len + 1))


def shared_fingerprint_count(rec_a: dict, rec_b: dict, channel: str) -> int:
    fa = {fp["hash"] for fp in rec_a["result"]["channels"][channel]["fingerprints"]}
    fb = {fp["hash"] for fp in rec_b["result"]["channels"][channel]["fingerprints"]}
    return len(fa & fb)


# --------------------------------------------------------------------------- TXT.2 vector verification


def run_txt2_vectors(clis: CliPair) -> tuple[dict[str, int], list[str], list[str]]:
    """Verify all 154 TXT.2 vectors across Rust and Go CLIs (criteria i & ii)."""
    crit_i: list[str] = []
    crit_ii: list[str] = []
    counts: dict[str, int] = {}

    cfg_plain_p = EXTRACTION_TEXT_DIR / "config-text-plain.json"
    cfg_lim16_p = EXTRACTION_TEXT_DIR / "config-text-plain-limit16.json"
    cfg_md_p = EXTRACTION_TEXT_DIR / "config-text-markdown.json"

    for fname, cfg_p in (
        ("text-plain.json", cfg_plain_p),
        ("limits-text.json", cfg_lim16_p),
        ("text-markdown.json", cfg_md_p),
    ):
        doc = json.loads((EXTRACTION_TEXT_DIR / fname).read_text("utf-8"))
        for v in doc["vectors"]:
            inp_b = base64.b64decode(v["inputBase64"])
            inp_p = clis.files.put(inp_b, ".txt")
            rec_b, errs = clis.extract_both(cfg_p, inp_p)
            crit_i.extend(f"{fname}/{v['id']}: {e}" for e in errs)
            if not errs:
                rec = json.loads(rec_b.decode("utf-8"))
                if fname in ("text-plain.json", "limits-text.json"):
                    if rec["result"] != v["result"]:
                        crit_i.append(f"{fname}/{v['id']}: result != committed expectation")
                    crit_ii.extend(verify_extraction_spans(inp_b, rec, f"{fname}/{v['id']}"))
                else:
                    if rec["result"].get("error", {}).get("code") != "unsupported-config":
                        crit_i.append(f"{fname}/{v['id']}: expected unsupported-config")
        counts[fname] = len(doc["vectors"])

    rec_doc = json.loads((EXTRACTION_TEXT_DIR / "records-text-plain.json").read_text("utf-8"))
    for v in rec_doc["records"]:
        cfg_b = base64.b64decode(v["configBase64"]) if "configBase64" in v else (EXTRACTION_TEXT_DIR / Path(v["configFile"]).name).read_bytes()
        inp_b = base64.b64decode(v["inputBase64"])
        rec_b, errs = clis.extract_both(clis.files.put(cfg_b, ".json"), clis.files.put(inp_b, ".txt"))
        crit_i.extend(f"records/{v['id']}: {e}" for e in errs)
        if not errs and rec_b != v["expectedRecordText"].encode("utf-8"):
            crit_i.append(f"records/{v['id']}: bytes != expectedRecordText")
    counts["records-text-plain.json"] = len(rec_doc["records"])

    neg_doc = json.loads((EXTRACTION_TEXT_DIR / "config-negative-text.json").read_text("utf-8"))
    dummy_p = clis.files.put(b"hello world\n", ".txt")
    for v in neg_doc["negatives"] + neg_doc["boundaryPositives"]:
        cfg_p = clis.files.put(v["configText"].encode("utf-8"), ".json")
        rec_b, errs = clis.extract_both(cfg_p, dummy_p)
        crit_i.extend(f"config-neg/{v['id']}: {e}" for e in errs)
        if not errs:
            rec = json.loads(rec_b.decode("utf-8"))
            if "expectedResult" in v:
                exp = v["expectedResult"]
                exp_result = {"status": exp["status"], "error": exp["error"]}
                matches_envelope = all(
                    rec.get(k) == exp.get(k)
                    for k in ("profile", "profileVersion", "configSha256", "inputSha256", "inputLength")
                )
                if rec["result"] != exp_result or not matches_envelope:
                    crit_i.append(f"config-neg/{v['id']}: record != expectedResult")
            elif v["id"] == "cfg-text-bounds-max":
                if rec["result"].get("error", {}).get("code") != "unsupported-config":
                    crit_i.append(f"config-neg/{v['id']}: expected unsupported-config")
            elif v["id"] == "cfg-text-bounds-min":
                if rec["result"].get("error", {}).get("code") != "input-too-large":
                    crit_i.append(f"config-neg/{v['id']}: expected input-too-large")
    counts["config-negative-text.json"] = len(neg_doc["negatives"]) + len(neg_doc["boundaryPositives"])
    counts["total"] = sum(counts.values())
    return counts, crit_i, crit_ii


# --------------------------------------------------------------------------- core Stage 1 evaluation pipeline


def evaluate_corpus(
    clis: CliPair,
    tables: Unicode17Tables,
    corpus_items: list[tuple[str, bytes]],
    boilerplate_items: list[tuple[str, bytes]],
    is_smoke: bool,
) -> dict[str, object]:
    """Run extraction, transformations, positive checks, negative pairs, and boilerplate checks."""
    crit_i: list[str] = []
    crit_ii: list[str] = []
    crit_iii: list[str] = []

    cfg_p = EXTRACTION_TEXT_DIR / "config-text-plain.json"
    cc1_p = clis.files.put(canonical_comparison_config(min_distinct=1, merge_gap=WINDOW), ".cc1.json")
    cc2_p = clis.files.put(canonical_comparison_config(min_distinct=2, merge_gap=WINDOW), ".cc2.json")

    bytes_by_id: dict[str, bytes] = {}
    records_by_id: dict[str, dict] = {}
    cat_sources: list[tuple[str, Path]] = []

    # 1. Extract originals.
    for rel_path, raw in corpus_items:
        item_id = artifact_id(rel_path)
        p = clis.files.put(raw, ".md")
        bytes_by_id[item_id] = raw
        cat_sources.append((item_id, p))
        rec_b, errs = clis.extract_both(cfg_p, p)
        crit_i.extend(f"orig/{item_id}: {e}" for e in errs)
        if not errs:
            rec = json.loads(rec_b.decode("utf-8"))
            records_by_id[item_id] = rec
            crit_ii.extend(verify_extraction_spans(raw, rec, f"orig/{item_id}"))

    # 2. Extract boilerplate set and build boilerplate catalogue.
    bp_sources: list[tuple[str, Path]] = []
    for rel_bp, raw in boilerplate_items:
        bp_id = artifact_id(rel_bp)
        p = clis.files.put(raw, ".txt")
        bytes_by_id[bp_id] = raw
        bp_sources.append((bp_id, p))
        rec_b, errs = clis.extract_both(cfg_p, p)
        crit_i.extend(f"bp/{bp_id}: {e}" for e in errs)
        if not errs:
            rec = json.loads(rec_b.decode("utf-8"))
            records_by_id[bp_id] = rec
            crit_ii.extend(verify_extraction_spans(raw, rec, f"bp/{bp_id}"))

    corpus_cat_b, corpus_cat_p, errs = clis.build_catalogue_both(cfg_p, cat_sources)
    crit_i.extend(errs)
    bp_cat_b, bp_cat_p, errs = clis.build_catalogue_both(cfg_p, bp_sources)
    crit_i.extend(errs)
    bp_cat_sha = sha256_bytes(bp_cat_b) if bp_cat_b else "none"
    cc_supp_p = clis.files.put(
        canonical_comparison_config(min_distinct=1, merge_gap=WINDOW, suppression_sha256=bp_cat_sha),
        ".ccsupp.json",
    )

    # 3. Transformations (13 per corpus file).
    transform_summary: dict[str, dict[str, object]] = {}
    for tx_name in TRANSFORMS:
        tx_rows: list[dict[str, object]] = []
        for idx, (rel_path, orig_raw) in enumerate(corpus_items):
            orig_id = artifact_id(rel_path)
            orig_rec = records_by_id[orig_id]
            tx_raw = apply_transform(tx_name, orig_raw, orig_rec, tables, idx)
            tx_id = artifact_id(rel_path, tx_name)
            tx_p = clis.files.put(tx_raw, ".txt")
            bytes_by_id[tx_id] = tx_raw
            rec_b, errs = clis.extract_both(cfg_p, tx_p)
            crit_i.extend(f"tx/{tx_id}: {e}" for e in errs)
            if errs:
                continue
            tx_rec = json.loads(rec_b.decode("utf-8"))
            records_by_id[tx_id] = tx_rec
            crit_ii.extend(verify_extraction_spans(tx_raw, tx_rec, f"tx/{tx_id}"))

            ref_single_b, ref_single_p, errs = clis.build_catalogue_both(cfg_p, [(orig_id, clis.files.put(orig_raw, ".md"))])
            crit_i.extend(errs)
            cand_single_b, cand_single_p, errs = clis.build_catalogue_both(cfg_p, [(tx_id, tx_p)])
            crit_i.extend(errs)
            if errs:
                continue

            body, _, errs = clis.compare_both(cc1_p, ref_single_p, cand_single_p)
            crit_i.extend(errs)
            crit_ii.extend(verify_report_spans(body, bytes_by_id, records_by_id, f"tx/{tx_id}"))

            orig_folded = orig_rec["result"]["channels"]["folded"]["values"]
            tx_folded = tx_rec["result"]["channels"]["folded"]["values"]
            orig_skel = orig_rec["result"]["channels"]["skeleton"]["values"]
            tx_skel = tx_rec["result"]["channels"]["skeleton"]["values"]

            unchanged_folded = has_unchanged_run(orig_folded, tx_folded, KW1)
            unchanged_skel = has_unchanged_run(orig_skel, tx_skel, KW1)
            shared_folded_fp = shared_fingerprint_count(orig_rec, tx_rec, "folded")
            shared_skel_fp = shared_fingerprint_count(orig_rec, tx_rec, "skeleton")

            pair_modes = body.get("pairs", [{}])[0].get("modes", {}) if body.get("pairs") else {}
            outcomes = {m: pair_modes[m]["outcome"]["code"] for m in ("exact", "folded", "skeleton")} if pair_modes else {}

            # Failure criterion (iii): unchanged folded run >= k+w-1 shares 0 folded fingerprints.
            if unchanged_folded and (shared_folded_fp == 0 or outcomes.get("folded") != "match"):
                crit_iii.append(
                    f"{tx_id}: unchanged folded run >= {KW1} but shared_folded_fp={shared_folded_fp}, outcome={outcomes.get('folded')}"
                )
            # Channel-specific verification for confusable on skeleton.
            if tx_name == "confusable" and unchanged_skel and (shared_skel_fp == 0 or outcomes.get("skeleton") != "match"):
                crit_iii.append(
                    f"{tx_id}: confusable skeleton run >= {KW1} but shared_skel_fp={shared_skel_fp}, outcome={outcomes.get('skeleton')}"
                )

            tx_rows.append({
                "id": rel_path,
                "artifactId": orig_id,
                "unchangedFoldedRunKw1": unchanged_folded,
                "unchangedSkeletonRunKw1": unchanged_skel,
                "sharedFingerprints": {
                    ch: shared_fingerprint_count(orig_rec, tx_rec, ch)
                    for ch in ("exact", "folded", "skeleton")
                },
                "outcomes": outcomes,
            })

        n_files = len(corpus_items)
        transform_summary[tx_name] = {
            "files": n_files,
            "isRecordedLimit": tx_name in LIMIT_TRANSFORMS,
            "unchangedFoldedRunCount": sum(1 for r in tx_rows if r["unchangedFoldedRunKw1"]),
            "matchedCount": {
                ch: sum(1 for r in tx_rows if r["outcomes"].get(ch) == "match")
                for ch in ("exact", "folded", "skeleton")
            },
            "sharedFingerprintFileCount": {
                ch: sum(1 for r in tx_rows if r["sharedFingerprints"][ch] > 0)
                for ch in ("exact", "folded", "skeleton")
            },
            **({"details": tx_rows} if not is_smoke else {}),
        }

    # 4. Ordered negative pairs: N*(N-1) (110 for full 11-file corpus).
    def eval_negatives(cc_path: Path, supp_path: Path | None, tag: str) -> dict[str, object]:
        body, _, errs = clis.compare_both(cc_path, corpus_cat_p, corpus_cat_p, supp_path)
        crit_i.extend(errs)
        crit_ii.extend(verify_report_spans(body, bytes_by_id, records_by_id, f"neg/{tag}"))
        off_diag = [
            p for p in body.get("pairs", [])
            if p["reference"]["id"] != p["candidate"]["id"]
        ]
        self_pairs = [
            p for p in body.get("pairs", [])
            if p["reference"]["id"] == p["candidate"]["id"]
        ]
        denom = len(off_diag)
        matches = {ch: 0 for ch in ("exact", "folded", "skeleton")}
        shared_pairs = {ch: 0 for ch in ("exact", "folded", "skeleton")}
        matched_examples: list[dict[str, object]] = []
        for p in off_diag:
            modes = p.get("modes", {})
            pair_matched = False
            for ch in ("exact", "folded", "skeleton"):
                if ch in modes:
                    if modes[ch]["outcome"]["code"] == "match":
                        matches[ch] += 1
                        pair_matched = True
                    if modes[ch]["seedCount"] > 0:
                        shared_pairs[ch] += 1
            if pair_matched and not is_smoke:
                matched_examples.append({
                    "reference": p["reference"]["id"],
                    "candidate": p["candidate"]["id"],
                    "outcomes": {ch: modes[ch]["outcome"]["code"] for ch in ("exact", "folded", "skeleton")},
                })
        return {
            "denominator": denom,
            "selfPairMatches": {
                ch: sum(1 for p in self_pairs if p.get("modes", {}).get(ch, {}).get("outcome", {}).get("code") == "match")
                for ch in ("exact", "folded", "skeleton")
            },
            "matches": matches,
            "sharedFingerprintPairs": shared_pairs,
            **({"matchedPairs": matched_examples} if not is_smoke else {}),
        }

    neg_unsuppressed_min1 = eval_negatives(cc1_p, None, "unsuppressed-min1")
    neg_unsuppressed_min2 = eval_negatives(cc2_p, None, "unsuppressed-min2")
    neg_suppressed_min1 = eval_negatives(cc_supp_p, bp_cat_p, "suppressed-min1")

    # 5. Boilerplate cross-pairs (corpus x boilerplate, unsuppressed) + suppression control.
    bp_body, _, errs = clis.compare_both(cc1_p, corpus_cat_p, bp_cat_p, None)
    crit_i.extend(errs)
    crit_ii.extend(verify_report_spans(bp_body, bytes_by_id, records_by_id, "bp-cross"))
    bp_pairs = bp_body.get("pairs", [])
    bp_cross = {
        "denominator": len(bp_pairs),
        "matches": {
            ch: sum(1 for p in bp_pairs if p.get("modes", {}).get(ch, {}).get("outcome", {}).get("code") == "match")
            for ch in ("exact", "folded", "skeleton")
        },
    }

    # Suppression control: append first boilerplate item to first corpus item; verify unsuppressed
    # matches on that boilerplate region and suppressed shifts it to common-only.
    ctrl_ref_rel, ctrl_ref_b = boilerplate_items[0]
    ctrl_ref_id = artifact_id(ctrl_ref_rel)
    ctrl_cand_raw = corpus_items[0][1] + b"\n\n" + ctrl_ref_b
    ctrl_cand_id = artifact_id(corpus_items[0][0], "with-bp")
    ctrl_cand_p = clis.files.put(ctrl_cand_raw, ".txt")
    bytes_by_id[ctrl_cand_id] = ctrl_cand_raw
    ctrl_rec_b, errs = clis.extract_both(cfg_p, ctrl_cand_p)
    crit_i.extend(errs)
    if not errs:
        ctrl_rec = json.loads(ctrl_rec_b.decode("utf-8"))
        records_by_id[ctrl_cand_id] = ctrl_rec
        crit_ii.extend(verify_extraction_spans(ctrl_cand_raw, ctrl_rec, "ctrl"))
    _, ctrl_ref_cat_p, errs = clis.build_catalogue_both(cfg_p, [(ctrl_ref_id, clis.files.put(ctrl_ref_b, ".txt"))])
    crit_i.extend(errs)
    _, ctrl_cand_cat_p, errs = clis.build_catalogue_both(cfg_p, [(ctrl_cand_id, ctrl_cand_p)])
    crit_i.extend(errs)
    ctrl_unsupp, _, errs = clis.compare_both(cc1_p, ctrl_ref_cat_p, ctrl_cand_cat_p, None)
    crit_i.extend(errs)
    crit_ii.extend(verify_report_spans(ctrl_unsupp, bytes_by_id, records_by_id, "ctrl-unsupp"))
    ctrl_supp, _, errs = clis.compare_both(cc_supp_p, ctrl_ref_cat_p, ctrl_cand_cat_p, bp_cat_p)
    crit_i.extend(errs)
    crit_ii.extend(verify_report_spans(ctrl_supp, bytes_by_id, records_by_id, "ctrl-supp"))
    unsupp_modes = ctrl_unsupp["pairs"][0].get("modes", {}) if ctrl_unsupp.get("pairs") else {}
    supp_modes = ctrl_supp["pairs"][0].get("modes", {}) if ctrl_supp.get("pairs") else {}
    suppression_control = {
        "unsuppressedOutcome": {
            ch: unsupp_modes[ch]["outcome"]["code"]
            for ch in ("exact", "folded", "skeleton")
            if ch in unsupp_modes
        },
        "suppressedOutcome": {
            ch: supp_modes[ch]["outcome"]["code"]
            for ch in ("exact", "folded", "skeleton")
            if ch in supp_modes
        },
    }

    return {
        "criterionI_cliAgreementErrors": crit_i,
        "criterionII_spanMismatchErrors": crit_ii,
        "criterionIII_localityMissErrors": crit_iii,
        "boilerplateCatalogueSha256": bp_cat_sha,
        "transformations": transform_summary,
        "negativesUnsuppressedMin1": neg_unsuppressed_min1,
        "negativesUnsuppressedMin2": neg_unsuppressed_min2,
        "negativesSuppressedMin1": neg_suppressed_min1,
        "boilerplateCrossPairs": bp_cross,
        "boilerplateSuppressionControl": suppression_control,
    }


def make_smoke_corpus() -> tuple[list[tuple[str, bytes]], list[tuple[str, bytes]]]:
    """Synthetic smoke prose completely disjoint from the 11 repo files."""
    smoke_bp_text = (
        "Synthetic smoke boilerplate notice alpha beta gamma delta epsilon zeta eta theta "
        "iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega.\n"
    ).encode("utf-8")
    smoke_docs = [
        (
            "smoke-doc-1.md",
            (
                "# Synthetic Smoke Document One\n\n"
                "Early autumn winds sweep across coastal meadows where migratory birds gather "
                "before departing southward along familiar shoreline ridges.\n\n"
                "See [reference guide](https://example.invalid/smoke/one) with *formatted* "
                "notes and `inline` examples, plus ½ and 2⁶ compatibility glyphs.\n"
            ).encode("utf-8"),
        ),
        (
            "smoke-doc-2.md",
            (
                "# Synthetic Smoke Document Two\n\n"
                "Deep geological strata preserve ancient marine shells inside limestone beds "
                "formed beneath shallow prehistoric seas across quiet basins.\n\n"
                "> Careful laboratory measurements establish mineral composition without "
                "altering fragile crystalline structures.\n"
            ).encode("utf-8"),
        ),
        (
            "smoke-doc-3.md",
            (
                "# Synthetic Smoke Document Three\n\n"
                "Winter observatories track faint comet trails across dark alpine skies "
                "using calibrated wide-field optical mirrors and cold sensors.\n"
            ).encode("utf-8"),
        ),
    ]
    return smoke_docs, [("smoke-boilerplate.txt", smoke_bp_text)]


# --------------------------------------------------------------------------- CLI & self-tests


def resolve_cli(explicit: str | None, env_key: str, default_name: str, impl_dir: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_val = os.environ.get(env_key)
    if env_val:
        return Path(env_val).expanduser().resolve()
    base_dir = impl_dir or os.environ.get("TRACEWEAVE_IMPL_DIR")
    if base_dir:
        return (Path(base_dir).expanduser().resolve() / "target" / default_name).resolve()
    found = shutil.which(default_name)
    if found:
        return Path(found).resolve()
    raise PreconditionError(
        f"Cannot locate {default_name}; pass --{default_name.replace('traceweave-', '')}-cli or --impl-dir"
    )


def run_self_tests() -> int:
    """Verify transformation determinism, protocol digest helper, and criteria (i)-(iii) detectors."""
    import unittest

    class HarnessTests(unittest.TestCase):
        @classmethod
        def setUpClass(cls) -> None:
            cls.tables = Unicode17Tables()

        def test_protocol_digest_matches(self) -> None:
            recorded, computed = protocol_digest()
            self.assertIsNotNone(recorded)
            self.assertEqual(recorded, computed)

        def test_pinned_files_match(self) -> None:
            digests = verify_pinned_files(check_protocol=False)
            self.assertEqual(len(digests), 11 + 6 + 10)

        def test_comparison_config_digests(self) -> None:
            self.assertEqual(sha256_bytes(canonical_comparison_config(1, 8)), COMPARISON_CONFIG_MIN1_SHA256)
            self.assertEqual(sha256_bytes(canonical_comparison_config(2, 8)), COMPARISON_CONFIG_MIN2_SHA256)

        def test_transforms_deterministic_on_smoke_doc(self) -> None:
            smoke_docs, _ = make_smoke_corpus()
            raw = smoke_docs[0][1]
            dummy_rec = {"result": {"tokens": [{"span": [i * 2, i * 2 + 1]} for i in range(25)]}}
            for name in TRANSFORMS:
                a = apply_transform(name, raw, dummy_rec, self.tables, 0)
                b = apply_transform(name, raw, dummy_rec, self.tables, 0)
                self.assertEqual(a, b, f"non-deterministic transform {name}")
                a.decode("utf-8")

        def test_criterion_ii_span_detector_catches_tampering(self) -> None:
            raw = b"alpha beta gamma delta epsilon zeta eta theta"
            rec = {
                "result": {
                    "status": "ok",
                    "tokens": [{"class": "word", "text": "alpha", "span": [0, 6]}],  # includes space
                    "channels": {
                        "exact": {"kgrams": [], "fingerprints": []},
                        "folded": {"kgrams": [], "fingerprints": []},
                        "skeleton": {"kgrams": [], "fingerprints": []},
                    },
                }
            }
            errs = verify_extraction_spans(raw, rec, "tampered")
            self.assertTrue(errs)

        def test_criterion_iii_unchanged_run_detector(self) -> None:
            a = [f"w{i}" for i in range(20)]
            b = ["x"] + a[2:17] + ["y"]  # 15 consecutive shared tokens == KW1
            c = ["x"] + a[2:16] + ["y"]  # 14 consecutive shared tokens < KW1
            self.assertTrue(has_unchanged_run(a, b, KW1))
            self.assertFalse(has_unchanged_run(a, c, KW1))

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(HarnessTests)
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if res.wasSuccessful() else 1


def write_summary(out_dir: Path, payload: dict[str, object], is_smoke: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "summary.json").write_text(text, encoding="utf-8")
    if is_smoke:
        (out_dir / "SMOKE_NOT_A_RESULT.txt").write_text(
            "SMOKE RUN - NOT A RESULT\n", encoding="utf-8"
        )


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="TXT.4 Stage 1 prose evaluation harness (e-txt-1)")
    sub = ap.add_subparsers(dest="mode", required=True)

    for mode_name in ("smoke", "full"):
        sp = sub.add_parser(mode_name)
        sp.add_argument("--rust-cli", help="Path to stamped Rust traceweave CLI")
        sp.add_argument("--go-cli", help="Path to stamped Go traceweave-go CLI")
        sp.add_argument("--impl-dir", help="Path to implementation checkout holding target/traceweave-{rust,go}")
        sp.add_argument("--out", help="Output directory (outside git checkout)")
        sp.add_argument("--jobs", type=int, default=4)
        sp.add_argument("--require-network-denied", action="store_true")
        if mode_name == "smoke":
            sp.add_argument("--allow-unstamped", action="store_true")
        else:
            sp.add_argument("--frozen-commit", required=True, help="40-hex commit freezing PROTOCOL.md and harness.py")

    cmp_p = sub.add_parser("compare")
    cmp_p.add_argument("dir_a")
    cmp_p.add_argument("dir_b")

    sub.add_parser("self-test")

    args = ap.parse_args(argv)

    if args.mode == "self-test":
        return run_self_tests()

    if args.mode == "compare":
        a = (Path(args.dir_a) / "summary.json").read_bytes()
        b = (Path(args.dir_b) / "summary.json").read_bytes()
        if a != b:
            print(f"FAIL: summary.json differs between {args.dir_a} and {args.dir_b}", file=sys.stderr)
            return 1
        print(f"PASS: byte-identical summary.json sha256={sha256_bytes(a)}")
        return 0

    is_smoke = args.mode == "smoke"
    t0 = time.time()

    try:
        digests = verify_pinned_files(check_protocol=True)
        recorded_proto, _ = protocol_digest()
        git_id = (
            {"mode": "smoke", "note": "SMOKE RUN - NOT A RESULT"}
            if is_smoke
            else check_git_identity(args.frozen_commit)
        )
        net_denied, net_note = check_network_denied()
        if (not is_smoke or args.require_network_denied) and not net_denied:
            raise PreconditionError(f"Network denial NOT proven: {net_note}")

        rust_cli = resolve_cli(args.rust_cli, "TRACEWEAVE_RUST_CLI", "traceweave-rust", args.impl_dir)
        go_cli = resolve_cli(args.go_cli, "TRACEWEAVE_GO_CLI", "traceweave-go", args.impl_dir)

        work_dir = Path(tempfile.mkdtemp(prefix="tw-txt4-"))
        try:
            clis = CliPair(
                rust_cli=rust_cli,
                go_cli=go_cli,
                work_dir=work_dir,
                allow_unstamped=(is_smoke and args.allow_unstamped),
                jobs=args.jobs,
            )
            try:
                tables = Unicode17Tables()
                txt2_counts, txt2_i, txt2_ii = run_txt2_vectors(clis)
                if is_smoke:
                    corpus_items, bp_items = make_smoke_corpus()
                else:
                    corpus_items = [
                        (rel, (REPO_ROOT / rel).read_bytes())
                        for rel in sorted(PINNED_PROSE_FILES.keys())
                    ]
                    bp_items = [
                        (rel, (REPO_ROOT / rel).read_bytes())
                        for rel in sorted(PINNED_BOILERPLATE_FILES.keys())
                    ]
                eval_res = evaluate_corpus(clis, tables, corpus_items, bp_items, is_smoke=is_smoke)
            finally:
                clis.close()
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
    except PreconditionError as exc:
        print(f"PRECONDITION FAILED: {exc}", file=sys.stderr)
        return 2

    all_i = txt2_i + list(eval_res["criterionI_cliAgreementErrors"])
    all_ii = txt2_ii + list(eval_res["criterionII_spanMismatchErrors"])
    all_iii = list(eval_res["criterionIII_localityMissErrors"])
    verdict = "negative-result" if (all_i or all_ii or all_iii) else ("smoke-ok" if is_smoke else "met")

    summary: dict[str, object] = {
        "protocolVersion": PROTOCOL_VERSION,
        "protocolSha256": recorded_proto,
        "mode": "SMOKE RUN - NOT A RESULT" if is_smoke else "full",
        "verdict": verdict,
        "networkDenied": net_denied,
        "networkProbe": net_note,
        "gitIdentity": git_id,
        "cliVersions": clis.versions,
        "pinnedDigestsCount": len(digests),
        "txt2VectorCounts": txt2_counts,
        "failureCriteria": {
            "criterionI_cliDiffCount": len(all_i),
            "criterionII_spanErrorCount": len(all_ii),
            "criterionIII_localityMissCount": len(all_iii),
            "criterionI_errors": all_i[:25],
            "criterionII_errors": all_ii[:25],
            "criterionIII_errors": all_iii[:25],
        },
        "stage1": {k: v for k, v in eval_res.items() if not k.startswith("criterion")},
    }
    elapsed = round(time.time() - t0, 2)

    if args.out:
        write_summary(Path(args.out), summary, is_smoke=is_smoke)

    tag = "SMOKE RUN - NOT A RESULT" if is_smoke else "FULL RUN"
    print(f"[{tag}] protocol={PROTOCOL_VERSION} ({recorded_proto[:12]}) verdict={verdict} elapsed={elapsed}s")
    print(f"  networkDenied={net_denied} ({net_note})")
    print(f"  txt2={txt2_counts['total']} cases; criterion(i)={len(all_i)} criterion(ii)={len(all_ii)} criterion(iii)={len(all_iii)}")
    neg1 = eval_res["negativesUnsuppressedMin1"]
    print(f"  negatives(min=1, unsuppressed)={neg1['matches']}/{neg1['denominator']}")
    return 3 if verdict == "negative-result" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
