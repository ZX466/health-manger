<template>
  <section class="card stress-shredder">
    <div class="section-head">
      <div>
        <p class="eyebrow">Pause & release</p>
        <h2>给情绪一个出口</h2>
      </div>
      <span class="sound-state" role="status">{{ soundEnabled ? '音效开' : '音效关' }}</span>
    </div>

    <div class="tool-grid">
      <!-- 电子木鱼 -->
      <div class="tool wooden-fish">
        <div class="tool-head">
          <div>
            <h3>电子木鱼</h3>
            <p>不求功德，只求这 10 秒属于你</p>
          </div>
          <button
            class="sound-btn"
            type="button"
            :aria-pressed="soundEnabled"
            @click="toggleSound"
          >
            {{ soundEnabled ? '静音' : '开声' }}
          </button>
        </div>

        <button
          class="fish-btn"
          :class="{ 'is-hitting': hitting }"
          type="button"
          aria-label="敲一下电子木鱼"
          @click="hitFish"
        >
          <span
            v-for="float in floats"
            :key="float.id"
            class="float-word"
            :style="{ left: `${float.x}%` }"
            aria-hidden="true"
          >
            {{ float.text }}
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
          <span class="fish-hint">点一下，放空一下</span>
        </button>

        <div class="tool-foot">
          <span>本轮 <strong>{{ fishCount }}</strong> 下</span>
          <span>心态 <strong>+{{ fishCount }}</strong></span>
        </div>
      </div>

      <!-- 烦恼粉碎机 -->
      <div class="tool shredder">
        <div class="tool-head">
          <div>
            <h3>烦恼粉碎机</h3>
            <p>只在前端裂解，不上传、不保存</p>
          </div>
          <span class="tool-count">已超度 {{ shreddedCount }} 件</span>
        </div>

        <form class="shredder-form" @submit.prevent="shred">
          <label class="sr-only" for="worry-input">写下烦心事</label>
          <input
            id="worry-input"
            v-model="worry"
            class="worry-input"
            type="text"
            maxlength="120"
            placeholder="把烦心事丢进来，一键物理超度..."
            autocomplete="off"
          />
          <button class="btn btn-primary btn-sm" type="submit" :disabled="!worry.trim()">
            粉碎
          </button>
        </form>

        <p v-if="error" class="shredder-error" role="alert">{{ error }}</p>

        <div class="shred-stage" aria-live="polite">
          <div v-if="!shreds.length" class="shred-empty">
            <span class="shred-empty__mark" aria-hidden="true"></span>
            <span>写下来的瞬间，它就已经小了一点。</span>
          </div>
          <div
            v-for="item in shreds"
            :key="item.id"
            class="shred-card"
            :class="{ 'is-shredding': item.shredding }"
          >
            <span
              v-for="piece in 8"
              :key="piece"
              class="shred-piece"
              :class="`piece-${piece}`"
              :style="{ '--dx': item.dx[piece - 1] + 'px', '--dy': item.dy[piece - 1] + 'px' }"
              aria-hidden="true"
            >{{ item.text }}</span>
            <span class="sr-only">{{ item.text }}</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onUnmounted, ref } from 'vue'
import { playWoodfish, useSound } from '../composables/useHealthU'

const { soundEnabled, toggleSound } = useSound()

const hitting = ref(false)
const fishCount = ref(0)
const floats = ref([])
let hitTimer = null
let floatTimer = null

function hitFish () {
  if (hitTimer) clearTimeout(hitTimer)
  hitting.value = true
  hitTimer = setTimeout(() => { hitting.value = false }, 170)

  fishCount.value += 1
  playWoodfish()

  const id = Date.now() + Math.random()
  floats.value = [
    ...floats.value.slice(-4),
    {
      id,
      x: 34 + Math.round(Math.random() * 32),
      text: fishCount.value % 3 === 0 ? '+1 功德' : '+1 心态'
    }
  ]
  if (floatTimer) clearTimeout(floatTimer)
  floatTimer = setTimeout(() => { floats.value = [] }, 900)
}

const worry = ref('')
const error = ref('')
const shreds = ref([])
const shreddedCount = ref(0)
let seq = 0

function makeOffsets () {
  return Array.from({ length: 8 }, (_, index) => {
    const spread = (index - 3.5) * 14
    return {
      dx: Math.round(spread + (Math.random() * 26 - 13)),
      dy: Math.round(24 + Math.random() * 34)
    }
  })
}

function shred () {
  const text = worry.value.trim()
  if (!text) {
    error.value = '先写一句烦心事，再按粉碎'
    return
  }
  error.value = ''
  worry.value = ''
  const offsets = makeOffsets()
  const item = {
    id: ++seq,
    text,
    shredding: false,
    dx: offsets.map(offset => offset.dx),
    dy: offsets.map(offset => offset.dy)
  }
  shreds.value = [...shreds.value.slice(-2), item]
  shreddedCount.value += 1

  requestAnimationFrame(() => {
    const target = shreds.value.find(entry => entry.id === item.id)
    if (target) target.shredding = true
  })

  setTimeout(() => {
    shreds.value = shreds.value.filter(entry => entry.id !== item.id)
  }, 1100)
}

onUnmounted(() => {
  if (hitTimer) clearTimeout(hitTimer)
  if (floatTimer) clearTimeout(floatTimer)
})
</script>

