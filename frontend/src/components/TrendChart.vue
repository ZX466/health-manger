<template>
  <figure class="trend-chart" role="img" :aria-label="ariaLabel">
    <svg :viewBox="`0 0 ${W} ${H}`" class="trend-chart__svg" aria-hidden="true" focusable="false">
      <g class="trend-chart__grid">
        <line v-for="gy in gridYs" :key="gy" :x1="padL" :x2="W - padR" :y1="gy" :y2="gy"/>
      </g>
      <path :d="areaPath" class="trend-chart__area"/>
      <line :x1="padL" :x2="W - padR" :y1="H - padB" :y2="H - padB" class="trend-chart__axis"/>
      <path :d="linePath" class="trend-chart__line"/>
      <g v-for="(pt, i) in points" :key="i">
        <circle class="trend-chart__dot" :cx="pt.x" :cy="pt.y" r="3.5"/>
        <text class="trend-chart__value" :x="pt.x" :y="pt.y - 14" text-anchor="middle">{{ fmt(pt.value) }}</text>
        <text class="trend-chart__label" :x="pt.x" :y="H - padB + 20" text-anchor="middle">{{ pt.label }}</text>
      </g>
    </svg>
  </figure>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data:   { type: Array, required: true }, // [{ label: '周一', value: 2200 }]
  width:  { type: Number, default: 560 },
  height: { type: Number, default: 190 },
  unit:   { type: String, default: '' },
})

const W = computed(() => props.width)
const H = computed(() => props.height)
const padL = 8, padR = 8, padT = 30, padB = 32

const maxVal = computed(() => {
  const m = Math.max(...props.data.map((d) => d.value))
  return m <= 0 ? 1 : m * 1.15 // 15% 上留白：最高点不贴顶
})

const points = computed(() => {
  const n = props.data.length
  const innerW = W.value - padL - padR
  const innerH = H.value - padT - padB
  const step = n > 1 ? innerW / (n - 1) : 0
  return props.data.map((d, i) => ({
    x: padL + (n > 1 ? i * step : innerW / 2),
    y: H.value - padB - (d.value / maxVal.value) * innerH,
    label: d.label,
    value: d.value,
  }))
})

const linePath = computed(() =>
  points.value.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
)
const areaPath = computed(() => {
  const pts = points.value
  if (!pts.length) return ''
  const last = pts[pts.length - 1]
  return `${linePath.value} L${last.x},${H.value - padB} L${pts[0].x},${H.value - padB} Z`
})

const gridYs = computed(() => {
  const top = padT, bottom = H.value - padB, count = 3
  return Array.from({ length: count + 1 }, (_, i) => bottom + ((top - bottom) / count) * i)
})

const fmt = (v) => `${v}${props.unit}`
const ariaLabel = computed(() =>
  `趋势图：` + props.data.map((d) => `${d.label} ${fmt(d.value)}`).join('，')
)
</script>

<style scoped>
.trend-chart { width: 100%; margin: 0; }
.trend-chart__svg { width: 100%; height: auto; display: block; overflow: visible; }
.trend-chart__grid line { stroke: var(--border); stroke-dasharray: 3 4; }
.trend-chart__axis { stroke: var(--border); }
.trend-chart__area { fill: rgba(26, 26, 46, 0.05); fill: color-mix(in oklch, var(--fg) 5%, transparent); }
.trend-chart__line { stroke: var(--fg); stroke-width: 1.6; }
.trend-chart__dot { fill: var(--surface); stroke: var(--fg); stroke-width: 1.6; }
.trend-chart__value { fill: var(--muted); font-size: 10px; font-variant-numeric: tabular-nums; }
.trend-chart__label { fill: var(--muted); font-size: 10px; letter-spacing: 0.02em; }
</style>
