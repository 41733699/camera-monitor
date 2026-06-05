<template>
  <div class="settings">
    <!-- 巡检设置 -->
    <el-card class="section-card">
      <template #header><span>⏱️ 定时任务设置</span></template>
      <el-form :label-position="isMobile ? 'top' : 'right'" label-width="120px" :style="{ maxWidth: isMobile ? '100%' : '500px' }">
        <el-form-item label="心跳间隔">
          <el-input-number v-model="patrolSettings.onvif_heartbeat_interval" :min="10" :max="3600" :step="10" />
          <span class="unit-label">秒</span>
          <div class="form-tip">ONVIF 心跳检测间隔。轻量 HTTP 探测，50~200ms/个</div>
        </el-form-item>
        <el-form-item label="截图间隔">
          <el-input-number v-model="patrolSettings.screenshot_interval" :min="0" :max="86400" :step="60" />
          <span class="unit-label">秒</span>
          <div class="form-tip">对在线摄像头定时截图。设为 0 禁用。建议 30 分钟以上</div>
        </el-form-item>
        <el-form-item label="自动通知">
          <el-switch v-model="patrolSettings.auto_notify" active-text="掉线自动飞书通知" />
        </el-form-item>

        <!-- 免打扰规则 -->
        <el-divider content-position="left">🚫 免打扰规则</el-divider>
        <div class="quiet-rules">
          <div v-if="quietRules.length === 0" class="empty-rules">暂无免打扰规则，所有告警都会发送通知</div>
          <div v-for="(rule, idx) in quietRules" :key="idx" class="rule-card">
            <div class="rule-header">
              <el-switch v-model="rule.active" size="small" />
              <el-input v-model="rule.name" size="small" placeholder="规则名称" style="width: 120px; margin: 0 8px" />
              <el-tag size="small" :type="ruleTypeTag(rule.type)">{{ ruleTypeLabel(rule.type) }}</el-tag>
              <el-button type="danger" link size="small" @click="quietRules.splice(idx, 1)" style="margin-left: auto">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <div class="rule-body">
              <!-- 每日时段 -->
              <template v-if="rule.type === 'daily'">
                <div class="rule-row">
                  <span class="rule-label">时段</span>
                  <el-time-picker v-model="rule.start" format="HH:mm" value-format="HH:mm" placeholder="开始" style="width: 100px" size="small" />
                  <span>至</span>
                  <el-time-picker v-model="rule.end" format="HH:mm" value-format="HH:mm" placeholder="结束" style="width: 100px" size="small" />
                  <span class="rule-hint">支持跨午夜，如 22:00~08:00</span>
                </div>
              </template>
              <!-- 指定日期 -->
              <template v-if="rule.type === 'date'">
                <div class="rule-row">
                  <span class="rule-label">日期</span>
                  <div class="date-tags">
                    <el-tag v-for="(d, di) in rule.dates" :key="di" closable size="small" @close="rule.dates.splice(di, 1)">{{ d }}</el-tag>
                  </div>
                </div>
                <div class="rule-row" style="margin-top: 6px">
                  <span class="rule-label">添加</span>
                  <el-date-picker v-model="newDate" type="date" value-format="YYYY-MM-DD" placeholder="单日" style="width: 140px" size="small" />
                  <el-button size="small" @click="addSingleDate(rule)">添加</el-button>
                  <span style="margin: 0 4px">或</span>
                  <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD" start-placeholder="起始" end-placeholder="结束" style="width: 240px" size="small" />
                  <el-button size="small" @click="addDateRange(rule)">添加</el-button>
                </div>
              </template>
              <!-- 每周几 -->
              <template v-if="rule.type === 'weekday'">
                <div class="rule-row">
                  <span class="rule-label">星期</span>
                  <el-checkbox-group v-model="rule.weekdays" size="small">
                    <el-checkbox-button :label="1">一</el-checkbox-button>
                    <el-checkbox-button :label="2">二</el-checkbox-button>
                    <el-checkbox-button :label="3">三</el-checkbox-button>
                    <el-checkbox-button :label="4">四</el-checkbox-button>
                    <el-checkbox-button :label="5">五</el-checkbox-button>
                    <el-checkbox-button :label="6">六</el-checkbox-button>
                    <el-checkbox-button :label="0">日</el-checkbox-button>
                  </el-checkbox-group>
                </div>
                <div class="rule-row" style="margin-top: 6px">
                  <span class="rule-label">时段</span>
                  <el-switch v-model="rule._limitTime" size="small" inactive-text="全天" active-text="指定时段" style="margin-right: 8px" />
                  <template v-if="rule._limitTime">
                    <el-time-picker v-model="rule.start" format="HH:mm" value-format="HH:mm" placeholder="开始" style="width: 100px" size="small" />
                    <span>至</span>
                    <el-time-picker v-model="rule.end" format="HH:mm" value-format="HH:mm" placeholder="结束" style="width: 100px" size="small" />
                  </template>
                </div>
              </template>
            </div>
          </div>
          <div class="add-rule-bar">
            <el-dropdown @command="addRule">
              <el-button type="primary" plain size="small">
                <el-icon><Plus /></el-icon> 添加规则
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="daily">🕐 每日时段</el-dropdown-item>
                  <el-dropdown-item command="date">📅 指定日期/节假日</el-dropdown-item>
                  <el-dropdown-item command="weekday">📆 每周几</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <el-form-item>
          <div class="btn-row">
            <el-button type="primary" @click="savePatrolSettings">保存设置</el-button>
            <el-button @click="triggerHeartbeat" :loading="heartbeatRunning">
              💓 立即心跳
            </el-button>
            <el-button @click="triggerScreenshot" :loading="screenshotRunning">
              📸 立即截图
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 飞书机器人配置 -->
    <el-card class="section-card">
      <template #header><span>🔔 飞书机器人通知</span></template>
      <el-form :label-position="isMobile ? 'top' : 'right'" label-width="120px" :style="{ maxWidth: isMobile ? '100%' : '550px' }">
        <el-form-item label="App ID">
          <el-input v-model="patrolSettings.feishu_app_id" placeholder="cli_xxxxxxxxxx" />
        </el-form-item>
        <el-form-item label="App Secret">
          <el-input v-model="patrolSettings.feishu_app_secret" placeholder="xxxxxxxxxx" show-password />
        </el-form-item>
        <el-form-item label="接收人 Open ID">
          <el-input v-model="patrolSettings.feishu_open_id" placeholder="ou_xxxxxxxxxx" />
          <div class="form-tip">个人私信通知，优先级高于群聊。在飞书开放平台用手机号查询获取</div>
        </el-form-item>
        <el-form-item :label="isMobile ? '群聊 Chat ID' : '群聊 Chat ID（可选）'">
          <el-input v-model="patrolSettings.feishu_chat_id" placeholder="oc_xxxxxxxxxx" />
          <div class="form-tip">群聊通知，机器人需先加入该群。不填则只发给上面的个人</div>
        </el-form-item>
        <el-form-item>
          <div class="btn-row">
            <el-button type="primary" @click="savePatrolSettings">保存配置</el-button>
            <el-button type="success" @click="testFeishu" :loading="feishuTesting">
              ✉️ 发送测试消息
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <el-alert v-if="feishuTestResult" :type="feishuTestResult.success ? 'success' : 'error'"
        :title="feishuTestResult.success ? feishuTestResult.message : feishuTestResult.error"
        show-icon style="margin-top: 10px" />
    </el-card>

    <!-- 导入导出 -->
    <el-card class="section-card">
      <template #header><span>💾 配置备份与恢复</span></template>
      <div class="backup-grid">
        <div class="backup-section">
          <h4>📤 导出配置</h4>
          <p class="desc">导出所有分组、摄像头、设置为 JSON 文件，用于备份或迁移到其他机器。</p>
          <el-button type="primary" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出 JSON
          </el-button>
        </div>
        <el-divider v-if="isMobile" />
        <div class="backup-section">
          <h4>📥 导入配置</h4>
          <p class="desc">从 JSON 文件导入配置。已存在的分组和摄像头会更新，不会重复创建。</p>
          <el-upload
            :show-file-list="false"
            accept=".json"
            :before-upload="handleImport"
          >
            <el-button type="success">
              <el-icon><Upload /></el-icon>
              导入 JSON
            </el-button>
          </el-upload>
        </div>
      </div>

      <!-- 导入结果 -->
      <div v-if="importResult" class="import-result">
        <el-alert
          :title="importResult.errors.length > 0 ? '导入完成（有部分错误）' : '导入成功'"
          :type="importResult.errors.length > 0 ? 'warning' : 'success'"
          show-icon
          :closable="false"
        >
          <template #default>
            <p>分组: +{{ importResult.groups_imported }} | 摄像头: +{{ importResult.cameras_imported }} | 设置: {{ importResult.settings_imported }} 条</p>
            <ul v-if="importResult.errors.length > 0">
              <li v-for="(err, i) in importResult.errors" :key="i" style="color: #e6a23c">{{ err }}</li>
            </ul>
          </template>
        </el-alert>
      </div>
    </el-card>

    <!-- 用户管理（仅管理员可见） -->
    <el-card v-if="isAdmin" class="section-card">
      <template #header>
        <div class="card-header">
          <span>👥 用户管理</span>
          <el-button type="primary" size="small" @click="showAddUser">
            <el-icon><Plus /></el-icon>
            添加用户
          </el-button>
        </div>
      </template>

      <!-- 手机端：卡片式用户列表 -->
      <template v-if="isMobile">
        <div v-for="user in users" :key="user.id" class="user-card">
          <div class="user-card-row">
            <span class="user-card-label">用户名</span>
            <span class="user-card-value">{{ user.username }}</span>
          </div>
          <div class="user-card-row">
            <span class="user-card-label">角色</span>
            <span class="user-card-value">
              <el-tag :type="user.is_admin ? 'danger' : 'info'" size="small">
                {{ user.is_admin ? '管理员' : '普通用户' }}
              </el-tag>
            </span>
          </div>
          <div class="user-card-row">
            <span class="user-card-label">创建时间</span>
            <span class="user-card-value">{{ user.created_at }}</span>
          </div>
          <div class="user-card-actions">
            <el-button type="warning" size="small" link @click="showEditUser(user)">编辑</el-button>
            <el-button type="primary" size="small" link @click="showResetPassword(user)">重置密码</el-button>
            <el-button type="danger" size="small" link @click="handleDeleteUser(user)" :disabled="user.id === currentUserId">删除</el-button>
          </div>
        </div>
      </template>

      <!-- 桌面端：表格 -->
      <el-table v-else :data="users" stripe>
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="is_admin" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_admin ? 'danger' : 'info'" size="small">
              {{ row.is_admin ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button type="warning" link @click="showEditUser(row)">编辑</el-button>
            <el-button type="primary" link @click="showResetPassword(row)">重置密码</el-button>
            <el-button type="danger" link @click="handleDeleteUser(row)" :disabled="row.id === currentUserId">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 用户管理弹窗 -->
    <el-dialog v-model="userDialogVisible" :title="userDialogTitle" :width="isMobile ? '95%' : '420px'" :fullscreen="isMobile">
      <el-form :model="userForm" :label-position="isMobile ? 'top' : 'right'" label-width="80px">
        <el-form-item label="用户名" required>
          <el-input v-model="userForm.username" placeholder="至少 2 位" />
        </el-form-item>
        <el-form-item v-if="userDialogMode !== 'edit'" label="密码" required>
          <el-input v-model="userForm.password" type="password" show-password placeholder="至少 4 位" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="userForm.is_admin">
            <el-option label="普通用户" :value="false" />
            <el-option label="管理员" :value="true" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUserSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码弹窗 -->
    <el-dialog v-model="resetDialogVisible" title="重置密码" :width="isMobile ? '95%' : '380px'" :fullscreen="isMobile">
      <p style="margin-bottom: 12px">为 <b>{{ resetTarget?.username }}</b> 设置新密码：</p>
      <el-input v-model="resetPassword" type="password" show-password placeholder="至少 4 位" />
      <template #footer>
        <el-button @click="resetDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResetPassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { exportConfig, importConfig } from '../api/backup'
import { getPatrolSettings, updatePatrolSettings, runHeartbeat, runScreenshot, testFeishuApi } from '../api/patrol'
import { getUsers, createUser, updateUser, deleteUser } from '../api/auth'

// 响应式断点
const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value < 768)
const onResize = () => { windowWidth.value = window.innerWidth }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))

