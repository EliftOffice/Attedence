from pydantic import BaseModel, ConfigDict


class CityCreate(BaseModel):
    name: str


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class StreetCreate(BaseModel):
    city_id: int
    name: str


class StreetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    city_id: int
    name: str
