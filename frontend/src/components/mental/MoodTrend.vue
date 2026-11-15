<template>
  <section class="card mood-trend">
    <div class="trend-head">
      <div>
        <p class="eyebrow">Last 14 days</p>
        <h2>心情和睡眠</h2>
      </div>
      <span class="trend-legend">
        <span><i class="legend-bar"></i>心情</span>
        <span><i class="legend-line"></i>睡眠</span>
      </span>
    </div>

    <div class="trend-stats">
      <div class="stat">
        <span class="stat-label">平均心情</span>
        <strong>{{ moodAvgText }}</strong>
        <span class="stat-sub">{{ moodAvgLabel }}</span>
      </div>
      <div class="stat">
        <span class="stat-label">平均睡眠</span>
        <strong>{{ sleepAvgText }}</strong>
        <span class="stat-sub">小时 / 晚</span>
      </div>
      <div class="stat">
        <span class="stat-label">睡眠欠账</span>
        <strong>{{ sleepDebtText }}</strong>
        <span class="stat-sub">小时 / 7 天</span>
      </div>
    </div>

    <div v-if="hasData" class="chart-wrap" role="img" :aria-label="chartAriaLabel">
      <div class="chart-grid" aria-hidden="true">
        <span v-for="line in 3" :key="line" class="grid-line"></span>
      </div>

      <div class="bars">
        <div v-for="(date, index) in dates" :key="date" class="bar-col">
          <div class="bar-track">
            <span
              v-if="moodAt(index) != null"
              class="bar"
              :style="{ height: `${moodHeight(moodAt(index))}%` }"
              :title="`${date} 心情 ${moodAt(index)}/5`"
            ></span>
          </div>
          <span v-if="showLabel(index)" class="bar-label">{{ shortDate(date) }}</span>
        </div>
      </div>

      <svg
        v-if="hasSleep"
        class="sleep-line"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <polyline
          v-for="(segment, index) in sleepSegments"
          :key="`sleep-segment-${index}`"
          :points="segment"
        />
        <circle
          v-for="point in sleepDots"
          :key="point.key"
          :cx="point.x"
          :cy="point.y"
          r="1.5"
        />
      </svg>
    </div>

    <div v-else class="trend-empty">
      <p>还没有足够的记录。</p>
      <span>先从今天的一次心情打卡开始，趋势会慢慢长出来。</span>
    </div>

    <p v-if="summary && summary.sleep_debt_7d >= 5" class="trend-note">
      这周睡眠欠账有点多，今晚可以试着早半小时放下手机。
    </p>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** GET /mental/trend?days=7 的返回 */
  trend: { type: Object, default: () => ({ dates: [], mood_score: [], sleep_hours: [] }) },
  /** GET /mental/summary 的返回 */
  summary: { type: Object, default: null }
})

const dates = computed(() => Array.isArray(props.trend?.dates) ? props.trend.dates : [])
const moodSeries = computed(() => Array.isArray(props.trend?.mood_score) ? props.trend.mood_score : [])
const sleepSeries = computed(() => Array.isArray(props.trend?.sleep_hours) ? props.trend.sleep_hours : [])

const hasData = computed(() =>
  dates.value.some((_, i) => moodAt(i) != null || sleepAt(i) != null)
)
const hasSleep = computed(() => dates.value.some((_, i) => sleepAt(i) != null))

function moodAt (index) {
  const value = moodSeries.value[index]
  return value == null || Number.isNaN(Number(value)) ? null : Number(value)
}

function sleepAt (index) {
  const value = sleepSeries.value[index]
  return value == null || Number.isNaN(Number(value)) ? null : Number(value)
}

function moodHeight (score) {
  const clamped = Math.max(1, Math.min(5, score))
  return 8 + ((clamped - 1) / 4) * 92
}

function sleepPoint (index) {
  const value = sleepAt(index)
  if (value == null) return null
  return {
    x: dates.value.length <= 1 ? 50 : (index / (dates.value.length - 1)) * 100,
    y: 100 - (Math.max(0, Math.min(12, value)) / 12) * 100
  }
}

// 缺失日断开折线，避免把两段不相邻的睡眠记录连成一条假趋势。
const sleepSegments = computed(() => {
  const segments = []
  let current = []
  dates.value.forEach((_, index) => {
    const point = sleepPoint(index)
    if (!point) {
      if (current.length) segments.push(current.join(' '))
      current = []
      return
    }
    current.push(`${point.x},${point.y}`)
  })
  if (current.length) segments.push(current.join(' '))
  return segments
})

const sleepDots = computed(() => {
  const dots = []
  dates.value.forEach((date, index) => {
    const point = sleepPoint(index)
    if (!point) return
    dots.push({ key: `${date}-${index}`, ...point })
  })
  return dots
})

