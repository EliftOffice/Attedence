"""Core recognition pipeline shared by the test endpoint AND the Telegram bot.

Group-scoped by design: detected faces are compared ONLY against members of the
resolved BSG (per product decision). A visiting member from another group falls
through as a visitor and is resolved in the Visitor Review page.

Flow:
  detect -> quality gate -> match within group (>= threshold) -> mark present
         -> unmatched real faces become VisitorEntry (crop stored)
         -> low-quality detections discarded (not counted)
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone

import cv2
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import BibleStudyGroup, FacialProfilePhoto, BSGMember, VisitorEntry
from app.schemas.recognition import (
    DiscardedFace,
    MatchedMember,
    RecognitionResult,
)
from app.services import config_store
from app.services.attendance import get_or_create_meeting, mark_present
from app.services.face.engine import DetectedFace, FaceEngine, cosine_similarity
from app.services.face.quality import quality_reject_reason


@dataclass
class _MemberEmbeddings:
    member_id: int
    name: str
    embeddings: list[np.ndarray]


def _load_group_profiles(db: Session, bsg_id: int) -> list[_MemberEmbeddings]:
    rows = db.execute(
        select(BSGMember.id, BSGMember.name, FacialProfilePhoto.embedding)
        .join(FacialProfilePhoto, FacialProfilePhoto.member_id == BSGMember.id)
        .where(BSGMember.bsg_id == bsg_id, BSGMember.status == "active")
    ).all()
    by_member: dict[int, _MemberEmbeddings] = {}
    for member_id, name, emb in rows:
        vec = np.asarray(emb, dtype=np.float32)
        slot = by_member.setdefault(member_id, _MemberEmbeddings(member_id, name, []))
        slot.embeddings.append(vec)
    return list(by_member.values())


def _best_member(
    face: DetectedFace, profiles: list[_MemberEmbeddings]
) -> tuple[_MemberEmbeddings | None, float]:
    best, best_sim = None, -1.0
    for prof in profiles:
        sim = max(cosine_similarity(face.embedding, e) for e in prof.embeddings)
        if sim > best_sim:
            best, best_sim = prof, sim
    return best, best_sim


def _save_visitor_crop(crop_bgr: np.ndarray | None) -> str | None:
    if crop_bgr is None or crop_bgr.size == 0:
        return None
    os.makedirs(settings.visitor_crop_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}.jpg"
    path = os.path.join(settings.visitor_crop_dir, fname)
    cv2.imwrite(path, crop_bgr)
    return path


def run_recognition(
    db: Session,
    *,
    engine: FaceEngine,
    image_bgr: np.ndarray,
    bsg: BibleStudyGroup,
    meeting_date: date,
    source: str,
    persist: bool,
) -> RecognitionResult:
    """Run the full pipeline. When persist=False (dry-run for the test endpoint),
    no Meeting/Attendance/Visitor rows are written and crops aren't stored."""
    detections = engine.detect(image_bgr)
    profiles = _load_group_profiles(db, bsg.id)
    cfg = config_store.recognition_config(db)  # admin-editable thresholds snapshot
    discard_enabled = config_store.get_bool("discard_low_quality", db)

    discarded: list[DiscardedFace] = []
    matched: dict[int, MatchedMember] = {}  # member_id -> best match (dedupe per member)
    visitor_faces: list[DetectedFace] = []

    for face in detections:
        # By default we DON'T discard: low-quality faces that don't match a member
        # fall through to Visitors for manual marking (so no attendee is lost).
        if discard_enabled:
            reason = quality_reject_reason(face, cfg)
            if reason:
                discarded.append(
                    DiscardedFace(
                        reason=reason,
                        det_score=round(face.det_score, 3),
                        size_px=min(face.width, face.height),
                        yaw_deg=round(face.yaw_deg, 1),
                        blur_var=round(face.blur_var, 1),
                    )
                )
                continue
        member, sim = _best_member(face, profiles)
        if member is not None and sim >= cfg.match_threshold:
            prev = matched.get(member.member_id)
            if prev is None or sim > prev.confidence:
                matched[member.member_id] = MatchedMember(
                    member_id=member.member_id, name=member.name, confidence=round(sim, 4)
                )
        else:
            visitor_faces.append(face)

    meeting_id = None
    if persist:
        meeting = get_or_create_meeting(
            db, bsg_id=bsg.id, meeting_date=meeting_date, source=source
        )
        meeting_id = meeting.id
        # Members finalized immediately (auto). Group-scoped => is_guest always False here.
        for m in matched.values():
            mark_present(
                db,
                meeting=meeting,
                member_id=m.member_id,
                confidence=m.confidence,
                method="auto",
                is_guest=False,
            )
        # Unmatched real faces -> visitor entries (crop stored until reviewed).
        for face in visitor_faces:
            crop_path = _save_visitor_crop(face.crop_bgr)
            db.add(
                VisitorEntry(
                    meeting_id=meeting.id,
                    face_crop_path=crop_path,
                    embedding=face.embedding.tolist(),
                    status="pending",
                    created_at=datetime.now(timezone.utc),
                )
            )
        db.commit()

    return RecognitionResult(
        bsg_id=bsg.id,
        bsg_name=bsg.name,
        meeting_id=meeting_id,
        faces_detected=len(detections),
        recognized_members=list(matched.values()),
        visitors=len(visitor_faces),
        discarded=discarded,
        saved=persist,
    )
