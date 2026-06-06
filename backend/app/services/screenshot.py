"""截图服务 — 捕获、清理、文件管理"""

import subprocess
import asyncio
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


def capture_screenshot_device(camera) -> str | None:
    """通过厂商 SDK 抓取快照（海康 ISAPI / 大华 CGI）

    在线程池中调用，内部运行异步 httpx 请求。
    Returns:
        截图文件路径，失败返回 None
    """
    from .device_api import HikvisionClient, DahuaClient

    vendor = getattr(camera, "vendor", "generic") or "generic"
    ip = camera.device_ip
    port = camera.http_port or 80
    channel = camera.channel or 1
    username = camera.username or ""
    password = camera.password or ""

    if not ip:
        logger.warning("设备截图 camera_%s: device_ip 未配置", camera.id)
        return None

    try:
        loop = asyncio.new_event_loop()
        try:
            if vendor == "hikvision":
                jpeg_bytes = loop.run_until_complete(
                    HikvisionClient.capture_snapshot(ip, port, channel, username, password)
                )
            elif vendor == "dahua":
                jpeg_bytes = loop.run_until_complete(
                    DahuaClient.capture_snapshot(ip, port, channel, username, password)
                )
            else:
                logger.warning("设备截图 camera_%s: 不支持的 vendor=%s", camera.id, vendor)
                return None
        finally:
            loop.close()
    except Exception as e:
        logger.warning("设备截图 camera_%s 异常: %s", camera.id, e)
        return None

    if not jpeg_bytes:
        return None

    # 保存到文件
    d = get_camera_screenshot_dir(camera.id)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = d / f"{ts}.jpg"
    try:
        filepath.write_bytes(jpeg_bytes)
        cleanup_old_screenshots(camera.id)
        logger.info("设备截图 camera_%s 保存成功: %s", camera.id, filepath)
        return str(filepath)
    except Exception as e:
        logger.warning("设备截图 camera_%s 保存失败: %s", camera.id, e)
        filepath.unlink(missing_ok=True)
        return None


def capture_screenshot_device_sync(camera) -> bytes | None:
    """通过厂商 SDK 抓取快照，返回原始 JPEG 字节（用于 API 端点）

    Returns:
        JPEG 字节数据，失败返回 None
    """
    from .device_api import HikvisionClient, DahuaClient

    vendor = getattr(camera, "vendor", "generic") or "generic"
    ip = camera.device_ip
    port = camera.http_port or 80
    channel = camera.channel or 1
    username = camera.username or ""
    password = camera.password or ""

    if not ip:
        logger.warning("设备截图 camera_%s: device_ip 未配置", camera.id)
        return None

    try:
        loop = asyncio.new_event_loop()
        try:
            if vendor == "hikvision":
                return loop.run_until_complete(
                    HikvisionClient.capture_snapshot(ip, port, channel, username, password)
                )
            elif vendor == "dahua":
                return loop.run_until_complete(
                    DahuaClient.capture_snapshot(ip, port, channel, username, password)
                )
            else:
                return None
        finally:
            loop.close()
    except Exception as e:
        logger.warning("设备截图 camera_%s 异常: %s", camera.id, e)
        return None
