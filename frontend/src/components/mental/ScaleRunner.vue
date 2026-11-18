<template>
  <section class="card scale-runner">
    <div class="runner-head">
      <div>
        <p class="eyebrow">Screening</p>
        <h2>{{ scale.name }}</h2>
      </div>
      <button class="close-btn" type="button" aria-label="关闭测评" @click="$emit('close')">×</button>
    </div>

    <!-- 开始页 -->
    <div v-if="!started && !result" class="runner-intro">
      <p class="intro-lead">
        回想<strong>过去两周</strong>，下面这些问题困扰你的频率。没有对错，按第一反应选择就好。
      </p>
      <div class="option-legend">
        <span v-for="option in scale.options" :key="option.score">
          <i>{{ option.score }}</i>{{ option.label }}
        </span>
      </div>
      <p class="intro-fine">
        共 {{ scale.questions.length }} 题，约 3 分钟。结果是初筛，不构成诊断；你可以决定是否告诉别人。
      </p>
      <div class="runner-actions">
        <button class="btn btn-primary" type="button" @click="start">开始测评</button>
        <button class="btn btn-ghost" type="button" @click="$emit('close')">先不测</button>
      </div>
    </div>

    <!-- 答题页 -->
    <div v-else-if="!result" class="runner-question">
      <div class="progress-row">
        <span>第 {{ current + 1 }} / {{ total }} 题</span>
        <span>已答 {{ answeredCount }} / {{ total }}</span>
      </div>
      <div class="progress-track" aria-hidden="true">
        <span class="progress-fill" :style="{ width: `${progressPercent}%` }"></span>
      </div>

      <fieldset class="question-field">
        <legend class="question-text">{{ scale.questions[current] }}</legend>
        <div class="answer-list" role="radiogroup" aria-label="选项">
          <button
            v-for="option in scale.options"
            :key="option.score"
            class="answer-option"
            :class="{ active: answers[current] === option.score }"
            type="button"
            role="radio"
            :aria-checked="answers[current] === option.score"
            @click="choose(option.score, $event)"
          >
            <span class="answer-score">{{ option.score }}</span>
            <span>{{ option.label }}</span>
            <span class="answer-check" aria-hidden="true"></span>
          </button>
        </div>
      </fieldset>

      <p class="runner-tip">选完会自动进入下一题；最后一题需要点“提交测评”。</p>
      <p v-if="error" class="error-msg" role="alert">{{ error }}</p>

      <div class="runner-actions runner-actions--between">
        <button class="btn btn-ghost" type="button" :disabled="current === 0 || submitting" @click="prev">
          上一题
        </button>
        <button
          v-if="current < total - 1"
          class="btn btn-primary"
          type="button"
          :disabled="answers[current] == null"
          @click="next"
        >
          下一题
        </button>
        <button
          v-else
          class="btn btn-primary"
          type="button"
          :disabled="submitting || answeredCount < total"
          @click="submit"
        >
          {{ submitting ? '提交中…' : '提交测评' }}
        </button>
      </div>
    </div>

    <!-- 结果页 -->
    <div v-else class="runner-result">
      <div class="result-hero">
        <div class="score-block">
          <span class="score-label">总分</span>
          <strong>{{ result.score }}<small>/{{ result.max_score }}</small></strong>
        </div>
        <div class="risk-block">
          <span class="risk-pill" :class="resultRiskClass">{{ resultLabel }}</span>
          <p>{{ riskAdvice }}</p>
        </div>
      </div>

      <SafetyNotice
        v-if="result.crisis_flag"
        crisis
        context="scale"
        :resources="result.resources || []"
      />
      <SafetyNotice
        v-else-if="needsSupport"
        serious
        context="scale"
        :resources="result.resources || []"
      />
      <p v-else class="result-note">
        这是初筛，不是诊断。如果这个结果让你有点意外，可以过几天再测一次，或找信任的人聊聊。
      </p>

      <div class="runner-actions">
        <button class="btn btn-primary" type="button" @click="reset">再测一次</button>
        <button class="btn btn-ghost" type="button" @click="$emit('close')">收起</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onUnmounted, ref, watch } from 'vue'
import api from '../../api'
import SafetyNotice from './SafetyNotice.vue'
import { scaleRiskAdvice } from '../../utils/scaleAdvice'

const props = defineProps({
  /** GET /mental/scales 的单项：{ key, name, questions: string[], options: [{score,label}], max_score } */
  scale: { type: Object, required: true }
})

const emit = defineEmits(['close', 'submitted'])

const started = ref(false)
const current = ref(0)
const answers = ref([])
const submitting = ref(false)
const error = ref('')
const result = ref(null)
let advanceTimer = null

const total = computed(() => props.scale?.questions?.length || 0)
const answeredCount = computed(() => answers.value.filter(value => value != null).length)
const progressPercent = computed(() => total.value ? ((current.value + 1) / total.value) * 100 : 0)
const needsSupport = computed(() =>
  result.value?.crisis_flag ||
  ['moderate', 'moderately_severe', 'severe'].includes(result.value?.risk_level)
)
const resultLabel = computed(() =>
  result.value?.crisis_flag ? '需要立即关注' : (result.value?.label || '已记录')
)
const resultRiskClass = computed(() =>
  result.value?.crisis_flag ? 'risk-severe' : `risk-${result.value?.risk_level || 'minimal'}`
)

