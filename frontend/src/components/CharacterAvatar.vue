<template>
  <div
    class="character-avatar"
    :class="[`type-${type}`, `state-${effectiveState}`, { animated, 'has-bubble': !!bubbleText }]"
    @click="shuffle"
  >
      <div class="character-avatar__face">
        <img v-if="src" :src="src" :alt="`${type} 角色`" class="avatar-img" loading="lazy" />
        <div v-else class="avatar-placeholder">
          {{ type === 'hajimi' ? '猫' : '龙' }}
        </div>

        <span v-if="effectiveState === 'night_owl'" class="accessory accessory--night" aria-hidden="true">
          <svg viewBox="0 0 100 100">
            <path d="M28 58c3 5 8 7 12 5" />
            <path d="M60 63c4 2 9 0 12-5" />
          </svg>
        </span>

        <span v-else-if="effectiveState === 'energetic'" class="accessory accessory--shades" aria-hidden="true">
          <svg viewBox="0 0 100 100">
            <path d="M26 44h20v10a8 8 0 0 1-8 8h-4a8 8 0 0 1-8-8z" />
            <path d="M54 44h20v10a8 8 0 0 1-8 8h-4a8 8 0 0 1-8-8z" />
            <path d="M46 48h8" />
          </svg>
        </span>

        <span v-else-if="effectiveState === 'low_mood'" class="accessory accessory--tea" aria-hidden="true">
          <svg viewBox="0 0 100 100">
            <path d="M66 78h22v10a8 8 0 0 1-8 8H74a8 8 0 0 1-8-8z" />
            <path d="M88 82c6 0 6 9 0 9" />
            <path d="M72 72c-2-4 2-5 0-9" />
            <path d="M80 72c-2-4 2-5 0-9" />
          </svg>
        </span>

        <span v-else-if="effectiveState === 'crisis'" class="accessory accessory--care" aria-hidden="true">
          <svg viewBox="0 0 100 100">
            <path d="M50 82c-12-7-19-14-19-22a10 10 0 0 1 19-4 10 10 0 0 1 19 4c0 8-7 15-19 22z" />
          </svg>
        </span>
      </div>

      <span v-if="stateTag" class="state-tag">{{ stateTag }}</span>

      <p v-if="bubbleText" class="avatar-bubble" role="status">
        <span class="avatar-bubble__name">{{ bubbleName }}</span>
        <span>{{ bubbleText }}</span>
      </p>
  </div>
</template>

<script>
import { hajimiImages, nailongGifs, randomHajimi, randomNailongGif } from '../assets/index.js'
import { useWellnessStore } from '../stores/wellness'
import { pickRandom, TIP_POOLS } from '../constants/copywriting'

const STATE_COPY = {
  crisis: {
    name: '搭子在',
    tag: '先照顾你',
    text: '今天先不玩梗。你不需要一个人扛，愿意的话，去心理空间看看支持资源。'
  },
  night_owl: {
    name: '修仙中',
    tag: '修仙中',
    text: '再熬下去，发际线就要和期末成绩一起起飞了。'
  },
  low_mood: {
    name: '搭子在',
    tag: '低电量',
    text: '允许自己今天当条咸鱼，深呼吸 3 次，天塌不下来。'
  },
  energetic: {
    name: '卷王本人',
    tag: '自律上线',
    text: '自律这块被你拿捏了，今天就是朋友圈卷王本人。'
  },
  default: {
    name: '宿舍搭子',
    tag: '',
    text: pickRandom(TIP_POOLS.daily)
  }
}

