# 摄像头状态监测系统 - 部署指南

## 快速部署（推荐）

### 1. 环境要求

- Docker
- Docker Compose

### 2. 部署步骤

```bash
# 克隆项目
git clone https://github.com/41733699/camera-monitor.git
cd camera-monitor

# 使用预构建镜像启动（推荐）
docker-compose up -d

# 或本地构建启动
docker-compose -f docker-compose.build.yml up -d --build

# 查看日志
docker-compose logs -f

# 访问系统
# 前端界面：http://localhost:8088
# API 文档：http://localhost:8088/docs
```

## 使用说明

### 1. 添加分组

1. 访问 http://localhost:8080
2. 点击左侧菜单"分组管理"
3. 点击"添加分组"
4. 填写分组名称（如：KTV、网吧、仓库）
5. 填写飞书 Webhook URL（可选）
6. 点击"确定"

### 2. 添加摄像头

1. 点击左侧菜单"摄像头管理"
2. 点击"添加设备"
3. 填写信息：
   - **摄像头名称**：自定义名称（可选）
   - **动态域名**：你的 Cloudflare 域名
   - **端口号**：摄像头对应的端口
   - **协议类型**：RTSP
   - **流路径**：默认 `/stream1`
   - **所属分组**：选择分组
4. 点击"确定"

### 3. 查看状态

1. 点击左侧菜单"仪表盘"
2. 查看摄像头状态统计
3. 查看摄像头列表
4. 点击"检测"按钮可立即检测摄像头状态

### 4. 查看告警

1. 点击左侧菜单"告警记录"
2. 查看所有告警记录
3. 可按摄像头筛选

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接地址 | `sqlite:///data/camera_monitor.db` |
| `FEISHU_WEBHOOK_URL` | 飞书 Webhook URL | 空 |

### 检测配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `check_interval` | 检测间隔（秒） | 30 |
| `retry_count` | 重试次数 | 3 |
| `timeout` | 超时时间（秒） | 5 |

## 常见问题

### Q: 摄像头一直显示"未知"状态？

A: 检查摄像头地址是否正确，端口是否开放，RTSP 流是否正常。

### Q: 收不到飞书通知？

A: 检查飞书 Webhook URL 是否正确，分组是否配置了 Webhook。

### Q: 检测太频繁导致摄像头卡顿？

A: 调整摄像头的"检测间隔"，建议 30-60 秒。

## 技术栈

- **后端**：Python 3.11 + FastAPI + SQLAlchemy
- **前端**：Vue 3 + Element Plus
- **数据库**：SQLite
- **检测引擎**：OpenCV
- **部署**：Docker Compose

## License

MIT