const riskAdvice = computed(() => scaleRiskAdvice(result.value, answers.value))

function resetAnswers () {
  answers.value = Array(total.value).fill(null)
  current.value = 0
  started.value = false
  result.value = null
  error.value = ''
  submitting.value = false
  clearAdvance()
}

function start () {
  resetAnswers()
  started.value = true
}

function clearAdvance () {
  if (advanceTimer) {
    clearTimeout(advanceTimer)
    advanceTimer = null
  }
}

function choose (score, event) {
  answers.value = answers.value.map((value, index) => index === current.value ? score : value)
  error.value = ''
  clearAdvance()
  // 键盘操作不自动跳题，避免焦点随按钮卸载而丢失。
  if (event?.detail === 0) return
  if (current.value < total.value - 1) {
    advanceTimer = setTimeout(() => {
      if (current.value < total.value - 1) current.value += 1
    }, 220)
  }
}

function next () {
  clearAdvance()
  if (current.value < total.value - 1) current.value += 1
}

function prev () {
  clearAdvance()
  if (current.value > 0) current.value -= 1
}

async function submit () {
  error.value = ''
  if (answeredCount.value < total.value) {
    error.value = '还有题目没作答'
    return
  }
  submitting.value = true
  try {
    const { data } = await api.submitMentalScale(props.scale.key, { answers: answers.value })
    result.value = data
    emit('submitted', data)
  } catch (e) {
    const detail = e?.response?.data?.detail
    if (e?.response?.status === 429) {
      error.value = detail || '今天这个量表测得太频繁了，明天再来吧'
    } else {
      error.value = detail || '提交失败，稍后再试一次'
    }
  } finally {
    submitting.value = false
  }
}

function reset () {
  resetAnswers()
}

watch(() => props.scale?.key, resetAnswers)
onUnmounted(clearAdvance)
</script>

<style scoped>
.scale-runner {
  padding: 22px;
}

.runner-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.runner-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 19px;
  letter-spacing: -0.01em;
}

.close-btn {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: var(--border-hairline);
  border-radius: 50%;
  background: var(--surface);
  color: var(--muted);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
}

.close-btn:hover {
  border-color: var(--accent);
  color: var(--fg);
}

.intro-lead {
  margin: 0 0 12px;
  color: var(--fg);
  font-size: 14px;
  line-height: 1.75;
}

.option-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 7px 14px;
  margin-bottom: 12px;
  color: var(--muted);
  font-size: 12px;
}

.option-legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.option-legend i {
  display: grid;
  place-items: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-family: var(--font-mono);
  font-size: 10px;
  font-style: normal;
}

.intro-fine,
.runner-tip {
  margin: 0 0 14px;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.6;
}

.progress-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 11px;
}

.progress-track {
  height: 3px;
  margin: 7px 0 18px;
  border-radius: 999px;
  background: var(--bg);
  overflow: hidden;
}

.progress-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
  transition: width var(--duration-base) var(--ease-out);
}

.question-field {
  margin: 0;
  padding: 0;
  border: 0;
}

.question-text {
  margin-bottom: 12px;
  padding: 0;
  color: var(--fg);
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  line-height: 1.55;
}

.answer-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.answer-option {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 44px;
  padding: 11px 13px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out);
}

.answer-option:hover {
  border-color: var(--accent);
}

.answer-option.active {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.answer-score {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--bg);
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 11px;
}

.answer-option.active .answer-score {
  background: var(--accent);
  color: var(--surface);
}

.answer-check {
  width: 14px;
  height: 14px;
  margin-left: auto;
  border: 1px solid var(--border);
  border-radius: 50%;
}

.answer-option.active .answer-check {
  border: 4px solid var(--accent);
  background: var(--surface);
}

.runner-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
}

.runner-actions--between {
  justify-content: space-between;
}

.result-hero {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 16px;
  margin-bottom: 12px;
  border-radius: var(--radius-md);
  background: var(--bg);
}

.score-block {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
}

.score-label {
  color: var(--muted);
  font-size: 11px;
}

.score-block strong {
  font-family: var(--font-mono);
  font-size: 34px;
  letter-spacing: -0.04em;
  line-height: 1.1;
}

.score-block small {
  color: var(--muted);
  font-size: 13px;
  font-weight: 400;
}

.risk-block {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.risk-pill {
  align-self: flex-start;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.risk-minimal {
  background: var(--success-soft);
  color: var(--success);
}

.risk-mild {
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.risk-moderate,
.risk-moderately_severe {
  background: var(--warn-soft);
  color: var(--warn);
}

.risk-severe {
  background: var(--danger-soft);
  color: var(--danger);
}

.risk-block p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.65;
}

.result-note {
  margin: 0;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--muted);
  font-size: 12px;
  line-height: 1.65;
}

@media (max-width: 560px) {
  .result-hero {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }

  .score-block strong {
    font-size: 30px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .progress-fill {
    transition: none;
  }
}
</style>
