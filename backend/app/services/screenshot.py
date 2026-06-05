"""截图服务 — 捕获、清理、文件管理"""

import subprocess
import logging
from datetime import datetime
from pathlib import Path
from ..config import SCREENSHOTS_DIR
from ..constants import MAX_SCREENSHOTS_PER_CAMERA

logger = logging.getLogger(__name__)


def get_camera_screenshot_dir(camera_id: int) -> Path:
    """获取摄像头截图目录"""
    d = SCREENSHOTS_DIR / f"camera_{camera_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cleanup_old_screenshots(camera_id: int):
    """保留最新 N 张截图，删除多余的"""
    d = get_camera_screenshot_dir(camera_id)
    files = sorted(d.glob("*.jpg"), key=lambda f: f.stat().st_mtime, reverse=True)
    for f in files[MAX_SCREENSHOTS_PER_CAMERA:]:
        f.unlink(missing_ok=True)


def capture_screenshot(rtsp_url: str, camera_id: int, timeout: int = 10):
    """同步截取 RTSP 流的一帧（在线程池中调用）"""
    if not rtsp_url or camera_id is None:
        return None

    d = get_camera_screenshot_dir(camera_id)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = d / f"{ts}.jpg"

    try:
        # 脱敏日志
        import re
        safe_url = re.sub(r"(://[^:]+:)[^@]+(@)", r"\1***\2", rtsp_url)
        logger.info("截图 camera_%s: %s", camera_id, safe_url)

        result = subprocess.run(
            ["ffmpeg", "-y", "-rtsp_transport", "tcp",
             "-timeout", str(timeout * 1000000),
             "-i", rtsp_url,
             "-frames:v", "1", "-q:v", "2",
             "-vf", "scale='min(640,iw)':-2",
             str(filepath)],
            capture_output=True,
            timeout=timeout + 5
        )
        if result.returncode == 0 and filepath.exists() and filepath.stat().st_size > 0:
            cleanup_old_screenshots(camera_id)
            return str(filepath)
        else:
            filepath.unlink(missing_ok=True)
            err = result.stderr.decode("utf-8", errors="ignore") if result.stderr else ""
            err_lines = [l.strip() for l in err.split("\n") if "error" in l.lower() or "401" in l or "failed" in l.lower()]
            logger.warning("截图失败 camera_%s: %s", camera_id, err_lines[-1] if err_lines else f"exit={result.returncode}")
            return None
    except Exception as e:
        filepath.unlink(missing_ok=True)
        logger.warning("截图失败 camera_%s: %s", camera_id, e)
        return None
