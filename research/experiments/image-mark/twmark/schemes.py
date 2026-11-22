"""Adapters for the three marking schemes of e-img-m-2 (protocol §4).

Each adapter exposes:
  name                         scheme id
  n_raw, n                     raw decoded bits, and the bits tested by the decision rule (protocol §5)
  payload(key_id, entry)       the n expected tested bits (np.uint8 0/1): exactly the HMAC output
  tested(raw)                  the n tested positions of the n_raw raw bits
  embed(rgb, key_id, entry)    marked RGB uint8 array of the same shape
  embed_bits(rgb, bits)        the same with explicit encoder input bits (used by the keyless forgery)
  forge_bits(raw)              what a keyless attacker re-embeds after decoding raw bits
  raw_bits(rgb)                n_raw raw decoded bits (np.uint8 0/1), before any error correction
TrustMark also exposes transmitted(key_id, entry) (its 100 BCH-coded bits), bch(raw) (the blind
BCH result, reported but never used to decide) and remove(rgb) (the authors' ReMark remover, used
as a removal attack on every scheme).

Upstream code runs unmodified from third_party/ at the pinned commits. Nothing here downloads:
model files come only from weight_path(), which checks size and SHA-256 first.
"""
from __future__ import annotations

import contextlib
import io

import numpy as np
from PIL import Image

from . import env  # noqa: F401  (sys.path, stubs and offline settings first)
from .env import weight_path
from .payload import payload_bits

import cv2  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(4)
torch.set_num_interop_threads(1)
torch.use_deterministic_algorithms(True)
cv2.setNumThreads(0)  # GCD backend: 0 disables parallel regions (getNumThreads() then reports 1); 1 is ignored
DEVICE = torch.device("cpu")


def _rgb(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a)
    if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] != 3:
        raise ValueError("expected an HxWx3 uint8 RGB array")
    return a


# --------------------------------------------------------------------------- TrustMark, variant Q


