"""Paths, import set-up, environment and identity checks for e-img-m-2.

Importing this module:
  * puts third_party/trustmark/python and third_party/videoseal on sys.path, and the frozen e-img-f-2
    harness directory (for its generator and edits, imported unchanged);
  * provides install_stubs(), which PixelSeal calls just before importing videoseal: fail-on-use stub
    modules for `av` and `pycocotools`, which videoseal imports at module load but never calls for
    still images (licence lane 12). Any attribute use raises;
  * forces CPU-only, offline settings for torch and the Hugging Face libraries before they load.
Nothing here touches the network.
"""
from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import types

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_REL = "research/experiments/image-mark"
THIRD = os.path.join(HERE, "third_party")
FINGERPRINT = os.path.normpath(os.path.join(HERE, "..", "image-fingerprint"))
PROTOCOL = os.path.normpath(os.path.join(HERE, "..", "..", "drafts", "image-mark-protocol.md"))
PROTOCOL_VERSION = "e-img-m-2"
FROZEN_PATHS = (
    "research/experiments/image-mark",
    "research/drafts/image-mark-protocol.md",
    # imported, not copied: the e-img-f-2 generator and edits must be unchanged since their freeze
    "research/experiments/image-fingerprint/twimg/generator.py",
    "research/experiments/image-fingerprint/twimg/transforms.py",
)
# e-img-f-2 frozen commit; the imported generator and edits must equal that commit's bytes.
E_IMG_F_2_FROZEN = "6f39e50"

for var, val in (
    ("HF_HUB_OFFLINE", "1"),
    ("TRANSFORMERS_OFFLINE", "1"),
    ("HF_HUB_DISABLE_TELEMETRY", "1"),
    ("TORCH_HOME", os.path.join(os.environ.get("TMPDIR", "/tmp"), "e-img-m-1-torch-home-unused")),
    ("CUDA_VISIBLE_DEVICES", ""),
    ("PYTORCH_ENABLE_MPS_FALLBACK", "0"),
    # Thread pins (protocol §6 W3 and §10): every pool torch or NumPy may use is fixed.
    ("OMP_NUM_THREADS", "4"),
    ("MKL_NUM_THREADS", "4"),
    ("OPENBLAS_NUM_THREADS", "4"),
    ("VECLIB_MAXIMUM_THREADS", "4"),
    ("NUMEXPR_NUM_THREADS", "4"),
    ("OPENCV_FOR_THREADS_NUM", "1"),
):
    os.environ[var] = val

for p in (os.path.join(THIRD, "trustmark", "python"), os.path.join(THIRD, "videoseal")):
    if p not in sys.path:
        sys.path.insert(0, p)
# Appended, not prepended: only the `twimg` package is wanted from there, and its `tests` package must
# not shadow this directory's own.
if FINGERPRINT not in sys.path:
    sys.path.append(FINGERPRINT)


class StubUsed(RuntimeError):
    pass


class _Stub(types.ModuleType):
    """A module that exists only so that `import X` succeeds; any attribute use raises StubUsed."""

    def __init__(self, name: str, children: dict | None = None):
        super().__init__(name)
        self.__dict__["_children"] = children or {}
        self.__dict__["__file__"] = None
        self.__dict__["__path__"] = []  # lets `from pkg import sub` resolve registered children

    def __getattr__(self, attr):
        if attr.startswith("__"):
            raise AttributeError(attr)
        if attr in self._children:
            return self._children[attr]
        raise StubUsed(f"stub module {self.__name__!r} was used (attribute {attr!r}); it must never be called")


STUBBED = ("av", "pycocotools", "pycocotools.mask")


def install_stubs() -> None:
    """Register the stubs. Libraries that probe for these packages at import time (torchvision.io
    for av; torchmetrics through lightning_utilities for pycocotools) are imported first, so their
    probes see the real state (not installed) and cache it."""
    import lightning  # noqa: F401
    import torchmetrics.detection  # noqa: F401
    import torchvision.io  # noqa: F401

    mask = _Stub("pycocotools.mask")
    for name, mod in (("av", _Stub("av")), ("pycocotools.mask", mask), ("pycocotools", _Stub("pycocotools", {"mask": mask}))):
        existing = sys.modules.get(name)
        if existing is not None and not isinstance(existing, _Stub):
            raise RuntimeError(f"{name} is really installed; the stub would shadow it")
        sys.modules[name] = mod


