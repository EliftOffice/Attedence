"""Reporting: attendance by group/member, percentages, visitor stats, growth, absentees.

Leaders see only their own group; admins may pass any bsg_id.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models import (
    AttendanceRecord,
    BSGLeader,
    BSGMember,
    Meeting,
    VisitorEntry,
    User,
)
from app.db.session import get_db
from app.schemas.report import (
    AbsenteeRow,
    GroupAttendanceRow,
    GrowthPoint,
    MemberAttendanceSummary,
    VisitorStats,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def _scope_bsg(db: Session, user: User, bsg_id: int | None) -> int:
    if user.role == "admin":
        if bsg_id is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "bsg_id required")
        return bsg_id
    leader = db.scalar(select(BSGLeader).where(BSGLeader.user_id == user.id))
    if not leader:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a leader")
    if bsg_id is not None and bsg_id != leader.bsg_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your group")
    return leader.bsg_id


@router.get("/group-attendance", response_model=list[GroupAttendanceRow])
def group_attendance(
    bsg_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bsg = _scope_bsg(db, user, bsg_id)
    rows = db.execute(
        select(
            Meeting.id,
            Meeting.meeting_date,
            func.count(AttendanceRecord.id).filter(AttendanceRecord.is_guest.is_(False)),
            func.count(AttendanceRecord.id).filter(AttendanceRecord.is_guest.is_(True)),
        )
        .outerjoin(AttendanceRecord, AttendanceRecord.meeting_id == Meeting.id)
        .where(Meeting.bsg_id == bsg)
        .group_by(Meeting.id, Meeting.meeting_date)
        .order_by(Meeting.meeting_date.desc())
    ).all()
    return [
        GroupAttendanceRow(meeting_id=mid, meeting_date=d, present=present, guests=guests)
        for mid, d, present, guests in rows
    ]


@router.get("/member-attendance", response_model=list[MemberAttendanceSummary])
def member_attendance(
    bsg_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bsg = _scope_bsg(db, user, bsg_id)
    meetings_held = db.scalar(select(func.count(Meeting.id)).where(Meeting.bsg_id == bsg)) or 0
    members = db.scalars(select(BSGMember).where(BSGMember.bsg_id == bsg)).all()
    out: list[MemberAttendanceSummary] = []
    for m in members:
        attended = db.scalar(
            select(func.count(AttendanceRecord.id))
            .join(Meeting, Meeting.id == AttendanceRecord.meeting_id)
            .where(
                Meeting.bsg_id == bsg,
                AttendanceRecord.member_id == m.id,
                AttendanceRecord.is_guest.is_(False),
            )
        ) or 0
        pct = round(100.0 * attended / meetings_held, 1) if meetings_held else 0.0
        out.append(
            MemberAttendanceSummary(
                member_id=m.id, name=m.name, meetings_held=meetings_held,
                meetings_attended=attended, attendance_pct=pct,
            )
        )
    return sorted(out, key=lambda r: r.attendance_pct, reverse=True)


@router.get("/visitor-stats", response_model=VisitorStats)
def visitor_stats(
    bsg_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bsg = _scope_bsg(db, user, bsg_id)

    def count(*statuses: str) -> int:
        q = (
            select(func.count(VisitorEntry.id))
            .join(Meeting, Meeting.id == VisitorEntry.meeting_id)
            .where(Meeting.bsg_id == bsg)
        )
        if statuses:
            q = q.where(VisitorEntry.status.in_(statuses))
        return db.scalar(q) or 0

    return VisitorStats(
        total_visitor_entries=count(),
        pending=count("pending"),
        kept=count("kept"),
        promoted=count("promoted"),
        mapped=count("mapped_same", "mapped_guest", "moved"),
    )


@router.get("/growth", response_model=list[GrowthPoint])
def growth(
    bsg_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cumulative members by month (based on join date)."""
    bsg = _scope_bsg(db, user, bsg_id)
    rows = db.execute(
        select(
            func.to_char(func.coalesce(BSGMember.joined_at, func.date(BSGMember.created_at)), "YYYY-MM"),
            func.count(BSGMember.id),
        )
        .where(BSGMember.bsg_id == bsg)
        .group_by(func.to_char(func.coalesce(BSGMember.joined_at, func.date(BSGMember.created_at)), "YYYY-MM"))
        .order_by(func.to_char(func.coalesce(BSGMember.joined_at, func.date(BSGMember.created_at)), "YYYY-MM"))
    ).all()
    cumulative = 0
    out: list[GrowthPoint] = []
    for period, n in rows:
        cumulative += n
        out.append(GrowthPoint(period=period, members=cumulative))
    return out


@router.get("/absentees", response_model=list[AbsenteeRow])
def absentees(
    bsg_id: int | None = None,
    min_missed: int = 3,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Members who have missed the last `min_missed` consecutive meetings."""
    bsg = _scope_bsg(db, user, bsg_id)
    meeting_dates = db.scalars(
        select(Meeting.meeting_date).where(Meeting.bsg_id == bsg).order_by(Meeting.meeting_date.desc())
    ).all()
    recent = meeting_dates[:min_missed]
    members = db.scalars(select(BSGMember).where(BSGMember.bsg_id == bsg)).all()
    out: list[AbsenteeRow] = []
    for m in members:
        attended_dates = set(
            db.scalars(
                select(Meeting.meeting_date)
                .join(AttendanceRecord, AttendanceRecord.meeting_id == Meeting.id)
                .where(Meeting.bsg_id == bsg, AttendanceRecord.member_id == m.id)
            ).all()
        )
        missed_in_row = 0
        for d in meeting_dates:
            if d in attended_dates:
                break
            missed_in_row += 1
        last_attended = max(attended_dates) if attended_dates else None
        if recent and missed_in_row >= min_missed:
            out.append(
                AbsenteeRow(
                    member_id=m.id, name=m.name,
                    last_attended=last_attended, meetings_missed_in_row=missed_in_row,
                )
            )
    return sorted(out, key=lambda r: r.meetings_missed_in_row, reverse=True)