const patrolSettings = ref({
  onvif_heartbeat_interval: 60, screenshot_interval: 1800,
  auto_notify: true,
  feishu_app_id: '', feishu_app_secret: '', feishu_open_id: '', feishu_chat_id: ''
})
const quietRules = ref([])
const newDate = ref('')
const dateRange = ref(null)
const patrolRunning = ref(false)
const heartbeatRunning = ref(false)
const screenshotRunning = ref(false)
const importResult = ref(null)
const feishuTesting = ref(false)
const feishuTestResult = ref(null)

// 用户管理
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const isAdmin = computed(() => currentUser.is_admin)
const currentUserId = currentUser.id
const users = ref([])
const userDialogVisible = ref(false)
const userDialogTitle = ref('')
const userDialogMode = ref('add')
const userForm = ref({ username: '', password: '', is_admin: false })
const editUserId = ref(null)
const resetDialogVisible = ref(false)
const resetTarget = ref(null)
const resetPassword = ref('')

const fetchSettings = async () => {
  const res = await getPatrolSettings()
  patrolSettings.value = res.data
  quietRules.value = (res.data.quiet_rules || []).map(r => ({
    ...r,
    _limitTime: !!(r.start && r.end && r.type === 'weekday'),
    weekdays: r.weekdays || [],
    dates: r.dates || [],
  }))
}

