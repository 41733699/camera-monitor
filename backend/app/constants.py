"""全局常量 — 设置键、默认值、资源控制"""


class SettingKeys:
    """数据库 settings 表的 key 常量"""
    AUTO_NOTIFY = "auto_notify"
    FEISHU_APP_ID = "feishu_app_id"
    FEISHU_APP_SECRET = "feishu_app_secret"
    FEISHU_OPEN_ID = "feishu_open_id"
    FEISHU_CHAT_ID = "feishu_chat_id"
    # ONVIF 心跳
    ONVIF_HEARTBEAT_INTERVAL = "onvif_heartbeat_interval"  # 秒
    # 截图
    SCREENSHOT_INTERVAL = "screenshot_interval"  # 秒，0 = 禁用
    # 免打扰规则（JSON 数组）
    QUIET_RULES = "quiet_rules"


# 设置键的默认值
SETTING_DEFAULTS = {
    SettingKeys.AUTO_NOTIFY: "true",
    SettingKeys.FEISHU_APP_ID: "",
    SettingKeys.FEISHU_APP_SECRET: "",
    SettingKeys.FEISHU_OPEN_ID: "",
    SettingKeys.FEISHU_CHAT_ID: "",
    SettingKeys.ONVIF_HEARTBEAT_INTERVAL: "60",    # 心跳间隔 60 秒
    SettingKeys.SCREENSHOT_INTERVAL: "1800",        # 截图间隔 30 分钟
    SettingKeys.QUIET_RULES: "[]",                  # 免打扰规则
}

# 截图保留数量
MAX_SCREENSHOTS_PER_CAMERA = 12

# 连续失败 N 次才标记离线（防抖）
CONSECUTIVE_FAILURES_THRESHOLD = 2
