from pydantic import BaseModel


class GroupAttendanceRow(BaseModel):
    meeting_id: int
    meeting_date: object
    present: int
    guests: int


class MemberAttendanceSummary(BaseModel):
    member_id: int
    name: str
    meetings_held: int
    meetings_attended: int
    attendance_pct: float


class VisitorStats(BaseModel):
    total_visitor_entries: int
    pending: int
    kept: int
    promoted: int
    mapped: int


class GrowthPoint(BaseModel):
    period: str  # e.g. "2026-06"
    members: int


class AbsenteeRow(BaseModel):
    member_id: int
    name: str
    last_attended: object | None
    meetings_missed_in_row: int