class TrustMarkQ:
    name = "tm"
    n_raw = 100  # BCH_5: 61 data + 35 ECC + 4 version bits = 100 transmitted
    n = 61  # tested: raw positions 0-60, the data bits. ECC bits are a function of them and the 4
    # version bits are the same for every payload, so neither is an independent fair coin (review B1)
    data_bits = 61

    def __init__(self, load_remover: bool = True):
        from trustmark import trustmark as tmmod

        paths = {
            "config": weight_path("trustmark-Q-config"),
            "encoder": weight_path("trustmark-Q-encoder"),
            "decoder": weight_path("trustmark-Q-decoder"),
        }
        if load_remover:
            paths["config-rm"] = weight_path("trustmark-Q-remover-config")
            paths["remover"] = weight_path("trustmark-Q-remover")
        verified = frozenset(paths.values())

        class _NoDownload(tmmod.TrustMark):
            _verified: frozenset = frozenset()

            def check_and_download(self, filename):  # upstream would fetch from the model host
                if filename not in self._verified:
                    raise env.WeightError(f"download refused for {filename}")

        # Upstream __init__ sets every attribute; its own model loads fail here (download refused,
        # upstream prints the error and stores None). The models are then loaded with the upstream
        # load_model from the verified paths.
        with contextlib.redirect_stdout(io.StringIO()):
            tm = _NoDownload(use_ECC=True, verbose=False, secret_len=self.n_raw, device="cpu", model_type="Q",
                             encoding_type=tmmod.TrustMark.Encoding.BCH_5, loadRemover=False)
        if tm.encoder is not None or tm.decoder is not None:
            raise RuntimeError("upstream constructor loaded a model from its package directory")
        tm._verified = verified
        tm.decoder = tm.load_model(paths["config"], paths["decoder"], "cpu", self.n_raw, part="decoder")
        tm.encoder = tm.load_model(paths["config"], paths["encoder"], "cpu", self.n_raw, part="encoder")
        if load_remover:
            tm.removal = tm.load_model(paths["config-rm"], paths["remover"], "cpu", self.n_raw, part="remover")
        if tm.decoder is None or tm.encoder is None or (load_remover and tm.removal is None):
            raise RuntimeError("TrustMark model load failed")
        self.tm = tm
        self.ecc = tm.ecc

    def data(self, key_id: str, entry: str) -> np.ndarray:
        return payload_bits(key_id, self.name, entry, self.data_bits)

    def payload(self, key_id: str, entry: str) -> np.ndarray:
        return self.data(key_id, entry)

    def tested(self, raw: np.ndarray) -> np.ndarray:
        return raw[: self.data_bits]

    def transmitted(self, key_id: str, entry: str) -> np.ndarray:
        d = self.data(key_id, entry)
        packet = self.ecc.encode_binary(["".join(map(str, d))])[0]
        return packet.astype(np.uint8)

    def embed_bits(self, rgb: np.ndarray, bits: np.ndarray) -> np.ndarray:
        if bits.size != self.data_bits:  # upstream process_encode silently truncates or pads (lane 08)
            raise ValueError("data length")
        out = self.tm.encode(Image.fromarray(_rgb(rgb), "RGB"), "".join(map(str, bits)), MODE="binary")
        return np.asarray(out.convert("RGB"), dtype=np.uint8)

    def embed(self, rgb: np.ndarray, key_id: str, entry: str) -> np.ndarray:
        return self.embed_bits(rgb, self.data(key_id, entry))

    def forge_bits(self, raw: np.ndarray) -> tuple[np.ndarray, str]:
        """A keyless attacker's best reading: the BCH-corrected data bits if BCH succeeds, else the
        raw data positions."""
        ok, data, ver = self.bch(raw)
        if ok and ver == 1 and len(data) == self.data_bits:
            return np.array([int(c) for c in data], dtype=np.uint8), "bch"
        return raw[: self.data_bits].copy(), "raw"

    @torch.no_grad()
    def raw_bits(self, rgb: np.ndarray) -> np.ndarray:
        """Upstream decode() up to the sign of the decoder output (no detector, no rotation)."""
        from torchvision import transforms

        tm = self.tm
        img = tm.get_the_image_for_processing(Image.fromarray(_rgb(rgb), "RGB"))
        img = img.resize((tm.model_resolution_dec, tm.model_resolution_dec), Image.BILINEAR)
        x = transforms.ToTensor()(img).unsqueeze(0).to(DEVICE) * 2.0 - 1.0
        return (tm.decoder.decoder(x) > 0).cpu().numpy()[0].astype(np.uint8)

    def bch(self, raw: np.ndarray) -> tuple[bool, str, int]:
        """Blind decode as upstream reports it: (bchValid, data bit string, version)."""
        data, ok, version = self.ecc.decode_bitstream(raw[None, :].astype(np.float32), "binary")[0]
        return bool(ok), str(data), int(version)

    @torch.no_grad()
    def remove(self, rgb: np.ndarray) -> np.ndarray:
        out = self.tm.remove_watermark(Image.fromarray(_rgb(rgb), "RGB"))
        return np.asarray(out.convert("RGB"), dtype=np.uint8)


# --------------------------------------------------------------------------- PixelSeal


