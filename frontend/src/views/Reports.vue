<template>
  <div class="reports">
    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :xs="12" :sm="5">
          <el-select v-model="filterDays" placeholder="时间范围" @change="fetchData">
            <el-option label="最近 1 天" :value="1" />
            <el-option label="最近 3 天" :value="3" />
            <el-option label="最近 7 天" :value="7" />
            <el-option label="最近 30 天" :value="30" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="5">
          <el-select v-model="filterGroupId" placeholder="全部分组" clearable @change="fetchData">
            <el-option label="全部分组" :value="null" />
            <el-option
              v-for="g in groups"
              :key="g.id"
              :label="g.name"
              :value="g.id"
            />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="5">
          <el-select v-model="filterCameraId" placeholder="全部摄像头" clearable @change="fetchData">
            <el-option
              v-for="c in filteredCameras"
              :key="c.id"
              :label="c.name || c.onvif_url"
              :value="c.id"
            />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="9" style="text-align: right">
          <el-button type="danger" plain @click="handleClearRecords">
            <el-icon><Delete /></el-icon>
            清除记录
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 可用率统计 - 按分组展示 -->
    <el-card class="section-card">
      <template #header><span>📊 摄像头可用率（{{ filterDays }}天）</span></template>

      <!-- 分组 Tabs -->
      <el-tabs v-model="activeGroupTab" type="card">
        <el-tab-pane label="全部" name="all">
          <el-table :data="cameraStats" stripe style="width: 100%">
            <el-table-column prop="camera_name" label="摄像头" min-width="150" />
            <el-table-column prop="group_name" label="分组" width="120" />
            <el-table-column label="可用率" width="200">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.uptime_percent"
                  :color="row.uptime_percent >= 95 ? '#67c23a' : row.uptime_percent >= 80 ? '#e6a23c' : '#f56c6c'"
                  :stroke-width="18"
                  :text-inside="true"
                />
              </template>
            </el-table-column>
            <el-table-column label="在线/总检测" width="120">
              <template #default="{ row }">
                {{ row.online_count }} / {{ row.total_checks }}
              </template>
            </el-table-column>
            <el-table-column label="ONVIF 延迟" width="110">
              <template #default="{ row }">
                {{ row.avg_onvif_time ? row.avg_onvif_time + 'ms' : '-' }}
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane
          v-for="group in groups"
          :key="group.id"
          :label="group.name"
          :name="String(group.id)"
        >
          <el-table :data="getGroupStats(group.id)" stripe style="width: 100%">
            <el-table-column prop="camera_name" label="摄像头" min-width="150" />
            <el-table-column label="可用率" width="200">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.uptime_percent"
                  :color="row.uptime_percent >= 95 ? '#67c23a' : row.uptime_percent >= 80 ? '#e6a23c' : '#f56c6c'"
                  :stroke-width="18"
                  :text-inside="true"
                />
              </template>
            </el-table-column>
            <el-table-column label="在线/总检测" width="120">
              <template #default="{ row }">
                {{ row.online_count }} / {{ row.total_checks }}
              </template>
            </el-table-column>
            <el-table-column label="ONVIF 延迟" width="110">
              <template #default="{ row }">
                {{ row.avg_onvif_time ? row.avg_onvif_time + 'ms' : '-' }}
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="getGroupStats(group.id).length === 0" description="该分组暂无摄像头" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 每小时趋势 -->
    <el-card class="section-card">
      <template #header><span>📈 每小时在线趋势</span></template>
      <div class="chart-container">
        <div v-if="hourlyData.length === 0" class="empty-hint">暂无数据，巡检运行后自动生成</div>
        <div v-else class="hourly-chart">
          <div
            v-for="(item, idx) in hourlyData"
            :key="idx"
            class="bar-item"
            :title="`${item.hour}\n在线: ${item.online}/${item.total} (${item.uptime_percent}%)`"
          >
            <div class="bar" :style="{ height: item.uptime_percent + '%', backgroundColor: item.uptime_percent >= 95 ? '#67c23a' : item.uptime_percent >= 80 ? '#e6a23c' : '#f56c6c' }" />
            <div class="bar-label">{{ item.hour.split(' ')[1] }}</div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 历史记录 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header-row">
          <span>📋 状态变更记录</span>
          <span class="record-count" v-if="historyTotal > 0">共 {{ historyTotal }} 条</span>
        </div>
      </template>
      <el-table :data="historyRecords" stripe style="width: 100%">
        <el-table-column label="摄像头" min-width="150">
          <template #default="{ row }">
            {{ getCameraName(row.camera_id) }}
          </template>
        </el-table-column>
        <el-table-column label="分组" width="120">
          <template #default="{ row }">
            {{ getCameraGroup(row.camera_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'danger'" size="small">
              {{ row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="检测类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.check_type === 'deep' ? 'warning' : 'info'" size="small">
              {{ row.check_type === 'deep' ? '深度' : '心跳' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="onvif_time" label="ONVIF" width="80">
          <template #default="{ row }">
            {{ row.onvif_time ? row.onvif_time + 'ms' : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="记录时间" min-width="180" />
      </el-table>
      <el-empty v-if="historyTotal === 0" description="暂无状态记录" />
      <div v-if="historyTotal > 0" class="pagination-bar">
        <el-pagination
          v-model:current-page="historyPage"
          :page-size="50"
          :total="historyTotal"
          layout="total, prev, pager, next"
          @current-change="fetchHistory"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCameras } from '../api/cameras'
import { getGroups } from '../api/groups'
import { getCameraStats, getHourlyStats, getStatusHistory, clearStatusRecords } from '../api/reports'

const cameras = ref([])
const groups = ref([])
const cameraStats = ref([])
const hourlyData = ref([])
const historyRecords = ref([])
const historyTotal = ref(0)
const historyPage = ref(1)
const filterDays = ref(7)
const filterCameraId = ref(null)
const filterGroupId = ref(null)
const activeGroupTab = ref('all')

// 摄像头ID -> 信息映射
const cameraMap = computed(() => {
  const map = {}
  cameras.value.forEach(c => { map[c.id] = c })
  return map
})

const getCameraName = (id) => {
  const c = cameraMap.value[id]
  return c ? (c.name || c.onvif_url) : `#${id}`
}

const getCameraGroup = (id) => {
  const c = cameraMap.value[id]
  if (!c || !c.group_id) return '未分组'
  const g = groups.value.find(g => g.id === c.group_id)
  return g ? g.name : '未分组'
}

// 按分组筛选摄像头
const filteredCameras = computed(() => {
  if (!filterGroupId.value) return cameras.value
  return cameras.value.filter(c => c.group_id === filterGroupId.value)
})

// 获取某个分组的统计数据
const getGroupStats = (groupId) => {
  return cameraStats.value.filter(s => {
    const c = cameras.value.find(cam => cam.id === s.camera_id)
    return c && c.group_id === groupId
  })
}

const fetchCameras = async () => {
  const res = await getCameras()
  cameras.value = res.data
}

const fetchGroups = async () => {
  const res = await getGroups()
  groups.value = res.data
}

const fetchStats = async () => {
  const params = { days: filterDays.value }
  const res = await getCameraStats(params)
  cameraStats.value = res.data
}

const fetchHourly = async () => {
  const params = { days: Math.min(filterDays.value, 3) }
  if (filterCameraId.value) params.camera_id = filterCameraId.value
  const res = await getHourlyStats(params)
  hourlyData.value = res.data
}

const fetchHistory = async () => {
  const params = {
    days: filterDays.value,
    skip: (historyPage.value - 1) * 50,
    limit: 50
  }
  if (filterCameraId.value) params.camera_id = filterCameraId.value
  const res = await getStatusHistory(params)
  historyRecords.value = res.data.records
  historyTotal.value = res.data.total
}

const fetchData = () => {
  fetchStats()
  fetchHourly()
  fetchHistory()
}

const handleClearRecords = async () => {
  const target = filterCameraId.value
    ? `摄像头「${getCameraName(filterCameraId.value)}」`
    : '全部'
  try {
    await ElMessageBox.confirm(
      `确定要清除${target}的状态记录吗？此操作不可恢复。`,
      '确认清除',
      { type: 'warning', confirmButtonText: '确定清除', cancelButtonText: '取消' }
    )
    const params = {}
    if (filterCameraId.value) params.camera_id = filterCameraId.value
    const res = await clearStatusRecords(params)
    ElMessage.success(`已清除 ${res.data.deleted} 条记录`)
    fetchData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('清除失败')
  }
}

onMounted(() => {
  fetchCameras()
  fetchGroups()
  fetchData()
})
</script>

<style scoped>
.reports { padding: 0; }
.filter-card { margin-bottom: 16px; }
.section-card { margin-bottom: 16px; }
.chart-container { min-height: 200px; }
.empty-hint { text-align: center; color: #999; padding: 80px 0; }
.hourly-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 200px;
  padding: 10px 0;
  overflow-x: auto;
}
.bar-item {
  flex: 1;
  min-width: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: flex-end;
  cursor: pointer;
}
.bar {
  width: 100%;
  border-radius: 3px 3px 0 0;
  transition: height 0.3s;
  min-height: 2px;
}
.bar-label {
  font-size: 10px;
  color: #999;
  margin-top: 4px;
  white-space: nowrap;
}
.pagination-bar {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.record-count {
  font-size: 13px;
  color: #999;
  font-weight: normal;
}

@media (max-width: 768px) {
  .reports { padding: 0; }
  .el-table { font-size: 13px; }
  .filter-card .el-select { margin-bottom: 8px; }
}
</style>
