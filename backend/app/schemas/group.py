"""分组 Schema"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GroupCreate(BaseModel):
    name: str
    notify_note: Optional[str] = ""


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    notify_note: Optional[str] = None


class GroupResponse(BaseModel):
    id: int
    name: str
    notify_note: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
