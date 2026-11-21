<template>
  <Teleport to="body">
    <div v-if="open" class="more-dialog-backdrop" @click.self="$emit('close')">
      <section
        ref="panel"
        class="more-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="more-dialog-title"
        tabindex="-1"
        @keydown.esc.stop.prevent="$emit('close')"
      >
        <div class="more-dialog-head">
          <div>
            <p class="micro">ALL PAGES</p>
            <h2 id="more-dialog-title">更多页面</h2>
          </div>
          <button class="icon-btn" type="button" aria-label="关闭" @click="$emit('close')">
            <AppIcon name="close" :size="18" />
          </button>
        </div>
        <div class="more-grid">
          <router-link
            v-for="item in pages"
            :key="item.path"
            :to="item.path"
            class="more-card"
            @click="$emit('close')"
          >
            <span class="micro">{{ item.num }}</span>
            <strong>{{ item.title }}</strong>
            <small>{{ item.desc }}</small>
          </router-link>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  open: { type: Boolean, default: false }
})
const emit = defineEmits(['close'])
const panel = ref(null)

const pages = [
  { path: '/sport-management', num: '04', title: '运动记录', desc: '活动、消耗与打卡' },
  { path: '/health-record', num: '05', title: '体检档案', desc: 'OCR 识别与历史' },
  { path: '/weekly-report', num: '06', title: '健康周报', desc: '一周睡眠 · 饮食 · 运动 · 心情' },
  { path: '/tongue-diagnosis', num: '07', title: '赛博把脉', desc: '舌象视觉识别' },
  { path: '/ai-settings', num: '08', title: '设置', desc: '搭子声画与提醒' }
]

watch(() => props.open, async (value) => {
  document.body.style.overflow = value ? 'hidden' : ''
  if (!value) return
  await nextTick()
  panel.value?.focus()
})

function onKeydown (event) {
  if (!props.open) return
  if (event.key === 'Escape') {
    event.preventDefault()
    emit('close')
  }
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>
