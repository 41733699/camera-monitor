"""认证服务 — JWT + bcrypt"""

import os
import logging
import bcrypt
import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import User

logger = logging.getLogger(__name__)

# JWT 配置
JWT_SECRET = os.getenv("JWT_SECRET", "camera-monitor-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 72  # 3 天过期


def hash_password(plain: str) -> str:
    """bcrypt 哈希密码"""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(user_id: int, username: str, is_admin: bool) -> str:
    """生成 JWT token"""
    payload = {
        "sub": str(user_id),
        "username": username,
        "is_admin": is_admin,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """解码 JWT token，失败返回 None"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("Token 已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning("Token 无效: %s", e)
        return None


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """验证用户名密码，返回 User 或 None"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def ensure_admin(db: Session):
    """确保至少有一个管理员账号（首次启动时创建默认 admin）"""
    admin = db.query(User).filter(User.is_admin == True).first()
    if admin:
        return
    # 创建默认管理员 admin / admin123
    default_pw = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_user = User(
        username="admin",
        password_hash=hash_password(default_pw),
        is_admin=True,
    )
    db.add(admin_user)
    db.commit()
    logger.info("已创建默认管理员账号 admin / %s（请尽快修改密码）", default_pw)
