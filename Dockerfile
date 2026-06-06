# ── Stage 1: 构建前端 ──
FROM node:18-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./

ARG NPM_REGISTRY=https://registry.npmmirror.com
RUN npm install --registry=${NPM_REGISTRY}

COPY frontend/ .

RUN npm run build

# ── Stage 2: 后端 + 前端静态文件 ──
FROM python:3.11-slim

WORKDIR /app

# 使用清华 Debian 镜像加速（HTTPS，适配 DEB822 格式）
RUN sed -i 's|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's|http://security.debian.org|https://mirrors.tuna.tsinghua.edu.cn/debian-security|g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# 安装 Python 依赖（默认使用清华源加速）
ARG PIP_INDEX_URL=https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
RUN pip install --no-cache-dir -i ${PIP_INDEX_URL} --trusted-host mirrors.tuna.tsinghua.edu.cn -r requirements.txt

# 复制后端代码
COPY backend/ .

# 复制前端构建产物
COPY --from=frontend-build /frontend/dist ./frontend/dist

# 创建数据目录
RUN mkdir -p /app/data/screenshots /app/data/uploads

EXPOSE 8088

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]
