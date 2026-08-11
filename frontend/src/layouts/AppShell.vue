<template>
  <div class="app-shell">
    <AppSidebar :mobileOpen="mobileOpen" @navigate="closeMobile" />
    <div class="sidebar-backdrop" :class="{ visible: mobileOpen }" @click="closeMobile" />
    <main class="main">
      <AppTopbar :title="pageTitle" @toggle-mobile-menu="toggleMobile" />
      <div class="content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script>
import AppSidebar from '../components/AppSidebar.vue'
import AppTopbar from '../components/AppTopbar.vue'

export default {
  name: 'AppShell',
  components: { AppSidebar, AppTopbar },
  data() {
    return {
      mobileOpen: false
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
