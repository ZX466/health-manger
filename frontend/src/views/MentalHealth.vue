<template>
  <div class="mental">
    <section class="mental-hero card">
      <div class="hero-copy">
        <p class="eyebrow">Mental space</p>
        <h1>心理空间</h1>
        <p class="hero-sub">把心情、睡眠和压力放在一个安全的地方。慢慢来，今天只做一小步。</p>
        <div class="hero-chips">
          <span
            v-for="chip in heroChips"
            :key="chip.label"
            class="hero-chip"
            :class="`hero-chip--${chip.tone}`"
          >
            {{ chip.label }}
          </span>
        </div>
      </div>
      <div class="hero-side">
        <div v-if="!seriousMode" class="hero-mascot" aria-hidden="true">
          <MiniNailong size="large" animation="float" />
        </div>
        <RouterLink class="btn btn-primary hero-chat" to="/chat">
          去聊聊
          <AppIcon name="arrow" :size="15" />
        </RouterLink>
        <span class="hero-fine">随时可以退出，不用解释</span>
      </div>
    </section>

    <div v-if="loadError" class="load-error" role="status">
      <span>部分模块没加载出来。</span>
      <button class="btn btn-ghost btn-sm" type="button" @click="loadAll">重试</button>
    </div>

    <section v-if="seriousMode && !loading" class="card serious-banner">
      <div class="serious-copy">
        <p class="eyebrow">Care first</p>
        <h2>先把玩梗放一边</h2>
        <p>最近的状态值得被认真对待。木鱼和玩梗先收起来，先照顾自己，必要时联系学校心理咨询中心。</p>
      </div>
      <SafetyNotice serious context="general" compact :resources="localCrisisResources" />
    </section>

    <div v-if="loading" class="mental-grid" aria-busy="true">
      <div class="card skeleton span-7"></div>
      <div class="card skeleton span-5"></div>
      <div class="card skeleton span-12"></div>
    </div>

    <template v-else>
      <div class="mental-grid">
        <MoodCheckIn class="span-7" :today="displayMood" @saved="onMoodSaved" />
        <MoodTrend class="span-5" :trend="trend" :summary="summary" />
        <BreathingRing :class="seriousMode ? 'span-6' : 'span-5'" />
        <WoodenFish v-if="!seriousMode" class="span-3" />
        <PersonaCard
          :class="seriousMode ? 'span-6' : 'span-4'"
          :serious="seriousMode"
          @change="onPersonaChange"
        />
      </div>

      <section ref="scaleSection" class="scales-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">Screening</p>
            <h2>心理测评</h2>
          </div>
          <span class="section-hint">PHQ-9 / GAD-7 · 初筛不构成诊断</span>
        </div>

        <ScaleRunner
          v-if="activeScale"
          :scale="activeScale"
          @close="activeScale = null"
          @submitted="onScaleSubmitted"
        />

        <div v-else class="scale-grid">
          <button
            v-for="scale in scales"
            :key="scale.key"
            class="card scale-card"
            type="button"
            @click="startScale(scale)"
          >
            <span class="scale-top">
              <span class="scale-key">{{ scale.key.toUpperCase() }}</span>
              <span v-if="latestFor(scale.key)" class="scale-latest">
                上次 {{ scaleResultLabel(latestFor(scale.key)) }}
              </span>
            </span>
            <h3>{{ scale.name }}</h3>
            <p>{{ scale.questions.length }} 题 · 最高 {{ scale.max_score }} 分</p>
            <span class="scale-cta">
              开始
              <AppIcon name="arrow" :size="14" />
            </span>
          </button>
          <p v-if="!scales.length" class="empty-note">
            {{ errors.scales ? '量表暂时没加载出来，稍后重试。' : '暂无量表。' }}
          </p>
        </div>

        <div v-if="history.length" class="card history-card">
          <div class="history-head">
            <h3>最近测评</h3>
            <span>仅自己可见</span>
          </div>
          <div class="history-list">
            <div v-for="item in history" :key="item.id" class="history-row">
              <span class="history-name">{{ scaleName(item.scale_type) }}</span>
              <span class="risk-pill" :class="scaleRiskClass(item)">
                {{ scaleResultLabel(item) }}
              </span>
              <span class="history-score">{{ item.score }}<small>/{{ item.max_score }}</small></span>
              <time class="history-time">{{ formatScaleDate(item.created_at) }}</time>
            </div>
          </div>
        </div>
      </section>

      <section class="card help-card">
        <div class="section-head">
          <div>
            <p class="eyebrow">Help</p>
            <h2>如果现在很难受</h2>
          </div>
          <span class="section-hint">不必一个人扛</span>
        </div>
        <SafetyNotice context="general" />
      </section>
    </template>

    <div v-if="toast" class="toast mental-toast" role="status">{{ toast }}</div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import api from '../api'
