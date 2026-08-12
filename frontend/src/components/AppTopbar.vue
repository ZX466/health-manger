<template>
  <header class="topbar">
    <div class="topbar-left">
      <h1>{{ title }}</h1>
      <p>{{ currentDate }}</p>
    </div>
    <div class="topbar-right">
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