# --------------------------------------------------------------------------- hashing


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def canonical_bytes(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


# --------------------------------------------------------------------------- weights


def models_dir() -> str:
    base = os.environ.get("TRACEWEAVE_EVAL_DIR") or os.path.join(os.path.expanduser("~"), "traceweave-eval")
    return os.path.realpath(os.path.join(base, "models"))


def weight_manifest() -> dict:
    with open(os.path.join(HERE, "weights.json")) as fh:
        return {e["id"]: e for e in json.load(fh)["files"]}


class WeightError(RuntimeError):
    pass


def weight_path(wid: str, check: bool = True) -> str:
    """Path of a pinned model file, after its size and SHA-256 are checked (never downloads)."""
    e = weight_manifest()[wid]
    p = os.path.join(models_dir(), e["path"])
    if check:
        if e["sha256"] is None:
            raise WeightError(f"{wid}: sha256 not pinned in weights.json")
        if not os.path.isfile(p) or os.path.getsize(p) != e["size"]:
            raise WeightError(f"{wid}: missing or wrong size at {p}")
        got = sha256_file(p)
        if got != e["sha256"]:
            raise WeightError(f"{wid}: sha256 {got} != pinned {e['sha256']}")
    return p


def weights_record() -> dict:
    """Pinned digests of every model file (the record's model digests)."""
    return {k: e["sha256"] for k, e in sorted(weight_manifest().items())}


# --------------------------------------------------------------------------- environment


def pinned_requirements() -> dict:
    text = open(os.path.join(HERE, "requirements.txt")).read().replace("\\\n", " ")
    out = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        m = re.match(r"([A-Za-z0-9_.-]+)==(\S+)\s+--hash=sha256:[0-9a-f]{64}$", line)
        if m:
            out[re.sub(r"[-_.]+", "-", m.group(1)).lower()] = m.group(2)
    return out


def redact(path: str | None) -> str | None:
    """A path as it may appear in a committed record: relative to this directory, or with the home
    directory replaced by "~". Committed files must not contain absolute home paths."""
    if not path:
        return path
    p = os.path.abspath(path)  # symlinks are not resolved: .venv/bin/python stays inside .venv
    if os.path.commonpath([p, HERE]) == HERE:
        return os.path.relpath(p, HERE)
    home = os.path.abspath(os.path.expanduser("~"))
    if os.path.commonpath([p, home]) == home:
        return "~/" + os.path.relpath(p, home)
    return p


def check_environment() -> dict:
    """Interpreter, platform and installed distributions against requirements.txt.

    `deviations` lists every pinned distribution that is missing or at another version, and every
    installed distribution that is not pinned (pip itself excepted)."""
    import importlib.metadata as md
    import platform

    pins = pinned_requirements()
    installed = {re.sub(r"[-_.]+", "-", d.metadata["Name"]).lower(): d.version for d in md.distributions()}
    dev = []
    for name, ver in sorted(pins.items()):
        if installed.get(name) != ver:
            dev.append(f"{name}: pinned {ver}, installed {installed.get(name)}")
    for name in sorted(set(installed) - set(pins) - {"pip"}):
        dev.append(f"{name}: installed {installed[name]}, not pinned")
    py = sys.version_info
    if (py.major, py.minor) != (3, 14):
        dev.append(f"python {py.major}.{py.minor}, protocol requires 3.14")
    if (sys.platform, platform.machine()) != ("darwin", "arm64"):
        dev.append(f"platform {sys.platform}/{platform.machine()}, protocol requires darwin/arm64")
    return {
        "python": sys.version.split()[0],
        "executable": redact(sys.executable),
        "prefix": redact(sys.prefix),
        "platform": f"{sys.platform}/{platform.machine()}",
        "macOS": platform.mac_ver()[0],
        "pinnedDistributions": len(pins),
        "deviations": dev,
    }


THREAD_ENV = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
              "NUMEXPR_NUM_THREADS", "OPENCV_FOR_THREADS_NUM")
PINNED_RUNTIME = {"torchThreads": 4, "torchInteropThreads": 1, "opencvThreads": 1, "deterministicAlgorithms": True}


def runtime() -> dict:
    """The thread and library settings in force (W3 inputs). `deviations` lists any that differ from
    PINNED_RUNTIME or from the thread environment set above."""
    import platform

    import cv2
    import numpy
    import torch

    rec = {
        "torch": torch.__version__,
        "torchThreads": torch.get_num_threads(),
        "torchInteropThreads": torch.get_num_interop_threads(),
        "deterministicAlgorithms": torch.are_deterministic_algorithms_enabled(),
        "mkldnnEnabled": bool(torch.backends.mkldnn.enabled),
        "opencv": cv2.__version__,
        "opencvThreads": cv2.getNumThreads(),
        "numpy": numpy.__version__,
        "threadEnv": {k: os.environ.get(k) for k in THREAD_ENV},
        "cpu": platform.processor(),
        "macOS": platform.mac_ver()[0],
    }
    dev = [f"{k}: {rec[k]} != {v}" for k, v in PINNED_RUNTIME.items() if rec[k] != v]
    dev += [f"{k} unset" for k, v in rec["threadEnv"].items() if v is None]
    rec["deviations"] = dev
    return rec


