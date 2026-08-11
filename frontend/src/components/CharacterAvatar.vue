<template>
  <div class="character-avatar" :class="[`type-${type}`, { animated }]" @click="shuffle">
    <img v-if="src" :src="src" :alt="`${type} 角色`" class="avatar-img" loading="lazy" />
    <div v-else class="avatar-placeholder">
      {{ type === 'hajimi' ? '🐱' : '🐉' }}
    </div>
  </div>
</template>

<script>
import { hajimiImages, nailongGifs, randomHajimi, randomNailongGif } from '../assets/index.js'

export default {
  name: 'CharacterAvatar',
  props: {
    type: { type: String, default: 'hajimi', validator: v => ['hajimi', 'nailong'].includes(v) },
    animated: { type: Boolean, default: true },
    fixed: { type: Boolean, default: false },
    index: { type: Number, default: -1 },
  },
  data() {
    return { src: '' }
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
    },
  },
}
</script>

<style scoped>
.character-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}
.character-avatar:hover { transform: scale(1.08); }
.animated.type-hajimi { animation: cat-bounce 2s ease-in-out infinite; }
.animated.type-nailong { animation: nailong-float 3s ease-in-out infinite; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder {
  font-size: 2rem;
  background: var(--bg, #FFF5EE);
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
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
</style>
