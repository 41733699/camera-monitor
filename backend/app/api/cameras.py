from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import Camera
from ..schemas import CameraCreate, CameraUpdate, CameraResponse, StatsResponse

router = APIRouter(prefix="/api/cameras", tags=["cameras"])

@router.get("/", response_model=List[CameraResponse])
def get_cameras(skip: int = 0, limit: int = 100, group_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Camera).options(joinedload(Camera.group))
    if group_id:
        query = query.filter(Camera.group_id == group_id)
    return query.offset(skip).limit(limit).all()

@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Camera).count()
    online = db.query(Camera).filter(Camera.status == "online").count()
    offline = db.query(Camera).filter(Camera.status == "offline").count()
    unknown = db.query(Camera).filter(Camera.status == "unknown").count()
    return StatsResponse(total=total, online=online, offline=offline, unknown=unknown)

@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(camera_id: int, db: Session = Depends(get_db)):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="摄像头不存在")
    return camera

@router.post("/", response_model=CameraResponse)
def create_camera(camera: CameraCreate, db: Session = Depends(get_db)):
    # ONVIF 地址必填
    if not camera.onvif_url:
        raise HTTPException(status_code=422, detail="ONVIF 地址为必填项")
    db_camera = Camera(
        name=camera.name,
        onvif_url=camera.onvif_url,
        screenshot_enabled=camera.screenshot_enabled,
        rtsp_url=camera.rtsp_url,
        notify_enabled=camera.notify_enabled,
        group_id=camera.group_id,
        check_interval=camera.check_interval,
        retry_count=camera.retry_count,
        location_note=camera.location_note,
    )
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)
    return db_camera

@router.put("/{camera_id}", response_model=CameraResponse)
def update_camera(camera_id: int, camera: CameraUpdate, db: Session = Depends(get_db)):
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not db_camera:
        raise HTTPException(status_code=404, detail="摄像头不存在")
    
    for field in ["name", "onvif_url", "screenshot_enabled", "rtsp_url", "notify_enabled",
                  "group_id", "check_interval", "retry_count", "location_note"]:
        val = getattr(camera, field)
        if val is not None:
            setattr(db_camera, field, val)
    
    db.commit()
    db.refresh(db_camera)
    return db_camera

@router.delete("/{camera_id}")
def delete_camera(camera_id: int, db: Session = Depends(get_db)):
    db_camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not db_camera:
        raise HTTPException(status_code=404, detail="摄像头不存在")
    db.delete(db_camera)
    db.commit()
    return {"message": "摄像头已删除"}

@router.post("/{camera_id}/check")
def check_camera_now(camera_id: int, db: Session = Depends(get_db)):
    """手动检测单个摄像头（ONVIF 心跳）"""
    from ..services.onvif_detector import check_onvif
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="摄像头不存在")
    is_online, latency_ms = check_onvif(camera.onvif_host, camera.onvif_port_parsed, 5, camera.onvif_path)
    now = datetime.now()
    camera.last_check = now
    if is_online:
        camera.status = "online"
        camera.last_online = now
    db.commit()
    db.refresh(camera)
    return {"camera_id": camera_id, "is_online": is_online, "onvif_time": latency_ms, "status": camera.status}
