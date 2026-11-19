<template>
  <div class="mental">
    <PageHead
      folio="02"
      eyebrow="MENTAL / CARE"
      title="心理空间"
      deck="不用每天都很稳定。先记录一下今天，再决定要不要做点什么。"
    >
      <template #actions>
        <span v-if="displayMood" class="status-chip">
          <span class="status-dot status-dot--success"></span>
          今日已打卡
        </span>
        <RouterLink class="btn" to="/chat?mode=mental">去聊聊</RouterLink>
      </template>
    </PageHead>

    <div class="mental-chips" aria-label="今日心理摘要">
      <span
        v-for="chip in heroChips"
        :key="chip.label"
        class="status-chip"
        :class="`status-chip--${chip.tone}`"
      >
        {{ chip.label }}
      </span>
    </div>

    <div v-if="loadError" class="load-error" role="status">
      <span>部分模块没加载出来。</span>
      <button class="btn btn-ghost btn-sm" type="button" @click="loadAll">重试</button>
    </div>

    <section v-if="seriousMode && !loading" class="card serious-banner">
      <div class="serious-copy">
        <p class="eyebrow">Care first · 关怀优先</p>
        <h2>先把玩梗放一边</h2>
        <p>最近的状态值得被认真对待。木鱼和玩梗先收起来，先照顾自己，必要时联系学校心理咨询中心。</p>
        <div class="crisis-lines">
          <a class="crisis-line" href="tel:4001619995">
            <span>全国 24 小时心理援助</span>
            <strong>400-161-9995</strong>
          </a>
          <a class="crisis-line" href="tel:12356">
            <span>全国心理援助热线</span>
            <strong>12356</strong>
          </a>
          <span class="crisis-line crisis-line--school">
            <span>校医院 / 心理咨询中心</span>
            <strong>工作日可预约</strong>
          </span>
        </div>
      </div>
      <SafetyNotice serious context="general" compact :resources="crisisResources" />
    </section>

    <div v-if="loading" class="mental-grid" aria-busy="true">
      <div class="card skeleton span-7"></div>
      <div class="card skeleton span-5"></div>
      <div class="card skeleton span-12"></div>
    </div>

    <template v-else>
      <div class="mental-grid">
        <MoodCheckIn class="span-7" :today="displayMood" :serious="seriousMode" @saved="onMoodSaved" />
        <MoodTrend class="span-5" :trend="trend" :summary="summary" :serious="seriousMode" />
      </div>

      <section class="toolbox-section v21-panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">TOOLBOX</p>
            <h2>随身减压</h2>
          </div>
          <span class="section-hint">4-7-8 呼吸 · 电子木鱼 · 烦恼粉碎机</span>
        </div>

        <div class="toolbox-grid" :class="{ 'toolbox-grid--single': seriousMode }">
          <div class="card breathing-card">
            <div class="tool-card-head">
              <div>
                <h3>4-7-8 减压呼吸</h3>
                <p>吸气 4 秒 · 屏息 7 秒 · 呼气 8 秒</p>
              </div>
              <AppIcon name="breathe" :size="18" />
            </div>
            <RingGauge mode="breathe" :size="188" />
          </div>

          <StressShredder v-if="!seriousMode" class="toolbox-shredder" />
        </div>
      </section>

      <section ref="scaleSection" class="scales-section v21-panel">
        <div class="section-head">
          <div>
            <p class="eyebrow">SELF-ASSESSMENT</p>
            <h2>心理量表自评</h2>
          </div>
          <span class="section-hint">PHQ-9 情绪晴雨表 / GAD-7 焦虑自测 · 初筛不构成诊断</span>
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
            <h3>{{ scaleTitle(scale.key) }} <small>{{ scaleName(scale.key) }}</small></h3>
            <p>{{ scale.questions.length }} 题 · 最高 {{ scale.max_score }} 分 · 约 3 分钟</p>
            <span class="scale-cta">
              开始
              <AppIcon name="arrow" :size="14" />
            </span>
          </button>
          <p v-if="!scales.length" class="empty-note">
            {{ errors.scales ? '量表暂时没加载出来，稍后重试。' : '暂无量表。' }}
          </p>
        </div>

        <div v-if="history.length" class="card history-trend-card">
          <div class="history-head">
            <div>
              <h3>历史趋势</h3>
              <span>分数越低越轻，断点表示当天未测</span>
            </div>
            <div class="trend-legend" aria-hidden="true">
              <span><i class="dot dot--accent"></i>PHQ-9</span>
              <span><i class="dot dot--teal"></i>GAD-7</span>
            </div>
          </div>
          <TrendChart :series="historySeries" :height="160" />
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
import PageHead from '../components/PageHead.vue'
import RingGauge from '../components/RingGauge.vue'
import StressShredder from '../components/StressShredder.vue'
import TrendChart from '../components/TrendChart.vue'
import MoodCheckIn from '../components/mental/MoodCheckIn.vue'
import MoodTrend from '../components/mental/MoodTrend.vue'
import ScaleRunner from '../components/mental/ScaleRunner.vue'
import SafetyNotice from '../components/mental/SafetyNotice.vue'
import { formatScaleDate, localDateKey, parseServerDate } from '../utils/date'
import { MOOD_LEVELS } from '../constants/copywriting'
import { useWellnessStore } from '../stores/wellness'

