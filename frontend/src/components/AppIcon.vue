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
  plus:    ['M12 5v14', 'M5 12h14'],
  chevron: ['m6 9 6 6 6-6'],
  device:  ['M7 2.5h10a2 2 0 0 1 2 2v15a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-15a2 2 0 0 1 2-2z', 'M10 5.5h4', 'M9.5 18.5h5'],
  close:   ['M6 6l12 12', 'M18 6 6 18'],
  arrow:   ['M5 12h14', 'M13 6l6 6-6 6'],
  mood:    ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z', 'M8.5 14.5c.9 1.3 2.1 2 3.5 2s2.6-.7 3.5-2', 'M9 9.5h.01', 'M15 9.5h.01'],
  breathe: ['M12 4a8 8 0 0 1 8 8', 'M12 7a5 5 0 0 1 5 5', 'M12 10a2 2 0 0 1 2 2', 'M12 20a8 8 0 0 1-8-8', 'M12 17a5 5 0 0 1-5-5', 'M12 14a2 2 0 0 1-2-2'],
  camera:  ['M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z', 'M12 16.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z'],
  sparkles:['M12 3l1.6 4.4L18 9l-4.4 1.6L12 15l-1.6-4.4L6 9l4.4-1.6z', 'M18.5 15.5l.8 2.2 2.2.8-2.2.8-.8 2.2-.8-2.2-2.2-.8 2.2-.8z', 'M5 15.5l.6 1.4 1.4.6-1.4.6L5 19.5l-.6-1.4L3 17.5l1.4-.6z'],
  copy:    ['M9 9h9a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2z', 'M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1'],
  volume:  ['M11 5 6 9H3v6h3l5 4z', 'M15.5 8.5a5 5 0 0 1 0 7', 'M18.5 5.5a9 9 0 0 1 0 13'],
  menu:    ['M4 7h16', 'M4 12h16', 'M4 17h16'],
  logout:  ['M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4', 'M16 17l5-5-5-5', 'M21 12H9'],
  eye:     ['M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z'],
  download:['M12 3v12', 'M7 10l5 5 5-5', 'M4 21h16'],
  trash:   ['M3 6h18', 'M8 6V4h8v2', 'M19 6l-1 15H6L5 6', 'M10 11v6', 'M14 11v6'],
}

const paths = computed(() => {
  if (props.name === 'more') return ['M5 12h.01', 'M12 12h.01', 'M19 12h.01']
  const d = PATHS[props.name]
  return d ? d.filter(Boolean) : []
})
</script>
