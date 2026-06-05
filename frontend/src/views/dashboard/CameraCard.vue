<template>
  <div class="camera-tile" @click="$emit('click', camera)">
    <!-- 截图区域 -->
    <div class="tile-preview">
      <img
        v-if="screenshot"
        :src="screenshot.url"
        class="preview-img"
        alt="截图"
      />
      <div v-else class="preview-placeholder">
        <el-icon :size="32"><VideoCamera /></el-icon>
        <span v-if="camera.status === 'online'">在线 · 等待截图</span>
        <span v-else-if="camera.status === 'offline'">离线</span>
        <span v-else>未检测</span>
      </div>
      <!-- 状态灯 -->
      <div class="status-dot-wrap">
        <span class="status-dot" :class="camera.status" />
      </div>
    </div>
    <!-- 信息 -->
    <div class="tile-info">
      <div class="tile-name">{{ camera.name || camera.onvif_url }}</div>
      <div class="tile-sub">
        <span>{{ camera.location_note || camera.onvif_url }}</span>
        <span class="tile-time">{{ formatTime(camera.last_check) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatTime } from '../../utils/format'

defineProps({
  camera: { type: Object, required: true },
  screenshot: { type: Object, default: null },
})
defineEmits(['click'])
</script>

<style scoped>
.camera-tile {
  border: 1px solid #e6e6e6;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.15s;
  background: #fff;
}
.camera-tile:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  transform: translateY(-2px);
}

.tile-preview {
  position: relative;
  width: 100%;
  height: 160px;
  background: #1a1a2e;
  overflow: hidden;
}
.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 13px;
  gap: 6px;
}

.status-dot-wrap {
  position: absolute;
  top: 10px;
  right: 10px;
}
.status-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 0 6px rgba(0,0,0,0.3);
}
.status-dot.online {
  background: #67c23a;
  box-shadow: 0 0 6px rgba(103,194,58,0.6);
}
.status-dot.offline {
  background: #f56c6c;
  box-shadow: 0 0 6px rgba(245,108,108,0.6);
}
.status-dot.unknown {
  background: #909399;
}

.tile-info {
  padding: 10px 12px;
}
.tile-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tile-sub {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
.tile-time {
  white-space: nowrap;
}

@media (max-width: 768px) {
  .tile-preview { height: 120px; }
}
</style>