const wellness = useWellnessStore()
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

// 全局共享高危状态：任一页面触发后，整站不再因刷新失败而降级。
const seriousMode = computed(() => localCrisis.value || !!summary.value?.serious_mode || wellness.isDanger)
const crisisResources = computed(() =>
  localCrisisResources.value.length ? localCrisisResources.value : wellness.crisisResources
)
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

const MOOD_LABELS = Object.fromEntries(MOOD_LEVELS.map(item => [item.level, item.title]))
const SERIOUS_MOOD_LABELS = { 1: '很难受', 2: '有些低落', 3: '一般', 4: '尚可', 5: '稳定' }
const RISK_LABELS = {
  minimal: '无明显症状',
  mild: '轻度',
  moderate: '中度',
  moderately_severe: '中重度',
  severe: '重度'
}
const SCALE_NAMES = { phq9: 'PHQ-9', gad7: 'GAD-7' }
const SCALE_TITLES = { phq9: '情绪晴雨表', gad7: '焦虑自测' }

function moodLabel (score) {
  return (seriousMode.value ? SERIOUS_MOOD_LABELS : MOOD_LABELS)[score] || '已记录'
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

function scaleTitle (type) {
  return SCALE_TITLES[type] || scaleName(type)
}

function historyKey (item) {
  const parsed = parseServerDate(item?.created_at)
  return parsed ? localDateKey(parsed) : String(item?.created_at || '').slice(0, 10)
}

const historyDates = computed(() => {
  const keys = [...new Set(history.value.map(historyKey).filter(Boolean))]
  return keys.sort()
})

function historySeriesData (type) {
  return historyDates.value.map(date => {
    const match = history.value.find(item => item.scale_type === type && historyKey(item) === date)
    return { label: date.slice(5).replace('-', '/'), value: match ? match.score : null }
  })
}

const historySeries = computed(() => {
  if (!historyDates.value.length) return []
  return [
    { name: 'PHQ-9', color: 'var(--accent)', unit: '分', max: 27, data: historySeriesData('phq9') },
    { name: 'GAD-7', color: 'var(--teal)', unit: '分', max: 21, data: historySeriesData('gad7') }
  ]
})

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
  if (data?.serious_mode) {
    localCrisis.value = true
    wellness.markSerious()
  }
}

async function loadTrend () {
  const { data } = await api.getMentalTrend({ days: 7 })
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
    wellness.markSerious(localCrisisResources.value)
  }
  showToast(result?.crisis_flag ? '结果已保存，请先看看下面的支持信息' : '测评结果已保存')
  await Promise.allSettled([loadSummary(), loadHistory()])
}

onMounted(() => {
  wellness.hydrateLocal()
  wellness.load()
  loadAll()
})
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

.serious-copy > p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.7;
}

.crisis-lines {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.crisis-line {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 132px;
  padding: 8px 11px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  text-decoration: none;
}

.crisis-line span {
  color: var(--muted);
  font-size: 10px;
}

.crisis-line strong {
  font-family: var(--font-mono);
  font-size: 13px;
  letter-spacing: 0.01em;
}

.crisis-line--school {
  border-style: dashed;
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

.toolbox-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.toolbox-grid {
  display: grid;
  grid-template-columns: minmax(0, 5fr) minmax(0, 7fr);
  gap: 14px;
  align-items: stretch;
}

.toolbox-grid--single {
  grid-template-columns: minmax(0, 1fr);
}

.breathing-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 18px 20px;
}

.tool-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  color: var(--accent-strong);
}

.tool-card-head h3 {
  margin: 0;
  color: var(--fg);
  font-family: var(--font-display);
  font-size: 15px;
}

.tool-card-head p {
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 11px;
}

.toolbox-shredder {
  min-width: 0;
}

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

.scale-card h3 small {
  margin-left: 4px;
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 400;
  letter-spacing: 0.03em;
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

.history-trend-card {
  padding: 16px 18px 10px;
}

.history-trend-card .history-head {
  align-items: flex-start;
}

.history-trend-card .history-head > div:first-child {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.trend-legend {
  display: flex;
  gap: 10px;
  color: var(--muted);
  font-size: 10px;
}

.trend-legend span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.dot--accent { background: var(--accent); }
.dot--teal { background: var(--teal); }

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

  .toolbox-grid {
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
