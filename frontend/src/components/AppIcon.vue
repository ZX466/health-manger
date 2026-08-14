<template>
  <svg
    :width="size" :height="size" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" :stroke-width="stroke"
    stroke-linecap="round" stroke-linejoin="round"
    :role="label ? 'img' : undefined"
    :aria-label="label || undefined"
    :aria-hidden="label ? undefined : 'true'"
    focusable="false"
  >
    <path v-for="(d, i) in paths" :key="i" :d="d" />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 20 },
  stroke: { type: [Number, String], default: 1.7 },
  label: { type: String, default: '' },
})

const PATHS = {
  home:    ['M3 10.5 12 3l9 7.5', 'M5 9.5V21h14V9.5', 'M9.5 21v-6h5v6'],
  record:  ['M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2', 'M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2', 'M9 12h6', 'M9 16h6'],
  diet:    ['M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2', 'M7 2v20', 'M21 15V2a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3zm0 0v7'],
  sport:   ['M22 12h-4l-3 9L9 3l-3 9H2'],
  ai:      ['M12 3l1.9 5.8a2 2 0 0 0 1.3 1.3L21 12l-5.8 1.9a2 2 0 0 0-1.3 1.3L12 21l-1.9-5.8a2 2 0 0 0-1.3-1.3L3 12l5.8-1.9a2 2 0 0 0 1.3-1.3z', 'M17.5 4.5v3', 'M19 6h-3'],
  tongue:  ['M3 7V5a2 2 0 0 1 2-2h2', 'M17 3h2a2 2 0 0 1 2 2v2', 'M21 17v2a2 2 0 0 1-2 2h-2', 'M7 21H5a2 2 0 0 1-2-2v-2', 'M8 14s1.5 2 4 2 4-2 4-2', 'M9 9h.01', 'M15 9h.01'],
  alert:   ['M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z', 'M12 9v4', 'M12 17h.01'],
  check:   ['M12 22a10 10 0 1 1 0-20 10 10 0 0 1 0 20z', 'm9 12 2 2 4-4'],
  sliders: ['M4 21v-7', 'M4 10V3', 'M12 21v-9', 'M12 8V3', 'M20 21v-5', 'M20 12V3', 'M1 14h6', 'M9 8h6', 'M17 16h6'],
  chart:   ['M12 20V10', 'M18 20V4', 'M6 20v-4'],
  calendar:['M8 2v4', 'M16 2v4', 'M3 4h18v16a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z', 'M3 10h18'],
  heart:   ['M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21.2l7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.8z', ''],
  water:   ['M12 3.5c3.4 4 5.7 6.6 5.7 9.3a5.7 5.7 0 0 1-11.4 0c0-2.7 2.3-5.3 5.7-9.3z'],
  activity:['M3 12h3.6l2.9 6 4.5-12 2.9 6H21'],
  moon:    ['M20.5 13.5A8.5 8.5 0 1 1 10.5 3a7 7 0 0 0 10 10.5z'],
  user:    ['M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z', 'M5 20a7 7 0 0 1 14 0'],
}

const paths = computed(() => {
  if (props.name === 'more') return ['M5 12h.01', 'M12 12h.01', 'M19 12h.01']
  const d = PATHS[props.name]
  return d ? d.filter(Boolean) : []
})
</script>
