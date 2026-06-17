"""Read a photo's capture date from EXIF and decide whether it's too old to use
for attendance.

Note: this relies on EXIF (DateTimeOriginal). Photos taken with a phone camera and
uploaded directly carry it; some chat apps (e.g. WhatsApp) strip EXIF on recompress.
When the capture date is unknown, we ALLOW the photo (can't prove it's stale).
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO

from PIL import Image

_EXIF_IFD = 0x8769
_DATETIME_ORIGINAL = 36867
_DATETIME_DIGITIZED = 36868
_DATETIME = 306  # base-IFD DateTime (fallback)


def photo_capture_datetime(data: bytes) -> datetime | None:
    """Best-effort EXIF capture timestamp, or None if unavailable/unparseable."""
    try:
        img = Image.open(BytesIO(data))
        exif = img.getexif()
        if not exif:
            return None
        raw = None
        try:
            ifd = exif.get_ifd(_EXIF_IFD)
            if ifd:
                raw = ifd.get(_DATETIME_ORIGINAL) or ifd.get(_DATETIME_DIGITIZED)
        except Exception:
            raw = None
        raw = raw or exif.get(_DATETIME)
        if not raw:
            return None
        return datetime.strptime(str(raw).strip(), "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None


def stale_reason(data: bytes, max_age_days: int) -> str | None:
    """Return a human message if the photo is `max_age_days` old or older, else None.
    Unknown capture date -> None (allowed)."""
    captured = photo_capture_datetime(data)
    if captured is None:
        return None
    age_days = (datetime.now() - captured).days
    if age_days >= max_age_days:
        return (
            f"This photo was taken on {captured.date()} ({age_days} days ago). "
            f"Only photos from the last {max_age_days} days can be used for attendance."
        )
    return None
