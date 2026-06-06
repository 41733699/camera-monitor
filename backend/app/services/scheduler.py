"""定时调度器 — ONVIF 心跳 + 截图 + 记录清理

架构：
  ONVIF 心跳（每 60 秒）：轻量 HTTP 探测，判断在线/离线
  截图任务（可选，默认 30 分钟）：对在线摄像头截取一帧
  记录清理（每天）：删除 7 天前的 StatusRecord
"""

import logging
import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler

from ..database import SessionLocal
from ..models import Camera, Alert, Setting, StatusRecord
from ..constants import SettingKeys, SETTING_DEFAULTS, CONSECUTIVE_FAILURES_THRESHOLD

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

# 防抖计数器（模块级持久化，不会每次重置）
_failure_counts: dict[int, int] = {}


# ── 设置读写（统一入口） ──────────────────────────────

def get_setting(key: str, default: str = None) -> str:
    db = SessionLocal()
    try:
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            return setting.value
        return SETTING_DEFAULTS.get(key, default)
    finally:
        db.close()


def set_setting(key: str, value: str):
    db = SessionLocal()
    try:
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.now()
        else:
            db.add(Setting(key=key, value=value))
        db.commit()
    finally:
        db.close()


# ── ONVIF 心跳检测 ─────────────────────────────────────

_heartbeat_running = False


def onvif_heartbeat_all():
    """ONVIF 心跳巡检 — 全量轻量检测"""
    global _heartbeat_running

    if _heartbeat_running:
        logger.debug("ONVIF 心跳正在执行，跳过")
        return

    _heartbeat_running = True
    started_at = datetime.now()

    try:
        db = SessionLocal()
        try:
            cameras = db.query(Camera).all()
            all_settings = {s.key: s.value for s in db.query(Setting).all()}
        finally:
            db.close()

        if not cameras:
            _heartbeat_running = False
            return

        logger.info("ONVIF 心跳开始：%d 个摄像头", len(cameras))

        executor = ThreadPoolExecutor(max_workers=10)
        online_count = offline_count = 0

        futures = []
        for cam in cameras:
            vendor = getattr(cam, "vendor", "generic") or "generic"
            if vendor != "generic" and cam.device_ip:
                fut = executor.submit(
                    _device_heartbeat,
                    vendor, cam.device_ip, cam.http_port or 80,
                    cam.username or "", cam.password or "", 5
                )
            else:
                fut = executor.submit(
                    _onvif_heartbeat_single,
                    cam.onvif_host, cam.onvif_port_parsed, 5, cam.onvif_path
                )
            futures.append((cam.id, cam.onvif_host, cam.onvif_port_parsed, fut))

        results = []
        for camera_id, domain, onvif_port, fut in futures:
            try:
                is_online, latency_ms = fut.result(timeout=10)
                results.append({
                    "camera_id": camera_id,
                    "is_online": is_online,
                    "onvif_time": latency_ms,
                })
                if is_online:
                    online_count += 1
                else:
                    offline_count += 1
            except Exception as e:
                logger.error("ONVIF 心跳 camera_%s 超时: %s", camera_id, e)
                results.append({
                    "camera_id": camera_id,
                    "is_online": False,
                    "onvif_time": 0,
                })
                offline_count += 1

        executor.shutdown(wait=False)

        _heartbeat_update_db(results, all_settings)

        elapsed = (datetime.now() - started_at).total_seconds()
        logger.info(
            "ONVIF 心跳完成：在线 %d，离线 %d，耗时 %.1f 秒",
            online_count, offline_count, elapsed
        )

    except Exception as e:
        logger.error("ONVIF 心跳异常: %s", e)
    finally:
        _heartbeat_running = False


def _onvif_heartbeat_single(domain: str, onvif_port: int, timeout: int = 5, path: str = "/onvif/device_service") -> tuple[bool, int]:
    from .onvif_detector import check_onvif
    return check_onvif(domain, onvif_port, timeout, path)


def _device_heartbeat(vendor: str, ip: str, port: int, username: str, password: str, timeout: int = 5) -> tuple[bool, int]:
    """厂商 SDK 心跳检测（在同步线程中运行异步调用）"""
    import asyncio
    from .device_api import HikvisionClient, DahuaClient

    try:
        loop = asyncio.new_event_loop()
        try:
            if vendor == "hikvision":
                return loop.run_until_complete(
                    HikvisionClient.check_alive(ip, port, username, password, timeout)
                )
            elif vendor == "dahua":
                return loop.run_until_complete(
                    DahuaClient.check_alive(ip, port, username, password, timeout)
                )
            else:
                return False, 0
        finally:
            loop.close()
    except Exception as e:
        logger.debug("厂商心跳检测异常 %s:%s: %s", ip, port, e)
        return False, 0


