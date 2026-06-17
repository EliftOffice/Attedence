from pydantic import BaseModel


class MatchedMember(BaseModel):
    member_id: int
    name: str
    confidence: float


class DiscardedFace(BaseModel):
    reason: str  # low_det_score | too_small | side_profile | blurry
    # Metrics, so you can see WHY it was discarded and tune thresholds in Settings.
    det_score: float
    size_px: int
    yaw_deg: float
    blur_var: float


class RecognitionResult(BaseModel):
    """Returned by both the test endpoint and (internally) the Telegram pipeline."""
    bsg_id: int
    bsg_name: str
    meeting_id: int | None = None
    faces_detected: int
    recognized_members: list[MatchedMember]
    visitors: int
    discarded: list[DiscardedFace]
    saved: bool
