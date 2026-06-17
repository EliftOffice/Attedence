"""Test recognition endpoint (Build step 4).

Run the SAME recognition pipeline the Telegram bot uses, on an uploaded photo,
without any Telegram involvement — so accuracy / thresholds can be validated early.

`persist=false` (default) is a pure dry run: nothing is written, no crops stored.
Set `persist=true` to also save attendance + visitors, exactly like the bot flow.
"""
from datetime import date

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models import BibleStudyGroup, BSGLeader, User
from app.db.session import get_db
from app.schemas.recognition import RecognitionResult
from app.services import config_store
from app.services.face.insightface_engine import decode_image, get_engine
from app.services.photo_meta import stale_reason
from app.services.recognition_pipeline import run_recognition

router = APIRouter(prefix="/recognition", tags=["recognition"])


@router.post("/test", response_model=RecognitionResult)
def test_recognition(
    bsg_id: int = Form(...),
    persist: bool = Form(False),
    meeting_date: date | None = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = db.get(BibleStudyGroup, bsg_id)
    if not group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found")

    # Leaders may only test against their own group.
    if user.role != "admin":
        leader = db.query(BSGLeader).filter(BSGLeader.user_id == user.id).one_or_none()
        if not leader or leader.bsg_id != bsg_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your group")

    data = file.file.read()

    # Block stale photos when this run would record attendance (persist). Dry-runs
    # are allowed so accuracy can still be validated on any image.
    if persist:
        max_age = int(float(config_store.get("max_photo_age_days", db)))
        reason = stale_reason(data, max_age)
        if reason:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, reason)

    try:
        img = decode_image(data)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unreadable image")

    return run_recognition(
        db,
        engine=get_engine(),
        image_bgr=img,
        bsg=group,
        meeting_date=meeting_date or date.today(),
        source="test_endpoint",
        persist=persist,
    )
