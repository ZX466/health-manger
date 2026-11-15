<template>
  <section class="card mood-checkin">
    <div class="checkin-head">
      <div>
        <p class="eyebrow">Daily check-in</p>
        <h2>今天感觉怎么样？</h2>
      </div>
      <span class="today-date">{{ todayLabel }}</span>
    </div>

    <div v-if="today && !editing" class="saved-state">
      <div class="saved-main">
        <span class="saved-emoji" aria-hidden="true">{{ moodEmoji(today.mood_score) }}</span>
        <div>
          <strong>今天已记录</strong>
          <p>
            心情 {{ today.mood_score }}/5
            <span v-if="today.stress_tags && today.stress_tags.length"> · 压力：{{ today.stress_tags.join('、') }}</span>
            <span v-else> · 没标记压力</span>
            <span v-if="today.sleep_hours != null"> · 睡了 {{ today.sleep_hours }}h</span>
          </p>
        </div>
      </div>
      <button class="btn btn-ghost btn-sm" type="button" @click="startEditing">改一下</button>
    </div>

    <form v-else class="checkin-form" @submit.prevent="submit">
      <fieldset class="mood-field">
        <legend>心情</legend>
        <div class="mood-options">
          <button
            v-for="option in moodOptions"
            :key="option.value"
            type="button"
            class="mood-option"
            :class="{ active: form.mood_score === option.value }"
            :aria-pressed="form.mood_score === option.value"
            @click="form.mood_score = option.value"
          >
            <span class="mood-emoji" aria-hidden="true">{{ option.emoji }}</span>
            <span>{{ option.label }}</span>
          </button>
        </div>
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
      </div>

      <div class="field">
        <label class="field-label" for="mood-note">想记点什么吗？<span class="optional">（可选）</span></label>
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
  </section>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import api from '../../api'
import { localDateKey } from '../../utils/date'

const props = defineProps({
  /** 后端 GET /mental/mood?days=1 中今天的记录 */
  today: { type: Object, default: null }
})

const emit = defineEmits(['saved'])

const moodOptions = [
  { value: 1, emoji: '😣', label: '很难受' },
  { value: 2, emoji: '😕', label: '有点丧' },
  { value: 3, emoji: '😐', label: '还行' },
  { value: 4, emoji: '🙂', label: '不错' },
  { value: 5, emoji: '😄', label: '很好' }
]

const sleepPresets = [5, 6, 7, 8, 9]
const stressOptions = ['学业', '考试', '睡眠', '人际关系', '家庭', '钱', '身体', '未来']

const editing = ref(false)
const saving = ref(false)
const error = ref('')

const form = reactive({
  mood_score: null,
  stress_tags: [],
  sleep_hours: null,
  note: ''
})

const todayLabel = computed(() =>
  new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short' })
)

function moodEmoji (score) {
  return moodOptions.find(o => o.value === score)?.emoji || '🙂'
}

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
    form.note = ''
    return
  }
  form.mood_score = props.today.mood_score ?? null
  form.stress_tags = Array.isArray(props.today.stress_tags) ? [...props.today.stress_tags] : []
  form.sleep_hours = props.today.sleep_hours ?? null
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
    error.value = '先选一个今天的心情吧'
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
    const { data } = await api.saveMentalMood(payload)
    emit('saved', { ...payload, ...data, record_date: data?.record_date || localDateKey() })
    editing.value = false
  } catch (e) {
    error.value = e?.response?.data?.detail || '没保存上，稍后再试一次'
  } finally {
    saving.value = false
  }
}

watch(() => props.today, (value) => {
  if (!value) editing.value = false
  else if (!editing.value) syncFromToday()
}, { immediate: true })
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
  background: var(--success-soft);
}

.saved-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.saved-emoji {
  font-size: 30px;
  line-height: 1;
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
  gap: 6px;
}

.mood-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: 9px 4px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--muted);
  font-size: 11px;
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}

.mood-emoji {
  font-size: 22px;
  line-height: 1.15;
}

.mood-option:hover {
  border-color: var(--accent);
}

.mood-option.active {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--fg);
}

.checkin-grid {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 16px;
}

.field {
  position: relative;
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
  min-height: 32px;
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
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.sleep-custom {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  color: var(--muted);
  font-size: 12px;
}

.sleep-custom input {
  width: 62px;
  min-height: 32px;
  padding: 4px 6px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  font: inherit;
  font-size: 12px;
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

  .mood-emoji {
    font-size: 20px;
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
