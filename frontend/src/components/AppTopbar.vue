<template>
  <header class="topbar">
    <div class="topbar-left">
      <button
        class="icon-btn topbar-more"
        type="button"
        :aria-label="mobileOpen ? '关闭导航菜单' : '打开导航菜单'"
        aria-controls="app-sidebar"
        :aria-expanded="mobileOpen"
        @click="$emit('toggle-mobile-menu')"
      >
        <AppIcon name="menu" :size="18" />
      </button>
      <span class="topbar-date">{{ currentDate }}</span>
      <span class="topbar-sep" aria-hidden="true" />
      <span class="topbar-title">{{ title }}</span>
    </div>
    <div class="topbar-right">
      <button
        class="icon-btn"
        type="button"
        :class="{ 'is-muted': effectivelyMuted }"
        :aria-pressed="effectivelyMuted"
        :aria-label="soundLabel"
        :title="soundLabel"
        @click="onToggleSound"
      >
        <AppIcon :name="effectivelyMuted ? 'mute' : 'volume'" :size="18" />
      </button>
      <button
        class="icon-btn"
        type="button"
        :aria-pressed="theme === 'dark'"
        :aria-label="theme === 'dark' ? '切换浅色模式' : '切换深色模式'"
        :title="theme === 'dark' ? '切换浅色模式' : '切换深色模式'"
        @click="toggleTheme"
      >
        <AppIcon :name="theme === 'dark' ? 'sun' : 'moon'" :size="18" />
      </button>
      <router-link
        class="icon-btn"
        to="/warnings"
        :aria-label="warningStore.stats.unread ? `${warningStore.stats.unread} 条未读健康预警` : '查看健康预警'"
      >
        <AppIcon name="alert" :size="18" />
        <span v-if="warningStore.stats.unread" class="notify-dot" aria-hidden="true" />
      </router-link>
      <span class="topbar-user">
        <span class="user-avatar user-avatar--sm">{{ userInitial }}</span>
        <span>{{ userName }}</span>
      </span>
    </div>
  </header>
</template>

<script>
import AppIcon from './AppIcon.vue'
import { useWarningStore } from '../stores/warnings'
import { useWellnessStore } from '../stores/wellness'
import { useSound } from '../composables/useHealthU'
import { usePreferences } from '../composables/usePreferences'

export default {
  name: 'AppTopbar',
  components: { AppIcon },
  props: {
    title: { type: String, default: '' },
    mobileOpen: { type: Boolean, default: false }
  },
  emits: ['toggle-mobile-menu'],
  setup() {
    const { soundEnabled, toggleSound } = useSound()
    const { theme, toggleTheme } = usePreferences()
    const wellness = useWellnessStore()
    const warningStore = useWarningStore()
    return { warningStore, wellness, soundEnabled, toggleSound, theme, toggleTheme }
  },
  data() {
    return {
      currentDate: ''
    }
  },
  computed: {
    userName() {
      return localStorage.getItem('userName') || '同学'
    },
    userInitial() {
      return this.userName.charAt(0)
    },
    effectivelyMuted() {
      return !this.soundEnabled || this.wellness.isDanger
    },
    soundLabel() {
      if (this.wellness.isDanger) return '关怀模式已自动静音'
      return this.effectivelyMuted ? '开启全局音效' : '关闭全局音效'
    }
  },
  methods: {
    onToggleSound() {
      if (this.wellness.isDanger) return
      this.toggleSound()
    }
  },
  mounted() {
    const now = new Date()
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    this.currentDate = `${now.getMonth() + 1} 月 ${now.getDate()} 日 · ${weekdays[now.getDay()]}`
    this.warningStore.refreshStats()
  }
}
</script>
