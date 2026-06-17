from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    user_id: int


class LoginRequest(BaseModel):
    mobile_number: str
    password: str


class MeResponse(BaseModel):
    user_id: int
    name: str
    role: str
    mobile_number: str
    leader_bsg_id: int | None = None
