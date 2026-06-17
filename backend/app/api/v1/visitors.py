"""Visitor Review — leader-facing. Scoped to the leader's own group's meetings.

Crops are served from a short-lived endpoint and deleted on resolution.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_leader
from app.db.models import BSGLeader, BSGMember, Meeting, VisitorEntry
from app.db.session import get_db
from app.schemas.visitor import (
    MapToMemberRequest,
    MemberSuggestion,
    PromoteNewMemberRequest,
    VisitorOut,
)
from app.services import visitors as visitor_svc

router = APIRouter(prefix="/visitors", tags=["visitors"])


def _load_own_pending_visitor(db: Session, leader: BSGLeader, visitor_id: int) -> VisitorEntry:
    visitor = db.get(VisitorEntry, visitor_id)
    if not visitor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Visitor entry not found")
    meeting = db.get(Meeting, visitor.meeting_id)
    if meeting.bsg_id != leader.bsg_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your group's visitor")
    if visitor.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Visitor already reviewed")
    return visitor


@router.get("", response_model=list[VisitorOut])
def list_pending(leader: BSGLeader = Depends(get_current_leader), db: Session = Depends(get_db)):
    rows = db.execute(
        select(VisitorEntry, Meeting)
        .join(Meeting, Meeting.id == VisitorEntry.meeting_id)
        .where(Meeting.bsg_id == leader.bsg_id, VisitorEntry.status == "pending")
        .order_by(VisitorEntry.created_at.desc())
    ).all()
    return [
        VisitorOut(
            id=v.id, meeting_id=v.meeting_id, bsg_id=m.bsg_id, meeting_date=m.meeting_date,
            status=v.status, created_at=v.created_at,
            crop_url=f"/api/v1/visitors/{v.id}/crop" if v.face_crop_path else None,
        )
        for v, m in rows
    ]


@router.get("/{visitor_id}/crop")
def get_crop(
    visitor_id: int, leader: BSGLeader = Depends(get_current_leader), db: Session = Depends(get_db)
):
    visitor = db.get(VisitorEntry, visitor_id)
    if not visitor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    meeting = db.get(Meeting, visitor.meeting_id)
    if meeting.bsg_id != leader.bsg_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your group's visitor")
    if not visitor.face_crop_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Crop no longer available")
    return FileResponse(visitor.face_crop_path, media_type="image/jpeg")


@router.get("/{visitor_id}/suggestions", response_model=list[MemberSuggestion])
def suggestions(
    visitor_id: int, leader: BSGLeader = Depends(get_current_leader), db: Session = Depends(get_db)
):
    visitor = _load_own_pending_visitor(db, leader, visitor_id)
    return visitor_svc.suggest_members(db, visitor=visitor, leader_bsg_id=leader.bsg_id)


@router.post("/{visitor_id}/map", response_model=VisitorOut)
def map_to_member(
    visitor_id: int,
    body: MapToMemberRequest,
    leader: BSGLeader = Depends(get_current_leader),
    db: Session = Depends(get_db),
):
    visitor = _load_own_pending_visitor(db, leader, visitor_id)
    member = db.get(BSGMember, body.member_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    v = visitor_svc.map_to_member(
        db, visitor=visitor, member=member,
        leader_bsg_id=leader.bsg_id, move_to_my_group=body.move_to_my_group,
    )
    meeting = db.get(Meeting, v.meeting_id)
    return VisitorOut(
        id=v.id, meeting_id=v.meeting_id, bsg_id=meeting.bsg_id,
        meeting_date=meeting.meeting_date, status=v.status, created_at=v.created_at,
    )


@router.post("/{visitor_id}/promote", response_model=VisitorOut)
def promote(
    visitor_id: int,
    body: PromoteNewMemberRequest,
    leader: BSGLeader = Depends(get_current_leader),
    db: Session = Depends(get_db),
):
    visitor = _load_own_pending_visitor(db, leader, visitor_id)
    visitor_svc.promote_to_new_member(
        db, visitor=visitor, leader_bsg_id=leader.bsg_id,
        name=body.name, surname=body.surname, mobile_number=body.mobile_number,
        city_id=body.city_id, street_id=body.street_id,
    )
    meeting = db.get(Meeting, visitor.meeting_id)
    return VisitorOut(
        id=visitor.id, meeting_id=visitor.meeting_id, bsg_id=meeting.bsg_id,
        meeting_date=meeting.meeting_date, status=visitor.status, created_at=visitor.created_at,
    )


@router.post("/{visitor_id}/keep", response_model=VisitorOut)
def keep(
    visitor_id: int, leader: BSGLeader = Depends(get_current_leader), db: Session = Depends(get_db)
):
    visitor = _load_own_pending_visitor(db, leader, visitor_id)
    visitor_svc.keep_as_visitor(db, visitor=visitor)
    meeting = db.get(Meeting, visitor.meeting_id)
    return VisitorOut(
        id=visitor.id, meeting_id=visitor.meeting_id, bsg_id=meeting.bsg_id,
        meeting_date=meeting.meeting_date, status=visitor.status, created_at=visitor.created_at,
    )
