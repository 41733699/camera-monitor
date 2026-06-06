"""数据库迁移 — 添加厂商 SDK 字段（vendor, device_ip, http_port, channel）

运行方式：python -m app.migrate_add_vendor_fields
"""

import sqlite3
import sys
import os


def get_db_path():
    """从 config 获取数据库路径"""
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./data/camera_monitor.db")
    # sqlite:///./data/camera_monitor.db -> ./data/camera_monitor.db
    if db_url.startswith("sqlite:///"):
        return db_url[len("sqlite:///"):]
    return db_url


def migrate(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查列是否已存在
    cursor.execute("PRAGMA table_info(cameras)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    new_columns = [
        ("vendor", "VARCHAR(20) NOT NULL DEFAULT 'generic'"),
        ("device_ip", "VARCHAR(200)"),
        ("http_port", "INTEGER DEFAULT 80"),
        ("channel", "INTEGER DEFAULT 1"),
    ]

    for col_name, col_def in new_columns:
        if col_name not in existing_cols:
            sql = f"ALTER TABLE cameras ADD COLUMN {col_name} {col_def}"
            print(f"执行: {sql}")
            cursor.execute(sql)
        else:
            print(f"列 {col_name} 已存在，跳过")

    conn.commit()
    conn.close()
    print("迁移完成")


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else get_db_path()
    print(f"数据库路径: {db_path}")
    migrate(db_path)
