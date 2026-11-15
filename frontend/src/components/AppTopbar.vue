<template>
  <header class="topbar">
    <div class="topbar-left">
      <button
        class="mobile-menu-btn topbar-btn"
        type="button"
        :aria-label="mobileOpen ? '关闭导航菜单' : '打开导航菜单'"
        aria-controls="app-sidebar"
        :aria-expanded="mobileOpen"
        @click="$emit('toggle-mobile-menu')"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
          <path d="M4 7h16M4 12h16M4 17h16" />
        </svg>
      </button>
      <div class="topbar-titles">
        <h1>{{ title }}</h1>
        <p>{{ currentDate }}</p>
      </div>
    </div>
  </header>
</template>

<script>
export default {
  name: 'AppTopbar',
  props: {
    title: { type: String, default: '' },
    mobileOpen: { type: Boolean, default: false }
  },
  emits: ['toggle-mobile-menu'],
  data() {
    return {
      currentDate: ''
    }
  },
  mounted() {
    const now = new Date()
    this.currentDate = now.toLocaleDateString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
    })
  }
}
</script>

<style scoped>
.topbar-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.topbar-titles { min-width: 0; }
.mobile-menu-btn { display: none; flex: 0 0 auto; }

@media (max-width: 768px) {
  .mobile-menu-btn { display: grid; }
}
</style>
