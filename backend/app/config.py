"""Central application settings.

Every OPEN-DECISION knob lives here (env-driven), never hard-coded at call sites:
  - Face match / quality thresholds
  - Telegram identity match field (user_id vs chat_id) and reply mode
There is intentionally NO visitor-retention window: visitor crops are held only
until a leader reviews them, then deleted (see services/visitors.py).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://attendance:attendance@localhost:5432/attendance"

    # Auth
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720

    # Bootstrap admin
    bootstrap_admin_mobile: str = "+910000000000"
    bootstrap_admin_password: str = "admin12345"
    bootstrap_admin_name: str = "System Admin"

    # Face recognition thresholds (OPEN DECISION: confidence + quality)
    face_match_threshold: float = 0.45
    # Detector already drops faces below ~0.50; keep this <= that so we don't
    # create a dead zone that discards detected close-up faces.
    face_det_score_min: float = 0.50
    face_min_pixels: int = 40
    face_max_yaw_deg: float = 45.0
    # Variance-of-Laplacian floor. Messaging apps (WhatsApp/Telegram) recompress
    # photos, which lowers this metric for sharp faces (~20), so keep it low.
    face_blur_var_min: float = 10.0
    insightface_model: str = "buffalo_l"
    insightface_providers: str = "CPUExecutionProvider"
    # Reject group photos whose capture date (EXIF) is this many days old or more.
    max_photo_age_days: int = 7

    # Telegram
    telegram_bot_token: str = ""
    # OPEN DECISION #5 — switch identity matching in ONE place.
    telegram_match_field: str = "user_id"  # user_id | chat_id
    telegram_reply_mode: str = "minimal"  # minimal | silent | private

    # Storage
    visitor_crop_dir: str = "./var/visitor_crops"
    # Member face thumbnails (retained with the profile, shown in Visitor Review).
    member_photo_dir: str = "./var/member_photos"

    # CORS
    cors_origins: str = "http://localhost:4200"

    @property
    def insightface_provider_list(self) -> list[str]:
        return [p.strip() for p in self.insightface_providers.split(",") if p.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
