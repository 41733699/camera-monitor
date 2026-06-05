"""报表 Schema"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StatusRecordResponse(BaseModel):
    id: int
    camera_id: int
    status: str
    response_time: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class CameraStatsResponse(BaseModel):
    camera_id: int
    camera_name: str
    total_checks: int
    online_count: int
    offline_count: int
    uptime_percent: float
    avg_response_time: Optional[float]
