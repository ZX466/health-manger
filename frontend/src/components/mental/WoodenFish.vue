<template>
  <section class="card wooden-fish">
    <div class="fish-head">
      <div>
        <p class="eyebrow">Pause</p>
        <h2>敲木鱼</h2>
      </div>
      <button
        class="sound-btn"
        type="button"
        :aria-label="soundEnabled ? '关闭木鱼声音' : '打开木鱼声音'"
        @click="toggleSound"
      >
        {{ soundEnabled ? '声音开' : '声音关' }}
      </button>
    </div>

    <button
      class="fish-btn"
      type="button"
      aria-label="敲一下木鱼"
      @click="hit"
    >
      <span
        v-for="ripple in ripples"
        :key="ripple.id"
        class="ripple"
        :style="{ left: `${ripple.x}%`, top: `${ripple.y}%` }"
        aria-hidden="true"
      >
        +1
      </span>
      <svg class="fish-svg" viewBox="0 0 130 96" aria-hidden="true">
        <path
          d="M18 62c0-20 19-35 46-35s46 15 46 35-19 25-46 25S18 82 18 62Z"
          class="fish-body"
        />
        <path d="M33 58c17-9 41-9 64 0" class="fish-slit" />
        <circle cx="92" cy="45" r="2.6" class="fish-eye" />
        <path d="M105 28 121 14" class="fish-handle" />
        <circle cx="123" cy="12" r="6" class="fish-knob" />
      </svg>
      <span class="fish-copy">
        <strong>敲一下，放空一下</strong>
        <span>不求功德，只求这 10 秒属于你</span>
      </span>
    </button>

    <div class="fish-foot">
      <span>今天 <strong>{{ todayCount }}</strong> 下</span>
      <span>累计 <strong>{{ totalCount }}</strong> 下</span>
    </div>
  </section>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useSound, playWoodfish } from '../../composables/useHealthU'
import { localDateKey } from '../../utils/date'

const { soundEnabled, toggleSound } = useSound()

const todayCount = ref(0)
const totalCount = ref(0)
const ripples = ref([])
let rippleId = 0
let rippleTimer = null

function readCount (key) {
  const value = Number(localStorage.getItem(key) || 0)
  return Number.isFinite(value) && value > 0 ? Math.floor(value) : 0
}

function readCounts () {
  try {
    const savedDate = localStorage.getItem('mf:date')
    const today = localDateKey()
    if (savedDate !== today) {
      localStorage.setItem('mf:date', today)
      localStorage.setItem('mf:count', '0')
      todayCount.value = 0
    } else {
      todayCount.value = readCount('mf:count')
    }
    totalCount.value = readCount('mf:total')
  } catch (e) {
    todayCount.value = 0
    totalCount.value = 0
  }
}

function spawnRipple () {
  const ripple = {
    id: ++rippleId,
    x: 30 + Math.round(Math.random() * 40),
    y: 28 + Math.round(Math.random() * 30)
  }
  ripples.value = [...ripples.value.slice(-5), ripple]
  if (rippleTimer) clearTimeout(rippleTimer)
  // 每次敲击都重新计时，统一清掉这一批飘字，避免旧 ripple 永久残留。
  rippleTimer = setTimeout(() => {
    ripples.value = []
    rippleTimer = null
  }, 900)
}

function hit () {
  const today = localDateKey()
  try {
    if (localStorage.getItem('mf:date') !== today) todayCount.value = 0
  } catch (e) { /* ignore */ }
  todayCount.value += 1
  totalCount.value += 1
  try {
    localStorage.setItem('mf:date', today)
    localStorage.setItem('mf:count', String(todayCount.value))
    localStorage.setItem('mf:total', String(totalCount.value))
  } catch (e) { /* ignore */ }
  playWoodfish()
  spawnRipple()
}

onMounted(readCounts)
onUnmounted(() => {
  if (rippleTimer) clearTimeout(rippleTimer)
})
</script>

<style scoped>
.wooden-fish {
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.fish-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.fish-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 18px;
  letter-spacing: -0.01em;
}

.sound-btn {
  padding: 3px 7px;
  border: var(--border-hairline);
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 10px;
  cursor: pointer;
}

.sound-btn:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.fish-btn {
  position: relative;
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  margin: 10px 0 12px;
  padding: 8px 6px;
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  cursor: pointer;
  overflow: hidden;
}

.fish-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.fish-svg {
  width: 112px;
  height: auto;
  transition: transform 140ms var(--ease-out);
}

.fish-btn:active .fish-svg {
  transform: rotate(-3deg) scale(0.97);
}

.fish-body {
  fill: var(--warn-soft);
  stroke: var(--warn);
  stroke-width: 2;
}

.fish-slit {
  fill: none;
  stroke: var(--warn);
  stroke-width: 2;
  stroke-linecap: round;
}

.fish-eye {
  fill: var(--warn);
}

.fish-handle {
  stroke: var(--muted);
  stroke-width: 2;
  stroke-linecap: round;
}

.fish-knob {
  fill: var(--muted);
}

.fish-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  text-align: center;
}

.fish-copy strong {
  font-size: 13px;
  font-weight: 600;
}

.fish-copy span {
  color: var(--muted);
  font-size: 11px;
}

.fish-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 10px;
  border-top: var(--border-hairline);
  color: var(--muted);
  font-size: 11px;
}

.fish-foot strong {
  color: var(--fg);
  font-family: var(--font-mono);
  font-size: 13px;
}

.ripple {
  position: absolute;
  z-index: 2;
  color: var(--warn);
  font-family: var(--font-mono);
  font-size: 11px;
  pointer-events: none;
  animation: ripple-up 900ms var(--ease-out) forwards;
}

@keyframes ripple-up {
  from {
    opacity: 0.9;
    transform: translate(-50%, 0) scale(0.8);
  }
  to {
    opacity: 0;
    transform: translate(-50%, -28px) scale(1.1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .fish-svg {
    transition: none;
  }

  .ripple {
    animation: none;
    opacity: 0;
  }
}
</style>
