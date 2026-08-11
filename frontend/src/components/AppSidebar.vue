<template>
  <aside class="sidebar" :class="{ open: mobileOpen }">
    <router-link to="/dashboard" class="sidebar-logo">
      <span class="logo-icon">慧</span>
      慧康
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
        {{ item.label }}
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
        {{ item.label }}
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
        {{ item.label }}
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
  knowledge: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>',
  reminder: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"/></svg>',
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
        { path: '/health-analysis', label: '健康分析', icon: ICONS.analysis }
      ],
      toolLinks: [
        { path: '/health-knowledge', label: '健康知识', icon: ICONS.knowledge },
        { path: '/health-reminder', label: '健康提醒', icon: ICONS.reminder },
        { path: '/tongue-diagnosis', label: '中医舌诊', icon: ICONS.tongue }
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
