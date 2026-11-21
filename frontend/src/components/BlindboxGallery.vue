<template>
  <section class="blindbox-panel v21-panel fun-only" aria-labelledby="blindbox-title">
    <div class="blindbox-head">
      <div>
        <p class="micro">PRESSURE / BLINDBOX</p>
        <h2 id="blindbox-title">今日解压盲盒</h2>
      </div>
      <div class="blindbox-controls">
        <span class="blindbox-audio-state" aria-live="polite">{{ audioState }}</span>
        <button
          v-if="playingClipId"
          class="mini-chip"
          type="button"
          @click="stopAudio"
        >
          停止播放
        </button>
        <button
          v-if="canShuffle"
          class="mini-chip"
          type="button"
          @click="shuffle"
        >
          换一批
        </button>
      </div>
    </div>

    <div class="blindbox-filters" role="group" aria-label="筛选解压卡片">
      <button
        v-for="filter in filters"
        :key="filter.key"
        class="seg-btn"
        :class="{ 'is-active': activeFilter === filter.key }"
        type="button"
        :aria-pressed="activeFilter === filter.key"
        @click="setFilter(filter.key)"
      >
        {{ filter.label }}
        <span v-if="filter.key === 'favorites'" class="fav-count">{{ favoriteIds.length }}</span>
      </button>
    </div>

    <div v-if="visibleItems.length" class="blindbox-grid">
      <article
        v-for="item in visibleItems"
        :key="item.id"
        class="blindbox-card"
        :class="{ 'is-playing': playingClipId === item.id }"
      >
        <div class="blindbox-media">
          <button
            class="blindbox-play-area"
            type="button"
            :aria-pressed="playingClipId === item.id"
            :aria-label="`试听「${captionFor(item)}」`"
            @click="togglePlay(item)"
          >
            <img
              :src="sourceFor(item)"
              :alt="item.alt"
              width="240"
              height="240"
              loading="lazy"
            />
            <span class="blindbox-badge">{{ characterLabel(item.character) }}</span>
            <span class="blindbox-play-pill">
              <span v-if="playingClipId === item.id" class="eq-bars" aria-hidden="true"><i></i><i></i><i></i></span>
              <AppIcon v-else name="play" :size="12" />
              {{ playingClipId === item.id ? '播放中' : '试听' }}
            </span>
          </button>
        </div>
        <div class="blindbox-meta">
          <div class="blindbox-title-row">
            <h3 class="blindbox-title">{{ captionFor(item) }}</h3>
            <span v-if="isCustom(item)" class="blindbox-custom-tag">自定义</span>
          </div>
          <p class="blindbox-sub">{{ AUDIO_CLIPS[item.audioKey]?.label || '趣味配音' }}</p>
        </div>
        <div class="blindbox-card-actions">
          <button
            class="blindbox-act-btn"
            :class="{ 'is-fav': isFavorite(item.id) }"
            type="button"
            :aria-pressed="isFavorite(item.id)"
            :title="isFavorite(item.id) ? '取消收藏' : '收藏卡片'"
            :aria-label="isFavorite(item.id) ? `取消收藏「${captionFor(item)}」` : `收藏「${captionFor(item)}」`"
            @click="onToggleFavorite(item)"
          >
            <AppIcon name="bookmark" :size="14" />
          </button>
          <button
            class="blindbox-act-btn"
            :class="{ 'is-edited': isCustom(item) }"
            type="button"
            title="编辑卡片配文"
            aria-label="编辑卡片配文"
            @click="openCaption(item)"
          >
            <AppIcon name="edit" :size="14" />
          </button>
        </div>
      </article>
    </div>

    <div v-else class="blindbox-empty">
      <AppIcon name="bookmark" :size="22" />
      <strong class="blindbox-empty-title">收藏夹还是空的</strong>
      <p class="panel-copy">看到顺眼的卡片点一下书签，下次崩溃前能更快找到它。</p>
      <button class="mini-chip" type="button" @click="setFilter('all')">去逛逛全部</button>
    </div>

    <Teleport to="body">
      <div v-if="editing" class="caption-backdrop" @click.self="closeCaption">
        <section class="caption-dialog" role="dialog" aria-modal="true" aria-labelledby="caption-dialog-title">
          <div class="caption-head">
            <div>
              <p class="micro">CUSTOM CAPTION</p>
              <h2 id="caption-dialog-title">自定义卡片配文</h2>
            </div>
            <button class="mini-icon-btn" type="button" aria-label="关闭" @click="closeCaption">
              <AppIcon name="close" :size="15" />
            </button>
          </div>
          <div class="caption-preview">
            <div class="caption-thumb">
              <img :src="sourceFor(editing)" :alt="editing.alt" width="72" height="72" />
            </div>
            <div>
              <strong>{{ captionFor(editing) }}</strong>
              <p>{{ characterLabel(editing.character) }} · {{ AUDIO_CLIPS[editing.audioKey]?.label }}</p>
              <small>默认配文：{{ editing.title }}</small>
            </div>
          </div>
          <label class="caption-field">
            <span>配文（最多 24 字）</span>
            <input
              ref="captionInput"
              v-model="captionDraft"
              type="text"
              maxlength="24"
              placeholder="写一句只有你懂的梗"
              @keydown.enter.prevent="saveCaption"
            />
          </label>
          <div class="caption-foot">
            <span>{{ captionDraft.trim().length }} / 24</span>
            <div class="caption-actions">
              <button class="btn btn-ghost btn-sm" type="button" :disabled="!isCustom(editing)" @click="resetCaption">
                恢复默认
              </button>
              <button class="btn btn-primary btn-sm" type="button" :disabled="!captionDraft.trim()" @click="saveCaption">
                保存配文
              </button>
            </div>
          </div>
        </section>
      </div>
    </Teleport>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'
