"""InsightFace implementation of FaceEngine (ArcFace 512-d embeddings).

Lazy-loaded singleton so the model pack loads once per process. The model is the
proven `buffalo_l` pack (RetinaFace detector + ArcFace recognition + pose).
"""
from __future__ import annotations

import math
import threading

import cv2
import numpy as np

from app.config import settings
from app.services.face.engine import DetectedFace
from app.services.face.quality import laplacian_variance

_lock = threading.Lock()
_app = None


def _get_app():
    global _app
    if _app is None:
        with _lock:
            if _app is None:
                from insightface.app import FaceAnalysis

                app = FaceAnalysis(
                    name=settings.insightface_model,
                    providers=settings.insightface_provider_list,
                )
                app.prepare(ctx_id=0, det_size=(640, 640))
                _app = app
    return _app


def _yaw_from_pose(face) -> float:
    """InsightFace exposes `.pose` as [pitch, yaw, roll] (degrees) when available."""
    pose = getattr(face, "pose", None)
    if pose is not None and len(pose) >= 2:
        return float(abs(pose[1]))
    # Fallback: estimate yaw from eye/nose landmark asymmetry.
    kps = getattr(face, "kps", None)
    if kps is not None and len(kps) >= 3:
        left_eye, right_eye, nose = kps[0], kps[1], kps[2]
        eye_mid_x = (left_eye[0] + right_eye[0]) / 2.0
        eye_dist = abs(right_eye[0] - left_eye[0]) or 1.0
        ratio = (nose[0] - eye_mid_x) / eye_dist
        return float(abs(math.degrees(math.atan(ratio * 2))))
    return 0.0


class InsightFaceEngine:
    def detect(self, image_bgr: np.ndarray) -> list[DetectedFace]:
        app = _get_app()
        faces = app.get(image_bgr)
        out: list[DetectedFace] = []
        h, w = image_bgr.shape[:2]
        for f in faces:
            x1, y1, x2, y2 = (int(v) for v in f.bbox)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            if x2 <= x1 or y2 <= y1:
                continue
            crop = image_bgr[y1:y2, x1:x2].copy()
            emb = np.asarray(f.normed_embedding, dtype=np.float32)  # already L2-normalized
            out.append(
                DetectedFace(
                    embedding=emb,
                    bbox=(x1, y1, x2, y2),
                    det_score=float(getattr(f, "det_score", 1.0)),
                    yaw_deg=_yaw_from_pose(f),
                    blur_var=laplacian_variance(crop) if crop.size else 0.0,
                    crop_bgr=crop,
                )
            )
        return out


def get_engine() -> InsightFaceEngine:
    """Single place the rest of the app gets a FaceEngine. Swap here to change impl."""
    return InsightFaceEngine()


def decode_image(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    return img
