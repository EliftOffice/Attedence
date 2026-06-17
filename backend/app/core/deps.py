"""Auth dependencies: current user, admin guard, and the leader's own group.

Leaders are always scoped to their own BSG (satisfies cross-group isolation for
manual actions). Admins are unrestricted.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import BSGLeader, User
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inactive or unknown user")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user


def get_current_leader(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> BSGLeader:
    """The BSGLeader record for the logged-in leader. 403 if the user isn't a leader."""
    leader = db.query(BSGLeader).filter(BSGLeader.user_id == user.id).one_or_none()
    if not leader:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a registered leader")
    return leader
