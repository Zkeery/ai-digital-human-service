from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from app.api.routes import agent_router, router
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler, http_error_handler
from app.db.session import SessionLocal, init_db
from app.services import settings_svc

STATIC_PAGE = Path(__file__).resolve().parent / "static" / "index.html"

# 正式前端（3050）本机联调；不上线、不放开任意来源
LOCAL_FRONTEND_ORIGINS = (
    "http://127.0.0.1:3050",
    "http://localhost:3050",
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    init_db()
    db = SessionLocal()
    try:
        settings_svc.seed_settings(
            db,
            settings.pilot_entry_id,
            settings.agent_enabled,
            settings.rag_enabled,
        )
    finally:
        db.close()
    yield


app = FastAPI(title="AI数字人客服", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(LOCAL_FRONTEND_ORIGINS),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.include_router(router)
app.include_router(agent_router)


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(
        STATIC_PAGE.read_text(encoding="utf-8"),
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@app.get("/favicon.ico")
def favicon():
    icon = Path(__file__).resolve().parent / "static" / "favicon.ico"
    if icon.exists():
        return FileResponse(icon)
    return HTMLResponse(status_code=204)
