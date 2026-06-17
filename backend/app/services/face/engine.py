"""FaceEngine isolation seam.

Callers depend ONLY on this protocol + the DetectedFace dataclass, never on
InsightFace directly. Swap the implementation (insightface_engine, a Python
microservice, a cloud API) without touching the recognition pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np


@dataclass
class DetectedFace:
    embedding: np.ndarray  # L2-normalized float32, shape (512,)
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2
    det_score: float
    yaw_deg: float  # absolute head yaw estimate (0 = frontal)
    blur_var: float  # variance-of-Laplacian on the crop (higher = sharper)
    crop_bgr: np.ndarray | None = field(default=None, repr=False)  # for visitor storage

    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]


class FaceEngine(Protocol):
    def detect(self, image_bgr: np.ndarray) -> list[DetectedFace]:
        """Detect faces and return one DetectedFace per detection (no quality filtering)."""
        ...


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity for already L2-normalized embeddings (dot product)."""
    return float(np.dot(a, b))
