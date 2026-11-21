<template>
  <div class="app-shell v21" :class="{ 'is-serious': serious }">
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
    <MobileTabs :inert="mobileOpen" @more="openMoreDialog" />
    <MoreDialog :open="moreOpen" @close="closeMoreDialog" />
  </div>
</template>

<script>
import AppSidebar from '../components/AppSidebar.vue'
import AppTopbar from '../components/AppTopbar.vue'
import MobileTabs from '../components/MobileTabs.vue'
import MoreDialog from '../components/MoreDialog.vue'
import { usePreferences, initPreferences } from '../composables/usePreferences'
import { setAudioSuppressed } from '../composables/useHealthU'
import { useWellnessStore } from '../stores/wellness'

export default {
  name: 'AppShell',
  components: { AppSidebar, AppTopbar, MobileTabs, MoreDialog },
  setup() {
    initPreferences()
    const wellness = useWellnessStore()
    const prefs = usePreferences()
    return { wellness, prefs }
  },
  data() {
    return {
      mobileOpen: false,
      moreOpen: false,
      isMobile: false,
      lastFocused: null
    }
  },
  computed: {
    pageTitle() {
      return this.$route.meta?.title || ''
    },
    serious() {
      return this.wellness.isDanger
    }
  },
  watch: {
    '$route.path'() {
      this.closeMobile()
      this.closeMoreDialog()
    },
    mobileOpen(value) {
      this.syncBodyLock(value)
      if (value) {
        this.lastFocused = document.activeElement
        this.$nextTick(() => this.focusFirstNav())
      }
    },
    serious(value) {
      setAudioSuppressed(value)
    }
  },
  mounted() {
    this.syncViewport()
    this.wellness.hydrateLocal()
    this.wellness.load()
    setAudioSuppressed(this.serious)
    window.addEventListener('keydown', this.onKeydown)
    window.addEventListener('resize', this.onResize)
  },
  beforeUnmount() {
    window.removeEventListener('keydown', this.onKeydown)
    window.removeEventListener('resize', this.onResize)
    this.syncBodyLock(false)
    setAudioSuppressed(false)
  },
  methods: {
    toggleMobile() {
      if (!this.isMobile) return
      if (this.mobileOpen) this.closeMobile()
      else this.mobileOpen = true
    },
    openMobile() {
      if (this.isMobile) this.mobileOpen = true
    },
    openMoreDialog() {
      if (!this.isMobile) return
      this.closeMobile()
      this.moreOpen = true
    },
    closeMoreDialog() {
      if (!this.moreOpen) return
      this.moreOpen = false
    },
    closeMobile() {
      if (!this.mobileOpen) return
      // 入口可能位于即将被 inert 的 MobileTabs 中：先关闭解除 inert，再归还焦点。
      let target = this.lastFocused
      if (!target || target === document.body || !target.isConnected || typeof target.focus !== 'function') {
        target = this.$refs.topbar?.$el?.querySelector('.mobile-menu-btn')
      }
      this.lastFocused = null
      this.mobileOpen = false
      this.$nextTick(() => {
        if (target?.isConnected && typeof target.focus === 'function') {
          target.focus()
          return
        }
        const fallback = this.$refs.topbar?.$el?.querySelector('.mobile-menu-btn')
        if (fallback?.isConnected) fallback.focus()
      })
    },
    onKeydown(event) {
      if (event.key === 'Escape' && this.moreOpen) {
        event.preventDefault()
        this.closeMoreDialog()
        return
      }
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