import AppIcon from '../components/AppIcon.vue'
import MiniNailong from '../components/mascots/MiniNailong.vue'
import MoodCheckIn from '../components/mental/MoodCheckIn.vue'
import MoodTrend from '../components/mental/MoodTrend.vue'
import BreathingRing from '../components/mental/BreathingRing.vue'
import WoodenFish from '../components/mental/WoodenFish.vue'
import PersonaCard from '../components/mental/PersonaCard.vue'
import ScaleRunner from '../components/mental/ScaleRunner.vue'
import SafetyNotice from '../components/mental/SafetyNotice.vue'
import { formatScaleDate, localDateKey, parseServerDate } from '../utils/date'

const loading = ref(true)
const summary = ref(null)
const trend = ref({ dates: [], mood_score: [], sleep_hours: [] })
const todayMood = ref(null)
const scales = ref([])
const history = ref([])
const activeScale = ref(null)
const scaleSection = ref(null)
const toast = ref('')
const localCrisis = ref(false)
const localCrisisResources = ref([])
const errors = reactive({ summary: '', trend: '', mood: '', scales: '', history: '' })

let toastTimer = null

// 一旦看到过危机结果或 serious_mode，本次页面会话不再因刷新失败而降级。
const seriousMode = computed(() => localCrisis.value || !!summary.value?.serious_mode)
const loadError = computed(() => Object.values(errors).some(Boolean))

const displayMood = computed(() => {
  if (todayMood.value) return todayMood.value
  const latest = summary.value?.latest_mood
  if (!latest) return null
  return isToday(latest.record_date) ? latest : null
})

const heroChips = computed(() => {
  const chips = []
  if (displayMood.value) {
    chips.push({ label: `今天：${moodLabel(displayMood.value.mood_score)}`, tone: 'accent' })
  } else {
    chips.push({ label: '今天还没打卡', tone: 'muted' })
  }

  if (summary.value?.sleep_avg_7d != null) {
    chips.push({ label: `7 天平均睡眠 ${Number(summary.value.sleep_avg_7d).toFixed(1)}h`, tone: 'muted' })
  }

  const latestScales = [summary.value?.latest_phq9, summary.value?.latest_gad7].filter(Boolean)
  const latestScale = latestScales.find(item => item.crisis_flag) || latestScales[0]
  if (latestScale) {
    chips.push({
      label: `${scaleName(latestScale.scale_type)} ${scaleResultLabel(latestScale)}`,
      tone: latestScale.crisis_flag ? 'warn' : 'muted'
    })
  }

  if (summary.value?.sleep_debt_7d != null && Number(summary.value.sleep_debt_7d) > 0) {
    chips.push({ label: `睡眠欠账 ${Number(summary.value.sleep_debt_7d).toFixed(1)}h`, tone: 'warn' })
  }

  return chips
})

const MOOD_LABELS = { 1: '很难受', 2: '有点丧', 3: '还行', 4: '不错', 5: '很好' }
const RISK_LABELS = {
  minimal: '无明显症状',
  mild: '轻度',
  moderate: '中度',
  moderately_severe: '中重度',
  severe: '重度'
}
const SCALE_NAMES = { phq9: 'PHQ-9', gad7: 'GAD-7' }

function moodLabel (score) {
  return MOOD_LABELS[score] || '已记录'
}

function riskLabel (risk) {
  return RISK_LABELS[risk] || risk || '已记录'
}

function scaleResultLabel (item) {
  if (!item) return '已记录'
  return item.crisis_flag ? '需要立即关注' : (item.label || riskLabel(item.risk_level))
}

function scaleRiskClass (item) {
  return item?.crisis_flag ? 'risk-severe' : `risk-${item?.risk_level || 'minimal'}`
}