import {
  AUDIO_CLIPS,
  BLINDBOX_CATALOG,
  BLINDBOX_FILTERS,
  MEDIA_ASSETS,
  mediaSrc
} from '../constants/media'
import { usePreferences } from '../composables/usePreferences'
import { playClip, playingClipId, stopAllAudio, useSound } from '../composables/useHealthU'

const emit = defineEmits(['toast'])
const {
  animated,
  favoriteIds,
  isFavorite,
  toggleFavorite,
  captionFor,
  setCaption,
  resetCaption: resetCaptionPref
} = usePreferences()
const { soundEnabled, suppressed } = useSound()

const filters = BLINDBOX_FILTERS
const activeFilter = ref('all')
const offset = ref(0)
const editing = ref(null)
const captionDraft = ref('')
const captionInput = ref(null)
let previousFocus = null

const audioState = computed(() => {
  if (suppressed.value) return '关怀模式已自动静音'
  if (!soundEnabled.value) return '全局音效已静音'
  if (playingClipId.value) {
    const item = BLINDBOX_CATALOG.find(entry => entry.id === playingClipId.value)
    return item ? `正在播放 · ${captionFor(item)}` : '正在播放'
  }
  return '点击卡片试听真实配音'
})

const filtered = computed(() => {
  if (activeFilter.value === 'favorites') {
    return BLINDBOX_CATALOG.filter(item => isFavorite(item.id))
  }
  if (activeFilter.value === 'all') return BLINDBOX_CATALOG
  return BLINDBOX_CATALOG.filter(item => item.character === activeFilter.value)
})

const visibleItems = computed(() => {
  const pool = filtered.value
  if (activeFilter.value === 'favorites') return pool
  const count = Math.min(3, pool.length)
  return Array.from({ length: count }, (_, i) => pool[(offset.value + i) % pool.length])
})

const canShuffle = computed(() => activeFilter.value !== 'favorites' && filtered.value.length > 3)

function characterLabel (key) {
  return MEDIA_ASSETS[key]?.label || '搭子'
}

function sourceFor (item) {
  return mediaSrc(item, animated.value)
}

function isCustom (item) {
  return Boolean(item && captionFor(item) !== item.title)
}

function setFilter (key) {
  activeFilter.value = key
  offset.value = 0
}

function shuffle () {
  offset.value += 3
}

function stopAudio () {
  stopAllAudio()
}

