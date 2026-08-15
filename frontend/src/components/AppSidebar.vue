<template>
  <aside class="sidebar" :class="{ open: mobileOpen }">
    <router-link to="/dashboard" class="sidebar-logo">
      <span class="logo-icon">慧</span>
      <span class="logo-text">慧康</span>
    </router-link>
    <nav class="sidebar-nav">
      <div class="nav-section">概览</div>
      <router-link
        v-for="item in overviewLinks"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="$emit('navigate')"
      >
        <span v-html="item.icon" />
        <span class="nav-label">{{ item.label }}</span>
      </router-link>

      <div class="nav-section">健康管理</div>
      <router-link
        v-for="item in healthLinks"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="$emit('navigate')"
      >
        <span v-html="item.icon" />
        <span class="nav-label">{{ item.label }}</span>
      </router-link>

      <div class="nav-section">工具</div>
      <router-link
        v-for="item in toolLinks"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="$emit('navigate')"
      >
        <span v-html="item.icon" />
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>
    <div class="sidebar-footer">
      <div class="avatar">{{ userInitial }}</div>
      <div class="user-info">
        <div class="user-name">{{ userName }}</div>
        <div class="user-role">在校大学生</div>
      </div>
      <button
        class="sound-toggle"
        :class="{ muted: !soundEnabled }"
        :title="soundEnabled ? '关闭音效' : '开启音效'"
        @click="toggleSound"
      >
        <svg v-if="soundEnabled" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
          <path d="M15.54 8.46a5 5 0 010 7.07"/>
          <path d="M19.07 4.93a10 10 0 010 14.14"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
          <line x1="23" y1="9" x2="17" y2="15"/>
          <line x1="17" y1="9" x2="23" y2="15"/>
        </svg>
      </button>
    </div>
  </aside>
</template>

<script>
import { useSound } from '../composables/useHealthU'

const ICONS = {
  dashboard: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>',
  healthRecord: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>',
  diet: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M18 8h1a4 4 0 010 8h-1M2 8h16v9a4 4 0 01-4 4H6a4 4 0 01-4-4V8z"/></svg>',
  sport: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="5" r="3"/><path d="M6.5 8h11M12 8v13M8 21l1.5-5M16 21l-1.5-5"/></svg>',
  analysis: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 3v18h18M7 16l4-8 4 4 4-10"/></svg>',
  ai: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/></svg>',
  sliders: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>',
  tongue: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/></svg>'
}

export default {
  name: 'AppSidebar',
  props: {
    mobileOpen: { type: Boolean, default: false }
  },
  emits: ['navigate'],
  setup() {
    const { soundEnabled, toggleSound } = useSound()
    return { soundEnabled, toggleSound }
  },
  data() {
    return {
      overviewLinks: [
        { path: '/dashboard', label: '仪表盘', icon: ICONS.dashboard }
      ],
      healthLinks: [
        { path: '/health-record', label: '健康记录', icon: ICONS.healthRecord },
        { path: '/diet-management', label: '饮食管理', icon: ICONS.diet },
        { path: '/sport-management', label: '运动管理', icon: ICONS.sport },
        { path: '/health-analysis', label: '健康分析', icon: ICONS.analysis },
        { path: '/chat', label: 'AI 对话', icon: ICONS.ai }
      ],
      toolLinks: [
        { path: '/tongue-diagnosis', label: '中医舌诊', icon: ICONS.tongue },
        { path: '/ai-settings', label: 'AI 设置', icon: ICONS.sliders }
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
    }
  }
}
</script>
