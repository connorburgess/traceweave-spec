"""Configuration bytes of the draft image profile and the environment check.

extraction-profile-image.md §2 reproduces EXTRACTION_CONFIG and MATCHING_CONFIG; their exact
bytes are canonical(...) below (sorted keys, no whitespace, final LF) and their SHA-256 values
are recorded in the profile and the protocol. Changing any value is a new profile version.
"""
from __future__ import annotations

import hashlib
import importlib.metadata as md
import json
import platform
import sys

EXTRACTION_CONFIG = {
    "profile": "traceweave-image-fingerprint",
    "profileVersion": "draft-2",
    "decoder": {
        "library": "Pillow",
        "version": "13.0.0",
        "libjpegTurbo": "3.2.0",
        "zlib": "1.3.1.zlib-ng",
        "jpegDraft": False,
    },
    "formats": ["JPEG", "PNG"],
    "jpeg": {"dctMethod": "islow", "fancyUpsampling": True, "blockSmoothing": True, "outColorSpace": "rgb-or-grayscale", "cmykYcck": "abstain"},
    "png": {"bitDepth": "8; palette indices 1-8", "colourChunks": "ignore-gAMA-cHRM-sRGB-iCCP"},
    "modes": ["L", "LA", "P", "RGB", "RGBA"],
    "multiFrame": "abstain",
    "exifOrientation": "apply-jpeg-only",
    "icc": "ignore-and-record",
    "alpha": "flatten-white-(c*a+255*(255-a)+127)//255",
    "minSide": 32,
    "maxPixels": 50000000,
    "maxBytes": 67108864,
    "pdq": {
        "implementation": "threatexchange-python-9f627fb1d6d2a4a26c9b5ee1d6ca5e5ccc8e06a2",
        "luma": "0.299R+0.587G+0.114B-float64",
        "preResize": "none",
        "bits": 256,
        "hexWordOrder": "vendor",
        "qualityFloor": 50,
        "dihedral": "catalogue-orig-query-8",
    },
    "iscc": {
        "implementation": "iscc-core-1.5.0",
        "algorithm": "image-code-v0",
        "normalization": "following-iscc-sdk-0.9.7-cc11f771-pillow-13.0.0",
        "bits": 64,
        "qualityFloor": "none",
        "dihedral": "catalogue-orig-query-8-on-32x32",
    },
}

MATCHING_CONFIG = {
    "matching": "traceweave-image-nearest-draft-1",
    "parameterStatus": "experimental",
    "pdq": {"threshold": 31, "comparison": "le"},
    "iscc": {"threshold": 7, "comparison": "le"},
    "distance": "hamming-min-over-query-dihedral",
    "tie": "abstain-ambiguous",
}

PINNED_PACKAGES = {
    "annotated-types": "0.8.0",
    "base58": "2.1.1",
    "bitarray": "3.12.4",
    "blake3": "1.0.11",
    "data-url": "1.4.0",
    "iscc-core": "1.5.0",
    "jcs": "0.3.0",
    "loguru": "0.8.0",
    "more-itertools": "11.2.1",
    "numpy": "2.5.5",
    "pillow": "13.0.0",
    "pybase64": "1.5.2",
    "pydantic": "2.14.4",
    "pydantic-core": "2.50.5",
    "python-dotenv": "1.2.4",
    "typing-extensions": "4.16.0",
    "typing-inspection": "0.4.5",
    "uvarint": "1.2.0",
    "xxhash": "4.1.0",
}


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode()


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def extraction_config_sha256() -> str:
    return sha256(canonical(EXTRACTION_CONFIG))


def matching_config_sha256() -> str:
    return sha256(canonical(MATCHING_CONFIG))


def environment() -> dict:
    from PIL import features

    pk = {}
    for name in PINNED_PACKAGES:
        try:
            pk[name] = md.version(name)
        except md.PackageNotFoundError:
            pk[name] = None
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "machine": platform.machine(),
        "system": platform.system(),
        "packages": pk,
        "libjpegTurbo": features.version_feature("libjpeg_turbo"),
        "zlib": features.version("zlib"),
    }


def check_environment() -> list[str]:
    """Return a list of deviations from the pinned environment (empty = OK)."""
    env = environment()
    errs = []
    if not env["python"].startswith("3.14."):
        errs.append(f"python {env['python']} (pinned 3.14.x)")
    for k, v in PINNED_PACKAGES.items():
        if env["packages"][k] != v:
            errs.append(f"{k} {env['packages'][k]} (pinned {v})")
    d = EXTRACTION_CONFIG["decoder"]
    if env["libjpegTurbo"] != d["libjpegTurbo"]:
        errs.append(f"libjpeg-turbo {env['libjpegTurbo']} (pinned {d['libjpegTurbo']})")
    if env["zlib"] != d["zlib"]:
        errs.append(f"zlib {env['zlib']} (pinned {d['zlib']})")
    return errs


if __name__ == "__main__":
    print("extraction", extraction_config_sha256())
    print("matching", matching_config_sha256())
    print(canonical(EXTRACTION_CONFIG).decode(), end="")
    print(canonical(MATCHING_CONFIG).decode(), end="")
    print("environment deviations:", check_environment() or "none")
    sys.exit(0)
