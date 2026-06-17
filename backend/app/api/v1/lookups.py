"""Address lookups: City + Street.

Reads are available to any authenticated user (leaders need them for the member
form). Create/delete are admin-only. Streets belong to a city (cascading dropdown).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin
from app.db.models import City, Street
from app.db.session import get_db
from app.schemas.location import CityCreate, CityOut, StreetCreate, StreetOut

router = APIRouter(prefix="/lookups", tags=["lookups"])


# ---- Cities ----
@router.get("/cities", response_model=list[CityOut])
def list_cities(_=Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(City).order_by(City.name)).all()


@router.post("/cities", response_model=CityOut, status_code=201, dependencies=[Depends(require_admin)])
def create_city(body: CityCreate, db: Session = Depends(get_db)):
    if db.scalar(select(City).where(City.name == body.name)):
        raise HTTPException(status.HTTP_409_CONFLICT, "City already exists")
    city = City(name=body.name)
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


@router.delete("/cities/{city_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_city(city_id: int, db: Session = Depends(get_db)):
    city = db.get(City, city_id)
    if city:
        db.delete(city)
        db.commit()


# ---- Streets ----
@router.get("/streets", response_model=list[StreetOut])
def list_streets(city_id: int | None = None, _=Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(Street)
    if city_id is not None:
        q = q.where(Street.city_id == city_id)
    return db.scalars(q.order_by(Street.name)).all()


@router.post("/streets", response_model=StreetOut, status_code=201, dependencies=[Depends(require_admin)])
def create_street(body: StreetCreate, db: Session = Depends(get_db)):
    if not db.get(City, body.city_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "City not found")
    street = Street(city_id=body.city_id, name=body.name)
    db.add(street)
    db.commit()
    db.refresh(street)
    return street


@router.delete("/streets/{street_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_street(street_id: int, db: Session = Depends(get_db)):
    street = db.get(Street, street_id)
    if street:
        db.delete(street)
        db.commit()
