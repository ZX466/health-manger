<template>
  <div class="app-shell">
    <AppSidebar :mobileOpen="mobileOpen" @navigate="closeMobile" />
    <div class="sidebar-backdrop" :class="{ visible: mobileOpen }" @click="closeMobile" />
    <main class="main app-main">
      <AppTopbar :title="pageTitle" @toggle-mobile-menu="toggleMobile" />
      <div class="content">
        <router-view />
      </div>
    </main>

    <!-- 移动端底部 Tab 栏（≤768px 由 layout.css 控制显示） -->
    <nav class="tab-bar" aria-label="底部导航">
      <RouterLink
        v-for="t in tabs" :key="t.to"
        :to="t.to"
        :class="{ active: $route.path === t.to }"
      >
        <AppIcon :name="t.icon" :size="20" />
        {{ t.label }}
      </RouterLink>
    </nav>
  </div>
</template>

<script>
import AppSidebar from '../components/AppSidebar.vue'
import AppTopbar from '../components/AppTopbar.vue'
import AppIcon from '../components/AppIcon.vue'

export default {
  name: 'AppShell',
  components: { AppSidebar, AppTopbar, AppIcon },
  data() {
    return {
      mobileOpen: false,
      tabs: [
        { to: '/dashboard', icon: 'home', label: '首页' },
        { to: '/health-record', icon: 'record', label: '记录' },
        { to: '/diet-management', icon: 'diet', label: '饮食' },
        { to: '/sport-management', icon: 'sport', label: '运动' },
        { to: '/tongue-diagnosis', icon: 'more', label: '更多' }
      ]
    }
  },
  computed: {
    pageTitle() {
      return this.$route.meta?.title || ''
    }
  },
  methods: {
    toggleMobile() {
      this.mobileOpen = !this.mobileOpen
    },
    closeMobile() {
      this.mobileOpen = false
    }
  }
}
</script>
