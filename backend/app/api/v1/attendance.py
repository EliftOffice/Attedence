"""Today view: present / absent / new visitors for a group, image-first.

Photo/crop URLs are returned so the mobile app shows FACES (load them with the
auth header). Present = members marked present at today's meeting; Absent = active
home members not present; New visitors = today's pending visitor entries.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models import (
    AttendanceRecord,
    BibleStudyGroup,
    BSGLeader,
    BSGMember,
    FacialProfilePhoto,
    Meeting,
    User,
    VisitorEntry,
)
from app.db.session import get_db
from app.schemas.today import MemberCard, TodayOut, VisitorCard

router = APIRouter(prefix="/attendance", tags=["attendance"])


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


def _has_photo(db: Session, member_id: int) -> bool:
    return bool(
        db.scalar(
            select(func.count(FacialProfilePhoto.id)).where(
                FacialProfilePhoto.member_id == member_id,
                FacialProfilePhoto.crop_path.is_not(None),
            )
        )
    )


def _member_card(db: Session, m: BSGMember, *, confidence=None, is_guest=False) -> MemberCard:
    return MemberCard(
        member_id=m.id, name=m.name, surname=m.surname,
        photo_url=f"/api/v1/members/{m.id}/photo" if _has_photo(db, m.id) else None,
        confidence=confidence, is_guest=is_guest,
    )


@router.get("/today", response_model=TodayOut)
def today(
    bsg_id: int | None = None,
    on: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bsg = _scope_bsg(db, user, bsg_id)
    group = db.get(BibleStudyGroup, bsg)
    day = on or date.today()

    meeting = db.scalar(
        select(Meeting).where(Meeting.bsg_id == bsg, Meeting.meeting_date == day)
    )

    present: list[MemberCard] = []
    present_ids: set[int] = set()
    new_visitors: list[VisitorCard] = []

    if meeting is not None:
        rows = db.execute(
            select(AttendanceRecord, BSGMember)
            .join(BSGMember, BSGMember.id == AttendanceRecord.member_id)
            .where(AttendanceRecord.meeting_id == meeting.id)
        ).all()
        for rec, member in rows:
            present_ids.add(member.id)
            present.append(
                _member_card(db, member, confidence=rec.confidence, is_guest=rec.is_guest)
            )

        visitors = db.scalars(
            select(VisitorEntry).where(
                VisitorEntry.meeting_id == meeting.id, VisitorEntry.status == "pending"
            )
        ).all()
        new_visitors = [
            VisitorCard(id=v.id, crop_url=f"/api/v1/visitors/{v.id}/crop" if v.face_crop_path else None)
            for v in visitors
        ]

    # Absent = active home members not present — but only meaningful once a
    # meeting exists for the day. With no meeting yet, nobody is "absent".
    absent: list[MemberCard] = []
    if meeting is not None:
        members = db.scalars(
            select(BSGMember).where(BSGMember.bsg_id == bsg, BSGMember.status == "active")
        ).all()
        absent = [_member_card(db, m) for m in members if m.id not in present_ids]

    return TodayOut(
        bsg_id=bsg, bsg_name=group.name, meeting_date=day,
        meeting_id=meeting.id if meeting else None,
        present=present, absent=absent, new_visitors=new_visitors,
    )
