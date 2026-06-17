from fastapi import APIRouter

from app.api.v1 import (
    attendance,
    auth,
    lookups,
    members,
    recognition,
    reports,
    setup,
    visitors,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(setup.router)
api_router.include_router(lookups.router)
api_router.include_router(members.router)
api_router.include_router(attendance.router)
api_router.include_router(recognition.router)
api_router.include_router(visitors.router)
api_router.include_router(reports.router)
