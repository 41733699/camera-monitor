"""飞书通知服务 — token 管理、卡片构建、消息发送"""

import time
import json
import logging
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

# 飞书 App token 缓存
_token_cache = {"token": None, "expires_at": 0}


async def get_tenant_token(app_id: str, app_secret: str) -> str:
    """获取飞书 tenant_access_token（自动缓存）"""
    now = time.time()
    if _token_cache["token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["token"]

    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={
                "app_id": app_id,
                "app_secret": app_secret,
            }, timeout=10)
            data = resp.json()
            if data.get("code") == 0:
                token = data["tenant_access_token"]
                expire = data.get("expire", 7200)
                _token_cache["token"] = token
                _token_cache["expires_at"] = now + expire
                return token
            else:
                logger.error("获取飞书 token 失败: %s", data)
                return None
    except Exception as e:
        logger.error("获取飞书 token 异常: %s", e)
        return None


def build_alert_card(camera_name: str, stream_url: str, group_name: str,
                     alert_type: str, notify_note: str = "") -> dict:
    """构建飞书卡片消息"""
    if alert_type == "offline":
        title = "🚨 摄像头离线告警"
        color = "red"
        status = "离线"
    else:
        title = "✅ 摄像头恢复通知"
        color = "green"
        status = "已恢复在线"

    content = (
        f"**设备名称**：{camera_name}\n"
        f"**设备地址**：{stream_url}\n"
        f"**所属分组**：{group_name}\n"
        f"**状态**：{status}\n"
        f"**时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    if notify_note:
        content += f"\n\n📋 **备注**：{notify_note}"

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": title},
            "template": color,
        },
        "elements": [{
            "tag": "div",
            "text": {"tag": "lark_md", "content": content},
        }],
    }


async def send_feishu_app(app_id: str, app_secret: str, receive_id: str,
                           card: dict, receive_id_type: str = "open_id") -> bool:
    """通过飞书 App 机器人发送消息"""
    token = await get_tenant_token(app_id, app_secret)
    if not token:
        return False

    url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body = {
        "receive_id": receive_id,
        "msg_type": "interactive",
        "content": json.dumps(card),
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=body, headers=headers, timeout=10)
            data = resp.json()
            if data.get("code") == 0:
                return True
            else:
                logger.error("飞书发送失败: %s", data)
                return False
    except Exception as e:
        logger.error("飞书发送异常: %s", e)
        return False


async def send_alert_for_camera(camera, alert_type: str, settings: dict = None) -> bool:
    """为摄像头发送告警通知"""
    group_name = camera.group.name if camera.group else "未分组"
    camera_name = camera.name or camera.onvif_host
    stream_url = camera.display_url
    notify_note = camera.group.notify_note if camera.group else ""

    card = build_alert_card(camera_name, stream_url, group_name, alert_type, notify_note)

    if not settings:
        logger.warning("未配置飞书通知，跳过 [%s]", camera_name)
        return False

    app_id = settings.get("feishu_app_id")
    app_secret = settings.get("feishu_app_secret")
    open_id = settings.get("feishu_open_id")
    chat_id = settings.get("feishu_chat_id")

    if not app_id or not app_secret:
        logger.warning("未配置飞书 App 凭证，跳过 [%s]", camera_name)
        return False

    # 优先发给个人
    if open_id:
        if await send_feishu_app(app_id, app_secret, open_id, card, "open_id"):
            logger.info("✅ 飞书通知发送成功（个人） [%s]", camera_name)
            return True

    # 其次发到群聊
    if chat_id:
        if await send_feishu_app(app_id, app_secret, chat_id, card, "chat_id"):
            logger.info("✅ 飞书通知发送成功（群聊） [%s]", camera_name)
            return True

    logger.error("❌ 飞书通知发送失败 [%s]", camera_name)
    return False
