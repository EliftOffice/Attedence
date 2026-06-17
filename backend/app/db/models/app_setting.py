"""Key-value runtime settings, editable by admins from the dashboard.

These override the .env defaults so config (Telegram token, recognition thresholds,
etc.) can be changed without a redeploy. See app/services/config_store.py.
"""
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class AppSetting(Base, TimestampMixin):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(nullable=True)
