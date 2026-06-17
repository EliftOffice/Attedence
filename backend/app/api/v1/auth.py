from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.db.models import BSGLeader, User
from app.db.session import get_db
from app.schemas.auth import MeResponse, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password form. `username` field carries the MOBILE NUMBER."""
    user = db.scalar(select(User).where(User.mobile_number == form.username))
    if not user or not user.is_active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid mobile number or password")
    token = create_access_token(user_id=user.id, role=user.role)
    return Token(
        access_token=token, role=user.role, name=user.name, user_id=user.id
    )


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    leader = db.scalar(select(BSGLeader).where(BSGLeader.user_id == user.id))
    return MeResponse(
        user_id=user.id, name=user.name, role=user.role,
        mobile_number=user.mobile_number,
        leader_bsg_id=leader.bsg_id if leader else None,
    )
