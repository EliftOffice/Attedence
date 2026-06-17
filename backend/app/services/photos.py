"""Member face-thumbnail storage. These thumbnails are retained with the member's
facial profile (unlike visitor crops, which are deleted on review) and are shown
in the Visitor Review page so a leader can compare faces visually.
"""
from __future__ import annotations

import os
import shutil
import uuid

import cv2
import numpy as np

from app.config import settings


def _dest_path() -> str:
    os.makedirs(settings.member_photo_dir, exist_ok=True)
    return os.path.join(settings.member_photo_dir, f"{uuid.uuid4().hex}.jpg")


def save_member_image(image_bgr: np.ndarray | None) -> str | None:
    """Persist a member image (the full uploaded photo, normalized to JPEG) to the
    server filesystem. Only the returned PATH is stored in the DB — never the bytes."""
    if image_bgr is None or image_bgr.size == 0:
        return None
    path = _dest_path()
    cv2.imwrite(path, image_bgr)
    return path


# Back-compat alias (used where only a face crop is available).
save_member_thumbnail = save_member_image


def copy_to_member_thumbnail(src_path: str | None) -> str | None:
    """Copy an existing crop file (e.g. a visitor crop being promoted) into the
    retained member-photo store, returning the new path."""
    if not src_path or not os.path.exists(src_path):
        return None
    path = _dest_path()
    shutil.copyfile(src_path, path)
    return path
