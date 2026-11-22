"""Unit tests for the e-img-m-1 harness. Run: .venv/bin/python -I -m unittest discover -s tests -t .

Only smoke seeds (3,000,000-3,000,002) and the e-img-f-2 golden seeds are generated here; no seed
in the experiment range (2,000,000-2,000,099 and 2,000,102-2,000,201) is touched.
Model tests need the pinned weights under $TRACEWEAVE_EVAL_DIR/models.
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from fractions import Fraction

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from twmark import attacks, env, payload  # noqa: E402

import fetch_weights  # noqa: E402
import run_mark  # noqa: E402

SMOKE = 3_000_000


class Payload(unittest.TestCase):
    def test_k_values(self):
        self.assertEqual(payload.k_for(100), 74)
        self.assertEqual(payload.k_for(256), 167)
        self.assertEqual(payload.k_for(32), 30)
        for n in (32, 100, 256):
            k = payload.k_for(n)
            self.assertLessEqual(payload.tail(n, k), Fraction(1, 10**6))
            self.assertGreater(payload.tail(n, k - 1), Fraction(1, 10**6))

    def test_tail_exact(self):
        self.assertEqual(payload.tail(4, 4), Fraction(1, 16))
        self.assertEqual(payload.tail(4, 0), 1)
        self.assertEqual(payload.tail(3, 2), Fraction(4, 8))

    def test_payload_deterministic_and_keyed(self):
        a = payload.payload_bits("A", "tm", "m1", 61)
        self.assertTrue(np.array_equal(a, payload.payload_bits("A", "tm", "m1", 61)))
        self.assertFalse(np.array_equal(a, payload.payload_bits("B", "tm", "m1", 61)))
        self.assertFalse(np.array_equal(a, payload.payload_bits("A", "tm", "m2", 61)))
        self.assertFalse(np.array_equal(payload.payload_bits("A", "ps", "m1", 61), a))
        self.assertEqual(payload.payload_bits("A", "ps", "x", 256).size, 256)

    def test_hex_round_trip(self):
        b = payload.payload_bits("A", "tm", "x", 100)
        self.assertTrue(np.array_equal(payload.hex_bits(payload.bits_hex(b), 100), b))
        self.assertEqual(payload.bits_hex(np.array([1, 0, 1, 1, 0, 0, 0, 1])), "b1")


class Search(unittest.TestCase):
    ids = ["a", "b", "c"]

    def test_outcomes(self):
        m = np.array([[1, 1, 1, 1], [0, 0, 0, 0], [1, 1, 0, 0]], dtype=np.uint8)
        r = run_mark.search(np.array([1, 1, 1, 1], dtype=np.uint8), m, self.ids, 4, "a")
        self.assertEqual((r["outcome"], r["entry"], r["agreeTrue"], r["agreeMaxOther"], r["agreeMaxOtherEntry"]), ("match", "a", 4, 2, "c"))
        r = run_mark.search(np.array([1, 1, 0, 1], dtype=np.uint8), m, self.ids, 4, "a")
        self.assertEqual(r["outcome"], "no-match")
        r = run_mark.search(np.array([1, 1, 0, 0], dtype=np.uint8), m, self.ids, 2, None)
        self.assertEqual(r["outcome"], "ambiguous")
        self.assertEqual(r["accepted"], [["a", 2], ["b", 2], ["c", 4]])

    def test_validate_query(self):
        q = {"id": "x", "scheme": "tm", "condition": "clean", "kind": "positive", "key": "A", "sha256": "0" * 64,
             "byteLength": 1, "decode": {"status": "ok"}, "rawBits": "0" * 25, "accepted": [["a", 80]],
             "outcome": "match", "entry": "a"}
        self.assertEqual(run_mark.validate_query(q, 74, 100), [])
        self.assertTrue(run_mark.validate_query(dict(q, accepted=[["a", 70]]), 74, 100))
        self.assertTrue(run_mark.validate_query(dict(q, outcome="no-match"), 74, 100))
        self.assertTrue(run_mark.validate_query(dict(q, extra=1), 74, 100))


class Environment(unittest.TestCase):
    def test_generator_goldens(self):
        self.assertEqual(env.generator_goldens()["matched"], 3)

    def test_redact(self):
        self.assertEqual(env.redact(os.path.join(HERE, ".venv", "bin", "python")), os.path.join(".venv", "bin", "python"))
        self.assertTrue(env.redact(os.path.join(os.path.expanduser("~"), "x", "y")).startswith("~/"))

    def test_protocol_digest_self_excluding(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "p.md")
            body = "x\nProtocol digest (SHA-256, self-excluding): `" + "0" * 64 + "`\ny\n"
            open(p, "w").write(body)
            _, computed = env.protocol_digest(p)
            open(p, "w").write(body.replace("0" * 64, computed))
            self.assertEqual(env.protocol_digest(p), (computed, computed))

    def test_probe_shape(self):
        denied, detail = env.network_denied()
        self.assertIsInstance(denied, bool)
        self.assertIn("loopback connect", detail)

    def test_weights_refused_on_mismatch(self):
        old = os.environ.get("TRACEWEAVE_EVAL_DIR")
        with tempfile.TemporaryDirectory() as d:
            os.environ["TRACEWEAVE_EVAL_DIR"] = d
            try:
                e = env.weight_manifest()["trustmark-Q-config"]
                p = os.path.join(d, "models", e["path"])
                os.makedirs(os.path.dirname(p))
                with open(p, "wb") as fh:
                    fh.write(b"x" * e["size"])
                with self.assertRaises(env.WeightError):
                    env.weight_path("trustmark-Q-config")
            finally:
                if old is None:
                    del os.environ["TRACEWEAVE_EVAL_DIR"]
                else:
                    os.environ["TRACEWEAVE_EVAL_DIR"] = old

    def test_fetch_refuses_work_tree(self):
        self.assertIsNotNone(fetch_weights.inside_work_tree(os.path.join(HERE, "out", "models")))
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(fetch_weights.inside_work_tree(os.path.realpath(d)))

    def test_stubs_fail_on_use(self):
        env.install_stubs()
        import av  # noqa: F401
        from pycocotools import mask

        with self.assertRaises(env.StubUsed):
            av.open
        with self.assertRaises(env.StubUsed):
            mask.decode


class Attacks(unittest.TestCase):
    def setUp(self):
        from twimg import generator

        self.rgb = generator.generate(SMOKE)

    def test_transplant_arithmetic(self):
        c = np.full((2, 2, 3), 100, np.uint8)
        m = c.copy()
        m[0, 0, 0] = 103
        h = np.full((2, 2, 3), 254, np.uint8)
        t = attacks.transplant(m, c, h)
        self.assertEqual(int(t[0, 0, 0]), 255)
        self.assertEqual(int(t[1, 1, 1]), 254)

    def test_attack_outputs(self):
        h, w = self.rgb.shape[:2]
        for data in (attacks.regen(self.rgb), attacks.rotate5(self.rgb), attacks.noise_jpeg(self.rgb, SMOKE), attacks.jpeg(self.rgb, 10)):
            self.assertEqual(attacks.decode(data).shape, (h, w, 3))
        self.assertEqual(attacks.noise_jpeg(self.rgb, SMOKE), attacks.noise_jpeg(self.rgb, SMOKE))
        self.assertNotEqual(attacks.noise_jpeg(self.rgb, SMOKE), attacks.noise_jpeg(self.rgb, SMOKE + 1))

    def test_decode_abstains(self):
        from PIL import Image

        b = io.BytesIO()
        Image.new("L", (4, 4)).save(b, format="PNG")
        with self.assertRaises(attacks.Abstain):
            attacks.decode(b.getvalue())
        with self.assertRaises(attacks.Abstain):
            attacks.decode(b"not an image")

    def test_psnr(self):
        a = np.zeros((2, 2, 3), np.uint8)
        b = a.copy()
        b[0, 0, 0] = 255
        self.assertAlmostEqual(attacks.psnr(a, b), 10.0 * np.log10(12), places=3)
        self.assertIsNone(attacks.psnr(a, a))


@unittest.skipUnless(os.environ.get("E_IMG_M_SKIP_MODELS") != "1", "model tests disabled")
class Models(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from twimg import generator

        from twmark import schemes

        cls.schemes = schemes
        cls.rgb = generator.generate(SMOKE)  # 512x512

    def test_trustmark_round_trip_and_raw_bits_match_upstream(self):
        tm = self.schemes.TrustMarkQ()
        for key in ("A", "B"):
            ok, data, ver = tm.bch(tm.payload(key, "m1"))
            self.assertEqual((ok, ver, data), (True, 1, "".join(map(str, tm.data(key, "m1")))))
        m1 = tm.embed(self.rgb, "A", "m1")
        self.assertTrue(np.array_equal(m1, tm.embed(self.rgb, "A", "m1")))  # deterministic in process
        from PIL import Image

        raw = tm.raw_bits(m1)
        up = tm.tm.decode(Image.fromarray(m1, "RGB"), MODE="binary")
        self.assertEqual(tm.bch(raw), (bool(up[1]), str(up[0]), int(up[2])))
        self.assertGreaterEqual(payload.agreement(raw, tm.payload("A", "m1")), payload.k_for(100))
        self.assertEqual(tm.remove(m1).shape, m1.shape)

    def test_pixelseal_round_trip_without_stub_use(self):
        ps = self.schemes.PixelSeal()  # installs the stubs; any use would raise StubUsed
        self.assertIn("All keys matched", ps.load_message)
        m1 = ps.embed(self.rgb, "A", "m1")
        self.assertEqual(m1.shape, self.rgb.shape)
        self.assertTrue(np.array_equal(m1, ps.embed(self.rgb, "A", "m1")))
        self.assertGreaterEqual(payload.agreement(ps.raw_bits(m1), ps.payload("A", "m1")), payload.k_for(256))
        self.assertIsInstance(sys.modules["av"], env._Stub)

    def test_dwtdct_runs(self):
        dw = self.schemes.DwtDct()
        m1 = dw.embed(self.rgb, "A", "m1")
        self.assertEqual(dw.raw_bits(m1).shape, (32,))
        self.assertTrue(np.array_equal(m1, dw.embed(self.rgb, "A", "m1")))


if __name__ == "__main__":
    unittest.main()
