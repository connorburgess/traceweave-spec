"""Adapters for the three marking schemes of e-img-m-1 (protocol §4).

Each adapter exposes:
  name, n                      scheme id and number of transmitted bits tested by the decision rule
  payload(key_id, entry)       the n expected transmitted bits (np.uint8 0/1)
  embed(rgb, key_id, entry)    marked RGB uint8 array of the same shape
  raw_bits(rgb)                n raw decoded bits (np.uint8 0/1), before any error correction
TrustMark also exposes bch(raw) (the blind BCH result, reported but never used to decide) and
remove(rgb) (the authors' ReMark remover, used as a removal attack on every scheme).

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

import torch  # noqa: E402

torch.set_num_threads(4)
torch.use_deterministic_algorithms(True)
DEVICE = torch.device("cpu")


def _rgb(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a)
    if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] != 3:
        raise ValueError("expected an HxWx3 uint8 RGB array")
    return a


# --------------------------------------------------------------------------- TrustMark, variant Q


class TrustMarkQ:
    name = "tm"
    n = 100
    data_bits = 61  # BCH_5: 61 data + 35 ECC + 4 version bits = 100 transmitted

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
            tm = _NoDownload(use_ECC=True, verbose=False, secret_len=self.n, device="cpu", model_type="Q",
                             encoding_type=tmmod.TrustMark.Encoding.BCH_5, loadRemover=False)
        if tm.encoder is not None or tm.decoder is not None:
            raise RuntimeError("upstream constructor loaded a model from its package directory")
        tm._verified = verified
        tm.decoder = tm.load_model(paths["config"], paths["decoder"], "cpu", self.n, part="decoder")
        tm.encoder = tm.load_model(paths["config"], paths["encoder"], "cpu", self.n, part="encoder")
        if load_remover:
            tm.removal = tm.load_model(paths["config-rm"], paths["remover"], "cpu", self.n, part="remover")
        if tm.decoder is None or tm.encoder is None or (load_remover and tm.removal is None):
            raise RuntimeError("TrustMark model load failed")
        self.tm = tm
        self.ecc = tm.ecc

    def data(self, key_id: str, entry: str) -> np.ndarray:
        return payload_bits(key_id, self.name, entry, self.data_bits)

    def payload(self, key_id: str, entry: str) -> np.ndarray:
        d = self.data(key_id, entry)
        if d.size != self.data_bits:  # upstream process_encode silently truncates or pads (lane 08)
            raise ValueError("data length")
        packet = self.ecc.encode_binary(["".join(map(str, d))])[0]
        return packet.astype(np.uint8)

    def embed(self, rgb: np.ndarray, key_id: str, entry: str) -> np.ndarray:
        d = "".join(map(str, self.data(key_id, entry)))
        out = self.tm.encode(Image.fromarray(_rgb(rgb), "RGB"), d, MODE="binary")
        return np.asarray(out.convert("RGB"), dtype=np.uint8)

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
    n = 256

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

    @torch.no_grad()
    def embed(self, rgb: np.ndarray, key_id: str, entry: str) -> np.ndarray:
        msg = torch.from_numpy(self.payload(key_id, entry).astype(np.float32)).unsqueeze(0)
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
    n = 32
    min_pixels = 256 * 256  # upstream raises below this

    def __init__(self):
        from imwatermark import WatermarkDecoder, WatermarkEncoder

        self._enc, self._dec = WatermarkEncoder, WatermarkDecoder

    def payload(self, key_id: str, entry: str) -> np.ndarray:
        return payload_bits(key_id, self.name, entry, self.n)

    def embed(self, rgb: np.ndarray, key_id: str, entry: str) -> np.ndarray:
        enc = self._enc()
        enc.set_watermark("bits", [int(b) for b in self.payload(key_id, entry)])
        bgr = np.ascontiguousarray(_rgb(rgb)[:, :, ::-1])
        out = np.asarray(enc.encode(bgr, "dwtDct"))
        out = np.clip(np.rint(out.astype(np.float64)), 0, 255).astype(np.uint8)
        return np.ascontiguousarray(out[:, :, ::-1])

    def raw_bits(self, rgb: np.ndarray) -> np.ndarray:
        bgr = np.ascontiguousarray(_rgb(rgb)[:, :, ::-1])
        bits = self._dec("bits", self.n).decode(bgr, "dwtDct")
        return np.asarray(bits, dtype=np.uint8).reshape(self.n)


SCHEMES = {"tm": TrustMarkQ, "ps": PixelSeal, "dw": DwtDct}
