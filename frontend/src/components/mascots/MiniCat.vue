<template>
  <div :class="['mini-cat', sizeClass, animationClass]">
    <div class="mini-cat-face">
      <div class="mini-cat-ear left"></div>
      <div class="mini-cat-ear right"></div>
      <div class="mini-cat-eyes">
        <div class="mini-cat-eye"></div>
        <div class="mini-cat-eye"></div>
      </div>
      <div class="mini-cat-blush left"></div>
      <div class="mini-cat-blush right"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MiniCat',
  props: {
    size: {
      type: String,
      default: 'normal',
      validator: v => ['normal', 'large'].includes(v)
    },
    animation: {
      type: String,
      default: 'float',
      validator: v => ['float', 'wobble', 'none'].includes(v)
    }
  },
  computed: {
    sizeClass() {
      return this.size === 'large' ? 'mini-cat--large' : ''
    },
    animationClass() {
      if (this.animation === 'wobble') return 'mini-cat--wobble'
      if (this.animation === 'none') return 'mini-cat--static'
      return 'mini-cat--float'
    }
  }
}
</script>

<style scoped>
.mini-cat-face {
  position: relative;
  width: 50px;
  height: 45px;
  background: var(--accent);
  border-radius: 50% 50% 45% 45%;
}

.mini-cat--float .mini-cat-face {
  animation: cat-float 3s ease-in-out infinite;
}
.mini-cat--wobble .mini-cat-face {
  animation: cat-wobble 0.8s ease-in-out infinite;
}

@keyframes cat-float {
  0%, 100% { transform: translateY(0) rotate(-2deg); }
  50% { transform: translateY(-8px) rotate(2deg); }
}
@keyframes cat-wobble {
  0%, 100% { transform: rotate(-5deg); }
  50% { transform: rotate(5deg); }
}

.mini-cat--large .mini-cat-face {
  transform: scale(1.5);
}

.mini-cat-ear {
  position: absolute;
  width: 18px;
  height: 20px;
  background: var(--accent);
  top: -8px;
  clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
  z-index: -1;
}
.mini-cat-ear::after {
  content: '';
  position: absolute;
  width: 10px;
  height: 11px;
  background: var(--cat-cream);
  top: 6px;
  left: 50%;
  transform: translateX(-50%);
  clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
}
.mini-cat-ear.left { left: 4px; transform: rotate(-15deg); }
.mini-cat-ear.right { right: 4px; transform: rotate(15deg); }

.mini-cat-eyes {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 12px;
}
.mini-cat-eye {
  width: 9px;
  height: 11px;
  background: #333;
  border-radius: 50%;
  position: relative;
  animation: blink-anim 4s ease-in-out infinite;
}
.mini-cat-eye::after {
  content: '';
  position: absolute;
  width: 3px;
  height: 3px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
}

.mini-cat-blush {
  position: absolute;
  width: 8px;
  height: 5px;
  background: var(--accent);
  border-radius: 50%;
  top: 28px;
  opacity: 0.7;
}
.mini-cat-blush.left { left: 5px; }
.mini-cat-blush.right { right: 5px; }

@keyframes blink-anim {
  0%, 42%, 46%, 100% { transform: scaleY(1); }
  44% { transform: scaleY(0.05); }
}
</style>
