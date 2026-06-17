"""Attendance + meeting helpers."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AttendanceRecord, Meeting


def get_or_create_meeting(
    db: Session, *, bsg_id: int, meeting_date: date, source: str
) -> Meeting:
    meeting = db.scalar(
        select(Meeting).where(Meeting.bsg_id == bsg_id, Meeting.meeting_date == meeting_date)
    )
    if meeting is None:
        meeting = Meeting(bsg_id=bsg_id, meeting_date=meeting_date, source=source)
        db.add(meeting)
        db.flush()
    return meeting


def mark_present(
    db: Session,
    *,
    meeting: Meeting,
    member_id: int,
    confidence: float | None,
    method: str,
    is_guest: bool,
) -> AttendanceRecord:
    """Idempotent: present-once per (meeting, member). Returns existing or new record."""
    existing = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.meeting_id == meeting.id,
            AttendanceRecord.member_id == member_id,
        )
    )
    if existing:
        return existing
    rec = AttendanceRecord(
        meeting_id=meeting.id,
        member_id=member_id,
        confidence=confidence,
        method=method,
        is_guest=is_guest,
    )
    db.add(rec)
    db.flush()
    return rec