class PixelSeal:
    name = "ps"
    n_raw = n = 256  # every payload bit is tested; the detection bit (preds[:, 0]) is not

    def __init__(self):
        import os

        from omegaconf import OmegaConf

        env.install_stubs()
        from videoseal.utils.cfg import setup_model

        card = os.path.join(env.THIRD, "videoseal", "videoseal", "cards", "pixelseal.yaml")
        config = OmegaConf.load(card)
        config.args.attenuation_config = os.path.join(env.THIRD, "videoseal", "configs", "attenuation.yaml")
        ckpt = weight_path("pixelseal")
        with contextlib.redirect_stdout(io.StringIO()) as log:
            model = setup_model(config, ckpt)
        self.load_message = log.getvalue().strip()
        model.eval()
        self.model = model.to(DEVICE)

    def payload(self, key_id: str, entry: str) -> np.ndarray:
        return payload_bits(key_id, self.name, entry, self.n)

    @staticmethod
    def _to_tensor(rgb: np.ndarray) -> torch.Tensor:
        return torch.from_numpy(_rgb(rgb).astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0)

    def tested(self, raw: np.ndarray) -> np.ndarray:
        return raw

    def forge_bits(self, raw: np.ndarray) -> tuple[np.ndarray, str]:
        return raw.copy(), "raw"

    def embed(self, rgb: np.ndarray, key_id: str, entry: str) -> np.ndarray:
        return self.embed_bits(rgb, self.payload(key_id, entry))

    @torch.no_grad()
    def embed_bits(self, rgb: np.ndarray, bits: np.ndarray) -> np.ndarray:
        if bits.size != self.n:
            raise ValueError("payload length")
        msg = torch.from_numpy(bits.astype(np.float32)).unsqueeze(0)
        out = self.model.embed(self._to_tensor(rgb), msgs=msg, is_video=False)["imgs_w"]
        q = torch.round(out.clamp(0, 1) * 255.0)  # round half to even
        return q[0].permute(1, 2, 0).to(torch.uint8).numpy()

    @torch.no_grad()
    def raw_bits(self, rgb: np.ndarray) -> np.ndarray:
        preds = self.model.detect(self._to_tensor(rgb), is_video=False)["preds"]  # b x (1+nbits)
        if preds.shape != (1, 1 + self.n):  # the pinned card's pixel decoder is not pixelwise
            raise RuntimeError(f"unexpected PixelSeal output shape {tuple(preds.shape)}")
        return (preds[0, 1:] > 0).cpu().numpy().astype(np.uint8)


# --------------------------------------------------------------------------- dwtDct negative control


class DwtDct:
    """invisible-watermark `dwtDct` (lane 10 F5): no key, no ECC, always emits bits. Control only."""

    name = "dw"
    n_raw = n = 32
    min_pixels = 256 * 256  # upstream raises below this

    def __init__(self):
        from imwatermark import WatermarkDecoder, WatermarkEncoder

        self._enc, self._dec = WatermarkEncoder, WatermarkDecoder

    def payload(self, key_id: str, entry: str) -> np.ndarray:
        return payload_bits(key_id, self.name, entry, self.n)

    def tested(self, raw: np.ndarray) -> np.ndarray:
        return raw

    def forge_bits(self, raw: np.ndarray) -> tuple[np.ndarray, str]:
        return raw.copy(), "raw"

    def embed(self, rgb: np.ndarray, key_id: str, entry: str) -> np.ndarray:
        return self.embed_bits(rgb, self.payload(key_id, entry))

    def embed_bits(self, rgb: np.ndarray, bits: np.ndarray) -> np.ndarray:
        if bits.size != self.n:
            raise ValueError("payload length")
        enc = self._enc()
        enc.set_watermark("bits", [int(b) for b in bits])
        bgr = np.ascontiguousarray(_rgb(rgb)[:, :, ::-1])
        out = np.asarray(enc.encode(bgr, "dwtDct"))
        out = np.clip(np.rint(out.astype(np.float64)), 0, 255).astype(np.uint8)
        return np.ascontiguousarray(out[:, :, ::-1])

    def raw_bits(self, rgb: np.ndarray) -> np.ndarray:
        bgr = np.ascontiguousarray(_rgb(rgb)[:, :, ::-1])
        bits = self._dec("bits", self.n).decode(bgr, "dwtDct")
        return np.asarray(bits, dtype=np.uint8).reshape(self.n)


SCHEMES = {"tm": TrustMarkQ, "ps": PixelSeal, "dw": DwtDct}
