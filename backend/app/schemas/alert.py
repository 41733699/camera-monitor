"""告警 Schema"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertResponse(BaseModel):
    id: int
    camera_id: int
    alert_type: str
    message: Optional[str]
    notified: int
    created_at: datetime

    class Config:
        from_attributes = True
