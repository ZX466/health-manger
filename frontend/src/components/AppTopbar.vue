<template>
  <header class="topbar">
    <div class="topbar-left">
      <h1>{{ title }}</h1>
      <p>{{ currentDate }}</p>
    </div>
  </header>
</template>

<script>
export default {
  name: 'AppTopbar',
  props: {
    title: { type: String, default: '' }
  },
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