function togglePlay (item) {
  if (suppressed.value) {
    emit('toast', '关怀模式已自动静音')
    return
  }
  if (!soundEnabled.value) {
    emit('toast', '当前已静音，点击顶栏喇叭可开启音效')
    return
  }
  playClip(item.audioKey, {
    clipId: item.id,
    label: `${captionFor(item)}（${AUDIO_CLIPS[item.audioKey]?.label}）`
  })
}

function onToggleFavorite (item) {
  const nowFavorite = toggleFavorite(item.id)
  if (activeFilter.value === 'favorites') {
    nextTick(() => {
      if (!favoriteIds.value.length) document.querySelector('.blindbox-empty .mini-chip')?.focus()
    })
  }
  emit('toast', nowFavorite ? `已收藏「${captionFor(item)}」` : `已取消收藏「${captionFor(item)}」`)
}

async function openCaption (item) {
  previousFocus = document.activeElement
  editing.value = item
  captionDraft.value = captionFor(item)
  await nextTick()
  captionInput.value?.focus()
  captionInput.value?.select()
}

function closeCaption () {
  editing.value = null
  previousFocus?.focus?.()
}

function saveCaption () {
  if (!editing.value) return
  const item = editing.value
  setCaption(item.id, captionDraft.value, item.title)
  emit('toast', captionDraft.value.trim() === item.title ? '已恢复默认配文' : '已保存自定义配文')
  closeCaption()
}

function resetCaption () {
  if (!editing.value) return
  const item = editing.value
  resetCaptionPref(item.id)
  emit('toast', '已恢复默认配文')
  closeCaption()
}

watch(() => favoriteIds.value.length, () => {
  if (activeFilter.value === 'favorites') offset.value = 0
})

onBeforeUnmount(() => {
  stopAllAudio()
})
</script>

<style scoped>
.blindbox-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 22px 22px;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: var(--surface);
}

.blindbox-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.blindbox-head h2 {
  margin: 2px 0 0;
  font-family: var(--font-display);
  font-size: 20px;
  letter-spacing: -0.02em;
}

.blindbox-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.blindbox-audio-state {
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.02em;
}

.blindbox-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.seg-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}

.seg-btn:hover {
  border-color: var(--line-strong);
  color: var(--fg);
}

.seg-btn.is-active {
  border-color: var(--ink);
  background: var(--ink);
  color: var(--surface);
}

.fav-count {
  display: inline-grid;
  place-items: center;
  min-width: 15px;
  height: 15px;
  padding: 0 4px;
  border-radius: 999px;
  background: color-mix(in oklch, currentColor 12%, transparent);
  font-family: var(--font-mono);
  font-size: 8px;
}

.blindbox-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.blindbox-card {
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--surface);
  transition: transform var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out);
}

.blindbox-card:hover {
  transform: translateY(-2px);
  border-color: var(--line-strong);
}

.blindbox-card.is-playing {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px color-mix(in oklch, var(--accent) 36%, transparent);
}

.blindbox-media {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
  background: var(--surface-2);
}

.blindbox-play-area {
  position: relative;
  display: block;
  width: 100%;
  height: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.blindbox-play-area img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.45s var(--ease-out);
}

.blindbox-card:hover .blindbox-play-area img {
  transform: scale(1.035);
}

.blindbox-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  padding: 2px 6px;
  border-radius: 999px;
  background: color-mix(in oklch, var(--surface) 88%, transparent);
  color: var(--fg);
  font-family: var(--font-mono);
  font-size: 8px;
  letter-spacing: 0.04em;
  backdrop-filter: blur(6px);
}

.blindbox-play-pill {
  position: absolute;
  right: 8px;
  bottom: 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border: 1px solid color-mix(in oklch, var(--surface) 35%, transparent);
  border-radius: 999px;
  background: color-mix(in oklch, var(--ink) 78%, transparent);
  color: var(--surface);
  font-family: var(--font-mono);
  font-size: 8px;
  letter-spacing: 0.03em;
  backdrop-filter: blur(6px);
}

.blindbox-card.is-playing .blindbox-play-pill {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--surface);
}

.eq-bars {
  display: inline-flex;
  align-items: flex-end;
  gap: 1.5px;
  height: 9px;
}

