from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.bootstrap import ensure_bootstrap_admin
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bootstrap_admin()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Church Bible Study Attendance System", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
