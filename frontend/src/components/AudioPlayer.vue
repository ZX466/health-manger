<template>
  <div class="audio-player">
    <button
      v-for="clip in clips"
      :key="clip.key"
      class="clip-btn"
      :class="{ playing: playingKey === clip.key }"
      @click="play(clip)"
    >
      <span class="clip-label">{{ clip.label }}</span>
    </button>
  </div>
</template>

<script>
import { audioClips } from '../assets/index.js'

const CLIP_META = [
  { key: 'bellyLaugh', label: '捧腹大笑' },
  { key: 'crazyLaugh', label: '疯狂大笑' },
  { key: 'giggle', label: '咯咯笑' },
  { key: 'pixabayLaugh', label: '卡通笑声' },
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
  background: var(--surface);
  border: 2px solid var(--accent-soft);
  border-radius: var(--radius-md);
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.25s;
  font-size: 14px;
  color: var(--fg);
}
.clip-btn:hover {
  background: var(--bg);
  border-color: var(--accent);
  transform: translateY(-2px);
  
}
.clip-btn.playing {
  background: var(--accent);
  border-color: var(--accent-strong);
  color: white;
}
.clip-icon { font-size: 1.3rem; }
.clip-label { font-weight: 600; }
@keyframes pulse-playing {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
</style>
