"""Visitor review resolution logic.

Crop retention = "until reviewed": every resolution path deletes the stored crop
file and nulls `face_crop_path`. The VisitorEntry row is retained for statistics.

Cross-group handling (per product decision):
  - map to a member in the SAME group        -> add crop to profile, mark present
  - map to a member in a DIFFERENT group:
       move_to_my_group=True  -> reassign member's home BSG to this group (+ history),
                                  add crop to profile, mark present (home attendance)
       move_to_my_group=False -> mark GUEST attendance at the attended meeting only,
                                  no group change (crop still added to profile)
  - promote to NEW member -> create member in the LEADER'S OWN group, crop = 1st photo
  - keep as visitor       -> just delete crop, retain row
"""
from __future__ import annotations

import os
from datetime import date, datetime, timezone

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    BibleStudyGroup,
    BSGMember,
    BSGMembershipHistory,
    FacialProfilePhoto,
    Meeting,
    VisitorEntry,
)
from app.services.attendance import mark_present
from app.services.photos import copy_to_member_thumbnail


def _delete_crop(visitor: VisitorEntry) -> None:
    if visitor.face_crop_path and os.path.exists(visitor.face_crop_path):
        try:
            os.remove(visitor.face_crop_path)
        except OSError:
            pass
    visitor.face_crop_path = None


def _add_embedding_to_profile(
    db: Session, member_id: int, embedding, source: str, crop_src_path: str | None = None
) -> None:
    """Add an embedding to a member's profile. If a crop source is given (the visitor
    crop being resolved), copy it into the retained member-photo store for display."""
    vec = embedding.tolist() if isinstance(embedding, np.ndarray) else list(embedding)
    db.add(
        FacialProfilePhoto(
            member_id=member_id,
            embedding=vec,
            crop_path=copy_to_member_thumbnail(crop_src_path),
            source=source,
        )
    )


def map_to_member(
    db: Session,
    *,
    visitor: VisitorEntry,
    member: BSGMember,
    leader_bsg_id: int,
    move_to_my_group: bool,
) -> VisitorEntry:
    meeting = db.get(Meeting, visitor.meeting_id)
    same_group = member.bsg_id == leader_bsg_id

    if same_group:
        _add_embedding_to_profile(
            db, member.id, visitor.embedding, "visitor_map", visitor.face_crop_path
        )
        mark_present(
            db, meeting=meeting, member_id=member.id,
            confidence=None, method="visitor_resolution", is_guest=False,
        )
        visitor.status = "mapped_same"
    else:
        # crop improves the member's recognition regardless of the group decision
        _add_embedding_to_profile(
            db, member.id, visitor.embedding, "visitor_map", visitor.face_crop_path
        )
        if move_to_my_group:
            db.add(
                BSGMembershipHistory(
                    member_id=member.id,
                    from_bsg_id=member.bsg_id,
                    to_bsg_id=leader_bsg_id,
                    moved_on=date.today(),
                )
            )
            member.bsg_id = leader_bsg_id
            mark_present(
                db, meeting=meeting, member_id=member.id,
                confidence=None, method="visitor_resolution", is_guest=False,
            )
            visitor.status = "moved"
        else:
            mark_present(
                db, meeting=meeting, member_id=member.id,
                confidence=None, method="visitor_resolution", is_guest=True,
            )
            visitor.status = "mapped_guest"

    visitor.resolved_member_id = member.id
    visitor.resolved_at = datetime.now(timezone.utc)
    _delete_crop(visitor)
    db.commit()
    return visitor


def promote_to_new_member(
    db: Session,
    *,
    visitor: VisitorEntry,
    leader_bsg_id: int,
    name: str,
    mobile_number: str | None,
    surname: str | None = None,
    city_id: int | None = None,
    street_id: int | None = None,
) -> BSGMember:
    member = BSGMember(
        bsg_id=leader_bsg_id, name=name, surname=surname, mobile_number=mobile_number,
        city_id=city_id, street_id=street_id,
        status="active", joined_at=date.today(),
    )
    db.add(member)
    db.flush()
    _add_embedding_to_profile(
        db, member.id, visitor.embedding, "visitor_promotion", visitor.face_crop_path
    )
    meeting = db.get(Meeting, visitor.meeting_id)
    mark_present(
        db, meeting=meeting, member_id=member.id,
        confidence=None, method="visitor_resolution", is_guest=False,
    )
    visitor.status = "promoted"
    visitor.resolved_member_id = member.id
    visitor.resolved_at = datetime.now(timezone.utc)
    _delete_crop(visitor)
    db.commit()
    return member


def keep_as_visitor(db: Session, *, visitor: VisitorEntry) -> VisitorEntry:
    visitor.status = "kept"
    visitor.resolved_at = datetime.now(timezone.utc)
    _delete_crop(visitor)
    db.commit()
    return visitor


def suggest_members(db: Session, *, visitor: VisitorEntry, leader_bsg_id: int, top_k: int = 5):
    """Rank candidate members (own group + others) by similarity to the visitor face.
    Cross-group suggestions are allowed so the leader can map a visiting member."""
    from app.services.face.engine import cosine_similarity

    target = np.asarray(visitor.embedding, dtype=np.float32)
    rows = db.execute(
        select(
            BSGMember.id, BSGMember.name, BSGMember.bsg_id,
            BibleStudyGroup.name, FacialProfilePhoto.embedding, FacialProfilePhoto.crop_path,
        )
        .join(FacialProfilePhoto, FacialProfilePhoto.member_id == BSGMember.id)
        .join(BibleStudyGroup, BibleStudyGroup.id == BSGMember.bsg_id)
        .where(BSGMember.status == "active")
    ).all()

    best: dict[int, dict] = {}
    has_photo: dict[int, bool] = {}
    for member_id, name, bsg_id, bsg_name, emb, crop_path in rows:
        if crop_path:
            has_photo[member_id] = True
        sim = cosine_similarity(target, np.asarray(emb, dtype=np.float32))
        cur = best.get(member_id)
        if cur is None or sim > cur["similarity"]:
            best[member_id] = {
                "member_id": member_id, "name": name, "bsg_id": bsg_id,
                "bsg_name": bsg_name, "same_group": bsg_id == leader_bsg_id,
                "similarity": round(sim, 4),
            }
    for member_id, row in best.items():
        row["photo_url"] = (
            f"/api/v1/members/{member_id}/photo" if has_photo.get(member_id) else None
        )
    ranked = sorted(best.values(), key=lambda r: r["similarity"], reverse=True)
    return ranked[:top_k]
