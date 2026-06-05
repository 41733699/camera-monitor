<template>
  <div class="dashboard">
    <StatsCards :stats="stats" :active-filter="statusFilter" @filter="handleFilter" />

    <!-- 摄像头网格 -->
    <el-card class="camera-grid-card">
      <template #header>
        <div class="card-header">
          <span>
            摄像头状态
            <el-tag v-if="statusFilter === 'online'" type="success" size="small" closable @close="statusFilter = null" style="margin-left: 8px">在线</el-tag>
            <el-tag v-if="statusFilter === 'offline'" type="danger" size="small" closable @close="statusFilter = null" style="margin-left: 8px">离线</el-tag>
          </span>
          <el-button type="primary" @click="refreshData">
            <el-icon><Refresh /></el-icon>
            <span class="btn-text">刷新</span>
          </el-button>
        </div>
      </template>

      <div class="camera-grid">
        <CameraCard
          v-for="cam in filteredCameras"
          :key="cam.id"
          :camera="cam"
          :screenshot="cameraScreenshots[cam.id]?.[0]"
          @click="openCameraDetail(cam)"
        />
      </div>
      <div v-if="filteredCameras.length === 0" class="empty-hint">
        {{ statusFilter ? '没有' + (statusFilter === 'online' ? '在线' : '离线') + '的摄像头' : '暂无摄像头，请先添加设备' }}
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="detailCamera?.name || detailCamera?.onvif_url"
      :width="isMobile ? '95%' : '750px'"
      class="detail-dialog"
    >
      <div v-if="detailCamera">
        <div class="detail-header">
          <span class="status-dot" :class="detailCamera.status" />
          <span>{{ detailCamera.status === 'online' ? '在线' : detailCamera.status === 'offline' ? '离线' : '未知' }}</span>
          <span class="detail-url">{{ detailCamera.display_url }}</span>
        </div>
        <ScreenshotGallery
          :screenshots="detailScreenshots"
          @preview="previewImage"
          @delete="handleDeleteShot"
          @deleteAll="handleDeleteAllScreenshots"
        />
      </div>
    </el-dialog>

    <!-- 图片预览 -->
    <el-dialog v-model="previewVisible" :width="isMobile ? '95%' : '70%'" destroy-on-close>
      <img :src="previewUrl" style="width: 100%; display: block;" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCameras, getStats } from '../api/cameras'
import { getScreenshots, deleteScreenshot, deleteAllScreenshots } from '../api/screenshots'
import StatsCards from './dashboard/StatsCards.vue'
import CameraCard from './dashboard/CameraCard.vue'
import ScreenshotGallery from './dashboard/ScreenshotGallery.vue'

const isMobile = computed(() => window.innerWidth < 768)

const cameras = ref([])
const stats = ref({ total: 0, online: 0, offline: 0, unknown: 0 })
const cameraScreenshots = reactive({})
const statusFilter = ref(null)

const filteredCameras = computed(() => {
  if (!statusFilter.value) return cameras.value
  return cameras.value.filter(c => c.status === statusFilter.value)
})

const handleFilter = (filter) => {
  statusFilter.value = filter
}

const detailVisible = ref(false)
const detailCamera = ref(null)
const detailScreenshots = ref([])

const previewVisible = ref(false)
const previewUrl = ref('')

const fetchData = async () => {
  const [camerasRes, statsRes] = await Promise.all([getCameras(), getStats()])
  cameras.value = camerasRes.data
  stats.value = statsRes.data

  // 并行加载截图
  await Promise.all(
    cameras.value.map(async (cam) => {
      try {
        const res = await getScreenshots(cam.id)
        cameraScreenshots[cam.id] = res.data
      } catch {
        cameraScreenshots[cam.id] = []
      }
    })
  )
}

const refreshData = () => fetchData()

const openCameraDetail = async (cam) => {
  detailCamera.value = cam
  detailVisible.value = true
  try {
    const res = await getScreenshots(cam.id)
    detailScreenshots.value = res.data
  } catch {
    detailScreenshots.value = []
  }
}

const previewImage = (url) => {
  previewUrl.value = url
  previewVisible.value = true
}

const handleDeleteShot = async (shot) => {
  try {
    await deleteScreenshot(detailCamera.value.id, shot.filename)
    detailScreenshots.value = detailScreenshots.value.filter(s => s.filename !== shot.filename)
    const res = await getScreenshots(detailCamera.value.id)
    cameraScreenshots[detailCamera.value.id] = res.data
    ElMessage.success('已删除')
  } catch {
    ElMessage.error('删除失败')
  }
}

const handleDeleteAllScreenshots = async () => {
  try {
    await ElMessageBox.confirm('确定清空该摄像头的全部截图？', '确认', { type: 'warning' })
    await deleteAllScreenshots(detailCamera.value.id)
    detailScreenshots.value = []
    cameraScreenshots[detailCamera.value.id] = []
    ElMessage.success('已清空')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('清空失败')
  }
}

onMounted(() => fetchData())
</script>

<style scoped>
.dashboard { padding: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.empty-hint { text-align: center; color: #999; padding: 60px 0; }

.camera-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

/* 状态指示灯（弹窗内用） */
.status-dot {
  display: inline-block;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 0 6px rgba(0,0,0,0.3);
}
.status-dot.online { background: #67c23a; }
.status-dot.offline { background: #f56c6c; }
.status-dot.unknown { background: #909399; }

.detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}
.detail-url {
  color: #999;
  margin-left: 8px;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 手机端适配 */
@media (max-width: 768px) {
  .camera-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  .btn-text { display: none; }
  .detail-url { display: none; }
}

@media (max-width: 480px) {
  .camera-grid {
    grid-template-columns: 1fr;
  }
}
</style>
