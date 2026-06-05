<template>
  <!-- 未登录：只显示登录页，不显示侧边栏 -->
  <router-view v-if="!isLoggedIn" />

  <!-- 已登录：完整布局 -->
  <el-container v-else class="layout-container">
    <!-- 手机端遮罩 -->
    <div v-if="sidebarOpen && isMobile" class="sidebar-overlay" @click="sidebarOpen = false" />

    <!-- 侧边栏 -->
    <el-aside :width="sidebarWidth" class="aside" :class="{ 'sidebar-hidden': isMobile && !sidebarOpen }">
      <div class="logo">
        <el-icon><VideoCamera /></el-icon>
        <span v-show="!isMobile || sidebarOpen">摄像头监测</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        class="el-menu-vertical"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        @select="onMenuSelect"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/cameras">
          <el-icon><VideoCamera /></el-icon>
          <span>摄像头管理</span>
        </el-menu-item>
        <el-menu-item index="/groups">
          <el-icon><Folder /></el-icon>
          <span>分组管理</span>
        </el-menu-item>
        <el-menu-item index="/alerts">
          <el-icon><Bell /></el-icon>
          <span>告警记录</span>
        </el-menu-item>
        <el-menu-item index="/reports">
          <el-icon><TrendCharts /></el-icon>
          <span>统计报表</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <el-icon class="hamburger" @click="sidebarOpen = !sidebarOpen">
          <Fold v-if="sidebarOpen" />
          <Expand v-else />
        </el-icon>
        <h2>摄像头状态监测系统</h2>
        <div class="header-right">
          <el-dropdown @command="handleUserMenu" trigger="click">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ currentUser?.username || '用户' }}
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>

  <!-- 修改密码弹窗 -->
  <el-dialog v-model="pwDialogVisible" title="修改密码" width="400px">
    <el-form :model="pwForm" label-width="80px">
      <el-form-item label="原密码" required>
        <el-input v-model="pwForm.old_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码" required>
        <el-input v-model="pwForm.new_password" type="password" show-password placeholder="至少 4 位" />
      </el-form-item>
      <el-form-item label="确认密码" required>
        <el-input v-model="pwForm.confirm" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="pwDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleChangePassword">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Fold, Expand, User, ArrowDown } from '@element-plus/icons-vue'
import { changePassword } from './api/auth'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)

// 登录用 ref 而非 computed（localStorage 不是响应式的）
const isLoggedIn = ref(!!localStorage.getItem('token'))
const currentUser = ref(null)

const refreshAuth = () => {
  isLoggedIn.value = !!localStorage.getItem('token')
  try {
    currentUser.value = JSON.parse(localStorage.getItem('user'))
  } catch {
    currentUser.value = null
  }
}
refreshAuth()

// 路由变化时刷新登录状态（登录成功 router.push 后自动触发）
watch(() => route.path, () => {
  refreshAuth()
})

const sidebarOpen = ref(false)
const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value < 768)
const sidebarWidth = computed(() => {
  if (isMobile.value) return sidebarOpen.value ? '200px' : '0px'
  return '200px'
})

const onResize = () => { windowWidth.value = window.innerWidth }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))

const onMenuSelect = () => {
  if (isMobile.value) sidebarOpen.value = false
}

// 用户菜单
const handleUserMenu = (cmd) => {
  if (cmd === 'logout') {
    ElMessageBox.confirm('确定退出登录？', '提示', { type: 'warning' }).then(() => {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      isLoggedIn.value = false
      currentUser.value = null
      router.push('/login')
    }).catch(() => {})
  } else if (cmd === 'password') {
    pwForm.value = { old_password: '', new_password: '', confirm: '' }
    pwDialogVisible.value = true
  }
}

// 修改密码
const pwDialogVisible = ref(false)
const pwForm = ref({ old_password: '', new_password: '', confirm: '' })

const handleChangePassword = async () => {
  const { old_password, new_password, confirm } = pwForm.value
  if (!old_password || !new_password) {
    ElMessage.warning('请填写完整')
    return
  }
  if (new_password !== confirm) {
    ElMessage.warning('两次密码不一致')
    return
  }
  try {
    await changePassword({ old_password, new_password })
    ElMessage.success('密码修改成功')
    pwDialogVisible.value = false
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '修改失败')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.aside {
  background-color: #304156;
  overflow: hidden;
  transition: width 0.3s;
}

.sidebar-hidden {
  width: 0 !important;
  overflow: hidden;
}

.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.4);
  z-index: 999;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  gap: 8px;
  white-space: nowrap;
}
.logo .el-icon { font-size: 24px; }

.el-menu-vertical {
  border-right: none;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  gap: 12px;
}
.header h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
  flex: 1;
}

.header-right {
  margin-left: auto;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #606266;
  font-size: 14px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}
.user-info:hover {
  background: #f5f7fa;
}

.hamburger {
  font-size: 22px;
  cursor: pointer;
  color: #666;
  display: none;
}

.main {
  background-color: #f5f5f5;
  padding: 20px;
}

/* 手机端适配 */
@media (max-width: 768px) {
  .hamburger { display: block; }
  .aside {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 1000;
    box-shadow: 2px 0 8px rgba(0,0,0,0.2);
  }
  .header h2 { font-size: 16px; }
  .main { padding: 12px; }
  .user-info span { display: none; }
}
</style>
