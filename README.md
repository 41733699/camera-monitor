# 📹 摄像头状态监测系统

> 轻量级摄像头在线状态监测平台，基于 ONVIF 心跳检测，支持飞书告警通知、定时截图、免打扰规则。

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![Vue3](https://img.shields.io/badge/Vue-3.3-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| **ONVIF 心跳检测** | 轻量 HTTP 探测（GetSystemDateAndTime），无需认证，50~200ms/个 |
| **定时截图** | 对在线摄像头定时截取 RTSP 视频画面（ffmpeg），可按摄像头开关 |
| **飞书通知** | 掉线/恢复自动推送到飞书群，支持全局开关 + 免打扰规则 + 单摄像头通知开关 |
| **免打扰规则** | 支持每日时段、指定日期、每周几三种规则，多条并存 |
| **分组管理** | 摄像头分组，每组可设通知备注（如"请通知张三"） |
| **统计报表** | 可用率统计、在线趋势图、状态变更记录 |
| **数据备份** | 导出/导入 JSON 备份，一键迁移 |
| **JWT 认证** | 管理后台登录保护，token 72h 有效 |

---

## 📸 界面预览

### 登录页
![登录页](screenshots/01-login.png)

### 仪表盘
![仪表盘](screenshots/02-dashboard.png)

### 添加摄像头
![添加摄像头](screenshots/03-add-camera-dialog.png)

### 摄像头管理
![摄像头管理](screenshots/04-cameras.png)

### 告警记录
![告警记录](screenshots/06-alerts.png)

### 统计报表
![统计报表](screenshots/07-reports.png)

### 系统设置
![系统设置](screenshots/08-settings.png)

---

## 🏗️ 技术架构

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Vue 3 前端  │────▶│  FastAPI 后端  │────▶│   SQLite DB   │
│  Element Plus │     │   APScheduler │     │   WAL 模式    │
│  Vite 构建    │     │   httpx       │     │              │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
          ONVIF 设备    RTSP 流      飞书 API
          (心跳检测)   (ffmpeg截图)  (告警通知)
```

### 后端技术栈
- **FastAPI** — 高性能异步 Web 框架
- **SQLAlchemy** — ORM 数据库操作
- **APScheduler** — 定时任务调度
- **httpx** — 异步 HTTP 客户端（ONVIF 检测）
- **ffmpeg** — RTSP 视频流截图
- **bcrypt + JWT** — 密码加密与身份认证

### 前端技术栈
- **Vue 3** — Composition API
- **Element Plus** — UI 组件库
- **Vue Router** — 路由管理
- **Axios** — HTTP 请求
- **Vite** — 构建工具

---

## 📁 项目结构

```
camera-monitor/
├── backend/
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   ├── alerts.py   # 告警记录 CRUD
│   │   │   ├── auth.py     # 登录认证
│   │   │   ├── backup.py   # 数据导入导出
│   │   │   ├── cameras.py  # 摄像头管理
│   │   │   ├── groups.py   # 分组管理
│   │   │   ├── patrol.py   # 巡检设置
│   │   │   └── reports.py  # 统计报表
│   │   ├── models.py       # 数据库模型
│   │   ├── schemas/        # Pydantic 校验
│   │   ├── services/       # 业务逻辑
│   │   │   ├── auth.py     # JWT 认证
│   │   │   ├── notifier.py # 飞书通知
│   │   │   ├── onvif_detector.py  # ONVIF 检测
│   │   │   ├── scheduler.py       # 定时任务
│   │   │   └── screenshot.py      # RTSP 截图
│   │   ├── config.py       # 路径/数据库配置
│   │   ├── constants.py    # 系统常量
│   │   ├── database.py     # SQLAlchemy 引擎
│   │   └── main.py         # FastAPI 入口
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # API 调用封装
│   │   ├── router/         # 路由配置
│   │   ├── utils/          # 工具函数
│   │   ├── views/          # 页面组件
│   │   │   ├── Dashboard.vue
│   │   │   ├── Cameras.vue
│   │   │   ├── Groups.vue
│   │   │   ├── Alerts.vue
│   │   │   ├── Reports.vue
│   │   │   ├── Settings.vue
│   │   │   └── Login.vue
│   │   ├── App.vue
│   │   └── main.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
├── camera-monitor.service  # systemd 服务文件
└── README.md
```

---

## 🚀 快速部署

### 方式一：systemd 直接部署（推荐）

#### 1. 环境要求

```bash
# Python 3.10+, Node.js 18+, ffmpeg
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm ffmpeg
```

#### 2. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/camera-monitor.git
cd camera-monitor
```

#### 3. 后端部署

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 创建 .env 配置文件
cat > .env << 'EOF'
# 飞书机器人配置（可选）
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_app_secret

# JWT 密钥（生产环境请修改）
JWT_SECRET=your-random-secret-key

# 管理员密码（首次启动时创建，默认 admin123）
ADMIN_PASSWORD=admin123
EOF

# 启动后端（开发模式）
uvicorn app.main:app --host 0.0.0.0 --port 8088
```

#### 4. 前端构建

```bash
cd frontend
npm install
npm run build
# 产物在 frontend/dist/
```

#### 5. 配置 nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/camera-monitor/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 6. systemd 服务

```bash
# 编辑 camera-monitor.service 中的路径
sudo cp camera-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable camera-monitor
sudo systemctl start camera-monitor
```

### 方式二：Docker Compose

```bash
docker-compose up -d
# 后端: http://localhost:8000
# 前端: http://localhost:8080
```

---

## 📖 使用说明

### 1. 登录系统

- 默认账号：`admin`
- 默认密码：`admin123`（首次部署后请修改）
- Token 有效期：72 小时

### 2. 添加摄像头

1. 进入「摄像头管理」→ 点击「添加设备」
2. 填写 **ONVIF 地址**（必填）：粘贴完整的 ONVIF 服务地址
   ```
   http://192.168.1.100:80/onvif/device_service
   ```
3. 可选：开启截图 → 填写 RTSP 地址
   ```
   rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101
   ```
4. 选择分组、填写安装位置
5. 点击「确定」保存

### 3. 配置飞书通知

1. 进入「系统设置」
2. 填写飞书 App ID 和 App Secret
3. 开启「自动通知」开关
4. 可选：添加免打扰规则（如夜间 23:00-07:00 不通知）

### 4. 查看报表

- 进入「统计报表」查看摄像头可用率、在线趋势
- 支持按时间范围、分组、摄像头筛选

### 5. 数据备份

- 进入「系统设置」→「导出备份」保存 JSON 文件
- 「导入备份」可恢复摄像头和分组配置

---

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///data/camera_monitor.db` |
| `JWT_SECRET` | JWT 签名密钥 | `camera-monitor-secret-key-change-in-production` |
| `JWT_EXPIRE_HOURS` | Token 有效期（小时） | `72` |
| `ADMIN_PASSWORD` | 默认管理员密码 | `admin123` |
| `FEISHU_APP_ID` | 飞书应用 ID | — |
| `FEISHU_APP_SECRET` | 飞书应用 Secret | — |
| `DETECT_TIMEOUT` | ONVIF 检测超时（秒） | `5` |

### 定时任务参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 心跳间隔 | ONVIF 检测频率 | 60 秒 |
| 截图间隔 | RTSP 截图频率 | 1800 秒（30分钟） |
| 自动通知 | 掉线自动飞书通知 | 开启 |

---

## 🔧 API 接口

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录获取 token |

### 摄像头

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cameras/` | 获取摄像头列表 |
| POST | `/api/cameras/` | 添加摄像头 |
| PUT | `/api/cameras/{id}` | 更新摄像头 |
| DELETE | `/api/cameras/{id}` | 删除摄像头 |
| POST | `/api/cameras/{id}/check` | 手动检测单个摄像头 |

### 分组

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/groups/` | 获取分组列表 |
| POST | `/api/groups/` | 创建分组 |
| PUT | `/api/groups/{id}` | 更新分组 |
| DELETE | `/api/groups/{id}` | 删除分组 |

### 告警

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/alerts/` | 获取告警记录 |
| DELETE | `/api/alerts/{id}` | 删除单条告警 |
| DELETE | `/api/alerts/` | 清空所有告警 |

### 设置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/patrol/settings` | 获取系统设置 |
| PUT | `/api/patrol/settings` | 更新系统设置 |
| POST | `/api/patrol/heartbeat` | 立即执行心跳检测 |
| POST | `/api/patrol/screenshot` | 立即执行截图 |

### 备份

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/backup/export` | 导出 JSON 备份 |
| POST | `/api/backup/import` | 导入 JSON 备份 |

### 报表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/reports/availability` | 可用率统计 |
| GET | `/api/reports/trend` | 在线趋势 |
| GET | `/api/reports/status-changes` | 状态变更记录 |

---

## 🔒 安全说明

- 默认密码为 `admin123`，**部署后请立即修改**
- JWT Secret 请使用随机字符串，勿使用默认值
- 生产环境建议使用 HTTPS（通过 nginx + Let's Encrypt）
- ONVIF/RTSP 地址中的密码会存储在数据库中，请确保数据库文件安全

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License
