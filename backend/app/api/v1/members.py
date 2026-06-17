"""Member registration + facial-profile building.

A leader manages members in their OWN group only; an admin may target any group via
`bsg_id`. Reference photos are processed into embeddings on upload; the original
image bytes are NOT stored.
"""
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models import (
    BibleStudyGroup,
    BSGLeader,
    BSGMembershipHistory,
    FacialProfilePhoto,
    BSGMember,
    User,
)
from app.db.session import get_db
from app.schemas.setup import MemberCreate, MemberDirectoryRow, MemberOut, MemberUpdate
from app.services import config_store
from app.services.face.insightface_engine import decode_image, get_engine
from app.services.face.quality import quality_reject_reason
from app.services.photos import save_member_image

router = APIRouter(prefix="/members", tags=["members"])


def _resolve_target_bsg(db: Session, user: User, requested_bsg_id: int | None) -> int:
    """Leaders are pinned to their own group; admins may pass any bsg_id."""
    if user.role == "admin":
        if requested_bsg_id is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "bsg_id required for admin")
        if not db.get(BibleStudyGroup, requested_bsg_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found")
        return requested_bsg_id
    leader = db.scalar(select(BSGLeader).where(BSGLeader.user_id == user.id))
    if not leader:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a registered leader")
    if requested_bsg_id is not None and requested_bsg_id != leader.bsg_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Leaders can only manage their own group")
    return leader.bsg_id


def _member_out(db: Session, m: BSGMember) -> MemberOut:
    count = db.scalar(
        select(func.count(FacialProfilePhoto.id)).where(FacialProfilePhoto.member_id == m.id)
    )
    return MemberOut(
        id=m.id, bsg_id=m.bsg_id, name=m.name, surname=m.surname,
        mobile_number=m.mobile_number,
        city_id=m.city_id, street_id=m.street_id,
        city_name=m.city.name if m.city else None,
        street_name=m.street.name if m.street else None,
        status=m.status, photo_count=count or 0,
    )


@router.post("", response_model=MemberOut, status_code=201)
def create_member(
    body: MemberCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    bsg_id = _resolve_target_bsg(db, user, body.bsg_id)
    member = BSGMember(
        bsg_id=bsg_id, name=body.name, surname=body.surname,
        mobile_number=body.mobile_number,
        city_id=body.city_id, street_id=body.street_id,
        joined_at=body.joined_at, status="active",
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return _member_out(db, member)


@router.patch("/{member_id}", response_model=MemberOut)
def update_member(
    member_id: int,
    body: MemberUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Edit a member's details and/or active status. Leaders may only edit members in
    their own group. Inactive members are excluded from recognition matching."""
    member = db.get(BSGMember, member_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    _resolve_target_bsg(db, user, member.bsg_id)  # authorization check

    data = body.model_dump(exclude_unset=True)
    if "status" in data and data["status"] not in ("active", "inactive"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "status must be active or inactive")
    for field, value in data.items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return _member_out(db, member)


@router.get("", response_model=list[MemberOut])
def list_members(
    bsg_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = _resolve_target_bsg(db, user, bsg_id) if (bsg_id or user.role != "admin") else None
    q = select(BSGMember)
    if target is not None:
        q = q.where(BSGMember.bsg_id == target)
    members = db.scalars(q.order_by(BSGMember.name)).all()
    return [_member_out(db, m) for m in members]


@router.post("/{member_id}/photos", response_model=MemberOut)
def add_photos(
    member_id: int,
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload one or more reference photos. Each must contain exactly one good-quality
    face; that face's embedding is added to the member's facial profile."""
    member = db.get(BSGMember, member_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    _resolve_target_bsg(db, user, member.bsg_id)  # authorization check

    engine = get_engine()
    cfg = config_store.recognition_config(db)
    added = 0
    errors: list[str] = []
    for f in files:
        data = f.file.read()
        try:
            img = decode_image(data)
        except ValueError:
            errors.append(f"{f.filename}: not a readable image")
            continue
        faces = engine.detect(img)
        usable = [face for face in faces if quality_reject_reason(face, cfg) is None]
        if not usable:
            errors.append(f"{f.filename}: no clear, frontal face detected")
            continue
        # Use the largest usable face (the registration subject) for the embedding,
        # but persist the FULL uploaded image to disk (path stored, not the bytes).
        face = max(usable, key=lambda fc: fc.width * fc.height)
        db.add(
            FacialProfilePhoto(
                member_id=member.id,
                embedding=face.embedding.tolist(),
                crop_path=save_member_image(img),
                source="registration",
            )
        )
        added += 1

    db.commit()
    if added == 0:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"message": "No usable faces in uploads", "errors": errors},
        )
    db.refresh(member)
    return _member_out(db, member)


@router.get("/{member_id}/photo")
def member_photo(
    member_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Serve the member's most recent face thumbnail (for visual comparison in review).
    Available to any authenticated user so cross-group suggestions can show a face."""
    row = db.scalar(
        select(FacialProfilePhoto)
        .where(FacialProfilePhoto.member_id == member_id, FacialProfilePhoto.crop_path.is_not(None))
        .order_by(FacialProfilePhoto.id.desc())
    )
    import os

    if not row or not row.crop_path or not os.path.exists(row.crop_path):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No photo for this member")
    from fastapi.responses import FileResponse

    return FileResponse(row.crop_path, media_type="image/jpeg")


@router.get("/directory", response_model=list[MemberDirectoryRow])
def directory(
    q: str | None = None,
    others_only: bool = True,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search members across ALL groups (for transfer/pull). Leaders use this to find
    a member belonging to another group and pull them into their own.

    `others_only=true` (default for the pull flow) hides the caller's own group.
    """
    own_bsg_id = None
    if user.role != "admin":
        leader = db.scalar(select(BSGLeader).where(BSGLeader.user_id == user.id))
        if not leader:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a registered leader")
        own_bsg_id = leader.bsg_id

    stmt = (
        select(BSGMember, BibleStudyGroup.name)
        .join(BibleStudyGroup, BibleStudyGroup.id == BSGMember.bsg_id)
        .order_by(BSGMember.name)
    )
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((BSGMember.name.ilike(like)) | (BSGMember.surname.ilike(like)))
    if others_only and own_bsg_id is not None:
        stmt = stmt.where(BSGMember.bsg_id != own_bsg_id)

    rows = db.execute(stmt).all()
    return [
        MemberDirectoryRow(
            id=m.id, name=m.name, surname=m.surname, bsg_id=m.bsg_id,
            bsg_name=bsg_name, is_own_group=(m.bsg_id == own_bsg_id),
        )
        for m, bsg_name in rows
    ]


@router.post("/{member_id}/transfer", response_model=MemberOut)
def transfer_member(
    member_id: int,
    target_bsg_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pull/transfer an existing member into a group (reassign their home BSG).

    - Leader: pulls into THEIR OWN group (target_bsg_id ignored).
    - Admin: must pass target_bsg_id.

    A BSGMembershipHistory row records the move. Attendance history is left intact
    (forward-only); facial profile travels with the member.
    """
    member = db.get(BSGMember, member_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")

    if user.role == "admin":
        if not target_bsg_id or not db.get(BibleStudyGroup, target_bsg_id):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Valid target_bsg_id required")
        dest = target_bsg_id
    else:
        leader = db.scalar(select(BSGLeader).where(BSGLeader.user_id == user.id))
        if not leader:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a registered leader")
        dest = leader.bsg_id

    if member.bsg_id == dest:
        raise HTTPException(status.HTTP_409_CONFLICT, "Member already in this group")

    db.add(
        BSGMembershipHistory(
            member_id=member.id, from_bsg_id=member.bsg_id,
            to_bsg_id=dest, moved_on=date.today(),
        )
    )
    member.bsg_id = dest
    db.commit()
    db.refresh(member)
    return _member_out(db, member)
