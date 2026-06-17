"""DB-backed runtime settings with .env fallbacks.

Admins edit these from the dashboard; they take effect without a redeploy:
  - API recognition reads a fresh threshold snapshot at the start of each run.
  - leader_resolver reads the Telegram match field per message.
  - The Telegram bot reads the token/reply mode at startup and restarts when the
    token changes (see app/telegram/bot.py).

Any key absent from the DB falls back to the corresponding .env value.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import settings as env
from app.db.models import AppSetting
from app.db.session import SessionLocal

# Editable keys -> default value (string), sourced from .env.
DEFAULTS: dict[str, str] = {
    "telegram_bot_token": env.telegram_bot_token,
    "telegram_match_field": env.telegram_match_field,
    "telegram_reply_mode": env.telegram_reply_mode,
    "face_match_threshold": str(env.face_match_threshold),
    "face_det_score_min": str(env.face_det_score_min),
    "face_min_pixels": str(env.face_min_pixels),
    "face_max_yaw_deg": str(env.face_max_yaw_deg),
    "face_blur_var_min": str(env.face_blur_var_min),
    # When "false" (default), low-quality faces are NOT discarded — they flow to the
    # Visitors screen so a leader can mark attendance manually. Set "true" to drop them.
    "discard_low_quality": "false",
    # Reject group photos whose EXIF capture date is this many days old or more.
    "max_photo_age_days": str(env.max_photo_age_days),
}


def get_bool(key: str, db: Session | None = None) -> bool:
    return str(get(key, db)).strip().lower() in ("1", "true", "yes")

# Keys that must never be sent to non-admin clients / logged.
SECRET_KEYS = {"telegram_bot_token"}


@dataclass
class RecognitionConfig:
    match_threshold: float
    det_score_min: float
    min_pixels: int
    max_yaw_deg: float
    blur_var_min: float


def _get_raw(db: Session, key: str) -> str | None:
    row = db.get(AppSetting, key)
    if row is not None and row.value is not None and row.value != "":
        return row.value
    return DEFAULTS.get(key)


def get(key: str, db: Session | None = None) -> str | None:
    if db is not None:
        return _get_raw(db, key)
    with SessionLocal() as own:
        return _get_raw(own, key)


def get_all(db: Session) -> dict[str, str | None]:
    return {k: _get_raw(db, k) for k in DEFAULTS}


def set_many(db: Session, values: dict[str, str]) -> None:
    for key, value in values.items():
        if key not in DEFAULTS:
            continue
        row = db.get(AppSetting, key)
        if row is None:
            db.add(AppSetting(key=key, value=value))
        else:
            row.value = value
    db.commit()


def seed(db: Session) -> None:
    """Insert default rows for any missing keys (idempotent)."""
    changed = False
    for key, default in DEFAULTS.items():
        if db.get(AppSetting, key) is None:
            db.add(AppSetting(key=key, value=default))
            changed = True
    if changed:
        db.commit()


def recognition_config(db: Session) -> RecognitionConfig:
    """Snapshot the recognition thresholds (read once per recognition run)."""
    return RecognitionConfig(
        match_threshold=float(_get_raw(db, "face_match_threshold")),
        det_score_min=float(_get_raw(db, "face_det_score_min")),
        min_pixels=int(float(_get_raw(db, "face_min_pixels"))),
        max_yaw_deg=float(_get_raw(db, "face_max_yaw_deg")),
        blur_var_min=float(_get_raw(db, "face_blur_var_min")),
    )
