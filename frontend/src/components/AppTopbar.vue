<template>
  <header class="topbar">
    <div class="topbar-left">
      <h1>{{ title }}</h1>
      <p>{{ currentDate }}</p>
    </div>
    <div class="topbar-right">
      <button class="topbar-btn" title="通知" @click="$router.push('/health-reminder')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0"/>
        </svg>
        <span v-if="unreadCount > 0" class="notif-dot"></span>
      </button>
      <button
        class="topbar-btn mobile-menu-btn"
        title="菜单"
        style="display:none"
        @click="$emit('toggle-mobile-menu')"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
    </div>
  </header>
</template>

<script>
export default {
  name: 'AppTopbar',
  props: {
    title: { type: String, default: '' }
  },
  emits: ['toggle-mobile-menu'],
  data() {
    return {
      currentDate: '',
      unreadCount: 0
    }
  },
  mounted() {
    const now = new Date()
    this.currentDate = now.toLocaleDateString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
    })
    this.loadUnreadCount()
  },
  methods: {
    async loadUnreadCount() {
      try {
        const response = await import('../api').then(m => m.default.getWarningStats())
        this.unreadCount = response.data?.unread || 0
      } catch (err) {
        // ignore
      }
    }
  }
}
</script>
