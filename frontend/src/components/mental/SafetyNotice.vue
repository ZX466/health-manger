<template>
  <section
    ref="root"
    class="safety-notice"
    :class="[`tone-${tone}`, { compact }]"
    :role="isAlert ? 'alert' : 'status'"
    :tabindex="isAlert ? -1 : undefined"
    :aria-live="isAlert ? 'assertive' : 'polite'"
  >
    <div class="safety-head">
      <span class="safety-dot" aria-hidden="true"></span>
      <div>
        <p class="safety-eyebrow">{{ eyebrow }}</p>
        <h3>{{ heading }}</h3>
      </div>
    </div>

    <p class="safety-body">{{ bodyText }}</p>

    <div class="safety-grid">
      <a class="safety-card safety-card--emergency" href="tel:120">
        <span class="safety-card-label">紧急医疗</span>
        <strong>120</strong>
        <span>如有立即危险，请先拨打</span>
      </a>
      <a class="safety-card safety-card--emergency" href="tel:110">
        <span class="safety-card-label">报警求助</span>
        <strong>110</strong>
        <span>身处危险或需要即时保护</span>
      </a>
      <a
        v-for="resource in validResources"
        :key="`${resource.name}-${resource.phone || ''}`"
        class="safety-card"
        :href="resource.phone ? `tel:${resource.phone}` : undefined"
      >
        <span class="safety-card-label">{{ resource.name }}</span>
        <strong>{{ resource.phone || resourceFallback(resource) }}</strong>
        <span>{{ resource.description || '以学校公布信息为准' }}</span>
      </a>
      <div v-if="!hasSchoolResource" class="safety-card safety-card--school">
        <span class="safety-card-label">学校心理咨询中心</span>
        <strong>工作日可预约</strong>
        <span>具体电话与地址以学校公布为准</span>
      </div>
    </div>

    <p v-if="!validResources.length" class="safety-fine">
      暂未配置更多本地资源；上面的紧急号码始终可用。
    </p>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'

const props = defineProps({
  /** info | elevated | crisis；为兼容后端事件也接受 serious */
  level: { type: String, default: 'info' },
  crisis: { type: Boolean, default: false },
  serious: { type: Boolean, default: false },
  /** 后端 safety.resources：{ name, phone, description } */
  resources: { type: Array, default: () => [] },
  /** chat | scale | general */
  context: { type: String, default: 'general' },
  compact: { type: Boolean, default: false }
})

const root = ref(null)

const tone = computed(() => {
  if (props.crisis || props.level === 'crisis') return 'crisis'
  if (props.level === 'elevated' || props.level === 'serious') return 'elevated'
  if (props.serious) return 'serious'
  return 'info'
})
const isAlert = computed(() => tone.value === 'crisis')

const validResources = computed(() => {
  const seen = new Set()
  return (Array.isArray(props.resources) ? props.resources : []).filter(r => {
    if (!r || !r.name) return false
    const key = `${r.name}|${r.phone || ''}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
})

const hasSchoolResource = computed(() =>
  validResources.value.some(r => String(r.name).includes('学校心理咨询'))
)

function resourceFallback (resource) {
  return String(resource?.name || '').includes('学校心理咨询') ? '校内资源' : '电话未配置'
}

const eyebrow = computed(() => ({
  crisis: 'Crisis support',
  elevated: 'Need support',
  serious: 'Serious care',
  info: 'Support'
}[tone.value]))

const heading = computed(() => {
  if (tone.value === 'crisis') return '请优先确保自己的安全'
  if (props.context === 'scale') return '这份结果值得被认真对待'
  if (props.context === 'chat') return '如果你现在很难受'
  if (tone.value === 'serious') return '最近的状态需要被认真对待'
  return '需要帮助时，不必一个人扛'
})

const bodyText = computed(() => {
  if (tone.value === 'crisis') {
    return '如果你有伤害自己的念头，请立刻联系下面的紧急服务，或告诉身边可信任的人陪你。你不需要一个人扛。'
  }
  if (props.context === 'scale') {
    return '这是一份初筛结果，不是诊断。建议尽快和学校心理咨询中心或信任的人聊聊，让专业的人陪你一起看。'
  }
  if (props.context === 'chat') {
    return '这里不是急诊。如果你正处在危险中，请直接拨打 120 / 110，或联系下面这些免费的支持资源。'
  }
  if (tone.value === 'serious') {
    return '先照顾自己：把节奏放慢，联系学校心理咨询中心，或让一个信任的人知道你现在不太好。'
  }
  return '心理困扰很常见。和信任的人聊聊、预约学校心理咨询中心，都是很勇敢的选择。'
})

async function focusAlert () {
  if (!isAlert.value) return
  await nextTick()
  if (root.value && typeof root.value.focus === 'function') root.value.focus()
}

onMounted(focusAlert)
watch(isAlert, focusAlert)
</script>

<style scoped>
.safety-notice {
  border: var(--border-hairline);
  border-radius: var(--radius-md);
  background: var(--surface);
  padding: 18px 20px;
  outline: none;
}

.safety-notice:focus-visible {
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.safety-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.safety-dot {
  width: 8px;
  height: 8px;
  margin-top: 7px;
  border-radius: 50%;
  background: var(--muted);
  flex-shrink: 0;
}

.safety-eyebrow {
  margin: 0 0 4px;
  color: var(--muted);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.safety-head h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 16px;
  line-height: 1.4;
}

.safety-body {
  margin: 10px 0 14px;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.7;
}

.safety-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.safety-card {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 12px 14px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--fg);
  text-decoration: none;
  transition: border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out);
}

.safety-card:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.safety-card-label {
  color: var(--muted);
  font-size: 12px;
}

.safety-card strong {
  font-family: var(--font-mono);
  font-size: 16px;
  letter-spacing: -0.01em;
}

.safety-card span:last-child {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.safety-card--emergency {
  background: var(--danger-soft);
  border-color: color-mix(in oklch, var(--danger) 22%, var(--border));
}

.safety-card--emergency strong {
  color: var(--danger);
}

.safety-card--school {
  background: var(--accent-soft);
  border-color: color-mix(in oklch, var(--accent) 18%, var(--border));
}

.safety-fine {
  margin: 10px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.safety-notice.tone-crisis {
  border-color: color-mix(in oklch, var(--danger) 34%, var(--border));
  background: var(--danger-soft);
}

.safety-notice.tone-crisis .safety-dot,
.safety-notice.tone-elevated .safety-dot {
  background: var(--danger);
}

.safety-notice.tone-serious {
  border-color: color-mix(in oklch, var(--warn) 28%, var(--border));
  background: var(--warn-soft);
}

.safety-notice.tone-serious .safety-dot {
  background: var(--warn);
}

.safety-notice.compact {
  padding: 14px 16px;
}

.safety-notice.compact .safety-body {
  margin: 6px 0 10px;
}

.safety-notice.compact .safety-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 560px) {
  .safety-grid,
  .safety-notice.compact .safety-grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .safety-card {
    transition: none;
  }
}
</style>