.eq-bars i {
  display: block;
  width: 2px;
  height: 6px;
  border-radius: 1px;
  background: currentColor;
  animation: eq-bounce 0.7s ease-in-out infinite;
}

.eq-bars i:nth-child(2) { height: 9px; animation-delay: 0.12s; }
.eq-bars i:nth-child(3) { height: 4px; animation-delay: 0.24s; }

@keyframes eq-bounce {
  0%, 100% { transform: scaleY(0.55); }
  50% { transform: scaleY(1); }
}

.blindbox-meta {
  padding: 9px 10px 4px;
}

.blindbox-title-row {
  display: flex;
  align-items: center;
  gap: 5px;
}

.blindbox-title {
  margin: 0;
  color: var(--fg);
  font-size: 12.5px;
  font-weight: 650;
  line-height: 1.45;
}

.blindbox-custom-tag {
  flex: 0 0 auto;
  padding: 1px 5px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-size: 8px;
  font-weight: 600;
}

.blindbox-sub {
  margin: 2px 0 0;
  color: var(--muted);
  font-size: 10px;
}

.blindbox-card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  padding: 4px 8px 8px;
}

.blindbox-act-btn {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  color: var(--muted);
  cursor: pointer;
  transition: color var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out);
}

.blindbox-act-btn:hover {
  border-color: var(--line-strong);
  color: var(--fg);
}

.blindbox-act-btn.is-fav {
  border-color: color-mix(in oklch, var(--warn) 30%, var(--line));
  background: var(--warn-soft);
  color: var(--warn);
}

.blindbox-act-btn.is-fav :deep(svg) {
  fill: currentColor;
}

.blindbox-act-btn.is-edited {
  border-color: color-mix(in oklch, var(--accent) 28%, var(--line));
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.blindbox-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 30px 12px;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-md);
  color: var(--muted);
  text-align: center;
}

.blindbox-empty-title {
  color: var(--fg);
  font-size: 13px;
}

.blindbox-empty p {
  max-width: 34ch;
  margin: 0;
  font-size: 11.5px;
  line-height: 1.65;
}

.caption-backdrop {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: grid;
  place-items: center;
  padding: 18px;
  background: oklch(15% 0.02 250 / 0.48);
  backdrop-filter: blur(4px);
}

.caption-dialog {
  width: min(440px, 100%);
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-pop);
}

.caption-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.caption-head h2 {
  margin: 3px 0 0;
  font-family: var(--font-display);
  font-size: 20px;
}

.caption-preview {
  display: flex;
  gap: 12px;
  align-items: center;
  margin: 16px 0;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--surface-2);
}

.caption-thumb {
  width: 64px;
  height: 64px;
  flex: 0 0 auto;
  overflow: hidden;
  border-radius: 10px;
  background: var(--surface);
}

.caption-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.caption-preview strong {
  display: block;
  font-size: 13px;
}

.caption-preview p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 11px;
}

.caption-preview small {
  display: block;
  margin-top: 3px;
  color: var(--muted-2);
  font-size: 10px;
}

.caption-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.caption-field span {
  color: var(--muted);
  font-size: 11px;
}

.caption-field input {
  width: 100%;
  min-height: 42px;
  padding: 0 12px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  font-size: 13px;
}

.caption-field input:focus {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
}

.caption-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 10px;
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 9px;
}

.caption-actions {
  display: flex;
  gap: 6px;
}

.mini-chip {
  min-height: 26px;
  padding: 0 9px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 9.5px;
  font-weight: 650;
  cursor: pointer;
}

.mini-chip:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.mini-icon-btn {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  cursor: pointer;
}

@media (max-width: 900px) {
  .blindbox-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .blindbox-controls { flex-wrap: wrap; justify-content: flex-end; }
}

@media (max-width: 640px) {
  .blindbox-panel { padding: 18px; }
  .blindbox-head { align-items: flex-start; flex-direction: column; }
  .blindbox-grid { grid-template-columns: 1fr; }
  .blindbox-audio-state { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .eq-bars i { animation: none; }
  .blindbox-card,
  .blindbox-play-area img { transition: none; }
}
</style>
