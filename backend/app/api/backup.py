from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import Group, Camera, Setting

router = APIRouter(prefix="/api/backup", tags=["backup"])

@router.get("/export")
def export_config(db: Session = Depends(get_db)):
    groups = db.query(Group).all()
    cameras = db.query(Camera).all()
    settings = db.query(Setting).all()
    
    data = {
        "version": "3.0",
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "groups": [
            {"name": g.name, "notify_note": g.notify_note}
            for g in groups
        ],
        "cameras": [
            {
                "name": c.name,
                "onvif_url": c.onvif_url,
                "screenshot_enabled": c.screenshot_enabled,
                "rtsp_url": c.rtsp_url,
                "check_interval": c.check_interval,
                "retry_count": c.retry_count,
                "location_note": c.location_note,
                "group_name": c.group.name if c.group else None,
            }
            for c in cameras
        ],
        "settings": [
            {"key": s.key, "value": "***" if "secret" in s.key.lower() or "password" in s.key.lower() else s.value}
            for s in settings
        ]
    }
    
    return JSONResponse(content=data)

@router.post("/import")
async def import_config(file: UploadFile = File(...), db: Session = Depends(get_db)):
    import json
    
    content = await file.read()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"error": "无效的 JSON 文件"})
    
    if "version" not in data:
        return JSONResponse(status_code=400, content={"error": "缺少版本信息"})
    
    errors = []
    groups_imported = cameras_imported = settings_imported = 0
    
    group_map = {}
    for g_data in data.get("groups", []):
        try:
            existing = db.query(Group).filter(Group.name == g_data["name"]).first()
            if existing:
                if g_data.get("notify_note"):
                    existing.notify_note = g_data["notify_note"]
                group_map[g_data["name"]] = existing
            else:
                group = Group(name=g_data["name"], notify_note=g_data.get("notify_note"))
                db.add(group)
                db.flush()
                group_map[g_data["name"]] = group
                groups_imported += 1
        except Exception as e:
            errors.append(f"分组 '{g_data.get('name')}' 失败: {str(e)}")
    
    for c_data in data.get("cameras", []):
        try:
            onvif_url = c_data.get("onvif_url", "")
            if not onvif_url:
                errors.append(f"摄像头 '{c_data.get('name', '?')}' 缺少 onvif_url，跳过")
                continue

            existing = db.query(Camera).filter(Camera.onvif_url == onvif_url).first()

            group_id = None
            if c_data.get("group_name") and c_data["group_name"] in group_map:
                group_id = group_map[c_data["group_name"]].id

            fields = ["name", "screenshot_enabled", "rtsp_url",
                      "check_interval", "retry_count", "location_note"]

            if existing:
                for field in fields:
                    if c_data.get(field) is not None:
                        setattr(existing, field, c_data[field])
                if group_id:
                    existing.group_id = group_id
            else:
                camera = Camera(
                    onvif_url=onvif_url,
                    group_id=group_id,
                    **{f: c_data.get(f) for f in fields}
                )
                db.add(camera)
                cameras_imported += 1
        except Exception as e:
            errors.append(f"摄像头 '{c_data.get('name', '?')}' 失败: {str(e)}")
    
    for s_data in data.get("settings", []):
        try:
            existing = db.query(Setting).filter(Setting.key == s_data["key"]).first()
            if existing:
                existing.value = s_data["value"]
                existing.updated_at = datetime.now()
            else:
                db.add(Setting(key=s_data["key"], value=s_data["value"]))
            settings_imported += 1
        except Exception as e:
            errors.append(f"设置 '{s_data.get('key')}' 失败: {str(e)}")
    
    db.commit()
    return {
        "groups_imported": groups_imported,
        "cameras_imported": cameras_imported,
        "settings_imported": settings_imported,
        "errors": errors,
    }
