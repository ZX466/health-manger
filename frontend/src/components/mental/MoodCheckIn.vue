<template>
  <section class="card mood-checkin">
    <div class="checkin-head">
      <div>
        <p class="eyebrow">10s check-in</p>
        <h2>今天的精神状态</h2>
      </div>
      <span class="today-date">{{ todayLabel }}</span>
    </div>

    <div v-if="today && !editing" class="saved-state">
      <div class="saved-main">
        <MoodFace :face="savedFace" :size="42" />
        <div>
          <strong>今天已记录 · {{ savedTitle }}</strong>
          <p>
            心情 {{ today.mood_score }}/5
            <span v-if="today.stress_tags && today.stress_tags.length"> · 压力：{{ today.stress_tags.join('、') }}</span>
            <span v-else> · 没标记压力</span>
            <span v-if="today.sleep_hours != null"> · 睡了 {{ today.sleep_hours }}h</span>
            <span v-if="bedtimeText"> · {{ bedtimeText }} 入睡</span>
          </p>
        </div>
      </div>
      <button class="btn btn-ghost btn-sm" type="button" @click="startEditing">改一下</button>
    </div>

    <form v-else class="checkin-form" @submit.prevent="submit">
      <fieldset class="mood-field">
        <legend>选一个最接近的状态</legend>
        <div class="mood-options">
          <button
            v-for="option in moodOptions"
            :key="option.level"
            type="button"
            class="mood-option"
            :class="{ active: form.mood_score === option.level }"
            :aria-pressed="form.mood_score === option.level"
            @click="selectMood(option)"
          >
            <span class="mood-num">{{ String(option.level).padStart(2, '0') }}</span>
            <MoodFace :face="option.face" :size="30" />
            <span class="mood-label">{{ option.title }}</span>
          </button>
        </div>
        <p v-if="selectedMood" class="mood-hint">{{ selectedMood.hint }}</p>
      </fieldset>

      <div class="checkin-grid">
        <div class="field">
          <span class="field-label">昨晚睡了多久</span>
          <div class="sleep-row">
            <button
              v-for="preset in sleepPresets"
              :key="preset"
              type="button"
              class="chip"
              :class="{ active: form.sleep_hours === preset }"
              :aria-pressed="form.sleep_hours === preset"
              @click="form.sleep_hours = form.sleep_hours === preset ? null : preset"
            >
              {{ preset }}h
            </button>
            <label class="sleep-custom">
              <span class="sr-only">自定义睡眠小时数</span>
              <input
                v-model.number="form.sleep_hours"
                type="number"
                min="0"
                max="16"
                step="0.5"
                inputmode="decimal"
                placeholder="自定义"
              />
              <span>h</span>
            </label>
          </div>
        </div>

        <div class="field">
          <label class="field-label" for="bedtime-input">昨晚几点睡</label>
          <input
            id="bedtime-input"
            class="bedtime-input"
            type="time"
            v-model="form.bedtime"
          />
          <span class="field-note">只在本机记录，用来判断要不要提醒你早点睡。</span>
        </div>
      </div>

      <div class="field">
        <span class="field-label">压力来自哪里？<span class="optional">（可多选，最多 5 个）</span></span>
        <div class="stress-row">
          <button
            v-for="tag in stressOptions"
            :key="tag"
            type="button"
            class="chip tag-chip"
            :class="{ active: form.stress_tags.includes(tag) }"
            :aria-pressed="form.stress_tags.includes(tag)"
            :disabled="!form.stress_tags.includes(tag) && form.stress_tags.length >= 5"
            @click="toggleTag(tag)"
          >
            {{ tag }}
          </button>
          <span class="stress-hint">{{ form.stress_tags.length }}/5</span>
        </div>
      </div>

      <div class="field">
        <label class="field-label" for="mood-note">树洞短记<span class="optional">（可选）</span></label>
        <textarea
          id="mood-note"
          v-model="form.note"
          rows="2"
          maxlength="500"
          placeholder="一句话就好，比如：今天终于把实验做完了"
        ></textarea>
        <span class="note-count">{{ form.note.length }}/500</span>
      </div>

      <p v-if="error" class="error-msg" role="alert">{{ error }}</p>

      <div class="checkin-actions">
        <button class="btn btn-primary" type="submit" :disabled="saving || !form.mood_score">
          {{ saving ? '保存中…' : '记下今天' }}
        </button>
        <button v-if="today" class="btn btn-ghost" type="button" :disabled="saving" @click="cancelEditing">
          取消
        </button>
      </div>
    </form>

    <ReactionStrip v-if="!serious && moodReaction" :reaction="moodReaction" surface />
  </section>
</template>

