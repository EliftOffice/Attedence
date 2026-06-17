from datetime import date

from pydantic import BaseModel


class MemberCard(BaseModel):
    member_id: int
    name: str
    surname: str | None = None
    photo_url: str | None = None       # /api/v1/members/{id}/photo (load with auth)
    confidence: float | None = None    # for present-by-recognition
    is_guest: bool = False


class VisitorCard(BaseModel):
    id: int
    crop_url: str | None = None        # /api/v1/visitors/{id}/crop


class TodayOut(BaseModel):
    """Image-first 'today' view for a group: who is present, who is absent, and
    today's new (pending) visitors. UI compares faces, not names."""
    bsg_id: int
    bsg_name: str
    meeting_date: date
    meeting_id: int | None
    present: list[MemberCard]
    absent: list[MemberCard]
    new_visitors: list[VisitorCard]
