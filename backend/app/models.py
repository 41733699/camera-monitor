from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    notify_note = Column(String(200), nullable=True, default="")
    created_at = Column(DateTime, default=datetime.now)

    cameras = relationship("Camera", back_populates="group", cascade="all, delete-orphan")

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    # 核心字段
    onvif_url = Column(String(500), nullable=True)        # ONVIF 完整地址
    screenshot_enabled = Column(Boolean, default=False)    # 是否启用截图
    rtsp_url = Column(String(500), nullable=True)          # 完整 RTSP 地址
    notify_enabled = Column(Boolean, default=True)         # 是否发送通知（仅记录不通知）
    # 以下为废弃字段，仅保留数据库兼容，新代码不再使用
    onvif_domain = Column(String(200), nullable=True)
    onvif_port = Column(Integer, default=80)
    domain = Column(String(200), nullable=True)
    port = Column(Integer, default=554)
    protocol = Column(String(20), default="rtsp")
    path = Column(String(200), default="/stream1")
    username = Column(String(100), nullable=True)
    password = Column(String(100), nullable=True)
    # 厂商 SDK 字段
    vendor = Column(String(20), default="generic", nullable=False)  # generic | hikvision | dahua
    device_ip = Column(String(200), nullable=True)
    http_port = Column(Integer, default=80)
    channel = Column(Integer, default=1)
    # 其他
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True, index=True)
    status = Column(String(20), default="unknown", index=True)
    last_check = Column(DateTime, nullable=True)
    last_online = Column(DateTime, nullable=True)
    check_interval = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    location_note = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    group = relationship("Group", back_populates="cameras")
    alerts = relationship("Alert", back_populates="camera", cascade="all, delete-orphan")
    status_records = relationship("StatusRecord", back_populates="camera", cascade="all, delete-orphan")

    @property
    def onvif_host(self):
        """ONVIF 检测地址（从 onvif_url 解析 host）"""
        if self.onvif_url:
            from urllib.parse import urlparse
            p = urlparse(self.onvif_url)
            return p.hostname or ""
        return self.onvif_domain or ""

    @property
    def onvif_port_parsed(self):
        """从 onvif_url 解析端口"""
        if self.onvif_url:
            from urllib.parse import urlparse
            p = urlparse(self.onvif_url)
            return p.port or 80
        return self.onvif_port or 80

    @property
    def onvif_path(self):
        """从 onvif_url 解析路径"""
        if self.onvif_url:
            from urllib.parse import urlparse
            p = urlparse(self.onvif_url)
            return p.path or "/onvif/device_service"
        return "/onvif/device_service"

    @property
    def display_url(self):
        """不暴露密码的显示 URL"""
        url = self.rtsp_url or self.onvif_url or ""
        if url:
            import re
            return re.sub(r"(://[^:]+:)[^@]+(@)", r"\1***\2", url)
        return self.onvif_host or "未配置"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(20), nullable=False)
    message = Column(Text, nullable=True)
    notified = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.now, index=True)

    camera = relationship("Camera", back_populates="alerts")

class StatusRecord(Base):
    __tablename__ = "status_records"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    tcp_time = Column(Integer, nullable=True)      # TCP 连接耗时 ms
    response_time = Column(Integer, nullable=True)  # RTSP 握手耗时 ms
    onvif_time = Column(Integer, nullable=True)     # ONVIF 心跳耗时 ms
    check_type = Column(String(20), default="onvif")  # onvif | deep（深度巡检）
    created_at = Column(DateTime, default=datetime.now, index=True)

    camera = relationship("Camera", back_populates="status_records")

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
