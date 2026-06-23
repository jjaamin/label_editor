from __future__ import annotations
import os
from typing import List, Tuple

import cv2
import numpy as np

ENCODER_FILENAME = "edge_sam_3x_encoder.onnx"
DECODER_FILENAME = "edge_sam_3x_decoder.onnx"
WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "weights")
ENCODER_PATH = os.path.join(WEIGHTS_DIR, ENCODER_FILENAME)
DECODER_PATH = os.path.join(WEIGHTS_DIR, DECODER_FILENAME)

_PIXEL_MEAN = np.array([123.675, 116.28, 103.53], dtype=np.float32)[None, :, None, None]
_PIXEL_STD  = np.array([58.395,  57.12,  57.375],  dtype=np.float32)[None, :, None, None]
_IMG_SIZE   = 1024


def is_installed() -> bool:
    try:
        import onnxruntime  # noqa: F401
        return True
    except ImportError:
        return False


class _ResizeLongestSide:
    def __init__(self, target: int = _IMG_SIZE) -> None:
        self._target = target

    def new_hw(self, h: int, w: int) -> Tuple[int, int]:
        scale = self._target / max(h, w)
        return int(h * scale + 0.5), int(w * scale + 0.5)

    def apply_image(self, image: np.ndarray) -> np.ndarray:
        nh, nw = self.new_hw(*image.shape[:2])
        return cv2.resize(image, (nw, nh))

    def apply_coords(self, coords: np.ndarray, orig_hw: Tuple[int, int]) -> np.ndarray:
        oh, ow = orig_hw
        nh, nw = self.new_hw(oh, ow)
        out = coords.copy().astype(np.float32)
        out[..., 0] *= nw / ow
        out[..., 1] *= nh / oh
        return out


class EdgeSAMPredictor:
    """ONNX Runtime based EdgeSAM predictor — no torch/mmdet/mmcv required."""

    def __init__(self, encoder_path: str, decoder_path: str) -> None:
        import onnxruntime as ort

        # Make cuDNN discoverable for onnxruntime by adding PyTorch's lib dir to PATH.
        # PyTorch bundles cudnn64_9.dll which onnxruntime-gpu 1.20+ needs.
        try:
            import torch, os
            torch_lib = os.path.join(os.path.dirname(torch.__file__), "lib")
            if torch_lib not in os.environ.get("PATH", ""):
                os.environ["PATH"] = torch_lib + os.pathsep + os.environ.get("PATH", "")
        except ImportError:
            pass

        providers = []
        if "CUDAExecutionProvider" in ort.get_available_providers():
            providers.append("CUDAExecutionProvider")
        providers.append("CPUExecutionProvider")

        self._enc = ort.InferenceSession(encoder_path, providers=providers)
        self._dec = ort.InferenceSession(decoder_path, providers=providers)
        self._tf  = _ResizeLongestSide()
        self._features:   np.ndarray | None = None
        self._input_size: Tuple[int, int]   = (0, 0)
        self._orig_size:  Tuple[int, int]   = (0, 0)

    @property
    def device(self) -> str:
        p = self._enc.get_providers()
        return "CUDA" if "CUDAExecutionProvider" in p else "CPU"

    def set_image(self, image_rgb: np.ndarray) -> None:
        h, w = image_rgb.shape[:2]
        self._orig_size = (h, w)

        resized = self._tf.apply_image(image_rgb)
        self._input_size = resized.shape[:2]   # (nh, nw)

        # NCHW float32, normalise, pad to IMG_SIZE × IMG_SIZE
        x = resized.astype(np.float32).transpose(2, 0, 1)[np.newaxis]
        x = (x - _PIXEL_MEAN) / _PIXEL_STD
        pad_h = _IMG_SIZE - resized.shape[0]
        pad_w = _IMG_SIZE - resized.shape[1]
        x = np.pad(x, ((0, 0), (0, 0), (0, pad_h), (0, pad_w)))

        self._features = self._enc.run(None, {"image": x})[0]

    def predict(
        self,
        points: List[Tuple[int, int]],
        labels: List[int],
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Return (masks [3,H,W] bool, scores [3] float32).

        The ONNX decoder outputs 4 candidates; index 0 is the single-mask
        best pick, indices 1-3 are the small/medium/large multi-mask set.
        We return only indices 1-3 to match the 3-option UI slider.
        """
        coords = self._tf.apply_coords(
            np.array(points, dtype=np.float32), self._orig_size
        )
        # Decoder expects batch dim: [1, N, 2] and [1, N]
        coords = coords[np.newaxis]
        lbls = np.array(labels, dtype=np.float32)[np.newaxis]

        out = self._dec.run(None, {
            "image_embeddings": self._features,
            "point_coords":     coords,
            "point_labels":     lbls,
        })
        scores  = out[0][0]   # (4,) — remove batch dim
        low_res = out[1][0]   # (4, 256, 256) — remove batch dim

        # Use multi-mask candidates (skip index 0 = single-mask output)
        scores  = scores[1:]    # (3,)
        low_res = low_res[1:]   # (3, 256, 256)

        # Upsample: 256×256 → IMG_SIZE → crop to input_size → orig_size
        ih, iw = self._input_size
        oh, ow = self._orig_size
        stacked = low_res.transpose(1, 2, 0)           # (256, 256, 3)
        m = cv2.resize(stacked, (_IMG_SIZE, _IMG_SIZE), interpolation=cv2.INTER_LINEAR)
        m = m[:ih, :iw]
        m = cv2.resize(m, (ow, oh), interpolation=cv2.INTER_LINEAR)
        if m.ndim == 2:                                 # single-point edge case
            m = m[:, :, np.newaxis]
        masks = (m > 0).transpose(2, 0, 1)             # (3, oh, ow) bool

        return masks, scores
