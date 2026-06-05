<template>
  <div class="alerts">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>告警记录</span>
          <el-button type="danger" @click="handleClearAll">清空记录</el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-select v-model="filterCameraId" placeholder="按摄像头筛选" clearable @change="fetchAlerts">
          <el-option
            v-for="camera in cameras"
            :key="camera.id"
            :label="camera.name || camera.onvif_url"
            :value="camera.id"
          />
        </el-select>
      </div>

      <el-table :data="alerts" stripe style="width: 100%">
        <el-table-column label="摄像头" min-width="160">
          <template #default="{ row }">
            <span v-if="row.camera">{{ row.camera.name || row.camera.onvif_url }}</span>
            <span v-else style="color: #999">已删除的设备</span>
          </template>
        </el-table-column>
        <el-table-column prop="alert_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.alert_type === 'offline' ? 'danger' : 'success'" size="small">
              {{ row.alert_type === 'offline' ? '离线' : '恢复' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="消息" min-width="250" />
        <el-table-column prop="notified" label="通知" width="80">
          <template #default="{ row }">
            <el-tag :type="row.notified ? 'success' : 'warning'" size="small">
              {{ row.notified ? '已' : '未' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="alerts.length === 0" class="empty-hint">暂无告警记录</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAlerts, deleteAlert } from '../api/alerts'
import { getCameras } from '../api/cameras'

const alerts = ref([])
const cameras = ref([])
const filterCameraId = ref(null)

const fetchAlerts = async () => {
  const params = {}
  if (filterCameraId.value) params.camera_id = filterCameraId.value
  alerts.value = (await getAlerts(params)).data
}

const fetchCameras = async () => {
  cameras.value = (await getCameras()).data
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定删除这条记录？', '提示', { type: 'warning' })
    await deleteAlert(row.id)
    ElMessage.success('已删除')
    fetchAlerts()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

const handleClearAll = async () => {
  try {
    await ElMessageBox.confirm('确定清空所有告警记录？不可恢复！', '警告', { type: 'warning' })
    // 调用批量清空 API
    const { default: api } = await import('../api')
    await api.delete('/alerts/')
    ElMessage.success('已清空')
    fetchAlerts()
  } catch (e) { if (e !== 'cancel') ElMessage.error('清空失败') }
}

onMounted(() => {
  fetchAlerts()
  fetchCameras()
})
</script>

<style scoped>
.alerts { padding: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-bar { margin-bottom: 20px; }
.empty-hint { text-align: center; color: #999; padding: 40px 0; }
</style>
