<template>
  <nav class="mobile-tabs" aria-label="移动端主导航">
    <router-link
      v-for="item in tabs"
      :key="item.path"
      :to="item.path"
      class="mobile-tab"
      :class="{ active: isActive(item.path) }"
    >
      <AppIcon :name="item.icon" :size="18" />
      <span>{{ item.label }}</span>
    </router-link>
    <button
      class="mobile-tab"
      type="button"
      :class="{ active: moreActive }"
      aria-label="打开更多页面"
      @click="$emit('more')"
    >
      <AppIcon name="more" :size="18" />
      <span>更多</span>
    </button>
  </nav>
</template>

<script>
import AppIcon from './AppIcon.vue'

export default {
  name: 'MobileTabs',
  components: { AppIcon },
  emits: ['more'],
  data() {
    return {
      tabs: [
        { path: '/dashboard', label: '总览', icon: 'home' },
        { path: '/mental', label: '心理', icon: 'heart' },
        { path: '/diet-management', label: '饮食', icon: 'diet' },
        { path: '/chat', label: '对话', icon: 'ai' }
      ]
    }
  },
  computed: {
    moreActive() {
      return !this.tabs.some(item => item.path === this.$route.path)
    }
  },
  methods: {
    isActive(path) {
      return this.$route.path === path
    }
  }
}
</script>
