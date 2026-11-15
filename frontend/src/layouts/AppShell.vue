<template>
  <div class="app-shell">
    <AppSidebar :mobileOpen="mobileOpen" @navigate="closeMobile" />
    <div
      class="sidebar-backdrop"
      :class="{ visible: mobileOpen }"
      aria-hidden="true"
      @click="closeMobile"
    />
    <main class="main app-main">
      <AppTopbar
        :title="pageTitle"
        :mobile-open="mobileOpen"
        @toggle-mobile-menu="toggleMobile"
      />
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
  watch: {
    '$route.path'() {
      this.closeMobile()
    },
    mobileOpen(value) {
      this.syncBodyLock(value)
    }
  },
  mounted() {
    window.addEventListener('keydown', this.onKeydown)
    window.addEventListener('resize', this.onResize)
  },
  beforeUnmount() {
    window.removeEventListener('keydown', this.onKeydown)
    window.removeEventListener('resize', this.onResize)
    this.syncBodyLock(false)
  },
  methods: {
    toggleMobile() {
      this.mobileOpen = !this.mobileOpen
    },
    closeMobile() {
      this.mobileOpen = false
    },
    onKeydown(event) {
      if (event.key === 'Escape' && this.mobileOpen) this.closeMobile()
    },
    onResize() {
      if (window.innerWidth > 768 && this.mobileOpen) this.closeMobile()
    },
    syncBodyLock(open) {
      document.body.style.overflow = open && window.innerWidth <= 768 ? 'hidden' : ''
    }
  }
}
</script>
