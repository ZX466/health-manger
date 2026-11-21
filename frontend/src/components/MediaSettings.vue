<template>
  <section class="media-settings v21-panel" aria-labelledby="media-settings-title">
    <div class="panel-head">
      <span class="micro">COMPANION &amp; AUDIO</span>
      <span class="micro">声画偏好</span>
    </div>
    <h2 id="media-settings-title">搭子形象与声画</h2>

    <div class="companion-choice" role="radiogroup" aria-label="选择搭子形象">
      <label
        v-for="item in companions"
        :key="item.key"
        class="companion-option"
        :class="{ 'is-selected': companion === item.key }"
      >
        <input
          type="radio"
          name="companion-type"
          :value="item.key"
          :checked="companion === item.key"
          @change="chooseCompanion(item.key)"
        />
        <span class="companion-option-thumb">
          <img :src="item.thumb" :alt="`${item.label}示例`" width="48" height="48" loading="lazy" />
        </span>
        <span class="option-copy">
          <strong>{{ item.label }}</strong>
          <em>{{ item.tagline }}</em>
        </span>
      </label>
    </div>

    <label class="switch-row">
      <span>
        <strong>全局音效</strong>
        <small>控制趣味配音、木鱼与呼吸节拍；关怀模式自动静音</small>
      </span>
      <input
        type="checkbox"
        :checked="soundEnabled"
        :disabled="serious"
        @change="setSoundEnabled($event.target.checked)"
      />
      <i class="switch" aria-hidden="true"></i>
    </label>

    <label class="switch-row">
      <span>
        <strong>动图偏好（GIF）</strong>
        <small>开启后优先展示动态表情；系统减少动态时自动静帧</small>
      </span>
      <input
        type="checkbox"
        :checked="animated"
        @change="setAnimated($event.target.checked)"
      />
      <i class="switch" aria-hidden="true"></i>
    </label>

    <div class="sound-test">
      <div class="sound-test-head">
        <span class="field-label">试听配音</span>
        <span class="fineprint">{{ soundEnabled && !serious ? '点击试听，音量约 70%' : (serious ? '关怀模式已自动静音' : '全局音效已静音') }}</span>
      </div>
      <div class="sound-test-list">
        <button
          v-for="(clip, key) in AUDIO_CLIPS"
          :key="key"
          class="sound-chip"
          type="button"
          :disabled="!soundEnabled || serious"
          @click="playClip(key)"
        >
          <AppIcon name="volume" :size="12" />
          {{ clip.label }}
        </button>
      </div>
    </div>

    <p class="fineprint media-note">偏好保存在当前浏览器，并同步到总览、心理空间与对话搭子。</p>
  </section>
</template>

<script setup>
import AppIcon from './AppIcon.vue'
import { AUDIO_CLIPS, MEDIA_ASSETS } from '../constants/media'
import { usePreferences } from '../composables/usePreferences'
import { playClip, useSound } from '../composables/useHealthU'

defineProps({
  serious: { type: Boolean, default: false }
})

const companions = Object.values(MEDIA_ASSETS)
const { companion, animated, setCompanion, setAnimated } = usePreferences()
const { soundEnabled, setSoundEnabled } = useSound()

function chooseCompanion (key) {
  setCompanion(key)
}
</script>

<style scoped>
.media-settings {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.media-settings h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 20px;
  letter-spacing: -0.02em;
}

.companion-choice {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.companion-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--surface);
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out);
}

.companion-option:hover {
  border-color: var(--line-strong);
}

.companion-option.is-selected {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.companion-option input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.companion-option-thumb {
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface-2);
}

.companion-option-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.option-copy {
  min-width: 0;
}

.option-copy strong {
  display: block;
  font-size: 13px;
}

.option-copy em {
  display: block;
  margin-top: 2px;
  color: var(--muted);
  font-size: 10.5px;
  font-style: normal;
  line-height: 1.55;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-top: 1px solid var(--line);
  cursor: pointer;
}

.switch-row > span {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.switch-row strong {
  font-size: 12.5px;
}

.switch-row small {
  color: var(--muted);
  font-size: 10.5px;
  line-height: 1.55;
}

.switch-row input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.switch {
  position: relative;
  width: 36px;
  height: 20px;
  flex: 0 0 auto;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: var(--surface-2);
  transition: background var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out);
}

.switch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--surface);
  box-shadow: 0 1px 2px oklch(20% 0.02 250 / 0.18);
  transition: transform var(--duration-fast) var(--ease-out);
}

.switch-row input:checked + .switch {
  border-color: var(--accent);
  background: var(--accent);
}

.switch-row input:checked + .switch::after {
  transform: translateX(16px);
}

.switch-row input:disabled + .switch {
  opacity: 0.5;
}

.sound-test {
  padding-top: 10px;
  border-top: 1px solid var(--line);
}

.sound-test-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.field-label {
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.sound-test-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.sound-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 28px;
  padding: 0 9px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 10.5px;
  cursor: pointer;
}

.sound-chip:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.sound-chip:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.media-note {
  margin: 0;
  color: var(--muted);
  font-size: 10px;
}

.fineprint {
  color: var(--muted);
  font-size: 10px;
}

@media (max-width: 640px) {
  .companion-choice { grid-template-columns: 1fr; }
}
</style>
