"""Church / group / leader setup & management. Admin-only."""
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.core.security import hash_password
from app.db.models import BibleStudyGroup, BSGLeader, Church, User
from app.db.session import get_db
from app.schemas.settings import SettingsOut, SettingsUpdate
from app.schemas.setup import (
    ChurchCreate,
    ChurchOut,
    GroupCreate,
    GroupOut,
    LeaderCreate,
    LeaderLinkCodeOut,
    LeaderOut,
)
from app.services import config_store

router = APIRouter(prefix="/setup", tags=["setup"], dependencies=[Depends(require_admin)])


# ---- Churches ----
@router.post("/churches", response_model=ChurchOut, status_code=201)
def create_church(body: ChurchCreate, db: Session = Depends(get_db)):
    church = Church(name=body.name)
    db.add(church)
    db.commit()
    db.refresh(church)
    return church


@router.get("/churches", response_model=list[ChurchOut])
def list_churches(db: Session = Depends(get_db)):
    return db.scalars(select(Church).order_by(Church.name)).all()


# ---- Groups ----
@router.post("/groups", response_model=GroupOut, status_code=201)
def create_group(body: GroupCreate, db: Session = Depends(get_db)):
    if not db.get(Church, body.church_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Church not found")
    group = BibleStudyGroup(
        church_id=body.church_id, name=body.name, meeting_day=body.meeting_day
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.get("/groups", response_model=list[GroupOut])
def list_groups(church_id: int | None = None, db: Session = Depends(get_db)):
    q = select(BibleStudyGroup)
    if church_id is not None:
        q = q.where(BibleStudyGroup.church_id == church_id)
    return db.scalars(q.order_by(BibleStudyGroup.name)).all()


# ---- Leaders ----
@router.post("/leaders", response_model=LeaderOut, status_code=201)
def create_leader(body: LeaderCreate, db: Session = Depends(get_db)):
    """Creates the login User (mobile + password) and the BSGLeader (one per group)."""
    group = db.get(BibleStudyGroup, body.bsg_id)
    if not group:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found")
    if db.scalar(select(BSGLeader).where(BSGLeader.bsg_id == body.bsg_id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Group already has a leader")
    if db.scalar(select(User).where(User.mobile_number == body.mobile_number)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Mobile number already registered")

    user = User(
        mobile_number=body.mobile_number,
        password_hash=hash_password(body.password),
        name=body.name,
        role="leader",
    )
    db.add(user)
    db.flush()
    leader = BSGLeader(user_id=user.id, bsg_id=body.bsg_id, name=body.name)
    db.add(leader)
    db.commit()
    db.refresh(leader)
    return leader


@router.get("/leaders", response_model=list[LeaderOut])
def list_leaders(db: Session = Depends(get_db)):
    return db.scalars(select(BSGLeader)).all()


@router.post("/leaders/{leader_id}/telegram-link-code", response_model=LeaderLinkCodeOut)
def issue_link_code(leader_id: int, db: Session = Depends(get_db)):
    """Generate a one-time code the leader DMs to the bot to capture their Telegram id."""
    leader = db.get(BSGLeader, leader_id)
    if not leader:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Leader not found")
    code = secrets.token_hex(4).upper()
    leader.telegram_link_code = code
    db.commit()
    return LeaderLinkCodeOut(
        link_code=code,
        instructions=(
            f"Open the attendance bot in Telegram and send:  /link {code}\n"
            "This captures your Telegram id so group photos you post are attributed to you."
        ),
    )


# ---- Runtime settings (admin-editable; override .env without redeploy) ----
def _mask(token: str | None) -> str | None:
    if not token:
        return None
    return f"…{token[-4:]}" if len(token) > 4 else "set"


@router.get("/settings", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    s = config_store.get_all(db)
    token = s.get("telegram_bot_token")
    return SettingsOut(
        telegram_bot_token=_mask(token),
        telegram_token_set=bool(token),
        telegram_match_field=s.get("telegram_match_field"),
        telegram_reply_mode=s.get("telegram_reply_mode"),
        face_match_threshold=float(s["face_match_threshold"]),
        face_det_score_min=float(s["face_det_score_min"]),
        face_min_pixels=int(float(s["face_min_pixels"])),
        face_max_yaw_deg=float(s["face_max_yaw_deg"]),
        face_blur_var_min=float(s["face_blur_var_min"]),
        discard_low_quality=str(s.get("discard_low_quality")).strip().lower() in ("1", "true", "yes"),
        max_photo_age_days=int(float(s["max_photo_age_days"])),
    )


@router.put("/settings", response_model=SettingsOut)
def update_settings(body: SettingsUpdate, db: Session = Depends(get_db)):
    values: dict[str, str] = {}
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        if value is None:
            continue
        # Don't overwrite the token with an empty string (used when only other fields change).
        if key == "telegram_bot_token" and str(value).strip() == "":
            continue
        if key == "telegram_match_field" and value not in ("user_id", "chat_id"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "match field must be user_id or chat_id")
        if key == "telegram_reply_mode" and value not in ("minimal", "silent", "private"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid reply mode")
        if key == "discard_low_quality":
            value = "true" if value else "false"
        if key == "max_photo_age_days" and int(value) < 1:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "max photo age must be >= 1 day")
        values[key] = str(value)
    config_store.set_many(db, values)
    return get_settings(db)


@router.post("/leaders/{leader_id}/deactivate")
def deactivate_leader(leader_id: int, db: Session = Depends(get_db)):
    """Deactivate a group's leader: disable their login and free the group so a new
    leader can be assigned. The User row is kept (inactive) for audit; the BSGLeader
    assignment is removed. To replace, call POST /setup/leaders with the new leader."""
    leader = db.get(BSGLeader, leader_id)
    if not leader:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Leader not found")
    freed_bsg_id = leader.bsg_id
    user = db.get(User, leader.user_id)
    if user:
        user.is_active = False
    db.delete(leader)
    db.commit()
    return {"ok": True, "freed_bsg_id": freed_bsg_id}
