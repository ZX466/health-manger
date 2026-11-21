<template>
  <div
    class="reaction-strip fun-only"
    :class="{ 'reaction-strip--surface': surface, 'is-warn': reaction?.tone === 'warn', 'is-success': reaction?.tone === 'success' }"
    aria-live="polite"
  >
    <div class="reaction-thumb">
      <img :src="reaction?.image" :alt="reaction?.tag || '搭子反馈'" width="52" height="52" loading="lazy" />
    </div>
    <div class="reaction-copy">
      <span class="micro">{{ reaction?.tag }}</span>
      <p>{{ reaction?.text }}</p>
    </div>
    <button
      v-if="reaction?.audio"
      class="mini-icon-btn"
      type="button"
      title="再听一次搭子反馈"
      aria-label="再听一次搭子反馈"
      @click="play"
    >
      <AppIcon name="volume" :size="14" />
    </button>
  </div>
</template>

<script setup>
import AppIcon from './AppIcon.vue'
import { playClip } from '../composables/useHealthU'

const props = defineProps({
  reaction: { type: Object, default: null },
  surface: { type: Boolean, default: false }
})

function play () {
  if (props.reaction?.audio) playClip(props.reaction.audio)
}
</script>

<style scoped>
.reaction-strip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--surface-2);
}

.reaction-strip--surface {
  background: var(--surface);
}

.reaction-strip.is-warn {
  border-color: color-mix(in oklch, var(--warn) 30%, var(--line));
  background: color-mix(in oklch, var(--warn-soft) 56%, var(--surface));
}

.reaction-strip.is-success {
  border-color: color-mix(in oklch, var(--success) 26%, var(--line));
  background: color-mix(in oklch, var(--success-soft) 46%, var(--surface));
}

.reaction-thumb {
  flex: 0 0 auto;
  width: 46px;
  height: 46px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface);
}

.reaction-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.reaction-copy {
  min-width: 0;
  flex: 1;
}

.reaction-copy p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 11.5px;
  line-height: 1.65;
}

.mini-icon-btn {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  flex: 0 0 auto;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  cursor: pointer;
}

.mini-icon-btn:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}
</style>