<style scoped>
.stress-shredder {
  padding: 22px;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 18px;
  letter-spacing: -0.01em;
}

.sound-state {
  color: var(--muted);
  font-size: 11px;
  white-space: nowrap;
}

.tool-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.tool {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 16px;
  border: var(--border-hairline);
  border-radius: var(--radius-md);
  background: var(--bg);
}

.tool-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.tool-head h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 15px;
  letter-spacing: -0.01em;
}

.tool-head p {
  margin: 2px 0 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.5;
}

.sound-btn {
  min-height: 32px;
  padding: 3px 8px;
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
  gap: 2px;
  width: 100%;
  min-height: 150px;
  margin: 8px 0;
  padding: 8px;
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  cursor: pointer;
  overflow: hidden;
}

.fish-btn:active .fish-svg,
.fish-btn.is-hitting .fish-svg {
  transform: scale(0.94);
}

.fish-svg {
  width: 118px;
  height: auto;
  transition: transform 160ms var(--ease-out);
}

.fish-body {
  fill: var(--warn-soft);
  stroke: var(--warn);
  stroke-width: 2;
}

.fish-slit,
.fish-handle {
  fill: none;
  stroke: var(--warn);
  stroke-width: 2;
  stroke-linecap: round;
}

.fish-eye,
.fish-knob {
  fill: var(--warn);
}

.fish-hint {
  color: var(--muted);
  font-size: 11px;
}

.tool-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 9px;
  border-top: var(--border-hairline);
  color: var(--muted);
  font-size: 11px;
}

.tool-foot strong {
  color: var(--fg);
  font-family: var(--font-mono);
  font-size: 13px;
}

.float-word {
  position: absolute;
  top: 34%;
  z-index: 2;
  color: var(--warn);
  font-family: var(--font-mono);
  font-size: 12px;
  white-space: nowrap;
  pointer-events: none;
  animation: float-up 900ms var(--ease-out) forwards;
}

@keyframes float-up {
  from { opacity: 0.9; transform: translate(-50%, 0) scale(0.86); }
  to { opacity: 0; transform: translate(-50%, -30px) scale(1.06); }
}

/* 粉碎机 */
.tool-count {
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 10px;
  white-space: nowrap;
}

.shredder-form {
  display: flex;
  gap: 8px;
  margin: 12px 0 8px;
}

.worry-input {
  flex: 1;
  min-width: 0;
  min-height: 40px;
  padding: 8px 11px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  font: inherit;
  font-size: 12px;
}

.worry-input:focus-visible {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.shredder-error {
  margin: 0 0 6px;
  color: var(--danger-fg);
  font-size: 11px;
}

.shred-stage {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 104px;
  padding: 10px;
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  overflow: hidden;
}

.shred-empty {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: var(--muted);
  font-size: 11px;
  text-align: center;
}

.shred-empty__mark {
  width: 26px;
  height: 26px;
  border: 1.4px dashed var(--border);
  border-radius: 50%;
}

.shred-card {
  position: relative;
  min-height: 32px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--accent-bg);
  color: var(--accent-fg);
  font-size: 12px;
  line-height: 32px;
  overflow: hidden;
}

.shred-piece {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  padding: 0 10px;
  white-space: nowrap;
  overflow: hidden;
  opacity: 0;
  transition: transform 900ms var(--ease-out), opacity 900ms var(--ease-out);
}

.shred-card.is-shredding .shred-piece {
  opacity: 0.92;
}

.shred-card.is-shredding .piece-1 { clip-path: inset(0 87.5% 0 0); transform: translate(var(--dx), var(--dy)) rotate(-9deg); }
.shred-card.is-shredding .piece-2 { clip-path: inset(0 75% 0 12.5%); transform: translate(var(--dx), var(--dy)) rotate(7deg); }
.shred-card.is-shredding .piece-3 { clip-path: inset(0 62.5% 0 25%); transform: translate(var(--dx), var(--dy)) rotate(-6deg); }
.shred-card.is-shredding .piece-4 { clip-path: inset(0 50% 0 37.5%); transform: translate(var(--dx), var(--dy)) rotate(10deg); }
.shred-card.is-shredding .piece-5 { clip-path: inset(0 37.5% 0 50%); transform: translate(var(--dx), var(--dy)) rotate(-11deg); }
.shred-card.is-shredding .piece-6 { clip-path: inset(0 25% 0 62.5%); transform: translate(var(--dx), var(--dy)) rotate(6deg); }
.shred-card.is-shredding .piece-7 { clip-path: inset(0 12.5% 0 75%); transform: translate(var(--dx), var(--dy)) rotate(-8deg); }
.shred-card.is-shredding .piece-8 { clip-path: inset(0 0 0 87.5%); transform: translate(var(--dx), var(--dy)) rotate(9deg); }

.shred-card.is-shredding {
  animation: shred-fade 1000ms var(--ease-out) forwards;
}

@keyframes shred-fade {
  0%, 45% { opacity: 1; }
  100% { opacity: 0; }
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 900px) {
  .tool-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .fish-svg {
    transition: none;
  }

  .float-word {
    animation: none;
    opacity: 0;
  }

  .shred-piece {
    transition: none;
    opacity: 0;
  }

  .shred-card.is-shredding {
    animation: none;
    opacity: 0;
  }
}
</style>
