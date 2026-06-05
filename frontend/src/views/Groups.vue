<template>
  <div class="groups">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>分组管理</span>
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>
            添加分组
          </el-button>
        </div>
      </template>

      <el-table :data="groups" stripe style="width: 100%">
        <el-table-column prop="name" label="分组名称" min-width="150" />
        <el-table-column prop="notify_note" label="通知备注" min-width="250">
          <template #default="{ row }">
            {{ row.notify_note || '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="warning" link @click="showEditDialog(row)">
              编辑
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="notify-tip">
        <el-icon><InfoFilled /></el-icon>
        告警通知在「设置 → 飞书机器人通知」中配置接收人。每个分组可设置不同的通知备注（如"请通知张三"），告警时会带上。
      </div>
    </el-card>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑分组' : '添加分组'"
      width="450px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="分组名称" required>
          <el-input v-model="form.name" placeholder="如：KTV、网吧、仓库" />
        </el-form-item>
        <el-form-item label="通知备注">
          <el-input v-model="form.notify_note" placeholder="如：请通知张三、联系王经理" />
          <div class="form-tip">告警消息里会带上这段文字，方便你知道该通知谁</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getGroups, createGroup, updateGroup, deleteGroup } from '../api/groups'

const groups = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)

const form = ref({
  name: '',
  notify_note: ''
})

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const fetchGroups = async () => {
  try {
    const res = await getGroups()
    groups.value = res.data
  } catch (error) {
    console.error('获取分组列表失败:', error)
  }
}

const showAddDialog = () => {
  isEdit.value = false
  editId.value = null
  form.value = { name: '', notify_note: '' }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.value = {
    name: row.name,
    notify_note: row.notify_note || ''
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    if (isEdit.value) {
      await updateGroup(editId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createGroup(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchGroups()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除这个分组吗？', '提示', {
      type: 'warning'
    })
    await deleteGroup(row.id)
    ElMessage.success('删除成功')
    fetchGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchGroups()
})
</script>

<style scoped>
.groups {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notify-tip {
  margin-top: 12px;
  padding: 8px 12px;
  background: #f0f9ff;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  display: flex;
  align-items: center;
  gap: 6px;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .groups { padding: 0; }
  .el-table { font-size: 13px; }
}
</style>