def generator_goldens() -> dict:
    """The e-img-f-2 generator's three golden pixel digests (its smoke seeds 1,000,000-1,000,002)."""
    from twimg import generator

    golden = {
        1_000_000: "073969ff4de8dbc4bab824dc379037d7d29e100f4f92ce9e23c6fc53f8a05a0a",
        1_000_001: "fe7a5de1f16f9bc5b7c30b6099d77dd5ae5b66d650b2eb3b0165c20c17e68da8",
        1_000_002: "3280bd0fe4482296d76a7da658c5f64ed59948e4f82b5ddb807ba3ee435294a7",
    }
    got = {s: generator.pixel_sha256(generator.generate(s)) for s in golden}
    return {"generator": generator.GENERATOR_ID, "matched": sum(got[s] == golden[s] for s in golden), "of": len(golden)}


def imported_from_third_party() -> dict:
    """Where trustmark and videoseal were imported from (must be third_party/)."""
    out = {}
    for name in ("trustmark", "videoseal", "twimg"):
        mod = sys.modules.get(name)
        f = getattr(mod, "__file__", None) if mod else None
        out[name] = os.path.relpath(f, HERE) if f else None
    return out


# --------------------------------------------------------------------------- network probe


def network_denied() -> tuple[bool, str]:
    """The probe of e-img-f-2 §8 (iii), re-implemented here: bind 127.0.0.1:0, then connect to
    127.0.0.1 port 1 (nothing listens). Under sandbox-exec deny network* both fail with EPERM/EACCES;
    with the network allowed the connect fails with ECONNREFUSED. No packet leaves the host."""
    notes = []
    denied_bind = denied_connect = False
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 0))
        notes.append("bind allowed")
    except OSError as e:
        denied_bind = e.errno in (errno.EPERM, errno.EACCES)
        notes.append(f"bind refused errno {e.errno}")
    finally:
        s.close()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect(("127.0.0.1", 1))
        notes.append("loopback connect accepted")
    except OSError as e:
        denied_connect = e.errno in (errno.EPERM, errno.EACCES)
        notes.append(f"loopback connect refused errno {e.errno} ({errno.errorcode.get(e.errno, '?')})")
    finally:
        s.close()
    return denied_bind and denied_connect, "; ".join(notes)


# --------------------------------------------------------------------------- protocol and code identity


DIGEST_RE = rb"Protocol digest \(SHA-256, self-excluding\): `([0-9a-f]{64})`"


def protocol_digest(path: str = PROTOCOL) -> tuple[str | None, str | None]:
    """(recorded, computed): computed over the file with the recorded 64 hex digits set to zeros."""
    if not os.path.exists(path):
        return None, None
    text = open(path, "rb").read()
    m = re.search(DIGEST_RE, text)
    zeroed = re.sub(rb"(Protocol digest \(SHA-256, self-excluding\): `)[0-9a-f]{64}(`)", rb"\g<1>" + b"0" * 64 + rb"\g<2>", text)
    return (m.group(1).decode() if m else None), hashlib.sha256(zeroed).hexdigest()


def _git(*args: str) -> tuple[int, str]:
    r = subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def git_status() -> str:
    return _git("status", "--porcelain", "--untracked-files=all")[1]


def code_identity(frozen_commit: str | None) -> dict:
    """Protocol §9 identity checks, logged verbatim."""
    rc, head = _git("rev-parse", "HEAD")
    status = git_status()
    version = None
    if os.path.exists(PROTOCOL):
        m = re.search(rb"Protocol version: `([a-z0-9-]+)`", open(PROTOCOL, "rb").read())
        version = m.group(1).decode() if m else None
    out: dict = {
        "frozenCommit": frozen_commit,
        "head": head if rc == 0 else None,
        "statusPorcelain": status.splitlines(),
        "protocolVersionInFile": version,
    }
    rc_f, _ = _git("diff", "--quiet", E_IMG_F_2_FROZEN, "--", *FROZEN_PATHS[2:])
    out["fingerprintImportsUnchangedSince"] = {"commit": E_IMG_F_2_FROZEN, "diffExitCode": rc_f}
    if frozen_commit:
        rc_diff, diff = _git("diff", "--exit-code", "--stat", frozen_commit, "--", *FROZEN_PATHS)
        rc_anc, _ = _git("merge-base", "--is-ancestor", frozen_commit, "HEAD")
        out["diffAgainstFrozen"] = {"exitCode": rc_diff, "stat": diff.splitlines()}
        out["frozenIsAncestorOfHead"] = rc_anc == 0
    out["ok"] = bool(
        frozen_commit
        and out["head"] == frozen_commit
        and status == ""
        and out["diffAgainstFrozen"]["exitCode"] == 0
        and out["frozenIsAncestorOfHead"]
        and out["protocolVersionInFile"] == PROTOCOL_VERSION
        and rc_f == 0
    )
    return out