def _is_quiet_hours(all_settings: dict) -> bool:
    """检查当前时间是否命中任何免打扰规则

    规则格式（JSON 数组存入 settings 表）：
    [
      {"name": "夜间", "type": "daily", "start": "22:00", "end": "08:00", "active": true},
      {"name": "元旦", "type": "date", "dates": ["2026-01-01", "2026-01-02"], "active": true},
      {"name": "国庆", "type": "date", "dates": ["2026-10-01~2026-10-07"], "active": true},
      {"name": "周末", "type": "weekday", "weekdays": [6, 0], "start": "00:00", "end": "23:59", "active": true},
    ]

    任意规则命中即返回 True。
    """
    import json

    rules_raw = all_settings.get(SettingKeys.QUIET_RULES, "[]")
    try:
        rules = json.loads(rules_raw)
    except (json.JSONDecodeError, TypeError):
        return False

    if not rules:
        return False

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    today_weekday = now.weekday()  # 0=周一, 6=周日
    now_minutes = now.hour * 60 + now.minute

    for rule in rules:
        if not rule.get("active", True):
            continue

        rtype = rule.get("type", "")

        if rtype == "daily":
            if _check_daily_rule(rule, now_minutes):
                return True

        elif rtype == "date":
            if _check_date_rule(rule, today_str):
                return True

        elif rtype == "weekday":
            if _check_weekday_rule(rule, today_weekday, now_minutes):
                return True

    return False


def _parse_hm(hm: str) -> int:
    """HH:MM -> 分钟数"""
    h, m = map(int, hm.split(":"))
    return h * 60 + m


def _check_daily_rule(rule: dict, now_minutes: int) -> bool:
    """检查每日时段规则，支持跨午夜"""
    start = _parse_hm(rule.get("start", "00:00"))
    end = _parse_hm(rule.get("end", "23:59"))
    if start <= end:
        return start <= now_minutes < end
    else:
        return now_minutes >= start or now_minutes < end


def _check_date_rule(rule: dict, today_str: str) -> bool:
    """检查指定日期规则，支持单日和日期范围"""
    for d in rule.get("dates", []):
        if "~" in d:
            parts = d.split("~")
            if len(parts) == 2:
                try:
                    start_date = datetime.strptime(parts[0].strip(), "%Y-%m-%d").date()
                    end_date = datetime.strptime(parts[1].strip(), "%Y-%m-%d").date()
                    today = datetime.strptime(today_str, "%Y-%m-%d").date()
                    if start_date <= today <= end_date:
                        return True
                except ValueError:
                    continue
        else:
            if d.strip() == today_str:
                return True
    return False


def _check_weekday_rule(rule: dict, today_weekday: int, now_minutes: int) -> bool:
    """检查每周几规则，可选时段限定"""
    weekdays = rule.get("weekdays", [])
    if today_weekday not in weekdays:
        return False
    # 如果指定了时段，在时段内才生效
    if "start" in rule and "end" in rule:
        return _check_daily_rule(rule, now_minutes)
    # 未指定时段，全天生效
    return True


def _heartbeat_update_db(results: list, all_settings: dict):
    """更新摄像头状态 + 触发告警"""
    global _failure_counts

    db = SessionLocal()
    try:
        camera_ids = [r["camera_id"] for r in results]
        cameras_map = {c.id: c for c in db.query(Camera).filter(Camera.id.in_(camera_ids)).all()}

        alerts_to_send = []

        for result in results:
            cam = cameras_map.get(result["camera_id"])
            if not cam:
                continue

            now = datetime.now()
            cam.last_check = now
            is_online = result["is_online"]

            if is_online:
                _failure_counts[cam.id] = 0
                if cam.status != "online":
                    cam.status = "online"
                    cam.last_online = now
                    db.add(Alert(
                        camera_id=cam.id, alert_type="recovered",
                        message=f"摄像头 {cam.name or cam.onvif_host} 已恢复在线",
                    ))
                else:
                    cam.last_online = now
            else:
                _failure_counts[cam.id] = _failure_counts.get(cam.id, 0) + 1
                if _failure_counts[cam.id] >= CONSECUTIVE_FAILURES_THRESHOLD:
                    if cam.status in ("online", "unknown"):
                        cam.status = "offline"
                        db.add(Alert(
                            camera_id=cam.id, alert_type="offline",
                            message=f"摄像头 {cam.name or cam.onvif_host} 已离线",
                        ))
                    else:
                        cam.status = "offline"

            # 记录心跳结果
            db.add(StatusRecord(
                camera_id=cam.id,
                status="online" if is_online else "offline",
                onvif_time=result["onvif_time"],
                check_type="onvif",
            ))

            # 收集待发告警
            pending = db.query(Alert).filter(
                Alert.camera_id == cam.id, Alert.notified == 0
            ).all()
            for alert in pending:
                alerts_to_send.append((cam, alert.alert_type, alert))

        db.commit()

        # 发送告警（检查免打扰 + 单摄像头通知开关）
        if all_settings.get(SettingKeys.AUTO_NOTIFY, "true") == "true":
            if _is_quiet_hours(all_settings):
                logger.info("当前为免打扰时段，跳过通知发送")
            else:
                for cam, alert_type, alert in alerts_to_send:
                    if not cam.notify_enabled:
                        logger.info("摄像头 %s 已关闭通知，跳过", cam.name or cam.onvif_host)
                        continue
                    try:
                        loop = asyncio.new_event_loop()
                        from .notifier import send_alert_for_camera
                        sent = loop.run_until_complete(
                            send_alert_for_camera(cam, alert_type, all_settings)
                        )
                        loop.close()
                        if sent:
                            alert.notified = 1
                    except Exception as e:
                        logger.error("发送通知失败: %s", e)

        db.commit()

    except Exception as e:
        logger.error("ONVIF 心跳更新数据库失败: %s", e)
        db.rollback()
    finally:
        db.close()


