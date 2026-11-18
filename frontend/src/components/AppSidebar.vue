<template>
  <aside
    id="app-sidebar"
    class="sidebar"
    :class="{ open: mobileOpen }"
    :aria-hidden="isMobile && !mobileOpen ? 'true' : null"
    aria-label="主导航"
    tabindex="-1"
  >
    <router-link to="/dashboard" class="brand" @click="$emit('navigate')">
      <span class="brand-mark">慧</span>
      <span class="brand-copy">
        <strong>慧康</strong>
        <small>HUIKANG / 02</small>
      </span>
    </router-link>

    <nav class="nav">
      <div class="nav-label">每日</div>
      <router-link
        v-for="item in dailyLinks"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="$emit('navigate')"
      >
        <span class="nav-num">{{ item.num }}</span>
        <AppIcon :name="item.icon" :size="18" />
        <span class="nav-text">{{ item.label }}</span>
        <span v-if="item.dot" class="nav-dot" aria-hidden="true" />
      </router-link>

      <div class="nav-label">档案</div>
      <router-link
        v-for="item in archiveLinks"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="$emit('navigate')"
      >
        <span class="nav-num">{{ item.num }}</span>
        <AppIcon :name="item.icon" :size="18" />
        <span class="nav-text">{{ item.label }}</span>
      </router-link>

      <div class="nav-label">助手</div>
      <router-link
        v-for="item in assistantLinks"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="$emit('navigate')"
      >
        <span class="nav-num">{{ item.num }}</span>
        <AppIcon :name="item.icon" :size="18" />
        <span class="nav-text">{{ item.label }}</span>
        <span v-if="item.dot" class="nav-dot" aria-hidden="true" />
      </router-link>
    </nav>

    <div class="sidebar-foot">
      <div class="user-avatar">{{ userInitial }}</div>
      <div class="user-copy">
        <strong>{{ userName }}</strong>
        <small>在校大学生</small>
      </div>
      <span class="user-status" aria-hidden="true" />
    </div>
    <div class="sidebar-tools">
      <button
        class="sidebar-tool"
        :title="soundEnabled ? '关闭音效' : '开启音效'"
        :aria-label="soundEnabled ? '关闭音效' : '开启音效'"
        @click="toggleSound"
      >
        <AppIcon name="volume" :size="15" />
      </button>
      <button
        class="sidebar-tool danger"
        type="button"
        title="退出登录"
        aria-label="退出登录"
        @click="logout"
      >
        <AppIcon name="logout" :size="15" />
      </button>
    </div>
  </aside>
</template>

<script>
import AppIcon from './AppIcon.vue'
import { useSound } from '../composables/useHealthU'

export default {
  name: 'AppSidebar',
  components: { AppIcon },
  props: {
    mobileOpen: { type: Boolean, default: false },
    isMobile: { type: Boolean, default: false }
  },
  emits: ['navigate'],
  setup() {
    const { soundEnabled, toggleSound } = useSound()
    return { soundEnabled, toggleSound }
  },
  data() {
    return {
      dailyLinks: [
        { path: '/dashboard', label: '总览', num: '01', icon: 'home' },
        { path: '/mental', label: '心理', num: '02', icon: 'heart', dot: true },
        { path: '/diet-management', label: '饮食', num: '03', icon: 'diet' },
        { path: '/sport-management', label: '运动', num: '04', icon: 'activity' }
      ],
      archiveLinks: [
        { path: '/health-record', label: '体检', num: '05', icon: 'record' },
        { path: '/health-analysis', label: '健康分析', num: '06', icon: 'chart' },
        { path: '/tongue-diagnosis', label: '舌诊', num: '07', icon: 'tongue' }
      ],
      assistantLinks: [
        { path: '/chat', label: '对话', num: '08', icon: 'ai', dot: true },
        { path: '/ai-settings', label: '设置', num: '09', icon: 'sliders' }
      ]
    }
  },
  computed: {
    userName() {
      return localStorage.getItem('userName') || '同学'
    },
    userInitial() {
      return this.userName.charAt(0)
    }
  },
  methods: {
    isActive(path) {
      return this.$route.path === path
    },
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('userName')
      this.$emit('navigate')
      this.$router.push('/login')
    }
  }
}
</script>
