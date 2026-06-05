<template>
  <el-row :gutter="16" class="stats-row">
    <el-col :xs="12" :sm="6">
      <el-card shadow="hover" class="stats-card">
        <div class="stats-content">
          <div class="stats-icon" style="background-color: #409eff">
            <el-icon><VideoCamera /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ stats.total }}</div>
            <div class="stats-label">摄像头总数</div>
          </div>
        </div>
      </el-card>
    </el-col>
    <el-col :xs="12" :sm="6">
      <el-card
        shadow="hover"
        class="stats-card clickable"
        :class="{ active: activeFilter === 'online' }"
        @click="$emit('filter', activeFilter === 'online' ? null : 'online')"
      >
        <div class="stats-content">
          <div class="stats-icon" style="background-color: #67c23a">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ stats.online }}</div>
            <div class="stats-label">在线</div>
          </div>
        </div>
      </el-card>
    </el-col>
    <el-col :xs="12" :sm="6">
      <el-card
        shadow="hover"
        class="stats-card clickable"
        :class="{ active: activeFilter === 'offline' }"
        @click="$emit('filter', activeFilter === 'offline' ? null : 'offline')"
      >
        <div class="stats-content">
          <div class="stats-icon" style="background-color: #f56c6c">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stats-info">
            <div class="stats-value">{{ stats.offline }}</div>
            <div class="stats-label">离线</div>
          </div>
        </div>
      </el-card>
    </el-col>
  </el-row>
</template>

<script setup>
import { VideoCamera, CircleCheck, CircleClose } from '@element-plus/icons-vue'

defineProps({
  stats: { type: Object, default: () => ({ total: 0, online: 0, offline: 0 }) },
  activeFilter: { type: String, default: null },
})
defineEmits(['filter'])
</script>

<style scoped>
.stats-row { margin-bottom: 16px; }
.stats-card { height: 90px; }
.stats-content { display: flex; align-items: center; height: 100%; }
.stats-icon {
  width: 50px; height: 50px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; margin-right: 12px;
  flex-shrink: 0;
}
.stats-icon .el-icon { font-size: 24px; color: #fff; }
.stats-info { flex: 1; min-width: 0; }
.stats-value { font-size: 24px; font-weight: bold; color: #333; line-height: 1.2; }
.stats-label { font-size: 13px; color: #999; margin-top: 2px; }

.clickable { cursor: pointer; transition: box-shadow 0.2s, transform 0.15s; }
.clickable:hover { transform: translateY(-2px); }
.clickable.active { border-color: var(--el-color-primary); box-shadow: 0 0 0 2px rgba(64,158,255,0.2); }

@media (max-width: 768px) {
  .stats-card { height: 80px; }
  .stats-icon { width: 40px; height: 40px; margin-right: 8px; }
  .stats-icon .el-icon { font-size: 20px; }
  .stats-value { font-size: 20px; }
  .stats-label { font-size: 12px; }
}
</style>
