from pydantic import BaseModel


class SettingsOut(BaseModel):
    telegram_bot_token: str | None = None  # masked for display
    telegram_token_set: bool = False
    telegram_match_field: str | None = None
    telegram_reply_mode: str | None = None
    face_match_threshold: float | None = None
    face_det_score_min: float | None = None
    face_min_pixels: int | None = None
    face_max_yaw_deg: float | None = None
    face_blur_var_min: float | None = None
    discard_low_quality: bool | None = None
    max_photo_age_days: int | None = None


class SettingsUpdate(BaseModel):
    # All optional; only provided fields are changed. Empty token string is ignored
    # (so saving other fields doesn't wipe the token).
    telegram_bot_token: str | None = None
    telegram_match_field: str | None = None
    telegram_reply_mode: str | None = None
    face_match_threshold: float | None = None
    face_det_score_min: float | None = None
    face_min_pixels: int | None = None
    face_max_yaw_deg: float | None = None
    face_blur_var_min: float | None = None
    discard_low_quality: bool | None = None
    max_photo_age_days: int | None = None
