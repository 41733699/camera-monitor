"""应用配置 — 路径、数据库、服务参数"""

import os
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────
# Docker 中通过 PROJECT_ROOT 环境变量覆盖，非 Docker 自动检测
_project_root = os.getenv("PROJECT_ROOT")
if _project_root:
    BASE_DIR = Path(_project_root).resolve()
else:
    # backend/app/config.py → 项目根目录
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
UPLOAD_DIR = DATA_DIR / "uploads"
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"
DB_PATH = DATA_DIR / "camera_monitor.db"

# 确保目录存在
for d in (DATA_DIR, SCREENSHOTS_DIR, UPLOAD_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── 数据库 ────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# ── 检测 ──────────────────────────────────────────────
DEFAULT_TIMEOUT = int(os.getenv("DETECT_TIMEOUT", "5"))