const labelStep = computed(() => Math.max(1, Math.ceil(dates.value.length / 6)))
function showLabel (index) {
  return index % labelStep.value === 0 || index === dates.value.length - 1
}
function shortDate (value) {
  const text = String(value || '')
  return text.length >= 10 ? text.slice(5) : text
}

const moodValues = computed(() =>
  dates.value.map((_, index) => moodAt(index)).filter(value => value != null)
)

const moodAvgText = computed(() => {
  if (!moodValues.value.length) return '—'
  const avg = moodValues.value.reduce((sum, value) => sum + value, 0) / moodValues.value.length
  return avg.toFixed(1)
})
const moodAvgLabel = computed(() => {
  if (!moodValues.value.length) return '本周还没有记录'
  const avg = moodValues.value.reduce((sum, value) => sum + value, 0) / moodValues.value.length
  const rounded = Math.max(1, Math.min(5, Math.round(avg)))
  return { 1: '很难受', 2: '有点丧', 3: '还行', 4: '不错', 5: '很好' }[rounded]
})
function formatSummaryNumber (value) {
  if (value == null) return '—'
  const number = Number(value)
  return Number.isFinite(number) ? number.toFixed(1) : '—'
}

// 后端在不足 4 天时返回 null；此时显示“—”，不要把少量样本算成 7 天均值/欠账。
const sleepAvgText = computed(() => formatSummaryNumber(props.summary?.sleep_avg_7d))
const sleepDebtText = computed(() => formatSummaryNumber(props.summary?.sleep_debt_7d))

const chartAriaLabel = computed(() => {
  const count = dates.value.length
  return `最近 ${count} 天的心情柱状图与睡眠折线图`
})
</script>

<style scoped>
.mood-trend {
  padding: 22px;
  display: flex;
  flex-direction: column;
}

.trend-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.trend-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 18px;
  letter-spacing: -0.01em;
}

.trend-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--muted);
  font-size: 11px;
  white-space: nowrap;
}

.trend-legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.legend-bar,
.legend-line {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
  background: var(--accent);
}

.legend-line {
  width: 12px;
  height: 2px;
  border-radius: 1px;
  background: var(--teal);
}

.trend-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 16px 0 12px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 9px 10px;
  border-radius: var(--radius-sm);
  background: var(--bg);
}

.stat-label {
  color: var(--muted);
  font-size: 11px;
}

.stat strong {
  font-family: var(--font-mono);
  font-size: 18px;
  letter-spacing: -0.02em;
}

.stat-sub {
  color: var(--muted);
  font-size: 10px;
}

.chart-wrap {
  position: relative;
  display: flex;
  flex: 1;
  min-height: 148px;
  padding-top: 6px;
}

.chart-grid {
  position: absolute;
  inset: 6px 0 22px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  pointer-events: none;
}

.grid-line {
  border-top: 1px dashed var(--border);
}

.bars {
  display: flex;
  align-items: stretch;
  gap: 6px;
  width: 100%;
  position: relative;
  z-index: 1;
}

.bar-col {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.bar-track {
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  height: 120px;
}

.bar {
  display: block;
  width: min(18px, 70%);
  min-height: 4px;
  border-radius: 4px 4px 2px 2px;
  background: var(--accent);
  opacity: 0.78;
  transition: opacity var(--duration-fast) var(--ease-out);
}

.bar:hover {
  opacity: 1;
}

.bar-label {
  margin-top: 6px;
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 9px;
  text-align: center;
  white-space: nowrap;
}

.sleep-line {
  position: absolute;
  inset: 6px 0 22px;
  width: 100%;
  height: calc(100% - 28px);
  pointer-events: none;
  z-index: 2;
  overflow: visible;
}

.sleep-line polyline {
  fill: none;
  stroke: var(--teal);
  stroke-width: 1.5;
  vector-effect: non-scaling-stroke;
  stroke-linejoin: round;
  stroke-linecap: round;
}

.sleep-line circle {
  fill: var(--teal);
  vector-effect: non-scaling-stroke;
}

.trend-empty {
  display: flex;
  flex: 1;
  flex-direction: column;
  justify-content: center;
  min-height: 148px;
  padding: 16px;
  border-radius: var(--radius-sm);
  background: var(--bg);
  text-align: center;
}

.trend-empty p {
  margin: 0 0 4px;
  font-weight: 600;
  font-size: 14px;
}

.trend-empty span {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

.trend-note {
  margin: 12px 0 0;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--warn-soft);
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 480px) {
  .trend-stats {
    gap: 5px;
  }

  .stat {
    padding: 8px 7px;
  }

  .stat strong {
    font-size: 16px;
  }

  .bars {
    gap: 3px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .bar {
    transition: none;
  }
}
</style>
