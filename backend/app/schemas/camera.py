"""摄像头 Schema"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .group import GroupResponse


class CameraCreate(BaseModel):
    name: Optional[str] = None
    onvif_url: Optional[str] = None
    screenshot_enabled: bool = False
    rtsp_url: Optional[str] = None
    notify_enabled: bool = True
    group_id: Optional[int] = None
    check_interval: int = 30
    retry_count: int = 3
    location_note: Optional[str] = None


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    onvif_url: Optional[str] = None
    screenshot_enabled: Optional[bool] = None
    rtsp_url: Optional[str] = None
    notify_enabled: Optional[bool] = None
    group_id: Optional[int] = None
    check_interval: Optional[int] = None
    retry_count: Optional[int] = None
    location_note: Optional[str] = None


class CameraResponse(BaseModel):
    id: int
    name: Optional[str]
    onvif_url: Optional[str]
    screenshot_enabled: bool
    rtsp_url: Optional[str]
    notify_enabled: bool
    group_id: Optional[int]
    group: Optional[GroupResponse] = None
    status: str
    last_check: Optional[datetime]
    last_online: Optional[datetime]
    check_interval: int
    retry_count: int
    display_url: str
    location_note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total: int
    online: int
    offline: int
    unknown: int
