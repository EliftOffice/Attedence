"""Create the bootstrap admin on startup if no admin user exists yet."""
from sqlalchemy import select

from app.config import settings
from app.core.security import hash_password
from app.db.models import User
from app.db.session import SessionLocal
from app.services import config_store


def ensure_bootstrap_admin() -> None:
    db = SessionLocal()
    try:
        # Seed editable settings (idempotent) so the admin Settings page is populated.
        config_store.seed(db)

        existing_admin = db.scalar(select(User).where(User.role == "admin"))
        if existing_admin:
            return
        admin = User(
            mobile_number=settings.bootstrap_admin_mobile,
            password_hash=hash_password(settings.bootstrap_admin_password),
            name=settings.bootstrap_admin_name,
            role="admin",
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()
