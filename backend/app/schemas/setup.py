"""Schemas for churches, groups, leaders, members."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChurchCreate(BaseModel):
    name: str


class ChurchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class GroupCreate(BaseModel):
    church_id: int
    name: str
    meeting_day: Optional[str] = None


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    church_id: int
    name: str
    meeting_day: Optional[str] = None


class LeaderCreate(BaseModel):
    """Admin registers a leader: creates the login User (mobile+password) and links a BSG."""
    bsg_id: int
    name: str
    mobile_number: str
    password: str


class LeaderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    bsg_id: int
    name: str
    telegram_user_id: Optional[int] = None
    telegram_linked_at: Optional[object] = None


class LeaderLinkCodeOut(BaseModel):
    """One-time code the leader sends to the bot (DM) to link Telegram."""
    link_code: str
    instructions: str


class MemberCreate(BaseModel):
    # Only `name` is required; everything else is optional.
    name: str
    surname: Optional[str] = None
    mobile_number: Optional[str] = None
    city_id: Optional[int] = None
    street_id: Optional[int] = None
    joined_at: Optional[date] = None
    # bsg_id is taken from the leader's own group (or admin-supplied) at the route.
    bsg_id: Optional[int] = None


class MemberUpdate(BaseModel):
    """Partial edit. Only fields present in the request are changed (exclude_unset)."""
    name: Optional[str] = None
    surname: Optional[str] = None
    mobile_number: Optional[str] = None
    city_id: Optional[int] = None
    street_id: Optional[int] = None
    status: Optional[str] = None  # active | inactive


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    bsg_id: int
    name: str
    surname: Optional[str] = None
    mobile_number: Optional[str] = None
    city_id: Optional[int] = None
    street_id: Optional[int] = None
    city_name: Optional[str] = None
    street_name: Optional[str] = None
    status: str
    photo_count: int = 0


class MemberDirectoryRow(BaseModel):
    """A member visible for transfer/pull (across groups)."""
    id: int
    name: str
    surname: Optional[str] = None
    bsg_id: int
    bsg_name: str
    is_own_group: bool