<script setup>
import { computed, h, reactive, ref, watch } from 'vue'
import api from '../../api'
import { localDateKey } from '../../utils/date'
import { MOOD_LEVELS, STRESS_TAGS, moodTitle } from '../../constants/copywriting'
import { useWellnessStore, timeToHour, hourToTime } from '../../stores/wellness'
import ReactionStrip from '../ReactionStrip.vue'
import { buildMoodReaction } from '../../constants/media'
import { usePreferences } from '../../composables/usePreferences'
import { playClip } from '../../composables/useHealthU'

const props = defineProps({
  /** 后端 GET /mental/mood?days=1 中今天的记录 */
  today: { type: Object, default: null },
  /** 高危状态下去掉玩梗标签，换成中性描述 */
  serious: { type: Boolean, default: false }
})

const emit = defineEmits(['saved'])
const wellness = useWellnessStore()
const { companion } = usePreferences()

const SERIOUS_TITLES = { 5: '状态稳定', 4: '状态尚可', 3: '一般', 2: '有些低落', 1: '很难受' }
const moodOptions = computed(() => props.serious
  ? MOOD_LEVELS.map(item => ({ ...item, title: SERIOUS_TITLES[item.level] || item.title }))
  : MOOD_LEVELS
)
const sleepPresets = [5, 6, 7, 8, 9]
const stressOptions = STRESS_TAGS

const editing = ref(false)
const saving = ref(false)
const error = ref('')

const form = reactive({
  mood_score: null,
  stress_tags: [],
  sleep_hours: null,
  bedtime: '',
  note: ''
})

const todayLabel = computed(() =>
  new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' })
)

const selectedMood = computed(() =>
  moodOptions.value.find(option => option.level === form.mood_score) || null
)
const savedTitle = computed(() => props.serious
  ? (SERIOUS_TITLES[props.today?.mood_score] || '已记录')
  : moodTitle(props.today?.mood_score)
)
const savedFace = computed(() =>
  moodOptions.value.find(option => option.level === props.today?.mood_score)?.face || 'neutral'
)
const moodReaction = computed(() => {
  const level = form.mood_score || props.today?.mood_score
  if (!level) return null
  return buildMoodReaction({ level, companion: companion.value })
})

function selectMood (option) {
  form.mood_score = option.level
  if (props.serious) return
  const reaction = buildMoodReaction({ level: option.level, companion: companion.value })
  if (reaction.audio) playClip(reaction.audio)
}

const bedtimeText = computed(() => {
  const recordDate = props.today?.record_date
  if (!recordDate) return ''
  const key = String(recordDate).slice(0, 10)
  const stored = wellness.bedtimeHour
  if (wellness.dateKey === key && stored != null) return hourToTime(stored)
  return ''
})

const MoodFace = (propsFace) => {
  const FACE_PATHS = {
    calm: ['M4 10c1.2-1.2 2.8-1.2 4 0', 'M16 10c1.2-1.2 2.8-1.2 4 0', 'M8 15c1.2 1.6 2.5 2.3 4 2.3s2.8-.7 4-2.3'],
    good: ['M8 10h.01', 'M16 10h.01', 'M8 14.5c1.1 1.4 2.4 2 4 2s2.9-.6 4-2'],
    neutral: ['M8 10h.01', 'M16 10h.01', 'M8.5 15h7'],
    low: ['M8 10h.01', 'M16 10h.01', 'M8.5 16c1.1-1.2 2.4-1.8 4-1.8s2.9.6 4 1.8'],
    bad: ['M8 10.5c.8-.9 1.9-.9 2.7 0', 'M13.3 10.5c.8-.9 1.9-.9 2.7 0', 'M8.5 16.5c1.1-1.6 2.4-2.3 4-2.3s2.9.7 4 2.3']
  }
  return h('svg', {
    width: propsFace.size,
    height: propsFace.size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    'stroke-width': 1.7,
    'stroke-linecap': 'round',
    'stroke-linejoin': 'round',
    'aria-hidden': 'true',
    focusable: 'false'
  }, [
    h('circle', { cx: 12, cy: 12, r: 9 }),
    ...(FACE_PATHS[propsFace.face] || FACE_PATHS.neutral).map(d => h('path', { d }))
  ])
}
MoodFace.props = { face: { type: String, default: 'neutral' }, size: { type: Number, default: 28 } }

function toggleTag (tag) {
  if (form.stress_tags.includes(tag)) {
    form.stress_tags = form.stress_tags.filter(item => item !== tag)
  } else if (form.stress_tags.length < 5) {
    form.stress_tags = [...form.stress_tags, tag]
  }
}

function syncFromToday () {
  if (!props.today) {
    form.mood_score = null
    form.stress_tags = []
    form.sleep_hours = null
    form.bedtime = hourToTime(wellness.bedtimeHour)
    form.note = ''
    return
  }
  form.mood_score = props.today.mood_score ?? null
  form.stress_tags = Array.isArray(props.today.stress_tags) ? [...props.today.stress_tags] : []
  form.sleep_hours = props.today.sleep_hours ?? null
  form.bedtime = hourToTime(wellness.bedtimeHour)
  form.note = props.today.note || ''
}

