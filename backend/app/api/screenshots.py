"""截图 API — 列表、查看、删除"""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from ..services.screenshot import get_camera_screenshot_dir

router = APIRouter(prefix="/api/screenshots", tags=["screenshots"])


@router.get("/{camera_id}")
def list_screenshots(camera_id: int):
    """获取某个摄像头的截图列表（最新12张）"""
    d = get_camera_screenshot_dir(camera_id)
    files = sorted(d.glob("*.jpg"), key=lambda f: f.stat().st_mtime, reverse=True)
    return [
        {
            "filename": f.name,
            "url": f"/api/screenshots/{camera_id}/{f.name}",
            "created_at": f.stat().st_mtime,
            "size": f.stat().st_size,
        }
        for f in files[:12]
    ]


@router.get("/{camera_id}/{filename}")
def get_screenshot(camera_id: int, filename: str):
    """获取截图文件"""
    filename = Path(filename).name  # 防止路径穿越
    d = get_camera_screenshot_dir(camera_id)
    filepath = d / filename
    if not filepath.exists() or not filepath.suffix == ".jpg":
        raise HTTPException(status_code=404, detail="截图不存在")
    return FileResponse(str(filepath), media_type="image/jpeg")


@router.delete("/{camera_id}/{filename}")
def delete_screenshot(camera_id: int, filename: str):
    """删除单张截图"""
    filename = Path(filename).name  # 防止路径穿越
    d = get_camera_screenshot_dir(camera_id)
    filepath = d / filename
    if not filepath.exists() or not filepath.suffix == ".jpg":
        raise HTTPException(status_code=404, detail="截图不存在")
    filepath.unlink()
    return {"message": "已删除", "filename": filename}


@router.delete("/{camera_id}")
def delete_all_screenshots(camera_id: int):
    """删除某个摄像头的全部截图"""
    d = get_camera_screenshot_dir(camera_id)
    count = 0
    for f in d.glob("*.jpg"):
        f.unlink()
        count += 1
    return {"deleted": count}
