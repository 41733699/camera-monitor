from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text, case
from sqlalchemy.orm import joinedload
from typing import Optional
from datetime import datetime, timedelta
from ..database import get_db
from ..models import StatusRecord, Camera
from ..schemas import StatusRecordResponse, CameraStatsResponse

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/history")
def get_status_history(
    camera_id: Optional[int] = None,
    days: int = Query(default=7, ge=1, le=90),
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db)
):
    """获取状态历史记录"""
    since = datetime.now() - timedelta(days=days)
    query = db.query(StatusRecord).filter(StatusRecord.created_at >= since)
    
    if camera_id:
        query = query.filter(StatusRecord.camera_id == camera_id)
    
    total = query.count()
    records = query.order_by(StatusRecord.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "records": [
            {
                "id": r.id,
                "camera_id": r.camera_id,
                "status": r.status,
                "tcp_time": r.tcp_time,
                "response_time": r.response_time,
                "onvif_time": r.onvif_time,
                "check_type": r.check_type or "onvif",
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for r in records
        ]
    }

@router.get("/camera-stats")
def get_camera_stats(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """获取各摄像头的可用率统计（单次 GROUP BY 查询）"""
    since = datetime.now() - timedelta(days=days)
    
    stats = db.query(
        StatusRecord.camera_id,
        func.count().label("total"),
        func.sum(case((StatusRecord.status == "online", 1), else_=0)).label("online"),
        func.avg(StatusRecord.tcp_time).label("avg_tcp"),
        func.avg(StatusRecord.response_time).label("avg_rt"),
        func.avg(StatusRecord.onvif_time).label("avg_onvif"),
    ).filter(
        StatusRecord.created_at >= since
    ).group_by(StatusRecord.camera_id).all()
    
    cameras = {c.id: c for c in db.query(Camera).options(
        joinedload(Camera.group)
    ).all()}
    
    results = []
    for row in stats:
        camera = cameras.get(row.camera_id)
        if not camera:
            continue
        total = row.total
        online = int(row.online or 0)
        avg_tcp = row.avg_tcp
        avg_rt = row.avg_rt
        avg_onvif = row.avg_onvif
        uptime = round((online / total * 100), 1) if total > 0 else 0.0
        
        results.append({
            "camera_id": camera.id,
            "camera_name": camera.name or camera.onvif_host,
            "group_name": camera.group.name if camera.group else "未分组",
            "total_checks": total,
            "online_count": online,
            "offline_count": total - online,
            "uptime_percent": uptime,
            "avg_tcp_time": round(avg_tcp, 1) if avg_tcp else None,
            "avg_response_time": round(avg_rt, 1) if avg_rt else None,
            "avg_onvif_time": round(avg_onvif, 1) if avg_onvif else None,
        })
    
    return results

@router.get("/hourly")
def get_hourly_stats(
    camera_id: Optional[int] = None,
    days: int = Query(default=1, ge=1, le=7),
    db: Session = Depends(get_db)
):
    """按小时聚合状态（用于图表展示）"""
    since = datetime.now() - timedelta(days=days)
    
    sql = """
        SELECT 
            strftime('%Y-%m-%d %H:00', created_at) as hour,
            count(*) as total,
            sum(CASE WHEN status='online' THEN 1 ELSE 0 END) as online
        FROM status_records 
        WHERE created_at >= :since
    """
    params = {"since": since.isoformat()}
    if camera_id:
        sql += " AND camera_id = :cid"
        params["cid"] = camera_id
    sql += " GROUP BY strftime('%Y-%m-%d %H:00', created_at) ORDER BY hour"
    
    results = db.execute(text(sql), params).fetchall()
    
    return [
        {
            "hour": row[0],
            "total": row[1],
            "online": row[2],
            "offline": row[1] - row[2],
            "uptime_percent": round(row[2] / row[1] * 100, 1) if row[1] > 0 else 0,
        }
        for row in results
    ]


@router.delete("/records")
def clear_status_records(
    camera_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """清除状态记录"""
    query = db.query(StatusRecord)
    if camera_id:
        query = query.filter(StatusRecord.camera_id == camera_id)
    deleted = query.delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}
