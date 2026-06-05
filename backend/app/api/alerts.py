from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from ..database import get_db
from ..models import Alert
from ..schemas import AlertResponse

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.get("/")
def get_alerts(skip: int = 0, limit: int = 100, camera_id: int = None, db: Session = Depends(get_db)):
    """获取告警记录（带摄像头信息）"""
    query = db.query(Alert).options(joinedload(Alert.camera)).order_by(Alert.created_at.desc())
    if camera_id:
        query = query.filter(Alert.camera_id == camera_id)
    alerts = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": a.id,
            "camera_id": a.camera_id,
            "alert_type": a.alert_type,
            "message": a.message,
            "notified": a.notified,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "camera": {
                "id": a.camera.id,
                "name": a.camera.name,
                "onvif_url": a.camera.onvif_url,
            } if a.camera else None,
        }
        for a in alerts
    ]

@router.get("/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).options(joinedload(Alert.camera)).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    return {
        "id": alert.id,
        "camera_id": alert.camera_id,
        "alert_type": alert.alert_type,
        "message": alert.message,
        "notified": alert.notified,
        "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "camera": {
            "id": alert.camera.id,
            "name": alert.camera.name,
            "onvif_url": alert.camera.onvif_url,
        } if alert.camera else None,
    }

@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")
    db.delete(alert)
    db.commit()
    return {"message": "告警已删除"}

@router.delete("/")
def clear_all_alerts(db: Session = Depends(get_db)):
    """清空所有告警"""
    count = db.query(Alert).delete()
    db.commit()
    return {"message": f"已清空 {count} 条告警"}
