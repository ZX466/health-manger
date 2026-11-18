<template>
  <figure class="trend-chart" role="img" :aria-label="ariaLabel">
    <svg :viewBox="`0 0 ${W} ${H}`" class="trend-chart__svg" aria-hidden="true" focusable="false">
      <g class="trend-chart__grid">
        <line v-for="gy in gridYs" :key="gy" :x1="padL" :x2="W - padR" :y1="gy" :y2="gy"/>
      </g>
      <line :x1="padL" :x2="W - padR" :y1="H - padB" :y2="H - padB" class="trend-chart__axis"/>

      <template v-if="isMulti">
        <g v-for="(line, index) in multiLines" :key="index">
          <path
            v-for="(segment, segIndex) in line.segments"
            :key="segIndex"
            :d="segment"
            class="trend-chart__line"
            :style="{ stroke: line.color }"
          />
          <circle
            v-for="(pt, ptIndex) in line.points"
            :key="`dot-${ptIndex}`"
            class="trend-chart__dot"
            :cx="pt.x" :cy="pt.y" r="3.2"
            :style="{ stroke: line.color }"
          />
        </g>
      </template>

      <template v-else>
        <path :d="areaPath" class="trend-chart__area"/>
        <path :d="linePath" class="trend-chart__line"/>
        <g v-for="(pt, i) in points" :key="i">
          <circle class="trend-chart__dot" :cx="pt.x" :cy="pt.y" r="3.5"/>
          <text class="trend-chart__value" :x="pt.x" :y="pt.y - 14" text-anchor="middle">{{ fmt(pt.value) }}</text>
        </g>
      </template>

      <g v-for="(label, i) in labels" :key="`label-${i}`">
        <text class="trend-chart__label" :x="labelX(i)" :y="H - padB + 20" text-anchor="middle">{{ label }}</text>
      </g>
    </svg>
  </figure>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:   { type: Array, default: () => [] }, // [{ label: '周一', value: 2200 }]
  series: { type: Array, default: () => [] }, // [{ name, color, unit, max, data: [{label,value}] }]
  width:  { type: Number, default: 560 },
  height: { type: Number, default: 190 },
  unit:   { type: String, default: '' },
})

const W = computed(() => props.width)
const H = computed(() => props.height)
const padL = 8, padR = 8, padT = 30, padB = 32

const isMulti = computed(() => Array.isArray(props.series) && props.series.length > 1)
const activeSeries = computed(() => isMulti.value
  ? props.series
  : [{ name: '', color: 'var(--fg)', unit: props.unit, data: props.data }]
)

const labels = computed(() => {
  const first = activeSeries.value[0]?.data || []
  return first.map(item => item.label)
})

const maxVal = computed(() => {
  if (isMulti.value) return null
  const m = Math.max(...(props.data || []).map((d) => Number(d.value) || 0), 0)
  return m <= 0 ? 1 : m * 1.15
})

function seriesMax (line) {
  if (line.max) return Number(line.max)
  const values = (line.data || []).map(item => Number(item.value)).filter(Number.isFinite)
  const m = Math.max(...values, 0)
  return m <= 0 ? 1 : m * 1.12
}

function buildPoints (line) {
  const n = (line.data || []).length
  const innerW = W.value - padL - padR
  const innerH = H.value - padT - padB
  const step = n > 1 ? innerW / (n - 1) : 0
  const max = isMulti.value ? seriesMax(line) : maxVal.value
  return (line.data || []).map((d, i) => {
    const value = Number(d.value)
    const valid = Number.isFinite(value)
    return {
      x: padL + (n > 1 ? i * step : innerW / 2),
      y: valid ? H.value - padB - (value / max) * innerH : null,
      label: d.label,
      value: valid ? value : null,
    }
  })
}

const points = computed(() => buildPoints(activeSeries.value[0] || { data: [] }))

const linePath = computed(() => {
  const valid = points.value.filter(p => p.y != null)
  return valid.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
})

const areaPath = computed(() => {
  const valid = points.value.filter(p => p.y != null)
  if (!valid.length) return ''
  const last = valid[valid.length - 1]
  return `${linePath.value} L${last.x},${H.value - padB} L${valid[0].x},${H.value - padB} Z`
})

const multiLines = computed(() => activeSeries.value.map(line => {
  const pts = buildPoints(line)
  const segments = []
  let current = []
  pts.forEach(point => {
    if (point.y == null) {
      if (current.length) segments.push(current.join(' '))
      current = []
      return
    }
    current.push(`${current.length === 0 ? 'M' : 'L'}${point.x},${point.y}`)
  })
  if (current.length) segments.push(current.join(' '))
  return {
    color: line.color || 'var(--fg)',
    points: pts.filter(point => point.y != null),
    segments
  }
}))

const gridYs = computed(() => {
  const top = padT, bottom = H.value - padB, count = 3
  return Array.from({ length: count + 1 }, (_, i) => bottom + ((top - bottom) / count) * i)
})

function labelX (index) {
  const n = Math.max(labels.value.length, 1)
  const innerW = W.value - padL - padR
  return n > 1 ? padL + (index / (n - 1)) * innerW : padL + innerW / 2
}

const fmt = (v) => `${v}${props.unit}`

const ariaLabel = computed(() => {
  const lines = activeSeries.value.map(line => {
    const rows = (line.data || []).map(item => `${item.label} ${item.value}${line.unit || ''}`)
    return `${line.name ? line.name + '：' : ''}${rows.join('，')}`
  })
  return `趋势图：${lines.join('；')}`
})
</script>

<style scoped>
.trend-chart { width: 100%; margin: 0; }
.trend-chart__svg { width: 100%; height: auto; display: block; overflow: visible; }
.trend-chart__grid line { stroke: var(--border); stroke-dasharray: 3 4; }
.trend-chart__axis { stroke: var(--border); }
.trend-chart__area { fill: color-mix(in oklch, var(--fg) 5%, transparent); }
.trend-chart__line { fill: none; stroke: var(--fg); stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.trend-chart__dot { fill: var(--surface); stroke: var(--fg); stroke-width: 1.8; }
.trend-chart__value { fill: var(--muted); font-size: 10px; font-variant-numeric: tabular-nums; }
.trend-chart__label { fill: var(--muted); font-size: 10px; letter-spacing: 0.02em; }
</style>
