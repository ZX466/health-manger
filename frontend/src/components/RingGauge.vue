<template>
  <div
    class="ring-gauge"
    :class="[`ring-gauge--${mode}`, { 'is-running': running }]"
    :style="{ width: size + 'px', height: size + 'px' }"
  >
    <svg
      v-if="mode === 'score'"
      :width="size" :height="size" viewBox="0 0 120 120"
      aria-hidden="true" focusable="false"
    >
      <circle class="ring-gauge__track" cx="60" cy="60" :r="radius" fill="none" :stroke-width="stroke"/>
      <circle
        class="ring-gauge__bar"
        cx="60" cy="60" :r="radius" fill="none"
        :stroke-width="stroke"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashOffset"
      />
    </svg>

    <div v-else class="breathe-stage" aria-hidden="true">
      <span class="breathe-halo"></span>
      <span :key="pulseKey" class="breathe-orb" :class="`phase-${phase}`"></span>
      <svg class="breathe-ring" viewBox="0 0 120 120" focusable="false">
        <circle class="breathe-ring__track" cx="60" cy="60" r="54" fill="none" stroke-width="2" />
      </svg>
    </div>

    <div class="ring-gauge__center" :class="{ 'ring-gauge__center--breathe': mode === 'breathe' }">
      <template v-if="mode === 'score'">
        <span class="ring-gauge__num num">{{ display }}</span>
        <span class="ring-gauge__label">{{ label }}</span>
        <span v-if="note" class="ring-gauge__note">{{ note }}</span>
      </template>
      <template v-else>
        <span class="ring-gauge__label">{{ phaseLabel }}</span>
        <span class="breathe-count num" aria-live="polite">{{ breatheCount }}</span>
        <span class="ring-gauge__note">{{ breatheHint }}</span>
      </template>
    </div>

    <div v-if="mode === 'breathe'" class="breathe-controls">
      <button
        v-if="!running"
        class="btn btn-primary btn-sm"
        type="button"
        @click="startBreathe"
      >
        {{ phase === 'idle' || phase === 'done' ? '开始呼吸' : '继续' }}
      </button>
      <button
        v-else
        class="btn btn-ghost btn-sm"
        type="button"
        @click="pauseBreathe"
      >
        暂停
      </button>
      <button class="btn btn-ghost btn-sm" type="button" @click="resetBreathe">重置</button>
      <button
        class="sound-btn"
        type="button"
        :aria-pressed="soundEnabled"
        @click="toggleSound"
      >
        {{ soundEnabled ? '节拍开' : '节拍关' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useSound, playBreathCue } from '../composables/useHealthU'

const props = defineProps({
  value:    { type: Number, default: 0 }, // 0–100
  label:    { type: String, default: '健康评分' },
  note:     { type: String, default: '' },
  size:     { type: Number, default: 168 },
  stroke:   { type: Number, default: 10 },
  duration: { type: Number, default: 900 },
  mode:     { type: String, default: 'score', validator: v => ['score', 'breathe'].includes(v) }
})

const { soundEnabled, toggleSound } = useSound()

/* ── 评分模式 ─────────────────────────────────────────── */
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
function animate () {
  const from = 0
  const to = clamped.value
  const t0 = performance.now()
  const step = (t) => {
    const k = Math.min(1, (t - t0) / props.duration)
    const eased = 1 - Math.pow(1 - k, 3)
    display.value = Math.round(from + (to - from) * eased)
    if (k < 1) raf = requestAnimationFrame(step)
  }
  raf = requestAnimationFrame(step)
}

/* ── 4-7-8 呼吸模式 ───────────────────────────────────── */
const PHASES = {
  inhale: { seconds: 4, label: '把焦虑吸进来', hint: '用鼻子慢慢吸气，肩膀放松' },
  hold: { seconds: 7, label: '把 DDL 冻住', hint: '轻轻屏住，不用用力' },
  exhale: { seconds: 8, label: '把烦恼全吐出去', hint: '用嘴巴缓缓呼气，把肩膀放下来' }
}
const ORDER = ['inhale', 'hold', 'exhale']

const phase = ref('idle')
const secondsLeft = ref(0)
const running = ref(false)
const pulseKey = ref(0)
const cycles = ref(0)
let timer = null

const phaseLabel = computed(() => {
  if (phase.value === 'idle') return '4-7-8 减压呼吸'
  if (phase.value === 'done') return '完成一轮'
  return PHASES[phase.value]?.label || ''
})
const breatheCount = computed(() => {
  if (phase.value === 'idle') return '4 · 7 · 8'
  if (phase.value === 'done') return '再来一轮'
  return `${Math.max(0, secondsLeft.value)}s`
})
const breatheHint = computed(() => {
  if (phase.value === 'idle') return '吸 4 秒 · 屏 7 秒 · 呼 8 秒'
  if (phase.value === 'done') return `已完成 ${cycles.value} 轮，随时可以再来`
  return PHASES[phase.value]?.hint || '跟着圆环的节奏'
})

function clearTimer () {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function enterPhase (next) {
  phase.value = next
  secondsLeft.value = PHASES[next].seconds
  playBreathCue(next)
}

function startBreathe () {
  if (running.value) return
  if (phase.value === 'idle' || phase.value === 'done') {
    cycles.value = 0
    pulseKey.value += 1
    enterPhase('inhale')
  }
  running.value = true
  clearTimer()
  timer = setInterval(() => {
    secondsLeft.value -= 1
    if (secondsLeft.value > 0) return
    const index = ORDER.indexOf(phase.value)
    if (index === ORDER.length - 1) {
      cycles.value += 1
      enterPhase('inhale')
      pulseKey.value += 1
    } else {
      enterPhase(ORDER[index + 1])
    }
  }, 1000)
}

function pauseBreathe () {
  running.value = false
  clearTimer()
}

function resetBreathe () {
  running.value = false
  clearTimer()
  phase.value = 'idle'
  secondsLeft.value = 0
  cycles.value = 0
  pulseKey.value += 1
}

onMounted(() => { if (props.mode === 'score' && !reduced) animate() })
onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  clearTimer()
})
</script>

