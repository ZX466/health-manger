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

export default {
  name: 'AppTopbar',
  components: { AppIcon },
  props: {
    title: { type: String, default: '' },
    mobileOpen: { type: Boolean, default: false }
  },
  emits: ['toggle-mobile-menu'],
  setup() {
    return { warningStore: useWarningStore() }
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
