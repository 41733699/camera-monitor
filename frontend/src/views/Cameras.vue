<template>
  <div class="cameras">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>摄像头管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加设备
          </el-button>
        </div>
      </template>

      <div class="filter-bar">
        <el-select v-model="filterGroupId" placeholder="按分组筛选" clearable @change="fetchCameras">
          <el-option v-for="group in groups" :key="group.id" :label="group.name" :value="group.id" />
        </el-select>
      </div>

      <el-table :data="cameras" stripe style="width: 100%">
        <el-table-column prop="name" label="名称" min-width="120">
          <template #default="{ row }">{{ row.name || row.onvif_url }}</template>
        </el-table-column>
        <el-table-column label="ONVIF 地址" min-width="200">
          <template #default="{ row }">{{ row.onvif_url }}</template>
        </el-table-column>
        <el-table-column label="截图" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.screenshot_enabled" type="success" size="small">开</el-tag>
            <el-tag v-else type="info" size="small">关</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="通知" width="70">
          <template #default="{ row }">
            <el-tag v-if="row.notify_enabled !== false" type="success" size="small">开</el-tag>
            <el-tag v-else type="warning" size="small">关</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="group.name" label="分组" width="100">
          <template #default="{ row }">{{ row.group?.name || '未分组' }}</template>
        </el-table-column>
        <el-table-column prop="location_note" label="位置" width="100">
          <template #default="{ row }">{{ row.location_note || '-' }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleCheck(row)">检测</el-button>
            <el-button type="warning" link @click="showEditDialog(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑摄像头' : '添加摄像头'" width="580px">
      <el-form :model="form" label-width="100px">

        <el-form-item label="摄像头名称">
          <el-input v-model="form.name" placeholder="可选，如：大门口摄像头" />
        </el-form-item>

        <el-divider content-position="left">ONVIF 检测（必填）</el-divider>

        <el-form-item label="ONVIF 地址" required>
          <el-input v-model="form.onvif_url" placeholder="http://192.168.1.100:8080/onvif/device_service" clearable />
          <div class="form-tip">粘贴完整的 ONVIF 服务地址</div>
        </el-form-item>

        <el-divider content-position="left">截图设置（可选）</el-divider>

        <el-form-item label="启用截图">
          <el-switch v-model="form.screenshot_enabled" active-text="开启后定时截取视频画面" />
        </el-form-item>

        <template v-if="form.screenshot_enabled">
          <el-form-item label="RTSP 地址" required>
            <el-input v-model="form.rtsp_url" placeholder="rtsp://admin:password@ip:port/path" clearable />
            <div class="form-tip">粘贴完整的 RTSP 地址，包含用户名密码</div>
          </el-form-item>
        </template>

        <el-form-item label="通知开关">
          <el-switch v-model="form.notify_enabled" active-text="掉线时发送飞书通知" />
          <div class="form-tip" v-if="!form.notify_enabled">关闭后掉线仅做记录，不发送通知</div>
        </el-form-item>

        <el-divider content-position="left">其他</el-divider>

        <el-form-item label="所属分组">
          <el-select v-model="form.group_id" placeholder="选择分组" clearable>
            <el-option v-for="group in groups" :key="group.id" :label="group.name" :value="group.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="安装位置">
          <el-input v-model="form.location_note" placeholder="如：大门口、收银台上方" />
        </el-form-item>

      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCameras, createCamera, updateCamera, deleteCamera, checkCamera } from '../api/cameras'
import { getGroups } from '../api/groups'
import { getStatusType, getStatusText } from '../utils/camera'

const cameras = ref([])
const groups = ref([])
const filterGroupId = ref(null)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)

const defaultForm = {
  name: '',
  onvif_url: '',
  screenshot_enabled: false,
  rtsp_url: '',
  notify_enabled: true,
  group_id: null, location_note: ''
}

const form = ref({ ...defaultForm })

const fetchCameras = async () => {
  const params = {}
  if (filterGroupId.value) params.group_id = filterGroupId.value
  cameras.value = (await getCameras(params)).data
}

const fetchGroups = async () => { groups.value = (await getGroups()).data }

const showAddDialog = () => {
  isEdit.value = false; editId.value = null
  form.value = { ...defaultForm }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true; editId.value = row.id
  form.value = {
    name: row.name || '',
    onvif_url: row.onvif_url || '',
    screenshot_enabled: row.screenshot_enabled || false,
    rtsp_url: row.rtsp_url || '',
    notify_enabled: row.notify_enabled !== false,
    group_id: row.group_id, location_note: row.location_note || ''
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.onvif_url) { ElMessage.warning('请输入 ONVIF 地址'); return }
  if (form.value.screenshot_enabled && !form.value.rtsp_url) { ElMessage.warning('启用截图需要填写 RTSP 地址'); return }
  try {
    const data = { ...form.value }

    if (isEdit.value) {
      await updateCamera(editId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createCamera(data)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchCameras()
  } catch (error) {
    ElMessage.error('操作失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个摄像头吗？', '提示', { type: 'warning' })
    await deleteCamera(row.id)
    ElMessage.success('删除成功'); fetchCameras()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}

const handleCheck = async (row) => {
  try {
    await checkCamera(row.id)
    ElMessage.success('检测完成'); fetchCameras()
  } catch { ElMessage.error('检测失败') }
}

onMounted(() => { fetchCameras(); fetchGroups() })
</script>

<style scoped>
.cameras { padding: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.filter-bar { margin-bottom: 20px; }
.form-tip { font-size: 12px; color: #999; margin-top: 4px; }

@media (max-width: 768px) {
  .cameras { padding: 0; }
  .el-table { font-size: 13px; }
}
</style>