function scaleName (type) {
  return SCALE_NAMES[type] || String(type || '').toUpperCase()
}

function isToday (value) {
  if (!value) return false
  const parsed = parseServerDate(value)
  if (parsed) return localDateKey(parsed) === localDateKey()
  return String(value).slice(0, 10) === localDateKey()
}

function latestFor (key) {
  if (key === 'phq9') return summary.value?.latest_phq9 || null
  if (key === 'gad7') return summary.value?.latest_gad7 || null
  return null
}

function showToast (message) {
  toast.value = message
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 3200)
}

function errorText (e, fallback) {
  const detail = e?.response?.data?.detail
  if (typeof detail === 'string') return detail
  return fallback
}

async function loadSummary () {
  const { data } = await api.getMentalSummary()
  summary.value = data
  if (data?.serious_mode) localCrisis.value = true
}

async function loadTrend () {
  const { data } = await api.getMentalTrend({ days: 14 })
  trend.value = data || { dates: [], mood_score: [], sleep_hours: [] }
}

async function loadMood () {
  const { data } = await api.getMentalMood({ days: 1 })
  const records = Array.isArray(data) ? data : []
  todayMood.value = records.find(record => isToday(record.record_date)) || null
}

async function loadScales () {
  const { data } = await api.getMentalScales()
  scales.value = Array.isArray(data) ? data : []
  if (activeScale.value) {
    activeScale.value = scales.value.find(scale => scale.key === activeScale.value?.key) || null
  }
}

async function loadHistory () {
  const { data } = await api.getMentalScaleHistory({ limit: 8 })
  history.value = Array.isArray(data) ? data : []
}

async function loadAll () {
  loading.value = true
  Object.keys(errors).forEach(key => { errors[key] = '' })

  const jobs = [
    ['summary', loadSummary, '心理概览没加载出来'],
    ['trend', loadTrend, '趋势没加载出来'],
    ['mood', loadMood, '今日打卡没加载出来'],
    ['scales', loadScales, '量表没加载出来'],
    ['history', loadHistory, '测评记录没加载出来']
  ]

  const results = await Promise.allSettled(jobs.map(([, run]) => run()))
  results.forEach((result, index) => {
    if (result.status === 'rejected') {
      const [key, , fallback] = jobs[index]
      errors[key] = errorText(result.reason, fallback)
    }
  })
  loading.value = false
}

function startScale (scale) {
  activeScale.value = scale
  nextTick(() => {
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    scaleSection.value?.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' })
  })
}

async function onMoodSaved (record) {
  todayMood.value = record
  showToast('今天的心情已记下')
  const results = await Promise.allSettled([loadSummary(), loadTrend()])
  results.forEach(result => {
    if (result.status === 'rejected') showToast('已保存，但概览刷新失败')
  })
}

async function onScaleSubmitted (result) {
  if (result?.crisis_flag) {
    // 先把危机状态和本次返回的资源锁在本地；刷新失败也不能退回玩梗模式。
    localCrisis.value = true
    localCrisisResources.value = Array.isArray(result.resources) ? result.resources : []
  }
  showToast(result?.crisis_flag ? '结果已保存，请先看看下面的支持信息' : '测评结果已保存')
  await Promise.allSettled([loadSummary(), loadHistory()])
}

function onPersonaChange () {
  showToast('已保存你的人设偏好')
}

onMounted(loadAll)
onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer)
})
</script>

<style scoped>
.mental {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.mental-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 26px 28px;
  background:
    radial-gradient(circle at 92% 12%, var(--accent-soft) 0, transparent 34%),
    var(--surface);
}

.hero-copy {
  min-width: 0;
}

.hero-copy h1 {
  margin: 2px 0 6px;
  font-family: var(--font-display);
  font-size: 27px;
  letter-spacing: -0.03em;
}

.hero-sub {
  max-width: 560px;
  margin: 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.7;
}

.hero-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 14px;
}

.hero-chip {
  padding: 3px 9px;
  border: var(--border-hairline);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 11px;
}