const savePatrolSettings = async () => {
  try {
    const data = { ...patrolSettings.value }
    // 清理规则中的临时字段
    data.quiet_rules = quietRules.value.map(r => {
      const rule = { name: r.name, type: r.type, active: r.active }
      if (r.type === 'daily') {
        rule.start = r.start || '00:00'
        rule.end = r.end || '23:59'
      } else if (r.type === 'date') {
        rule.dates = r.dates || []
      } else if (r.type === 'weekday') {
        rule.weekdays = r.weekdays || []
        if (r._limitTime && r.start && r.end) {
          rule.start = r.start
          rule.end = r.end
        }
      }
      return rule
    })
    await updatePatrolSettings(data)
    ElMessage.success('设置已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}

const triggerHeartbeat = async () => {
  heartbeatRunning.value = true
  try {
    await runHeartbeat()
    ElMessage.success('ONVIF 心跳检测完成')
  } catch {
    ElMessage.error('心跳检测失败')
  } finally {
    heartbeatRunning.value = false
  }
}

const triggerScreenshot = async () => {
  screenshotRunning.value = true
  try {
    await runScreenshot()
    ElMessage.success('截图完成')
  } catch {
    ElMessage.error('截图失败')
  } finally {
    screenshotRunning.value = false
  }
}

const handleExport = async () => {
  try {
    const res = await exportConfig()
    const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    const date = new Date().toISOString().slice(0, 10)
    a.download = `camera-monitor-backup-${date}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('配置已导出')
  } catch {
    ElMessage.error('导出失败')
  }
}

const handleImport = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await importConfig(formData)
    importResult.value = res.data
    ElMessage.success('导入完成')
  } catch (err) {
    ElMessage.error(err.response?.data?.error || '导入失败')
  }
  return false
}

const testFeishu = async () => {
  feishuTesting.value = true
  feishuTestResult.value = null
  try {
    await updatePatrolSettings(patrolSettings.value)
    const res = await testFeishuApi()
    feishuTestResult.value = res.data
  } catch (err) {
    feishuTestResult.value = { success: false, error: err.response?.data?.error || '测试失败' }
  } finally {
    feishuTesting.value = false
  }
}

// ── 免打扰规则管理 ────────────────────────────────

const ruleTypeLabel = (type) => ({ daily: '每日', date: '日期', weekday: '星期' }[type] || type)
const ruleTypeTag = (type) => ({ daily: 'primary', date: 'warning', weekday: 'success' }[type] || 'info')

const addRule = (type) => {
  const base = { type, active: true }
  if (type === 'daily') {
    quietRules.value.push({ ...base, name: '夜间免打扰', start: '22:00', end: '08:00' })
  } else if (type === 'date') {
    quietRules.value.push({ ...base, name: '节假日', dates: [] })
  } else if (type === 'weekday') {
    quietRules.value.push({ ...base, name: '周末', weekdays: [6, 0], _limitTime: false })
  }
}

const addSingleDate = (rule) => {
  if (!newDate.value) return
  if (!rule.dates.includes(newDate.value)) {
    rule.dates.push(newDate.value)
    rule.dates.sort()
  }
  newDate.value = ''
}

const addDateRange = (rule) => {
  if (!dateRange.value || dateRange.value.length !== 2) return
  const rangeStr = `${dateRange.value[0]}~${dateRange.value[1]}`
  if (!rule.dates.includes(rangeStr)) {
    rule.dates.push(rangeStr)
  }
  dateRange.value = null
}

// ── 用户管理 ────────────────────────────────────────

const fetchUsers = async () => {
  try {
    const res = await getUsers()
    users.value = res.data
  } catch {}
}

const showAddUser = () => {
  userDialogMode.value = 'add'
  userDialogTitle.value = '添加用户'
  userForm.value = { username: '', password: '', is_admin: false }
  editUserId.value = null
  userDialogVisible.value = true
}

const showEditUser = (row) => {
  userDialogMode.value = 'edit'
  userDialogTitle.value = '编辑用户'
  userForm.value = { username: row.username, is_admin: row.is_admin }
  editUserId.value = row.id
  userDialogVisible.value = true
}

const handleUserSubmit = async () => {
  try {
    if (userDialogMode.value === 'add') {
      if (!userForm.value.username || !userForm.value.password) {
        ElMessage.warning('请填写用户名和密码')
        return
      }
      await createUser(userForm.value)
      ElMessage.success('用户已创建')
    } else {
      await updateUser(editUserId.value, {
        username: userForm.value.username,
        is_admin: userForm.value.is_admin,
      })
      ElMessage.success('用户已更新')
    }
    userDialogVisible.value = false
    fetchUsers()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}

const showResetPassword = (row) => {
  resetTarget.value = row
  resetPassword.value = ''
  resetDialogVisible.value = true
}

const handleResetPassword = async () => {
  if (!resetPassword.value || resetPassword.value.length < 4) {
    ElMessage.warning('密码至少 4 位')
    return
  }
  try {
    await updateUser(resetTarget.value.id, { password: resetPassword.value })
    ElMessage.success('密码已重置')
    resetDialogVisible.value = false
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '重置失败')
  }
}

const handleDeleteUser = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除用户「${row.username}」？`, '确认', { type: 'warning' })
    await deleteUser(row.id)
    ElMessage.success('用户已删除')
    fetchUsers()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

onMounted(() => {
  fetchSettings()
  if (isAdmin.value) fetchUsers()
})
</script>

<style scoped>
.settings { padding: 0; }
.section-card { margin-bottom: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }

.unit-label {
  margin-left: 8px;
  color: #999;
  font-size: 14px;
  white-space: nowrap;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.5;
}

/* 免打扰规则 */
.quiet-rules { margin-bottom: 16px; }
.empty-rules { color: #999; font-size: 13px; padding: 12px 0; text-align: center; }
.rule-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  background: #fafbfc;
}
.rule-card:hover { border-color: #c0c4cc; }
.rule-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
}
.rule-body { padding-left: 4px; }
.rule-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.rule-label {
  font-size: 13px;
  color: #606266;
  min-width: 36px;
  flex-shrink: 0;
}
.rule-hint { font-size: 12px; color: #999; }
.date-tags { display: flex; gap: 4px; flex-wrap: wrap; }
.add-rule-bar { margin-top: 8px; }

.btn-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 备份与恢复 */
.backup-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.backup-section { padding: 10px 0; }
.backup-section h4 { margin: 0 0 8px 0; font-size: 15px; }
.backup-section .desc { font-size: 13px; color: #999; margin-bottom: 12px; line-height: 1.5; }
.import-result { margin-top: 16px; }

/* 用户管理 — 手机端卡片式 */
.user-card {
  background: #f9fafb;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
}
.user-card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}
.user-card-label {
  font-size: 13px;
  color: #909399;
  flex-shrink: 0;
}
.user-card-value {
  font-size: 14px;
  color: #303133;
  text-align: right;
}
.user-card-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #ebeef5;
}

/* 手机端适配 */
@media (max-width: 768px) {
  .section-card { margin-bottom: 12px; }

  /* el-input-number 手机端加大触摸区域 */
  :deep(.el-input-number) {
    width: 120px !important;
  }
  :deep(.el-input-number .el-input__wrapper) {
    padding-left: 8px;
    padding-right: 8px;
  }

  /* switch 文字缩小 */
  :deep(.el-switch__label) {
    font-size: 12px;
  }

  /* 备份区改为纵向 */
  .backup-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }

  /* 全宽按钮 */
  .btn-row {
    width: 100%;
  }
  .btn-row .el-button {
    flex: 1;
  }

  /* 弹窗按钮区 */
  :deep(.el-dialog__footer .el-button) {
    min-width: 80px;
  }
}
</style>
