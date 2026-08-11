<template>
  <div :class="['mini-nailong-wrap', sizeClass, animationClass]">
    <div class="mini-nailong">
      <div class="mini-nl-body"></div>
      <div class="mini-nl-belly"></div>
      <div class="mini-nl-eyes">
        <div class="mini-nl-eye"></div>
        <div class="mini-nl-eye"></div>
      </div>
      <div class="mini-nl-blush left"></div>
      <div class="mini-nl-blush right"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MiniNailong',
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
      return this.size === 'large' ? 'mini-nailong-wrap--large' : ''
    },
    animationClass() {
      if (this.animation === 'wobble') return 'mini-nailong-wrap--wobble'
      if (this.animation === 'none') return 'mini-nailong-wrap--static'
      return 'mini-nailong-wrap--float'
    }
  }
}
</script>

<style scoped>
.mini-nailong {
  position: relative;
  width: 50px;
  height: 50px;
}

.mini-nailong-wrap--float .mini-nailong {
  animation: nl-float 2.5s ease-in-out infinite;
}
.mini-nailong-wrap--wobble .mini-nailong {
  animation: nl-wiggle 2.5s ease-in-out infinite;
}

@keyframes nl-float {
  0%, 100% { transform: translateY(0) rotate(-2deg); }
  50% { transform: translateY(-8px) rotate(2deg); }
}
@keyframes nl-wiggle {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-5deg); }
  75% { transform: rotate(5deg); }
}

.mini-nailong-wrap--large .mini-nailong {
  transform: scale(1.5);
}

.mini-nl-body {
  position: absolute;
  width: 46px;
  height: 42px;
  background: linear-gradient(145deg, #FFE066, #FFD93D, #F5C800);
  border-radius: 50% 50% 45% 45%;
  box-shadow: inset -5px -5px 10px rgba(0, 0, 0, 0.08),
              inset 3px 3px 8px rgba(255, 255, 255, 0.3);
}
.mini-nl-belly {
  position: absolute;
  width: 28px;
  height: 22px;
  background: linear-gradient(145deg, #FFF8E1, #FFF0D0);
  border-radius: 50%;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%);
}
.mini-nl-eyes {
  position: absolute;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 10px;
  z-index: 1;
}
.mini-nl-eye {
  width: 9px;
  height: 11px;
  background: #333;
  border-radius: 50%;
  position: relative;
  animation: blink-anim 5s ease-in-out infinite;
}
.mini-nl-eye::after {
  content: '';
  position: absolute;
  width: 3px;
  height: 3px;
  background: white;
  border-radius: 50%;
  top: 2px;
  left: 2px;
}
.mini-nl-blush {
  position: absolute;
  width: 8px;
  height: 5px;
  background: #FFB5C2;
  border-radius: 50%;
  top: 26px;
  opacity: 0.6;
  z-index: 1;
}
.mini-nl-blush.left { left: 6px; }
.mini-nl-blush.right { right: 6px; }

@keyframes blink-anim {
  0%, 42%, 46%, 100% { transform: scaleY(1); }
  44% { transform: scaleY(0.05); }
}
</style>
