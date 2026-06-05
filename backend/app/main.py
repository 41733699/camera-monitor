"""FastAPI 应用入口 — 仅负责组装，不含业务逻辑"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 配置日志 — 让 app 层 logger 输出到 journalctl
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

from .database import engine, Base, SessionLocal
from .config import FRONTEND_DIR, UPLOAD_DIR
from .api import cameras, groups, alerts, patrol, reports, backup, screenshots, auth
from .services.scheduler import start_scheduler, stop_scheduler
from .services.auth import ensure_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    Base.metadata.create_all(bind=engine)
    # 确保有管理员账号
    db = SessionLocal()
    try:
        ensure_admin(db)
    finally:
        db.close()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="摄像头状态监测系统",
    description="监控摄像头在线状态，掉线自动通知",
    version="2.1.0",
    lifespan=lifespan,
)

# ── 中间件 ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API 路由 ───────────────────────────────────────────
API_ROUTERS = [
    auth, cameras, groups, alerts, patrol,
    reports, backup, screenshots,
]
for mod in API_ROUTERS:
    app.include_router(mod.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# ── 静态文件 ───────────────────────────────────────────
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """前端路由兜底：所有非 API 路径返回 index.html"""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API 路径不存在")
        file_path = FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
