from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
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
    # 厂商 SDK 模式不需要 onvif_url，generic 模式需要
    if camera.vendor == "generic" and not camera.onvif_url:
        raise HTTPException(status_code=422, detail="ONVIF 地址为必填项（generic 模式）")
    if camera.vendor != "generic" and not camera.device_ip:
        raise HTTPException(status_code=422, detail="厂商 SDK 模式需要 device_ip")
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
        vendor=camera.vendor,
        device_ip=camera.device_ip,
        http_port=camera.http_port,
        channel=camera.channel,
        username=camera.username,
        password=camera.password,
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
                  "group_id", "check_interval", "retry_count", "location_note",
                  "vendor", "device_ip", "http_port", "channel", "username", "password"]:
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
    """手动检测单个摄像头（ONVIF 心跳或厂商 SDK）"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="摄像头不存在")

    vendor = getattr(camera, "vendor", "generic") or "generic"
    if vendor != "generic" and camera.device_ip:
        from ..services.scheduler import _device_heartbeat
        is_online, latency_ms = _device_heartbeat(
            vendor, camera.device_ip, camera.http_port or 80,
            camera.username or "", camera.password or "", 5
        )
    else:
        from ..services.onvif_detector import check_onvif
        is_online, latency_ms = check_onvif(camera.onvif_host, camera.onvif_port_parsed, 5, camera.onvif_path)

    now = datetime.now()
    camera.last_check = now
    if is_online:
        camera.status = "online"
        camera.last_online = now
    else:
        camera.status = "offline"
    db.commit()
    db.refresh(camera)
    return {"camera_id": camera_id, "is_online": is_online, "latency_ms": latency_ms, "status": camera.status}


@router.get("/{camera_id}/stream")
def get_stream_url(camera_id: int, db: Session = Depends(get_db)):
    """获取摄像头 RTSP 流地址"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="摄像头不存在")

    vendor = getattr(camera, "vendor", "generic") or "generic"

    if camera.rtsp_url:
        return {"rtsp_url": camera.rtsp_url, "vendor": vendor}

    if vendor != "generic" and camera.device_ip:
        from ..services.device_api import HikvisionClient, DahuaClient
        ip = camera.device_ip
        port = camera.http_port or 80
        channel = camera.channel or 1
        username = camera.username or ""
        password = camera.password or ""

        if vendor == "hikvision":
            rtsp_url = HikvisionClient.get_rtsp_url(ip, port, channel, username, password)
        elif vendor == "dahua":
            rtsp_url = DahuaClient.get_rtsp_url(ip, port, channel, username, password)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的厂商: {vendor}")

        return {"rtsp_url": rtsp_url, "vendor": vendor}

    raise HTTPException(status_code=400, detail="未配置 RTSP 地址或设备信息")


@router.post("/{camera_id}/snapshot")
def take_snapshot(camera_id: int, db: Session = Depends(get_db)):
    """实时抓取摄像头快照"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="摄像头不存在")

    vendor = getattr(camera, "vendor", "generic") or "generic"

    if vendor != "generic" and camera.device_ip:
        from ..services.screenshot import capture_screenshot_device_sync
        jpeg_bytes = capture_screenshot_device_sync(camera)
    elif camera.rtsp_url:
        # 对 generic 摄像头使用 ffmpeg 截取
        import subprocess, tempfile, os
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.close()
        try:
            result = subprocess.run(
                ["ffmpeg", "-y", "-rtsp_transport", "tcp",
                 "-timeout", "10000000",
                 "-i", camera.rtsp_url,
                 "-frames:v", "1", "-q:v", "2",
                 "-vf", "scale='min(640,iw)':-2",
                 tmp.name],
                capture_output=True, timeout=15
            )
            if result.returncode == 0 and os.path.getsize(tmp.name) > 0:
                jpeg_bytes = open(tmp.name, "rb").read()
            else:
                raise HTTPException(status_code=502, detail="RTSP 截图失败")
        finally:
            os.unlink(tmp.name)
    else:
        raise HTTPException(status_code=400, detail="未配置截图所需的设备信息或 RTSP 地址")

    if not jpeg_bytes:
        raise HTTPException(status_code=502, detail="截图失败")

    return Response(content=jpeg_bytes, media_type="image/jpeg")
