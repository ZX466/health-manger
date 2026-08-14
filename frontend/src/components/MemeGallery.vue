<template>
  <div class="meme-gallery">
    <div v-if="title" class="gallery-title">{{ title }}</div>
    <div class="gallery-grid" :class="[`cols-${cols}`]">
      <div
        v-for="(src, i) in displayList"
        :key="i"
        class="meme-item"
        @click="$emit('select', src)"
      >
        <img :src="src" :alt="`表情包 ${i + 1}`" loading="lazy" />
      </div>
    </div>
    <button v-if="canShuffle" class="shuffle-btn" @click="shuffle">
      🎲 换一批
    </button>
  </div>
</template>

<script>
import { nailongMemes, nailongGifs } from '../assets/index.js'

export default {
  name: 'MemeGallery',
  props: {
    source: { type: String, default: 'memes', validator: v => ['memes', 'gifs'].includes(v) },
    title: { type: String, default: '' },
    count: { type: Number, default: 6 },
    cols: { type: Number, default: 3 },
    canShuffle: { type: Boolean, default: true },
  },
  emits: ['select'],
  data() {
    return { displayList: [] }
  },
  created() {
    this.shuffle()
  },
  methods: {
    shuffle() {
      const pool = this.source === 'gifs' ? [...nailongGifs] : [...nailongMemes]
      for (let i = pool.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [pool[i], pool[j]] = [pool[j], pool[i]]
      }
      this.displayList = pool.slice(0, this.count)
    },
  },
}
</script>

<style scoped>
.meme-gallery { text-align: center; }
.gallery-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--accent-strong);
  margin-bottom: 16px;
}
.gallery-grid {
  display: grid;
  gap: 12px;
}
.cols-2 { grid-template-columns: repeat(2, 1fr); }
.cols-3 { grid-template-columns: repeat(3, 1fr); }
.cols-4 { grid-template-columns: repeat(4, 1fr); }
.meme-item {
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.25s, box-shadow 0.25s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}
.meme-item:hover {
  transform: translateY(-4px) scale(1.03);
  box-shadow: 0 8px 24px rgba(255, 155, 113, 0.2);
}
.meme-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.shuffle-btn {
  margin-top: 16px;
  background: var(--accent, #FF9B71);
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: var(--radius, 16px);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}
.shuffle-btn:hover {
  background: var(--accent-strong);
  transform: translateY(-2px);
}
</style>
