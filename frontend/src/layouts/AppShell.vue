<template>
  <div class="app-shell">
    <AppSidebar
      ref="sidebar"
      :mobile-open="mobileOpen"
      :is-mobile="isMobile"
      @navigate="closeMobile"
    />
    <div
      class="sidebar-backdrop"
      :class="{ visible: mobileOpen }"
      aria-hidden="true"
      @click="closeMobile"
    />
    <main class="main app-main">
      <AppTopbar
        ref="topbar"
        :title="pageTitle"
        :mobile-open="mobileOpen"
        @toggle-mobile-menu="toggleMobile"
      />
      <div class="content" :inert="mobileOpen">
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
      mobileOpen: false,
      isMobile: false,
      lastFocused: null
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
      if (value) {
        this.lastFocused = document.activeElement
        this.$nextTick(() => this.focusFirstNav())
      }
    }
  },
  mounted() {
    this.syncViewport()
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
      if (!this.isMobile) return
      if (this.mobileOpen) this.closeMobile()
      else this.mobileOpen = true
    },
    closeMobile() {
      if (!this.mobileOpen) return
      // 先把焦点移出即将 aria-hidden 的抽屉，再关闭，避免读屏焦点被困。
      let target = this.lastFocused
      if (!target || target === document.body || !target.isConnected || typeof target.focus !== 'function') {
        target = this.$refs.topbar?.$el?.querySelector('.mobile-menu-btn')
      }
      this.lastFocused = null
      if (target?.isConnected && typeof target.focus === 'function') target.focus()
      this.mobileOpen = false
    },
    onKeydown(event) {
      if (event.key === 'Escape' && this.mobileOpen) {
        event.preventDefault()
        this.closeMobile()
        return
      }
      if (event.key !== 'Tab' || !this.mobileOpen || !this.isMobile) return

      const focusables = this.navFocusables()
      if (!focusables.length) return
      const first = focusables[0]
      const last = focusables[focusables.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    },
    onResize() {
      this.syncViewport()
      if (!this.isMobile && this.mobileOpen) this.closeMobile()
    },
    syncViewport() {
      this.isMobile = window.innerWidth <= 768
      if (!this.isMobile) this.syncBodyLock(false)
    },
    syncBodyLock(open) {
      document.body.style.overflow = open && this.isMobile ? 'hidden' : ''
    },
    navFocusables() {
      const root = this.$refs.sidebar?.$el
      if (!root) return []
      return Array.from(
        root.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])')
      ).filter(element => element.getClientRects().length > 0)
    },
    focusFirstNav() {
      const [first] = this.navFocusables()
      if (first) first.focus()
      else this.$refs.sidebar?.$el?.focus?.()
    }
  }
}
</script>
