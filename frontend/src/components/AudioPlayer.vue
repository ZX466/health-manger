<template>
  <div class="audio-player">
    <button
      v-for="clip in clips"
      :key="clip.key"
      class="clip-btn"
      :class="{ playing: playingKey === clip.key }"
      @click="play(clip)"
    >
      <span class="clip-icon">{{ clip.icon }}</span>
      <span class="clip-label">{{ clip.label }}</span>
    </button>
  </div>
</template>

<script>
import { audioClips } from '../assets/index.js'

const CLIP_META = [
  { key: 'bellyLaugh', icon: '😂', label: '捧腹大笑' },
  { key: 'crazyLaugh', icon: '🤣', label: '疯狂大笑' },
  { key: 'giggle', icon: '🤭', label: '咯咯笑' },
  { key: 'pixabayLaugh', icon: '😆', label: '卡通笑声' },
]

export default {
  name: 'AudioPlayer',
  data() {
    return {
      clips: CLIP_META,
      playingKey: '',
      audio: null,
    }
  },
  beforeUnmount() {
    this.stop()
  },
  methods: {
    play(clip) {
      this.stop()
      const src = audioClips[clip.key]
      if (!src) return
      this.audio = new Audio(src)
      this.playingKey = clip.key
      this.audio.play().catch(() => {})
      this.audio.addEventListener('ended', () => {
        this.playingKey = ''
      })
    },
    stop() {
      if (this.audio) {
        this.audio.pause()
        this.audio.currentTime = 0
        this.audio = null
      }
      this.playingKey = ''
    },
  },
}
</script>

<style scoped>
.audio-player {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}
.clip-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--surface, #fff);
  border: 2px solid var(--accent-soft, #FFBFA0);
  border-radius: var(--radius, 16px);
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.25s;
  font-size: 14px;
  color: var(--fg, #333);
}
.clip-btn:hover {
  background: var(--bg, #FFF5EE);
  border-color: var(--accent, #FF9B71);
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(255, 155, 113, 0.2);
}
.clip-btn.playing {
  background: var(--accent, #FF9B71);
  border-color: var(--accent-hover, #FF7B4A);
  color: white;
  animation: pulse-playing 0.8s ease-in-out infinite;
}
.clip-icon { font-size: 1.3rem; }
.clip-label { font-weight: 600; }
@keyframes pulse-playing {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
</style>