.hero-chip--accent {
  border-color: color-mix(in oklch, var(--accent) 18%, var(--border));
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.hero-chip--warn {
  border-color: color-mix(in oklch, var(--warn) 22%, var(--border));
  background: var(--warn-soft);
  color: var(--warn);
}

.hero-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.hero-mascot {
  display: grid;
  place-items: center;
  width: 86px;
  height: 72px;
  margin-bottom: 2px;
}

.hero-chat {
  text-decoration: none;
}

.hero-fine {
  color: var(--muted);
  font-size: 10px;
}

.load-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 12px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--warn-soft);
  color: var(--muted);
  font-size: 12px;
}

.serious-banner {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 16px;
  padding: 20px 22px;
  border-color: color-mix(in oklch, var(--warn) 26%, var(--border));
  background: var(--warn-soft);
}

.serious-copy h2 {
  margin: 2px 0 6px;
  font-family: var(--font-display);
  font-size: 18px;
}

.serious-copy p:last-child {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.7;
}

.mental-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 14px;
}

.span-3 { grid-column: span 3; }
.span-4 { grid-column: span 4; }
.span-5 { grid-column: span 5; }
.span-6 { grid-column: span 6; }
.span-7 { grid-column: span 7; }
.span-12 { grid-column: span 12; }

.skeleton {
  min-height: 170px;
  background: var(--bg);
  animation: skeleton-pulse 1.6s ease-in-out infinite;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.55; }
}

.scales-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  scroll-margin-top: 18px;
}

.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.section-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 20px;
  letter-spacing: -0.02em;
}

.section-hint {
  color: var(--muted);
  font-size: 11px;
}

.scale-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.scale-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 18px 20px;
  border: var(--border-hairline);
  background: var(--surface);
  color: var(--fg);
  text-align: left;
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out);
}

.scale-card:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.scale-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;
}

.scale-key {
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.03em;
}

.scale-latest {
  color: var(--muted);
  font-size: 10px;
}

.scale-card h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 16px;
}

.scale-card p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
}

.scale-cta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  color: var(--accent-strong);
  font-size: 12px;
  font-weight: 600;
}

.empty-note {
  grid-column: 1 / -1;
  margin: 0;
  padding: 18px;
  border: var(--border-hairline);
  border-radius: var(--radius-md);
  color: var(--muted);
  font-size: 13px;
  text-align: center;
}

.history-card {
  padding: 16px 18px;
}

.history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.history-head h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 14px;
}

.history-head span {
  color: var(--muted);
  font-size: 10px;
}

.history-list {
  display: flex;
  flex-direction: column;
}

.history-row {
  display: grid;
  grid-template-columns: 70px auto 1fr auto;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-top: var(--border-hairline);
  font-size: 12px;
}

.history-row:first-child {
  border-top: 0;
}

.history-name {
  font-weight: 600;
}

.history-score {
  justify-self: end;
  font-family: var(--font-mono);
  font-size: 13px;
}

.history-score small {
  color: var(--muted);
  font-size: 10px;
  font-weight: 400;
}

.history-time {
  color: var(--muted);
  font-size: 10px;
  white-space: nowrap;
}

.risk-pill {
  justify-self: start;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
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

.help-card {
  padding: 20px 22px;
}

.help-card .section-head {
  margin-bottom: 12px;
}

.mental-toast {
  bottom: 24px;
}

@media (max-width: 900px) {
  .serious-banner {
    grid-template-columns: 1fr;
  }

  .span-3,
  .span-4,
  .span-5,
  .span-6,
  .span-7 {
    grid-column: span 6;
  }

  .span-7 {
    grid-column: span 12;
  }
}

@media (max-width: 768px) {
  .mental-hero {
    align-items: flex-start;
    flex-direction: column;
    padding: 22px;
  }

  .hero-side {
    align-items: flex-start;
    flex-direction: row;
    flex-wrap: wrap;
    width: 100%;
  }

  .hero-mascot {
    width: 64px;
    height: 56px;
  }

  .hero-fine {
    width: 100%;
  }

  .span-3,
  .span-4,
  .span-5,
  .span-6,
  .span-7 {
    grid-column: span 12;
  }

  .scale-grid {
    grid-template-columns: 1fr;
  }

  .history-row {
    grid-template-columns: 58px auto 1fr;
  }

  .history-time {
    grid-column: 1 / -1;
    justify-self: start;
  }

  .section-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 3px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton {
    animation: none;
  }

  .scale-card {
    transition: none;
  }
}
</style>
