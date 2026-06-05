"""巡检 API — 心跳、截图、设置管理"""

import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..constants import SettingKeys, SETTING_DEFAULTS
from ..services.scheduler import (
    get_setting, set_setting, update_heartbeat_interval, update_screenshot_interval,
)
from ..services.notifier import get_tenant_token, send_feishu_app, build_alert_card

router = APIRouter(prefix="/api/patrol", tags=["patrol"])


# ── 手动触发 ────────────────────────────────────────────

@router.post("/heartbeat")
def run_heartbeat():
    """立即执行一次 ONVIF 心跳检测"""
    from ..services.scheduler import onvif_heartbeat_all
    onvif_heartbeat_all()
    return {"message": "ONVIF 心跳检测已完成"}


@router.post("/screenshot")
def run_screenshot():
    """立即对所有在线摄像头截图"""
    from ..services.scheduler import screenshot_all
    screenshot_all()
    return {"message": "截图任务已完成"}


# ── 设置管理 ────────────────────────────────────────────

@router.get("/settings")
def get_patrol_settings():
    """获取巡检设置（secret 脱敏）"""
    secret = get_setting(SettingKeys.FEISHU_APP_SECRET, "")
    return {
        "onvif_heartbeat_interval": int(get_setting(SettingKeys.ONVIF_HEARTBEAT_INTERVAL, SETTING_DEFAULTS[SettingKeys.ONVIF_HEARTBEAT_INTERVAL])),
        "screenshot_interval": int(get_setting(SettingKeys.SCREENSHOT_INTERVAL, SETTING_DEFAULTS[SettingKeys.SCREENSHOT_INTERVAL])),
        "auto_notify": get_setting(SettingKeys.AUTO_NOTIFY, "true") == "true",
        "quiet_rules": json.loads(get_setting(SettingKeys.QUIET_RULES, "[]")),
        "feishu_app_id": get_setting(SettingKeys.FEISHU_APP_ID, ""),
        "feishu_app_secret": "***" if secret else "",
        "feishu_open_id": get_setting(SettingKeys.FEISHU_OPEN_ID, ""),
        "feishu_chat_id": get_setting(SettingKeys.FEISHU_CHAT_ID, ""),
    }


@router.put("/settings")
def update_patrol_settings(body: dict):
    """更新巡检设置"""
    auto_notify = body.get("auto_notify", True)
    set_setting(SettingKeys.AUTO_NOTIFY, "true" if auto_notify else "false")

    # 心跳间隔
    if "onvif_heartbeat_interval" in body:
        hi = max(10, min(int(body["onvif_heartbeat_interval"]), 3600))
        update_heartbeat_interval(hi)

    # 截图间隔
    if "screenshot_interval" in body:
        si = max(0, min(int(body["screenshot_interval"]), 86400))
        update_screenshot_interval(si)

    # 飞书配置
    if body.get("feishu_app_id"):
        set_setting(SettingKeys.FEISHU_APP_ID, body["feishu_app_id"])
    if body.get("feishu_app_secret"):
        set_setting(SettingKeys.FEISHU_APP_SECRET, body["feishu_app_secret"])
    if body.get("feishu_open_id") is not None:
        set_setting(SettingKeys.FEISHU_OPEN_ID, body["feishu_open_id"])
    if body.get("feishu_chat_id") is not None:
        set_setting(SettingKeys.FEISHU_CHAT_ID, body["feishu_chat_id"])

    # 免打扰规则
    if "quiet_rules" in body:
        set_setting(SettingKeys.QUIET_RULES, json.dumps(body["quiet_rules"], ensure_ascii=False))

    return {
        "onvif_heartbeat_interval": int(get_setting(SettingKeys.ONVIF_HEARTBEAT_INTERVAL)),
        "screenshot_interval": int(get_setting(SettingKeys.SCREENSHOT_INTERVAL)),
        "auto_notify": auto_notify,
    }


# ── 飞书测试 ────────────────────────────────────────────

@router.post("/test-feishu")
async def test_feishu():
    """测试飞书 App 机器人连接"""
    app_id = get_setting(SettingKeys.FEISHU_APP_ID, "")
    app_secret = get_setting(SettingKeys.FEISHU_APP_SECRET, "")
    open_id = get_setting(SettingKeys.FEISHU_OPEN_ID, "")
    chat_id = get_setting(SettingKeys.FEISHU_CHAT_ID, "")

    if not app_id or not app_secret:
        return {"success": False, "error": "未配置 App ID 或 App Secret"}
    if not open_id and not chat_id:
        return {"success": False, "error": "未配置接收方（需填写 Open ID 或 Chat ID）"}

    token = await get_tenant_token(app_id, app_secret)
    if not token:
        return {"success": False, "error": "获取 Token 失败，请检查 App ID 和 App Secret"}

    card = build_alert_card("测试摄像头", "test", "测试分组", "recovered", "请通知张三处理")
    if open_id:
        if await send_feishu_app(app_id, app_secret, open_id, card, "open_id"):
            return {"success": True, "message": "测试消息发送成功！请检查你的飞书私信"}
    if chat_id:
        if await send_feishu_app(app_id, app_secret, chat_id, card, "chat_id"):
            return {"success": True, "message": "测试消息发送成功！请检查飞书群聊"}

    return {"success": False, "error": "发送失败，请检查配置是否正确"}
