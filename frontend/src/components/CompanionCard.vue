<template>
  <div class="companion" :class="[`companion--${state}`, { 'is-care': state === 'crisis' }]">
    <button
      class="mascot"
      :class="[`mascot--${state}`]"
      type="button"
      title="点击换一张搭子表情"
      aria-label="点击换一张搭子表情"
      @click="shuffle"
    >
      <img
        v-if="state !== 'crisis'"
        class="mascot-img"
        :src="src"
        :alt="`${companionMeta.label}宿舍搭子`"
        width="64"
        height="64"
      />
      <span v-else class="mascot-care-icon" aria-hidden="true">
        <AppIcon name="heart" :size="28" />
      </span>
      <span v-if="state !== 'crisis'" class="mascot-accessory" aria-hidden="true">
        <svg v-if="state === 'night_owl'" viewBox="0 0 64 64">
          <path d="M46 10c-5 1-8 5-8 10 6 1 11-2 12-8-2 0-3 0-4-2Z" />
        </svg>
        <svg v-else-if="state === 'low_mood'" viewBox="0 0 64 64">
          <path d="M40 46h14v7a5 5 0 0 1-5 5h-4a5 5 0 0 1-5-5z" />
          <path d="M54 49c4 0 4 6 0 6" />
          <path d="M44 41c-1-3 1-3 0-6M50 41c-1-3 1-3 0-6" />
        </svg>
        <svg v-else-if="state === 'energetic'" viewBox="0 0 64 64">
          <path d="M14 26h14v7a5 5 0 0 1-5 5h-4a5 5 0 0 1-5-5z" />
          <path d="M36 26h14v7a5 5 0 0 1-5 5h-4a5 5 0 0 1-5-5z" />
          <path d="M28 29h8" />
        </svg>
      </span>
      <span class="mascot-state-pill">{{ pillText }}</span>
    </button>

    <div class="companion-body">
      <div class="companion-head">
        <p class="micro">{{ tagText }}</p>
        <div v-if="state !== 'crisis'" class="companion-tools fun-only">
          <button class="mini-chip" type="button" title="切换搭子形象" @click="switchCompanion">
            换{{ nextLabel }}
          </button>
          <button class="mini-icon-btn" type="button" title="换一张表情" aria-label="换一张表情" @click="shuffle">
            <AppIcon name="shuffle" :size="14" />
          </button>
          <button class="mini-icon-btn" type="button" title="听一句搭子音效" aria-label="听一句搭子音效" @click="playCompanionSound">
            <AppIcon name="volume" :size="14" />
          </button>
        </div>
      </div>
      <p class="companion-text">{{ bubbleText }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'
import { COMPANION_STATE_COPY, CLINICAL_BUBBLE, MEDIA_ASSETS, companionImage } from '../constants/media'
import { usePreferences } from '../composables/usePreferences'
import { playClip } from '../composables/useHealthU'

const props = defineProps({
  state: { type: String, default: 'default' },
  bubble: { type: String, default: '' },
  tag: { type: String, default: '' },
  persona: { type: String, default: 'humorous' }
})
const emit = defineEmits(['switch', 'shuffle'])

const { companion, companionMeta, setCompanion } = usePreferences()
const index = ref(0)

const src = computed(() => companionImage(companion.value, index.value))
const nextLabel = computed(() => (companion.value === 'hajimi' ? MEDIA_ASSETS.nailong.label : MEDIA_ASSETS.hajimi.label))
const pillText = computed(() => {
  if (props.persona === 'clinical' && props.state !== 'crisis') return '校医简评'
  return COMPANION_STATE_COPY[props.state]?.pill || COMPANION_STATE_COPY.default.pill
})
const tagText = computed(() => {
  if (props.tag) return props.tag
  if (props.state === 'crisis') return '关怀模式'
  if (props.persona === 'clinical') return '校医简评'
  return `宿舍搭子 · ${companionMeta.value.label}`
})
const bubbleText = computed(() => {
  if (props.bubble) return props.bubble
  if (props.state === 'crisis') return COMPANION_STATE_COPY.crisis.bubble
  if (props.persona === 'clinical') return CLINICAL_BUBBLE
  return COMPANION_STATE_COPY[props.state]?.bubble || COMPANION_STATE_COPY.default.bubble
})

watch(companion, () => { index.value = 0 })

function shuffle () {
  index.value += 1
  emit('shuffle')
}

function switchCompanion () {
  const next = companion.value === 'hajimi' ? 'nailong' : 'hajimi'
  setCompanion(next)
  index.value = 0
  emit('switch', next)
}

function playCompanionSound () {
  const key = props.state === 'energetic' ? 'belly' : 'giggle'
  playClip(key)
}
</script>

<style scoped>
.companion {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid var(--line);
}

.mascot {
  position: relative;
  flex: 0 0 auto;
  width: 64px;
  height: 64px;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: var(--surface-2);
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out);
}

.mascot:hover {
  transform: translateY(-2px) rotate(-1.5deg);
  border-color: var(--line-strong);
}

.mascot:active {
  transform: scale(0.96);
}

.mascot-img {
  width: 100%;
  height: 100%;
  border-radius: 15px;
  object-fit: cover;
}

.mascot-care-icon {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  border-radius: 15px;
  background: var(--danger-soft);
  color: var(--danger);
}

.mascot-accessory {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 22px;
  height: 22px;
  padding: 2px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
}

.mascot-accessory svg {
  width: 100%;
  height: 100%;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.mascot--night_owl .mascot-accessory { color: var(--accent-strong); }
.mascot--low_mood .mascot-accessory { color: var(--warn); }
.mascot--energetic .mascot-accessory { color: var(--ink); }

.mascot-state-pill {
  position: absolute;
  left: 50%;
  bottom: -7px;
  transform: translateX(-50%);
  padding: 1px 7px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 8px;
  line-height: 1.6;
  white-space: nowrap;
}

.mascot--night_owl .mascot-state-pill { color: var(--accent-strong); border-color: color-mix(in oklch, var(--accent) 24%, var(--line)); }
.mascot--low_mood .mascot-state-pill { color: var(--warn); border-color: color-mix(in oklch, var(--warn) 24%, var(--line)); }
.mascot--care .mascot-state-pill { color: var(--danger); border-color: color-mix(in oklch, var(--danger) 24%, var(--line)); }

.companion-body {
  min-width: 0;
  flex: 1;
}

.companion-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.companion-tools {
  display: flex;
  align-items: center;
  gap: 4px;
}

.companion-text {
  margin: 5px 0 0;
  color: var(--fg);
  font-size: 12px;
  line-height: 1.7;
}

.companion.is-care .companion-text {
  color: var(--muted);
}

.mini-chip {
  min-height: 24px;
  padding: 0 8px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 9px;
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}

.mini-chip:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.mini-icon-btn {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}

.mini-icon-btn:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

@media (max-width: 480px) {
  .companion-tools .mini-chip {
    display: none;
  }
}
</style>
