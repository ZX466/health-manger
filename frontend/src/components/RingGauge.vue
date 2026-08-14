<template>
  <div class="ring-gauge" :style="{ width: size + 'px', height: size + 'px' }">
    <svg :width="size" :height="size" viewBox="0 0 120 120" aria-hidden="true" focusable="false">
      <circle class="ring-gauge__track" cx="60" cy="60" :r="radius" fill="none" :stroke-width="stroke"/>
      <circle
        class="ring-gauge__bar"
        cx="60" cy="60" :r="radius" fill="none"
        :stroke-width="stroke"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashOffset"
      />
    </svg>
    <div class="ring-gauge__center">
      <span class="ring-gauge__num num">{{ display }}</span>
      <span class="ring-gauge__label">{{ label }}</span>
      <span v-if="note" class="ring-gauge__note">{{ note }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  value:    { type: Number, required: true }, // 0–100
  label:    { type: String, default: '健康评分' },
  note:     { type: String, default: '' },
  size:     { type: Number, default: 168 },
  stroke:   { type: Number, default: 10 },
  duration: { type: Number, default: 900 },
})

const radius = computed(() => (120 - props.stroke) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const clamped = computed(() => Math.max(0, Math.min(100, props.value)))
const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

const display = ref(reduced ? clamped.value : 0)
const dashOffset = computed(() => {
  const p = reduced ? clamped.value : display.value
  return circumference.value * (1 - p / 100)
})

let raf = 0
function animate() {
  const from = 0, to = clamped.value, t0 = performance.now()
  const step = (t) => {
    const k = Math.min(1, (t - t0) / props.duration)
    const eased = 1 - Math.pow(1 - k, 3) // ease-out cubic
    display.value = Math.round(from + (to - from) * eased)
    if (k < 1) raf = requestAnimationFrame(step)
  }
  raf = requestAnimationFrame(step)
}

onMounted(() => { if (!reduced) animate() })
onBeforeUnmount(() => cancelAnimationFrame(raf))
</script>

<style scoped>
.ring-gauge { position: relative; display: grid; place-items: center; }
.ring-gauge svg { display: block; transform: rotate(-90deg); }
.ring-gauge__track { stroke: var(--border); }
.ring-gauge__bar { stroke: var(--accent); stroke-linecap: round; }
.ring-gauge__center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; text-align: center; }
.ring-gauge__num { font-size: 34px; font-weight: 600; letter-spacing: -0.01em; font-variant-numeric: tabular-nums; line-height: 1; }
.ring-gauge__label { font-size: 12px; color: var(--muted); letter-spacing: 0.02em; }
.ring-gauge__note { font-size: 11px; color: var(--muted); }
</style>