<style scoped>
.ring-gauge { position: relative; display: grid; place-items: center; }
.ring-gauge svg { display: block; }
.ring-gauge--score svg { transform: rotate(-90deg); }
.ring-gauge__track { stroke: var(--border); }
.ring-gauge__bar { stroke: var(--accent); stroke-linecap: round; }
.ring-gauge__center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  text-align: center;
  pointer-events: none;
}
.ring-gauge__num { font-size: 34px; font-weight: 600; letter-spacing: -0.01em; font-variant-numeric: tabular-nums; line-height: 1; }
.ring-gauge__label { font-size: 12px; color: var(--muted); letter-spacing: 0.02em; }
.ring-gauge__note { font-size: 11px; color: var(--muted); }

/* 呼吸模式 */
.ring-gauge--breathe {
  padding-bottom: 34px;
}

.breathe-stage {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
}

.breathe-halo {
  position: absolute;
  inset: 6px;
  border: 1px solid var(--border);
  border-radius: 50%;
}

.breathe-orb {
  position: absolute;
  width: 72%;
  height: 72%;
  border-radius: 50%;
  background: color-mix(in oklch, var(--accent-soft), var(--surface) 26%);
  border: 1px solid color-mix(in oklch, var(--accent) 18%, var(--border));
  transform: scale(0.78);
  animation: breathe-478 19s linear infinite;
  animation-play-state: paused;
}

.is-running .breathe-orb {
  animation-play-state: running;
}

.breathe-ring {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.breathe-ring__track {
  stroke: color-mix(in oklch, var(--accent) 20%, var(--border));
  stroke-dasharray: 4 7;
  stroke-linecap: round;
}

.breathe-count {
  font-family: var(--font-mono);
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.02em;
}

.ring-gauge__center--breathe { padding-top: 8px; }

.breathe-controls {
  position: absolute;
  left: 50%;
  bottom: -34px;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.breathe-controls .btn {
  min-height: 36px;
  padding: 6px 12px;
  font-size: 12px;
}

.sound-btn {
  min-height: 36px;
  padding: 4px 9px;
  border: var(--border-hairline);
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 11px;
  cursor: pointer;
}

.sound-btn:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

@keyframes breathe-478 {
  0%   { transform: scale(0.78); }
  21%  { transform: scale(1.12); }
  58%  { transform: scale(1.12); }
  100% { transform: scale(0.78); }
}

@media (prefers-reduced-motion: reduce) {
  .breathe-orb {
    animation: none;
    transform: scale(1);
  }
}
</style>
