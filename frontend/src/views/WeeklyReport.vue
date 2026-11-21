<template>
  <div class="weekly">
    <PageHead
      folio="06"
      eyebrow="WEEKLY / RECAP"
      title="健康周报"
      deck="把这一周的睡眠、饮食、运动和心情摊开看看。数据不够也没关系，能记多少算多少。"
    >
      <template #actions>
        <div class="week-nav" role="group" aria-label="切换周报日期">
          <button class="btn btn-ghost" type="button" @click="shiftWeek(-7)">上一周</button>
          <button
            class="btn btn-ghost"
            type="button"
            :disabled="!canGoNext"
            @click="shiftWeek(7)"
          >下一周</button>
        </div>
        <button
          v-if="report?.has_data"
          class="btn btn-primary copy-action"
          type="button"
          @click="copySummary"
        >
          <AppIcon :name="copied ? 'check' : 'copy'" :size="15" />
          {{ copied ? '已复制' : '复制小结' }}
        </button>
      </template>
    </PageHead>

    <div v-if="loading" class="weekly-skeleton" aria-busy="true" aria-label="周报加载中">
      <div class="card skeleton skeleton--hero"></div>
      <div class="skeleton-row">
        <div v-for="n in 4" :key="n" class="card skeleton skeleton--metric"></div>
      </div>
      <div class="card skeleton skeleton--body"></div>
    </div>

    <div v-else-if="error" class="card weekly-error" role="alert">
      <p>{{ error }}</p>
      <button class="btn btn-ghost btn-sm" type="button" @click="load">重试</button>
    </div>

    <template v-else-if="report">
      <section class="weekly-hero card">
        <div class="hero-copy">
          <p class="eyebrow">{{ rangeLabel }}</p>
          <h2>{{ heroTitle }}</h2>
          <p class="hero-summary">{{ report.summary_text }}</p>
          <div class="hero-tags">
            <span class="hero-tag">{{ report.recorded_days }} / 7 天有记录</span>
            <span v-if="report.warnings_danger" class="hero-tag hero-tag--warn">
              {{ report.warnings_danger }} 条危险级预警
            </span>
            <span v-if="report.top_stress_tags.length" class="hero-tag">
              压力：{{ report.top_stress_tags.join(' / ') }}
            </span>
          </div>
        </div>
        <div v-if="!report.crisis_flag" class="hero-score" :class="`hero-score--${scoreTone}`">
          <span class="micro">AVG SCORE</span>
          <strong>{{ scoreDisplay }}</strong>
          <small>{{ scoreChangeText }}</small>
        </div>
        <div v-else class="hero-care">
          <span class="hero-care-mark"><AppIcon name="heart" :size="20" /></span>
          <strong>先照顾自己</strong>
          <small>分数先放一边</small>
        </div>
      </section>

      <section v-if="report.crisis_flag" class="card safety-card" aria-labelledby="weekly-care">
        <div class="safety-mark"><AppIcon name="heart" :size="20" /></div>
        <div>
          <p class="eyebrow">CARE FIRST</p>
          <h2 id="weekly-care">这一周，先把自己照顾好</h2>
          <p>周报里出现了需要认真对待的心理信号。玩梗和数据都先放一边，愿意的话联系学校心理咨询中心；如有危机想法，请立即拨打 120 或 12356。</p>
          <div class="safety-lines">
            <a href="tel:120">120</a>
            <a href="tel:12356">12356</a>
            <router-link class="btn btn-ghost btn-sm" to="/mental">去心理空间</router-link>
          </div>
        </div>
      </section>

      <div v-if="!report.has_data" class="card empty-week">
        <div class="empty-week-mark"><AppIcon name="calendar" :size="26" /></div>
        <h2>这一周还是空白页</h2>
        <p>不用补作业。接下来从一顿饭、一次散步或一次睡前打卡开始，周报自己会长出来。</p>
        <div class="empty-week-actions">
          <router-link class="btn btn-primary" to="/health-record">记一条体检</router-link>
          <router-link class="btn btn-ghost" to="/diet-management">拍一餐</router-link>
          <router-link class="btn btn-ghost" to="/sport-management">记一次运动</router-link>
        </div>
      </div>

      <template v-else>
        <div class="metric-grid">
          <article v-for="metric in metrics" :key="metric.key" class="card metric-card">
            <div class="metric-head">
              <span class="metric-icon" :class="`metric-icon--${metric.tone}`">
                <AppIcon :name="metric.icon" :size="16" />
              </span>
              <span class="micro">{{ metric.label }}</span>
            </div>
            <p class="metric-value">
              {{ metric.value }}<small v-if="metric.unit">{{ metric.unit }}</small>
            </p>
            <p class="metric-note">{{ metric.note }}</p>
          </article>
        </div>

        <div class="weekly-grid">
          <section class="card daily-card" aria-labelledby="weekly-daily">
            <div class="panel-title-row">
              <div>
                <p class="eyebrow">DAY BY DAY</p>
                <h2 id="weekly-daily">每天发生了什么</h2>
              </div>
              <span class="panel-hint">睡眠 / 心情 / 摄入 / 运动</span>
            </div>

            <p class="mobile-swipe-hint">左右滑动查看摄入与运动 →</p>
            <div class="daily-scroll">
              <div class="daily-head" aria-hidden="true">
                <span>日期</span>
                <span>睡眠</span>
                <span>心情</span>
                <span>摄入</span>
                <span>运动</span>
              </div>
              <div class="daily-list">
                <div
                  v-for="day in report.daily"
                  :key="day.date"
                  class="daily-row"
                  :class="{ 'daily-row--empty': !day.has_data, 'daily-row--today': day.date === todayISO }"
                >
                  <span class="day-date">
                    {{ dayLabel(day.date) }}
                    <small v-if="day.date === todayISO">今天</small>
                  </span>
                  <span class="day-cell day-cell--sleep">
                    <i
                      v-if="day.sleep_hours != null"
                      class="sleep-bar"
                      :class="{ 'sleep-bar--low': day.sleep_hours < 7 }"
                      :style="{ width: sleepWidth(day.sleep_hours) }"
                    />
                    <b>{{ day.sleep_hours != null ? `${day.sleep_hours}h` : '—' }}</b>
                  </span>
                  <span class="day-cell">
                    <b>{{ day.mood_score != null ? `${day.mood_score}/5` : '—' }}</b>
                  </span>
                  <span class="day-cell">
                    <b>{{ day.calories_in ? `${Math.round(day.calories_in)} kcal` : '—' }}</b>
                  </span>
                  <span class="day-cell">
                    <b>{{ day.sport_minutes ? `${day.sport_minutes} min` : '—' }}</b>
                  </span>
                </div>
              </div>
            </div>
            <p class="panel-foot">
              睡眠优先取体检记录，缺失时用心理打卡兜底；摄入与运动按自然日汇总。
            </p>
          </section>

          <aside class="weekly-side">
            <section class="card insights-card" aria-labelledby="weekly-insights">
              <div class="panel-title-row">
                <h2 id="weekly-insights">这一周的观察</h2>
                <span class="panel-hint">{{ report.insights.length }} 条</span>
              </div>
              <ul class="insight-list">
                <li
                  v-for="item in report.insights"
                  :key="item.title"
                  class="insight"
                  :class="`insight--${item.kind}`"
                >
                  <span class="insight-dot" aria-hidden="true" />
                  <div>
                    <strong>{{ item.title }}</strong>
                    <p>{{ item.text }}</p>
                  </div>
                </li>
              </ul>
            </section>

            <section class="card suggestion-card" aria-labelledby="weekly-next">
              <p class="eyebrow">NEXT WEEK</p>
              <h2 id="weekly-next">接下来可以试试</h2>
              <ol class="suggestion-list">
                <li v-for="(item, index) in report.suggestions" :key="item">
                  <span>{{ String(index + 1).padStart(2, '0') }}</span>
                  <p>{{ item }}</p>
                </li>
              </ol>
            </section>
          </aside>
        </div>

        <section v-if="!report.crisis_flag" class="card ai-card" aria-labelledby="weekly-ai">
          <div class="ai-head">
            <span class="ai-mark"><AppIcon name="sparkles" :size="18" /></span>
            <div>
              <p class="eyebrow">AI RECAP</p>
              <h2 id="weekly-ai">让搭子把这一周读给你听</h2>
            </div>
            <button
              class="btn btn-primary"
              type="button"
              :disabled="aiLoading"
              @click="generateAI"
            >
              {{ aiLoading ? '正在读…' : aiText ? '重新解读' : '生成 AI 解读' }}
            </button>
          </div>
          <p v-if="aiError" class="ai-error" role="alert">{{ aiError }}</p>
          <div v-if="aiText" class="ai-text">{{ aiText }}</div>
          <p v-else class="ai-placeholder">
            只把上面的真实数据交给 AI，不补造缺失项。先肯定做得好的地方，再给两条接下来能执行的小建议。
          </p>
          <p class="fineprint">AI 解读仅作生活方式参考，不构成诊断或治疗建议；数据不足时不会生成。</p>
        </section>
      </template>
    </template>

    <div class="toast" :class="{ show: toastVisible }" role="status" aria-live="polite">
      <AppIcon name="check" :size="16" :stroke="2.2" />
      <span>{{ toastText }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api'
import AppIcon from '../components/AppIcon.vue'
import PageHead from '../components/PageHead.vue'

function localISO (value) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function shiftISO (iso, days) {
  const [year, month, day] = iso.split('-').map(Number)
  const value = new Date(year, month - 1, day)
  value.setDate(value.getDate() + days)
  return localISO(value)
}

const todayISO = localISO(new Date())
const endDate = ref(todayISO)
const report = ref(null)
const loading = ref(true)
const error = ref('')
const aiText = ref('')
const aiLoading = ref(false)
const aiError = ref('')
const copied = ref(false)
const toastVisible = ref(false)
const toastText = ref('')
let copyTimer = null
let toastTimer = null
let requestSeq = 0

const canGoNext = computed(() => endDate.value < todayISO)

const rangeLabel = computed(() => {
  if (!report.value) return ''
  return `${formatDay(report.value.start_date)} – ${formatDay(report.value.end_date)}`
})

const scoreDisplay = computed(() => {
  const value = report.value?.score_avg
  return value == null ? '—' : Math.round(value)
})

const scoreTone = computed(() => {
  const value = report.value?.score_avg
  if (value == null) return 'none'
  if (value >= 85) return 'good'
  if (value >= 70) return 'ok'
  return 'watch'
})

const scoreChangeText = computed(() => {
  const change = report.value?.score_change
  if (change == null) return '这一周数据还不够看变化'
  if (change === 0) return '与这一周首条记录持平'
  return `${change > 0 ? '↑' : '↓'} 较这一周首条 ${Math.abs(change)} 分`
})

const heroTitle = computed(() => {
  if (!report.value?.has_data) return '这一周，还没有留下记录'
  if (report.value.crisis_flag) return '这一周，先把状态放稳'
  const score = report.value.score_avg
  if (score == null) return '这一周，慢慢来也算数'
  if (score >= 85) return '这一周，状态在线'
  if (score >= 70) return '这一周，基本稳住了'
  return '这一周，先照顾好睡眠'
})

const metrics = computed(() => {
  const data = report.value
  if (!data) return []
  return [
    {
      key: 'sleep',
      label: '平均睡眠',
      icon: 'moon',
      value: data.sleep_avg == null ? '—' : data.sleep_avg,
      unit: data.sleep_avg == null ? '' : 'h',
      note: data.sleep_days >= 4
        ? `${data.sleep_days} 天有记录 · 睡眠债 ${data.sleep_debt}h`
        : `${data.sleep_days} 天有记录，满 4 天才算均值`,
      tone: data.sleep_avg == null ? 'muted' : data.sleep_avg >= 7 ? 'good' : 'watch'
    },
    {
      key: 'mood',
      label: '心情均值',
      icon: 'heart',
      value: data.mood_avg == null ? '—' : data.mood_avg,
      unit: data.mood_avg == null ? '' : '/ 5',
      note: `${data.mood_days} 天打卡`,
      tone: data.mood_avg == null ? 'muted' : data.mood_avg >= 4 ? 'good' : data.mood_avg < 3 ? 'watch' : 'ok'
    },
    {
      key: 'sport',
      label: '运动时长',
      icon: 'activity',
      value: data.sport_minutes_total,
      unit: 'min',
      note: `${data.sport_days} 天运动 · 目标 150 分钟`,
      tone: data.sport_minutes_total >= 150 ? 'good' : data.sport_minutes_total ? 'ok' : 'watch'
    },
    {
      key: 'food',
      label: '有记录日均摄入',
      icon: 'meal',
      value: data.calories_in_avg == null ? '—' : Math.round(data.calories_in_avg),
      unit: data.calories_in_avg == null ? '' : 'kcal',
      note: `${data.food_days} 天有饮食记录`,
      tone: data.food_days ? 'ok' : 'muted'
    },
    {
      key: 'record',
      label: '记录天数',
      icon: 'calendar',
      value: data.recorded_days,
      unit: '/ 7 天',
      note: data.recorded_days >= 5 ? '这周很稳定' : '能记多少算多少',
      tone: data.recorded_days >= 5 ? 'good' : data.recorded_days ? 'ok' : 'muted'
    }
  ]
})

function formatDay (iso) {
  if (!iso) return ''
  const [, month, day] = iso.split('-').map(Number)
  return `${month} 月 ${day} 日`
}

function dayLabel (iso) {
  if (!iso) return ''
  const [, month, day] = iso.split('-').map(Number)
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  const [year] = iso.split('-').map(Number)
  const weekday = weekdays[new Date(year, month - 1, day).getDay()]
  return `${month}.${String(day).padStart(2, '0')} 周${weekday}`
}

function sleepWidth (hours) {
  const ratio = Math.max(0, Math.min(100, (Number(hours) / 10) * 100))
  return `${ratio}%`
}

function showToast (message) {
  toastText.value = message
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 2600)
}

