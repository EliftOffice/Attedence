"""Quality gate — discards detections that shouldn't count (OPEN DECISION, all
thresholds from config): tiny faces, side-profiles, blurred crops, low detector score.
"""
from __future__ import annotations

import cv2
import numpy as np

from app.services.config_store import RecognitionConfig
from app.services.face.engine import DetectedFace


def laplacian_variance(crop_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def quality_reject_reason(face: DetectedFace, cfg: RecognitionConfig) -> str | None:
    """Return a reason string if the face should be discarded, else None.
    Thresholds come from the admin-editable config snapshot."""
    if face.det_score < cfg.det_score_min:
        return "low_det_score"
    if min(face.width, face.height) < cfg.min_pixels:
        return "too_small"
    if abs(face.yaw_deg) > cfg.max_yaw_deg:
        return "side_profile"
    if face.blur_var < cfg.blur_var_min:
        return "blurry"
    return None
