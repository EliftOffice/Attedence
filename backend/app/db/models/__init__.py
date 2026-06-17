"""Import all models so Alembic's autogenerate + Base.metadata see them."""
from app.db.models.app_setting import AppSetting
from app.db.models.attendance import AttendanceRecord
from app.db.models.bsg import BibleStudyGroup
from app.db.models.church import Church
from app.db.models.facial_profile import FacialProfilePhoto
from app.db.models.leader import BSGLeader
from app.db.models.location import City, Street
from app.db.models.meeting import Meeting
from app.db.models.member import BSGMember
from app.db.models.membership_history import BSGMembershipHistory
from app.db.models.user import User
from app.db.models.visitor import VisitorEntry

__all__ = [
    "AppSetting",
    "AttendanceRecord",
    "BibleStudyGroup",
    "Church",
    "FacialProfilePhoto",
    "BSGLeader",
    "City",
    "Street",
    "Meeting",
    "BSGMember",
    "BSGMembershipHistory",
    "User",
    "VisitorEntry",
]
