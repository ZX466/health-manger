<template>
  <section class="card breathing">
    <div class="breathing-head">
      <div>
        <p class="eyebrow">Breathe</p>
        <h2>呼吸一下</h2>
      </div>
      <button
        v-if="running"
        class="btn btn-ghost btn-sm"
        type="button"
        @click="stop"
      >
        结束
      </button>
    </div>

    <div class="breathing-stage" :class="`phase-${phase}`">
      <button
        class="ring"
        type="button"
        :aria-label="running ? '结束呼吸练习' : '开始 4-4-6 呼吸练习'"
        @click="toggle"
      >
        <span class="ring-halo" aria-hidden="true"></span>
        <span class="ring-orb" aria-hidden="true"></span>
        <span class="ring-content">
          <strong>{{ displayPhase }}</strong>
          <span>{{ displayCount }}</span>
        </span>
      </button>
      <p class="breathing-hint">{{ hint }}</p>
    </div>

    <div class="breathing-meta">
      <span>4-4-6 呼吸</span>
      <span>约 28 秒 · 2 轮</span>
      <span v-if="running" class="remaining">还剩 {{ totalSeconds - elapsed }} 秒</span>
    </div>
  </section>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'

const INHALE = 4
const HOLD = 4
const EXHALE = 6
const CYCLE = INHALE + HOLD + EXHALE
const CYCLES = 2
const totalSeconds = CYCLE * CYCLES

const running = ref(false)
const done = ref(false)
const elapsed = ref(0)
let timer = null

const inCycle = computed(() => elapsed.value % CYCLE)
const phase = computed(() => {
  if (!running.value) return done.value ? 'done' : 'idle'
  if (inCycle.value < INHALE) return 'inhale'
  if (inCycle.value < INHALE + HOLD) return 'hold'
  return 'exhale'
})

const phaseLeft = computed(() => {
  if (phase.value === 'inhale') return INHALE - inCycle.value
  if (phase.value === 'hold') return INHALE + HOLD - inCycle.value
  if (phase.value === 'exhale') return CYCLE - inCycle.value
  return 0
})

const displayPhase = computed(() => ({
  idle: '开始',
  inhale: '吸气',
  hold: '屏住',
  exhale: '呼气',
  done: '完成'
}[phase.value]))

const displayCount = computed(() => {
  if (phase.value === 'idle') return '4-4-6'
  if (phase.value === 'done') return '再来一轮'
  return `${Math.max(1, phaseLeft.value)}s`
})

const hint = computed(() => ({
  idle: '点一下圆环，跟着节奏慢慢来',
  inhale: '用鼻子慢慢吸气，肩膀放松',
  hold: '轻轻屏住，不用用力',
  exhale: '用嘴巴缓缓呼气，把肩膀放下来',
  done: '做得很好，随时可以再来'
}[phase.value]))

function clearTimer () {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function start () {
  clearTimer()
  done.value = false
  elapsed.value = 0
  running.value = true
  timer = setInterval(() => {
    elapsed.value += 1
    if (elapsed.value >= totalSeconds) {
      clearTimer()
      running.value = false
      done.value = true
      elapsed.value = totalSeconds
    }
  }, 1000)
}

function stop () {
  clearTimer()
  running.value = false
  done.value = false
  elapsed.value = 0
}

function toggle () {
  if (running.value) stop()
  else start()
}

onUnmounted(clearTimer)
</script>

<style scoped>
.breathing {
  display: flex;
  flex-direction: column;
  padding: 22px;
}

.breathing-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.breathing-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 18px;
  letter-spacing: -0.01em;
}

.breathing-stage {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 12px 0 8px;
}

.ring {
  position: relative;
  display: grid;
  place-items: center;
  width: 164px;
  height: 164px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
}

.ring:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 4px;
}

.ring-halo {
  position: absolute;
  inset: 0;
  border: 1px solid var(--border);
  border-radius: 50%;
}

.ring-orb {
  position: absolute;
  width: 112px;
  height: 112px;
  border-radius: 50%;
  background: color-mix(in oklch, var(--accent-soft), var(--surface) 22%);
  border: 1px solid color-mix(in oklch, var(--accent) 18%, var(--border));
  transform: scale(0.78);
  transition: transform 600ms var(--ease-out), background 600ms var(--ease-out);
}

.phase-inhale .ring-orb {
  transform: scale(1.12);
  transition-duration: 4s;
  transition-timing-function: linear;
}

.phase-hold .ring-orb {
  transform: scale(1.12);
  transition-duration: 700ms;
}

.phase-exhale .ring-orb {
  transform: scale(0.78);
  transition-duration: 6s;
  transition-timing-function: linear;
}

.ring-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.ring-content strong {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.ring-content span {
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 12px;
}

.breathing-hint {
  margin: 0;
  padding: 0 12px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
  text-align: center;
}

.breathing-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 10px;
  border-top: var(--border-hairline);
  color: var(--muted);
  font-size: 11px;
}

.remaining {
  color: var(--accent-strong);
  font-family: var(--font-mono);
}

@media (prefers-reduced-motion: reduce) {
  .ring-orb,
  .phase-inhale .ring-orb,
  .phase-hold .ring-orb,
  .phase-exhale .ring-orb {
    transition: none;
    transform: none;
  }
}
</style>