async function load () {
  const seq = ++requestSeq
  loading.value = true
  error.value = ''
  aiLoading.value = false
  aiText.value = ''
  aiError.value = ''
  try {
    const response = await api.getWeeklyReport({ end_date: endDate.value })
    if (seq !== requestSeq) return
    report.value = response.data
  } catch (err) {
    if (seq !== requestSeq) return
    report.value = null
    error.value = err?.response?.data?.detail || '周报暂时没加载出来，稍后再试。'
  } finally {
    if (seq === requestSeq) loading.value = false
  }
}

function shiftWeek (days) {
  if (days > 0 && !canGoNext.value) return
  endDate.value = shiftISO(endDate.value, days)
  load()
}

async function copySummary () {
  const text = report.value?.summary_text
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
  } catch (e) {
    const area = document.createElement('textarea')
    area.value = text
    area.style.position = 'fixed'
    area.style.opacity = '0'
    document.body.appendChild(area)
    area.select()
    document.execCommand('copy')
    area.remove()
  }
  copied.value = true
  clearTimeout(copyTimer)
  copyTimer = setTimeout(() => { copied.value = false }, 2400)
  showToast('小结已复制')
}

async function generateAI () {
  if (aiLoading.value) return
  const seq = requestSeq
  const week = endDate.value
  aiLoading.value = true
  aiError.value = ''
  try {
    const response = await api.generateWeeklyReportAI({ end_date: week })
    if (seq !== requestSeq || week !== endDate.value) return
    aiText.value = response.data.content
  } catch (err) {
    if (seq !== requestSeq || week !== endDate.value) return
    aiError.value = err?.response?.data?.detail || 'AI 解读暂时没生成成功，稍后再试。'
  } finally {
    if (seq === requestSeq) aiLoading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.weekly {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.week-nav {
  display: inline-flex;
  gap: 8px;
}

.weekly-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 28px;
  padding: 28px;
  background:
    radial-gradient(circle at 92% 10%, var(--accent-soft) 0, transparent 36%),
    var(--surface);
}

.hero-copy h2 {
  margin: 4px 0 8px;
  font-family: var(--font-display);
  font-size: clamp(24px, 3vw, 34px);
  letter-spacing: -0.04em;
}

.hero-summary {
  max-width: 680px;
  margin: 0;
  color: var(--muted);
  font-size: 15px;
  line-height: 1.8;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.hero-tag {
  padding: 4px 10px;
  border: var(--border-hairline);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 12px;
}

.hero-tag--warn {
  border-color: color-mix(in oklch, var(--warn) 24%, var(--border));
  background: var(--warn-soft);
  color: var(--warn);
}

.hero-score {
  display: grid;
  justify-items: center;
  min-width: 148px;
  padding: 20px 18px;
  border: var(--border-hairline);
  border-radius: var(--radius-lg);
  background: var(--bg);
}

.hero-score strong {
  font-family: var(--font-display);
  font-size: 54px;
  line-height: 1;
  letter-spacing: -0.06em;
  font-variant-numeric: tabular-nums;
}

.hero-score .micro {
  white-space: nowrap;
}

.hero-score small {
  max-width: 150px;
  margin-top: 8px;
  color: var(--muted);
  font-size: 12px;
  text-align: center;
}

.hero-care {
  display: grid;
  justify-items: center;
  gap: 6px;
  min-width: 148px;
  padding: 20px 18px;
  border: 1px solid color-mix(in oklch, var(--danger) 22%, var(--border));
  border-radius: var(--radius-lg);
  background: var(--danger-soft);
  text-align: center;
}

.hero-care-mark {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--surface);
  color: var(--danger);
}

.hero-care strong {
  font-size: 16px;
  color: var(--danger);
}

.hero-care small {
  color: var(--muted);
  font-size: 12px;
}

.hero-score--good strong { color: var(--success); }
.hero-score--ok strong { color: var(--accent-strong); }
.hero-score--watch strong { color: var(--warn); }
.hero-score--none strong { color: var(--muted); }

.safety-card {
  display: flex;
  gap: 16px;
  border-color: color-mix(in oklch, var(--danger) 22%, var(--border));
  background: var(--danger-soft);
}

.safety-mark {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--surface);
  color: var(--danger);
}

.safety-card h2 {
  margin: 2px 0 6px;
  font-size: 20px;
}

.safety-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.safety-lines {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 12px;
}

.safety-lines a {
  min-height: 36px;
  padding: 6px 14px;
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: var(--surface);
  color: var(--danger);
  font-weight: 600;
  text-decoration: none;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.metric-head {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
}

.metric-icon {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 9px;
  background: var(--bg);
  color: var(--muted);
}

.metric-icon--good { background: var(--success-soft); color: var(--success); }
.metric-icon--watch { background: var(--warn-soft); color: var(--warn); }
.metric-icon--ok { background: var(--accent-soft); color: var(--accent-strong); }

.metric-value {
  margin: 0;
  font-family: var(--font-display);
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.04em;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}

.metric-value small {
  margin-left: 4px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0;
}

.metric-note {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.weekly-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.panel-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.panel-title-row h2,
.insights-card h2,
.suggestion-card h2,
.ai-card h2 {
  margin: 0;
  font-size: 19px;
  letter-spacing: -0.02em;
}

.panel-hint {
  color: var(--muted);
  font-size: 12px;
  white-space: nowrap;
}

.daily-scroll {
  overflow-x: auto;
}

.mobile-swipe-hint {
  display: none;
  margin: 0 0 8px;
  color: var(--muted);
  font-size: 11px;
}

.daily-head,
.daily-row {
  display: grid;
  grid-template-columns: minmax(96px, 1.2fr) minmax(96px, 1.1fr) 72px minmax(88px, 1fr) 84px;
  align-items: center;
  gap: 10px;
}

.daily-head {
  padding: 0 10px 8px;
  border-bottom: var(--border-hairline);
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.06em;
}

.daily-row {
  padding: 11px 10px;
  border-bottom: 1px solid color-mix(in oklch, var(--border) 65%, transparent);
  font-size: 13px;
}

.daily-row:last-child { border-bottom: 0; }
.daily-row--empty { color: var(--muted); }
.daily-row--today { background: var(--accent-soft); border-radius: var(--radius-sm); }

.day-date {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-variant-numeric: tabular-nums;
}

.day-date small {
  color: var(--accent-strong);
  font-size: 10px;
}

.day-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.day-cell b {
  font-weight: 550;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.day-cell--sleep {
  position: relative;
  padding: 4px 6px;
  border-radius: 6px;
  background: var(--bg);
  overflow: hidden;
}

.sleep-bar {
  position: absolute;
  inset: 0 auto 0 0;
  background: color-mix(in oklch, var(--success) 20%, transparent);
}

.sleep-bar--low { background: color-mix(in oklch, var(--warn) 22%, transparent); }

.day-cell--sleep b { position: relative; }

.panel-foot {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.6;
}

.weekly-side {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.insight-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.insight {
  display: flex;
  gap: 10px;
  padding: 11px 12px;
  border-radius: var(--radius-sm);
  background: var(--bg);
}

.insight-dot {
  width: 8px;
  height: 8px;
  margin-top: 5px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--muted);
}

.insight strong { font-size: 13px; }
.insight p { margin: 3px 0 0; color: var(--muted); font-size: 12px; line-height: 1.6; }

.insight--positive { background: var(--success-soft); }
.insight--positive .insight-dot { background: var(--success); }
.insight--attention { background: var(--warn-soft); }
.insight--attention .insight-dot { background: var(--warn); }
.insight--safety { background: var(--danger-soft); }
.insight--safety .insight-dot { background: var(--danger); }
.insight--info .insight-dot { background: var(--accent); }

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.suggestion-list li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.suggestion-list span {
  color: var(--accent-strong);
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.8;
}

.suggestion-list p {
  margin: 0;
  color: var(--fg);
  font-size: 13px;
  line-height: 1.65;
}

.ai-card {
  background:
    linear-gradient(120deg, var(--accent-soft) 0%, transparent 55%),
    var(--surface);
}

.ai-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-head > div { flex: 1; min-width: 0; }

.ai-mark {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border-radius: 12px;
  background: var(--accent);
  color: var(--surface);
}

.ai-placeholder,
.ai-text {
  margin: 16px 0 0;
  padding: 16px 18px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: color-mix(in oklch, var(--surface) 82%, transparent);
  font-size: 14px;
  line-height: 1.85;
  white-space: pre-wrap;
}

.ai-placeholder { color: var(--muted); }

.ai-error {
  margin: 12px 0 0;
  color: var(--danger);
  font-size: 13px;
}

.fineprint {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.6;
}

.empty-week {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 40px 24px;
  text-align: center;
}

.empty-week-mark {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.empty-week h2 { margin: 4px 0 0; font-size: 22px; }
.empty-week p { max-width: 540px; margin: 0; color: var(--muted); line-height: 1.7; }

.empty-week-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-top: 10px;
}

.weekly-error {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  color: var(--muted);
}

.weekly-error p { margin: 0; }

.weekly-skeleton {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.skeleton {
  background: linear-gradient(90deg, var(--bg) 20%, var(--surface) 45%, var(--bg) 70%);
  background-size: 220% 100%;
  animation: weekly-shimmer 1.5s linear infinite;
  border-radius: var(--radius-md);
}

.skeleton--hero { height: 170px; }
.skeleton-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.skeleton--metric { height: 118px; }
.skeleton--body { height: 340px; }

@keyframes weekly-shimmer {
  from { background-position: 120% 0; }
  to { background-position: -120% 0; }
}

.toast {
  position: fixed;
  left: 50%;
  bottom: 28px;
  z-index: 80;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: var(--border-hairline);
  border-radius: 999px;
  background: var(--surface);
  box-shadow: var(--shadow-pop);
  color: var(--fg);
  font-size: 13px;
  opacity: 0;
  transform: translate(-50%, 10px);
  pointer-events: none;
  transition: opacity var(--duration-base) var(--ease-out), transform var(--duration-base) var(--ease-out);
}

.toast.show { opacity: 1; transform: translate(-50%, 0); }

@media (max-width: 1100px) {
  .metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .weekly-grid { grid-template-columns: minmax(0, 1fr); }
}

@media (max-width: 760px) {
  .weekly-hero { grid-template-columns: minmax(0, 1fr); padding: 22px; }
  .hero-score { display: flex; justify-self: start; align-items: center; gap: 12px; }
  .hero-score strong { font-size: 42px; }
  .hero-score small { margin-top: 0; text-align: left; }
  .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .mobile-swipe-hint { display: block; }
  .daily-head, .daily-row { min-width: 540px; }
  .ai-head { flex-wrap: wrap; }
  .ai-head .btn { width: 100%; }
}

@media (max-width: 520px) {
  .week-nav { width: 100%; }
  .week-nav .btn { flex: 1; }
  .copy-action { width: 100%; }
  .safety-card { flex-direction: column; }
  .skeleton-row { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 360px) {
  .metric-grid { grid-template-columns: minmax(0, 1fr); }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton { animation: none; }
  .toast { transition: none; }
}
</style>
