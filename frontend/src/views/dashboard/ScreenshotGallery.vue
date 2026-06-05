<template>
  <div class="screenshot-gallery">
    <div v-if="screenshots.length === 0" class="empty-hint" style="padding: 40px 0;">
      暂无截图（摄像头在线时自动截取）
    </div>
    <div v-else>
      <div class="screenshot-toolbar">
        <el-button type="danger" size="small" plain @click="$emit('deleteAll')">
          清空全部截图
        </el-button>
      </div>
      <div class="screenshot-grid">
        <div
          v-for="(shot, idx) in screenshots"
          :key="idx"
          class="screenshot-item"
        >
          <img :src="shot.url" alt="截图" @click="$emit('preview', shot.url)" />
          <div class="shot-time">{{ formatTimestamp(shot.created_at) }}</div>
          <div class="shot-delete" @click.stop="$emit('delete', shot)">
            <el-icon><Close /></el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { formatTimestamp } from '../../utils/format'

defineProps({
  screenshots: { type: Array, default: () => [] },
})
defineEmits(['preview', 'delete', 'deleteAll'])
</script>

<style scoped>
.screenshot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}
.screenshot-item {
  border: 1px solid #e6e6e6;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.2s;
  position: relative;
}
.screenshot-item:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,0.15);
}
.screenshot-item img {
  width: 100%;
  height: 110px;
  object-fit: cover;
  display: block;
}
.shot-time {
  font-size: 11px;
  color: #999;
  padding: 6px 8px;
  text-align: center;
  background: #fafafa;
}
.screenshot-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}
.shot-delete {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  background: rgba(0,0,0,0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
}
.screenshot-item:hover .shot-delete {
  opacity: 1;
}

@media (max-width: 768px) {
  .screenshot-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  .screenshot-item img { height: 90px; }
}
</style>
