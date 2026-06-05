"""Schema 包 — 按域拆分，统一导出"""

from .group import GroupCreate, GroupUpdate, GroupResponse
from .camera import CameraCreate, CameraUpdate, CameraResponse, StatsResponse
from .alert import AlertResponse
from .report import StatusRecordResponse, CameraStatsResponse

__all__ = [
    "GroupCreate", "GroupUpdate", "GroupResponse",
    "CameraCreate", "CameraUpdate", "CameraResponse", "StatsResponse",
    "AlertResponse",
    "StatusRecordResponse", "CameraStatsResponse",
]