function startEditing () {
  syncFromToday()
  error.value = ''
  editing.value = true
}

function cancelEditing () {
  editing.value = false
  error.value = ''
  syncFromToday()
}

async function submit () {
  error.value = ''
  if (!form.mood_score) {
    error.value = '先选一个今天的精神状态吧'
    return
  }
  const sleep = form.sleep_hours
  if (sleep != null && sleep !== '' && (Number.isNaN(Number(sleep)) || sleep < 0 || sleep > 16)) {
    error.value = '睡眠时长需要在 0–16 小时之间'
    return
  }

  saving.value = true
  try {
    const payload = {
      mood_score: form.mood_score,
      stress_tags: [...form.stress_tags],
      sleep_hours: sleep == null || sleep === '' ? null : Number(sleep),
      note: form.note.trim() || null
    }
    const { data } = await api.createMentalRecord(payload)
    const bedtimeHour = timeToHour(form.bedtime)
    wellness.applyMood({
      level: form.mood_score,
      tags: form.stress_tags,
      sleepHours: payload.sleep_hours,
      bedtimeHour
    })
    emit('saved', {
      ...payload,
      ...data,
      record_date: data?.record_date || localDateKey()
    })
    editing.value = false
  } catch (e) {
    const detail = e?.response?.data?.detail
    error.value = typeof detail === 'string' ? detail : '没保存上，稍后再试一次'
  } finally {
    saving.value = false
  }
}

watch(() => props.today, (value) => {
  if (!value) editing.value = false
  else if (!editing.value) syncFromToday()
}, { immediate: true })

watch(() => wellness.bedtimeHour, () => {
  if (!editing.value) form.bedtime = hourToTime(wellness.bedtimeHour)
})
</script>

<style scoped>
.mood-checkin {
  padding: 22px;
}

.checkin-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.checkin-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 18px;
  letter-spacing: -0.01em;
}

.today-date {
  color: var(--muted);
  font-size: 12px;
  white-space: nowrap;
}

.saved-state {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
  border-radius: var(--radius-sm);
  background: var(--success-bg);
}

.saved-main {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--success-fg);
}

.saved-main strong {
  display: block;
  font-size: 14px;
}

.saved-main p {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.checkin-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mood-field {
  margin: 0;
  padding: 0;
  border: 0;
}

.mood-field legend,
.field-label {
  display: block;
  margin-bottom: 8px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.03em;
}

.mood-options {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0;
  border: 1px solid var(--line, var(--border));
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--surface);
}

.mood-option {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 5px;
  padding: 10px 9px;
  border: 0;
  border-right: 1px solid var(--line, var(--border));
  border-radius: 0;
  background: var(--surface);
  color: var(--muted);
  font-size: 11px;
  text-align: left;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}

.mood-option:last-child {
  border-right: 0;
}

.mood-option:hover {
  background: var(--surface-2);
}

.mood-option.active {
  background: var(--ink, #191c22);
  color: var(--surface, #fff);
}

.mood-num {
  color: var(--muted-2, var(--muted));
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.06em;
}

.mood-option.active .mood-num {
  color: color-mix(in oklch, var(--surface) 55%, transparent);
}

.mood-label {
  line-height: 1.35;
  text-align: left;
}

.mood-hint {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.checkin-grid {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 16px;
}

.field {
  position: relative;
  min-width: 0;
}

.sleep-row,
.stress-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  min-width: 42px;
  min-height: 34px;
  padding: 4px 8px;
  border: var(--border-hairline);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 12px;
  cursor: pointer;
}

.chip.active {
  border-color: var(--accent);
  background: var(--accent-bg);
  color: var(--accent-fg);
}

.sleep-custom {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: var(--muted);
  font-size: 12px;
}

.sleep-custom input {
  width: 64px;
  min-height: 34px;
  padding: 4px 6px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  font: inherit;
  font-size: 12px;
}

.bedtime-input {
  width: 100%;
  min-height: 38px;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  font: inherit;
  font-size: 13px;
}

.bedtime-input:focus-visible {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.field-note {
  display: block;
  margin-top: 5px;
  color: var(--muted);
  font-size: 10px;
  line-height: 1.5;
}

.tag-chip:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.stress-hint {
  margin-left: 2px;
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 11px;
}

.optional {
  font-weight: 400;
}

textarea {
  width: 100%;
  resize: vertical;
}

.note-count {
  position: absolute;
  right: 4px;
  bottom: 6px;
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 10px;
}

.checkin-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-msg {
  margin: 0;
  color: var(--danger-fg);
  font-size: 12px;
}

.mood-checkin :deep(.reaction-strip) {
  margin-top: 12px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 640px) {
  .checkin-grid {
    grid-template-columns: 1fr;
  }

  .mood-option {
    padding: 8px 2px;
  }

  .saved-state {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mood-option {
    transition: none;
  }
}
</style>
