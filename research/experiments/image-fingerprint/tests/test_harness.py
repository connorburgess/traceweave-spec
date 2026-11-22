"""Harness unit tests. Run: .venv/bin/python -m unittest discover -s tests -v

Only smoke-range seeds (>= 1,000,000) are generated here; no experiment seed (0..1,999) is
touched by any test.
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "vendor", "threatexchange_pdq"))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import iscc_core  # noqa: E402
import run_experiment as rx  # noqa: E402
from twimg import generator, transforms  # noqa: E402
from twimg.decode import Abstain, decode  # noqa: E402
from twimg.iscc_img import iscc_from_rgb, iscc_string, normalize  # noqa: E402
from twimg.pdq_np import DIHEDRAL_NAMES, hamming_hex, luma_from_rgb, pdq_from_luma  # noqa: E402
from twimg.profile import canonical, check_environment, extraction_config_sha256, matching_config_sha256  # noqa: E402

SMOKE = 1_000_000
GOLDEN = {
    1_000_000: "073969ff4de8dbc4bab824dc379037d7d29e100f4f92ce9e23c6fc53f8a05a0a",
    1_000_001: "fe7a5de1f16f9bc5b7c30b6099d77dd5ae5b66d650b2eb3b0165c20c17e68da8",
    1_000_002: "3280bd0fe4482296d76a7da658c5f64ed59948e4f82b5ddb807ba3ee435294a7",
}


def raw_png(w, h, depth, ctype, row: bytes) -> bytes:
    import struct
    import zlib

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", w, h, depth, ctype, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(row * h)) + chunk(b"IEND", b"")


def png_bytes(img: Image.Image, **kw) -> bytes:
    b = io.BytesIO()
    img.save(b, format="PNG", **kw)
    return b.getvalue()


class TestEnvironment(unittest.TestCase):
    def test_pinned_environment(self):
        self.assertEqual(check_environment(), [])

    def test_config_digests(self):
        self.assertEqual(extraction_config_sha256(), "c740e92de69a47904fa81bb3614c086194717be856fa6a44d89ad6fdba3bb927")
        self.assertEqual(matching_config_sha256(), "fe3fa0395d3701fa5b1b55839063998eba528851d4f9e3dcaca62d3a0f6c97ac")
        self.assertTrue(canonical({"b": 1, "a": [True]}).endswith(b"\n"))


class TestGenerator(unittest.TestCase):
    def test_golden_digests(self):
        for seed, want in GOLDEN.items():
            self.assertEqual(generator.pixel_sha256(generator.generate(seed)), want, seed)

    def test_repeatable_in_process(self):
        a = generator.generate(SMOKE + 5)
        b = generator.generate(SMOKE + 5)
        self.assertTrue(np.array_equal(a, b))

    def test_sizes_cycle_and_distinct(self):
        sizes = [generator.generate(SMOKE + k).shape for k in range(3)]
        self.assertEqual(sizes, [(768, 1024, 3), (1080, 1920, 3), (512, 512, 3)])
        self.assertNotEqual(generator.pixel_sha256(generator.generate(SMOKE + 3)), generator.pixel_sha256(generator.generate(SMOKE + 6)))

    def test_seed_range(self):
        with self.assertRaises(ValueError):
            generator.generate(-1)


class TestPdq(unittest.TestCase):
    def test_port_equals_vendor(self):
        rng = np.random.default_rng(7)
        imgs = [rng.integers(0, 256, (h, w, 3), dtype=np.uint8) for h, w in ((64, 64), (97, 131), (200, 150))]
        imgs.append(np.asarray(Image.fromarray(generator.generate(SMOKE + 2)).resize((256, 256))))
        imgs.append(np.full((80, 80, 3), 128, np.uint8))  # featureless: quality 0
        for rgb in imgs:
            nh, nq = pdq_from_luma(luma_from_rgb(rgb), dihedral=True)
            vh, vq = rx.vendor_pdq(rgb)
            self.assertEqual(nq, vq)
            self.assertEqual(nh, vh)

    def test_format(self):
        h, q = pdq_from_luma(luma_from_rgb(generator.generate(SMOKE + 2)))
        self.assertRegex(h, r"^[0-9a-f]{64}$")
        self.assertTrue(0 <= q <= 100)
        self.assertEqual(hamming_hex("0" * 64, "f" * 64), 256)

    def test_flat_image_low_quality(self):
        _, q = pdq_from_luma(luma_from_rgb(np.full((100, 100, 3), 77, np.uint8)))
        self.assertEqual(q, 0)


class TestIscc(unittest.TestCase):
    def test_conformance_vectors(self):
        with open(os.path.join(os.path.dirname(iscc_core.__file__), "data.json")) as fh:
            data = json.load(fh)
        for name, v in data["gen_image_code_v0"].items():
            self.assertEqual(iscc_core.gen_image_code_v0(*v["inputs"])["iscc"], v["outputs"]["iscc"], name)

    def test_string_and_variants(self):
        rgb = generator.generate(SMOKE + 2)
        d = iscc_from_rgb(rgb, dihedral=True)
        self.assertEqual(set(d), set(DIHEDRAL_NAMES))
        self.assertTrue(iscc_string(d["orig"]).startswith("ISCC:EEA"))
        # A 90-degree rotation of the image is found among the query's 8 variants.
        rot = np.ascontiguousarray(np.rot90(rgb, 1))
        q = iscc_from_rgb(rot, dihedral=True)
        best = min(hamming_hex(q[n], d["orig"]) for n in DIHEDRAL_NAMES)
        self.assertLessEqual(best, 8)

    def test_trim_removes_uniform_border(self):
        rgb = generator.generate(SMOKE + 2)
        padded = np.full((rgb.shape[0] + 80, rgb.shape[1] + 80, 3), 240, np.uint8)
        padded[40:-40, 40:-40] = rgb
        self.assertTrue(np.array_equal(normalize(padded), normalize(rgb)))


class TestTransforms(unittest.TestCase):
    rgb = generator.generate(SMOKE + 2)  # 512 x 512

    def test_all_decode_with_expected_size(self):
        want = {
            "jpeg90": (512, 512), "jpeg75": (512, 512), "jpeg50": (512, 512), "jpeg30": (512, 512),
            "resize50": (512, 512), "resize25": (512, 512), "crop90": (486, 486), "crop75": (443, 443),
            "crop50": (362, 362), "flip": (512, 512), "png": (512, 512), "screenshot": (474, 474),
        }
        self.assertEqual(tuple(want), transforms.TRANSFORMS)
        for name in transforms.TRANSFORMS:
            rgb, info = decode(transforms.apply(name, self.rgb))
            self.assertEqual((info["width"], info["height"]), want[name], name)
            self.assertEqual(info["format"], "JPEG" if name.startswith("jpeg") else "PNG")

    def test_deterministic_bytes(self):
        for name in transforms.TRANSFORMS:
            self.assertEqual(transforms.apply(name, self.rgb), transforms.apply(name, self.rgb), name)

    def test_lossless_edits(self):
        rgb, _ = decode(transforms.apply("png", self.rgb))
        self.assertTrue(np.array_equal(rgb, self.rgb))
        rgb, _ = decode(transforms.apply("flip", self.rgb))
        self.assertTrue(np.array_equal(rgb, self.rgb[:, ::-1]))

    def test_screenshot_sizes_other_resolutions(self):
        for w, h, ws, hs in ((1024, 768, 883, 678), (1920, 1080, 1600, 928)):
            rgb = np.zeros((h, w, 3), np.uint8)
            _, info = decode(transforms.apply("screenshot", rgb))
            self.assertEqual((info["width"], info["height"]), (ws, hs))


class TestDecode(unittest.TestCase):
    def code(self, data):
        with self.assertRaises(Abstain) as cm:
            decode(data)
        return cm.exception.code

    def test_abstentions(self):
        base = Image.fromarray(generator.generate(SMOKE + 2))
        self.assertEqual(self.code(b"not an image"), "undecodable")
        b = io.BytesIO()
        base.save(b, format="GIF")
        self.assertEqual(self.code(b.getvalue()), "unsupported-format")
        self.assertEqual(self.code(png_bytes(base.resize((31, 64)))), "too-small")
        self.assertEqual(self.code(png_bytes(Image.new("I;16", (64, 64)))), "unsupported-bit-depth")
        b = io.BytesIO()
        base.convert("CMYK").save(b, format="JPEG")
        self.assertEqual(self.code(b.getvalue()), "unsupported-mode")
        self.assertEqual(self.code(raw_png(40, 40, 16, 2, b"\x00" + b"\x00" * 240)), "unsupported-bit-depth")
        self.assertEqual(self.code(raw_png(40, 40, 2, 0, b"\x00" + b"\x00" * 10)), "unsupported-bit-depth")
        b = io.BytesIO()
        base.save(b, format="PNG", save_all=True, append_images=[base.rotate(90)])
        self.assertEqual(self.code(b.getvalue()), "multi-frame")
        self.assertEqual(self.code(png_bytes(base)[:200]), "undecodable")

    def test_alpha_flattened_on_white(self):
        rgba = Image.new("RGBA", (64, 64), (10, 20, 30, 0))
        rgb, _ = decode(png_bytes(rgba))
        self.assertTrue((rgb == 255).all())

    def test_flatten_equals_pillow_paste(self):
        rng = np.random.default_rng(11)
        c = rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)
        a = rng.integers(0, 256, (64, 64), dtype=np.uint8)
        rgba = Image.fromarray(np.dstack([c, a]), "RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.getchannel("A"))
        rgb, _ = decode(png_bytes(rgba))
        self.assertTrue(np.array_equal(rgb, np.asarray(bg)))

    def test_palette_and_grey(self):
        base = Image.fromarray(generator.generate(SMOKE + 2)).resize((64, 64))
        p = base.quantize(16)
        rgb, info = decode(png_bytes(p))
        self.assertEqual(info["sourceMode"], "P")
        self.assertTrue(np.array_equal(rgb, np.asarray(p.convert("RGB"))))
        p.info["transparency"] = 3
        rgb, _ = decode(png_bytes(p, transparency=3))
        idx = np.asarray(p)
        self.assertTrue((rgb[idx == 3] == 255).all())
        g = base.convert("L")
        rgb, _ = decode(png_bytes(g))
        self.assertTrue(np.array_equal(rgb[..., 0], np.asarray(g)) and np.array_equal(rgb[..., 0], rgb[..., 2]))

    def test_pillow_grey_formula(self):
        rng = np.random.default_rng(5)
        a = rng.integers(0, 256, (50, 50, 3), dtype=np.uint8)
        r, g, b = (a[..., i].astype(np.int64) for i in range(3))
        want = (r * 19595 + g * 38470 + b * 7471 + 0x8000) >> 16
        self.assertTrue(np.array_equal(np.asarray(Image.fromarray(a).convert("L")), want))

    def test_png_exif_orientation_not_applied(self):
        img = Image.fromarray(generator.generate(SMOKE + 1)).resize((200, 100))
        exif = Image.Exif()
        exif[0x0112] = 6
        rgb, info = decode(png_bytes(img, exif=exif.tobytes()))
        self.assertEqual((info["exifOrientation"], rgb.shape[:2]), (1, (100, 200)))

    def test_exif_orientation_applied(self):
        img = Image.fromarray(generator.generate(SMOKE + 1)).resize((200, 100))
        exif = Image.Exif()
        exif[0x0112] = 6
        b = io.BytesIO()
        img.save(b, format="JPEG", quality=95, exif=exif.tobytes())
        rgb, info = decode(b.getvalue())
        self.assertEqual(info["exifOrientation"], 6)
        self.assertEqual(rgb.shape[:2], (200, 100))


class TestMatching(unittest.TestCase):
    ids = ["a", "b", "c"]

    def test_threshold_boundary_and_tie(self):
        d = rx.decide(np.array([31, 40, 50]), self.ids, 31, "a")
        self.assertEqual((d["outcome"], d["entry"], d["wrongWithinThreshold"]), ("match", "a", 0))
        d = rx.decide(np.array([32, 40, 50]), self.ids, 31, "a")
        self.assertEqual(d["outcome"], "no-match")
        d = rx.decide(np.array([5, 5, 50]), self.ids, 31, "a")
        self.assertEqual((d["outcome"], d["wrongWithinThreshold"]), ("abstain-ambiguous", 1))
        d = rx.decide(np.array([9, 3, 50]), self.ids, 31, "a")
        self.assertEqual((d["outcome"], d["entry"], d["wrongWithinThreshold"]), ("match", "b", 1))
        d = rx.decide(np.array([0, 0, 0]), self.ids, -1, None)
        self.assertEqual(d["outcome"], "no-match")

    def test_nearest_min_over_variants(self):
        q = {n: "f" * 64 for n in DIHEDRAL_NAMES}
        q["flipp"] = "0" * 64
        cat = rx.hex_to_bytes_matrix(["0" * 64, "0" * 63 + "1"])
        self.assertEqual(rx.nearest(q, ["x", "y"], cat).tolist(), [0, 1])

    def test_probe_and_identity_shapes(self):
        denied, note = rx.network_denied()
        self.assertIsInstance(denied, bool)
        self.assertIn("loopback connect", note)
        self.assertFalse(rx.code_identity(None)["ok"])
        self.assertFalse(rx.code_identity("0" * 40)["ok"])

    def test_protocol_digest_self_excluding(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "p.md")
            line = "Protocol digest (SHA-256, self-excluding): `" + "0" * 64 + "`\n"
            Path(p).write_text("# x\n" + line)
            _, computed = rx.protocol_digest(p)
            Path(p).write_text("# x\n" + line.replace("0" * 64, computed))
            recorded, again = rx.protocol_digest(p)
            self.assertEqual((recorded, again), (computed, computed))

    def test_vector_verdict(self):
        with open(os.path.join(HERE, "vectors", "check-results.json")) as fh:
            v = json.load(fh)
        self.assertTrue(rx.vector_verdict(v)["pass"])
        v["pdqCorePortVsVendor"]["equal"] -= 1
        self.assertFalse(rx.vector_verdict(v)["pass"])


class TestQueryValidation(unittest.TestCase):
    def make(self):
        h8 = {n: "a" * 64 for n in DIHEDRAL_NAMES}
        i8 = {n: "b" * 16 for n in DIHEDRAL_NAMES}
        q = {
            "id": "s0000001.jpeg75", "split": "contract", "kind": "positive", "source": "s0000001", "transform": "jpeg75",
            "sha256": "c" * 64, "byteLength": 5,
            "decode": {"status": "ok"},
            "pdq": {"status": "ok", "quality": 90, "hashes": h8},
            "iscc": {"status": "ok", "hashes": i8},
        }
        q["pdq"].update(rx.decide(np.array([3, 40]), ["s0000001", "s0000002"], 31, "s0000001"))
        q["iscc"].update(rx.decide(np.array([20, 30]), ["s0000001", "s0000002"], 7, "s0000001"))
        return q

    def test_valid_and_corruptions(self):
        ids = {"s0000001", "s0000002"}
        self.assertEqual(rx.validate_query(self.make(), ids), [])
        bad = self.make(); bad["score"] = 1
        self.assertTrue(rx.validate_query(bad, ids))
        bad = self.make(); bad["pdq"]["outcome"] = "maybe"
        self.assertTrue(rx.validate_query(bad, ids))
        bad = self.make(); bad["pdq"]["entry"] = "s0000009"
        self.assertTrue(rx.validate_query(bad, ids))
        bad = self.make(); bad["iscc"]["hashes"]["rot90"] = "b" * 15
        self.assertTrue(rx.validate_query(bad, ids))
        bad = self.make(); bad["pdq"]["distance"] = 300
        self.assertTrue(rx.validate_query(bad, ids))
        bad = self.make(); bad["iscc"]["withinThresholdCount"] = 1
        self.assertTrue(rx.validate_query(bad, ids))
        bad = self.make(); bad["pdq"] = {"status": "abstain", "code": "low-quality", "quality": 10, "outcome": "abstain-low-quality"}
        self.assertEqual(rx.validate_query(bad, ids), [])
        bad["pdq"]["outcome"] = "abstain-too-small"
        self.assertTrue(rx.validate_query(bad, ids))


class TestCatalogueValidation(unittest.TestCase):
    def make(self):
        from twimg.profile import EXTRACTION_CONFIG

        def entry(i, h):
            return {
                "id": f"s{i:07d}", "seed": i, "pixelSha256": "0" * 64, "sha256": h * 64, "byteLength": 10,
                "decode": {"status": "ok", "format": "PNG", "sourceMode": "RGB", "width": 64, "height": 64, "exifOrientation": 1, "iccPresent": False},
                "pdq": {"status": "ok", "hash": "a" * 64, "quality": 80},
                "iscc": {"status": "ok", "hash": "b" * 16},
            }
        return {
            "catalogueVersion": "traceweave-image-catalogue-draft-1",
            "profile": {"configSha256": extraction_config_sha256(), "id": EXTRACTION_CONFIG["profile"], "version": EXTRACTION_CONFIG["profileVersion"]},
            "extractionConfig": EXTRACTION_CONFIG,
            "matchingConfigSha256": matching_config_sha256(),
            "split": "smoke",
            "artifacts": [entry(1, "1"), entry(2, "2")],
        }

    def test_valid_and_corruptions(self):
        cat = self.make()
        self.assertEqual(rx.validate_catalogue(rx.canonical_bytes(cat)), [])
        self.assertIn("not canonical", rx.validate_catalogue(json.dumps(cat, sort_keys=True).encode()))
        bad = self.make(); bad["artifacts"].reverse()
        self.assertIn("ids not strictly increasing", rx.validate_catalogue(rx.canonical_bytes(bad)))
        bad = self.make(); bad["profile"]["configSha256"] = "f" * 64
        self.assertIn("extraction config binding", rx.validate_catalogue(rx.canonical_bytes(bad)))
        bad = self.make(); bad["artifacts"][1]["sha256"] = "1" * 64
        self.assertIn("duplicate artifact bytes", rx.validate_catalogue(rx.canonical_bytes(bad)))
        bad = self.make(); bad["artifacts"][0]["owner"] = "x"
        self.assertTrue(rx.validate_catalogue(rx.canonical_bytes(bad)))
        bad = self.make(); bad["artifacts"][0]["pdq"]["hash"] = "A" * 64
        self.assertTrue(rx.validate_catalogue(rx.canonical_bytes(bad)))


if __name__ == "__main__":
    unittest.main()