export default {
  name: 'CharacterAvatar',
  props: {
    type: { type: String, default: 'hajimi', validator: v => ['hajimi', 'nailong'].includes(v) },
    animated: { type: Boolean, default: true },
    fixed: { type: Boolean, default: false },
    index: { type: Number, default: -1 },
    /** 手动指定状态；不传时可由 wellness store 驱动 */
    state: { type: String, default: '' },
    /** 是否读取 Pinia 中的真实健康状态 */
    reactive: { type: Boolean, default: false },
    /** 是否展示气泡台词（小头像场景默认关闭） */
    bubble: { type: Boolean, default: false }
  },
  data() {
    return { src: '' }
  },
  computed: {
    store() {
      return useWellnessStore()
    },
    effectiveState() {
      if (this.state) return this.state
      if (!this.reactive) return 'default'
      return this.store.avatarState
    },
    stateTag() {
      if (this.effectiveState === 'night_owl') return '修仙中'
      if (this.effectiveState === 'low_mood') return '低电量'
      if (this.effectiveState === 'energetic') return '自律上线'
      if (this.effectiveState === 'crisis') return '先照顾你'
      return ''
    },
    bubbleName() {
      const copy = STATE_COPY[this.effectiveState] || STATE_COPY.default
      return copy.name
    },
    bubbleText() {
      if (!this.bubble) return ''
      if (this.state) return STATE_COPY[this.state]?.text || STATE_COPY.default.text
      return this.reactive ? this.store.avatarBubble : STATE_COPY.default.text
    }
  },
  created() {
    this.pickImage()
  },
  methods: {
    pickImage() {
      if (this.index >= 0) {
        const pool = this.type === 'hajimi' ? hajimiImages : nailongGifs
        this.src = pool[this.index % pool.length]
      } else {
        this.src = this.type === 'hajimi' ? randomHajimi() : randomNailongGif()
      }
    },
    shuffle() {
      if (!this.fixed) this.pickImage()
    }
  }
}
</script>

<style scoped>
.character-avatar {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  cursor: pointer;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 6px 20px color-mix(in oklch, var(--fg) 12%, transparent);
}

.character-avatar:hover { transform: scale(1.06); }
.animated.type-hajimi { animation: cat-bounce 2s ease-in-out infinite; }
.animated.type-nailong { animation: nailong-float 3s ease-in-out infinite; }

.character-avatar__face {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  overflow: hidden;
  background: var(--bg);
}

.avatar-img { width: 100%; height: 100%; object-fit: cover; }

.avatar-placeholder {
  font-size: 1.4rem;
  background: var(--bg);
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  color: var(--muted);
}

.accessory {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.accessory svg {
  width: 100%;
  height: 100%;
  fill: none;
  stroke: var(--fg);
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: 0.78;
}

.accessory--night svg { stroke: var(--accent-strong); }
.accessory--shades svg { fill: var(--fg); stroke: var(--fg); opacity: 0.62; }
.accessory--tea svg { stroke: var(--warn); opacity: 0.9; }
.accessory--care svg { stroke: var(--danger); fill: var(--danger-soft); opacity: 0.92; }

.state-tag {
  position: absolute;
  left: 50%;
  bottom: -6px;
  transform: translateX(-50%);
  padding: 1px 7px;
  border: var(--border-hairline);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 10px;
  line-height: 1.5;
  white-space: nowrap;
}

.state-crisis { box-shadow: 0 0 0 2px var(--danger-bg); }
.state-energetic { box-shadow: 0 0 0 2px var(--accent-bg); }

.avatar-bubble {
  position: absolute;
  top: calc(100% + 8px);
  left: 50%;
  z-index: 4;
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 210px;
  margin: 0;
  padding: 10px 12px;
  transform: translateX(-50%);
  border: var(--border-hairline);
  border-radius: var(--radius-md);
  background: var(--surface);
  box-shadow: var(--shadow-pop);
  color: var(--fg);
  font-size: 12px;
  line-height: 1.65;
  text-align: left;
}

.avatar-bubble__name {
  color: var(--muted);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.state-crisis + .avatar-bubble,
.has-bubble .state-crisis ~ .avatar-bubble {
  border-color: color-mix(in oklch, var(--danger) 24%, var(--border));
}

@keyframes cat-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
@keyframes nailong-float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  25% { transform: translateY(-4px) rotate(2deg); }
  75% { transform: translateY(4px) rotate(-2deg); }
}

@media (prefers-reduced-motion: reduce) {
  .character-avatar,
  .animated.type-hajimi,
  .animated.type-nailong {
    animation: none;
    transition: none;
  }
}
</style>
