from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VisitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    meeting_id: int
    bsg_id: int
    meeting_date: object
    status: str
    crop_url: str | None = None
    created_at: datetime


class MemberSuggestion(BaseModel):
    """A candidate member match for a visitor face (own group or other groups)."""
    member_id: int
    name: str
    bsg_id: int
    bsg_name: str
    same_group: bool
    similarity: float
    photo_url: str | None = None  # member's face thumbnail, for visual comparison


class MapToMemberRequest(BaseModel):
    member_id: int
    # When the member belongs to a DIFFERENT group:
    #   move_to_my_group=True  -> reassign member's home group to this one (logs history)
    #   move_to_my_group=False -> just mark guest attendance, no group change
    move_to_my_group: bool = False


class PromoteNewMemberRequest(BaseModel):
    name: str
    surname: str | None = None
    mobile_number: str | None = None
    city_id: int | None = None
    street_id: int | None = None