# ── 截图任务（独立调度） ────────────────────────────────

_screenshot_running = False


def screenshot_all():
    """对所有在线摄像头截图"""
    global _screenshot_running

    if _screenshot_running:
        logger.debug("截图任务正在执行，跳过")
        return

    _screenshot_running = True
    started_at = datetime.now()

    try:
        db = SessionLocal()
        try:
            from sqlalchemy import or_
            cameras = db.query(Camera).filter(
                Camera.status == "online",
                Camera.screenshot_enabled == True,
                or_(
                    Camera.rtsp_url.isnot(None),
                    Camera.device_ip.isnot(None),
                ),
            ).all()
        finally:
            db.close()

        if not cameras:
            logger.info("截图任务：没有在线摄像头，跳过")
            _screenshot_running = False
            return

        logger.info("截图任务开始：%d 个在线摄像头", len(cameras))

        from .screenshot import capture_screenshot, capture_screenshot_device
        success = fail = 0

        for cam in cameras:
            try:
                vendor = getattr(cam, "vendor", "generic") or "generic"
                if vendor != "generic" and cam.device_ip:
                    result = capture_screenshot_device(cam)
                elif cam.rtsp_url:
                    result = capture_screenshot(
                        camera_id=cam.id,
                        rtsp_url=cam.rtsp_url,
                    )
                else:
                    fail += 1
                    continue
                if result:
                    success += 1
                else:
                    fail += 1
            except Exception as e:
                logger.warning("截图失败 camera_%s: %s", cam.id, e)
                fail += 1

        elapsed = (datetime.now() - started_at).total_seconds()
        logger.info("截图任务完成：成功 %d，失败 %d，耗时 %.1f 秒", success, fail, elapsed)

    except Exception as e:
        logger.error("截图任务异常: %s", e)
    finally:
        _screenshot_running = False


# ── 记录清理 ────────────────────────────────────────────

def cleanup_old_records():
    """删除 7 天前的 StatusRecord"""
    db = SessionLocal()
    try:
        cutoff = datetime.now() - timedelta(days=7)
        deleted = db.query(StatusRecord).filter(StatusRecord.created_at < cutoff).delete()
        db.commit()
        if deleted:
            logger.info("已清理 %d 条过期状态记录", deleted)
    except Exception as e:
        logger.error("清理记录失败: %s", e)
        db.rollback()
    finally:
        db.close()


# ── 调度器生命周期 ──────────────────────────────────────

def start_scheduler():
    """启动定时调度器 — ONVIF 心跳 + 截图 + 记录清理"""
    onvif_interval = int(get_setting(SettingKeys.ONVIF_HEARTBEAT_INTERVAL, SETTING_DEFAULTS[SettingKeys.ONVIF_HEARTBEAT_INTERVAL]))
    screenshot_interval = int(get_setting(SettingKeys.SCREENSHOT_INTERVAL, SETTING_DEFAULTS[SettingKeys.SCREENSHOT_INTERVAL]))

    _add_heartbeat_job(onvif_interval)
    _add_screenshot_job(screenshot_interval)

    # 每天凌晨 4 点清理过期记录
    scheduler.add_job(
        cleanup_old_records, "cron", hour=4, id="cleanup_records",
        replace_existing=True, max_instances=1,
    )

    scheduler.start()
    logger.info("调度器已启动 — 心跳: %d秒, 截图: %d秒", onvif_interval, screenshot_interval)


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("调度器已停止")


def update_heartbeat_interval(seconds: int):
    set_setting(SettingKeys.ONVIF_HEARTBEAT_INTERVAL, str(seconds))
    _add_heartbeat_job(seconds)
    logger.info("心跳间隔已更新为 %s秒", seconds)


def update_screenshot_interval(seconds: int):
    set_setting(SettingKeys.SCREENSHOT_INTERVAL, str(seconds))
    _add_screenshot_job(seconds)
    logger.info("截图间隔已更新为 %s秒", seconds)


def _add_heartbeat_job(seconds: int):
    try:
        scheduler.remove_job("onvif_heartbeat")
    except Exception:
        pass
    scheduler.add_job(
        onvif_heartbeat_all, "interval", seconds=seconds,
        id="onvif_heartbeat", replace_existing=True,
        max_instances=1, coalesce=True,
    )


def _add_screenshot_job(seconds: int):
    try:
        scheduler.remove_job("screenshot_all")
    except Exception:
        pass
    if seconds <= 0:
        logger.info("截图任务已禁用")
        return
    scheduler.add_job(
        screenshot_all, "interval", seconds=seconds,
        id="screenshot_all", replace_existing=True,
        max_instances=1, coalesce=True,
    )


