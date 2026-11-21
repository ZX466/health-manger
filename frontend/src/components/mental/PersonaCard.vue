<template>
  <section :class="compact ? 'persona-compact' : 'card persona-card'">
    <div v-if="compact" class="persona-compact-head">
      <span class="persona-compact-label">聊天人设</span>
      <span class="persona-saved" role="status">{{ savedNote }}</span>
    </div>
    <div v-else class="persona-head">
      <div>
        <p class="eyebrow">Chat persona</p>
        <h2>聊天人设</h2>
      </div>
      <span class="persona-saved" role="status">{{ savedNote }}</span>
    </div>

    <p v-if="!compact" class="persona-intro">选一个你此刻更需要的说话方式。安全提示始终优先，不被人设覆盖。</p>

    <div class="persona-options" :class="{ 'persona-options--compact': compact }" role="radiogroup" aria-label="聊天人设">
      <button
        v-for="option in options"
        :key="option.key"
        class="persona-option"
        :class="{ active: current === option.key, disabled: isDisabled(option) }"
        type="button"
        role="radio"
        :aria-checked="current === option.key"
        :disabled="isDisabled(option) || saving"
        @click="select(option)"
      >
        <span v-if="!compact" class="persona-radio" aria-hidden="true">
          <i></i>
        </span>

        <span class="persona-copy">
          <span class="persona-name">
            {{ compact ? option.name : option.fullName }}
            <span v-if="current === option.key" class="persona-current">当前</span>
            <span v-else-if="isDisabled(option)" class="persona-current">暂不可选</span>
          </span>
          <span v-if="!compact" class="persona-desc">{{ option.description }}</span>
          <span v-if="!compact" class="persona-quote">“{{ option.quote }}”</span>
        </span>
      </button>
    </div>

    <div v-if="!compact" class="persona-preview" aria-live="polite">
      <span class="persona-preview-label">PREVIEW</span>
      <p>{{ currentQuote }}</p>
    </div>

    <p
      v-if="serious && current === 'humorous'"
      class="persona-warn"
      :class="{ 'persona-warn--compact': compact }"
    >
      当前状态更适合「理性陪伴」。聊天里的安全提示会优先出现，不会被人设盖住。
    </p>
    <p v-else-if="!compact" class="persona-note">
      角色设定只影响语气，不改变事实与安全边界。
    </p>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import api from '../../api'

const props = defineProps({
  /** 当心理摘要进入 serious_mode 时，禁用玩梗人设 */
  serious: { type: Boolean, default: false },
  /** 聊天页用紧凑模式，避免把消息区挤到首屏之外 */
  compact: { type: Boolean, default: false }
})

const emit = defineEmits(['change'])

const STORAGE_KEY = 'mf:persona'
const options = [
  {
    key: 'humorous',
    name: '玩梗搭子',
    fullName: '幽默宿舍搭子风',
    description: '懂梗、松弛、不爹味，关键时刻也绝不掉链子。',
    quote: '再熬下去，发际线就要比你的绩点先起飞了。'
  },
  {
    key: 'clinical',
    name: '理性陪伴',
    fullName: '严谨校医风',
    description: '专业、克制，先给判断和下一步。',
    quote: '建议先补充睡眠，观察 3 天；如持续心悸，请到校医院就诊。'
  }
]

const current = ref('humorous')
const currentQuote = computed(() => options.find(option => option.key === current.value)?.quote || '')
const saving = ref(false)
const savedNote = ref('')
const remoteConfig = ref(null)
let savedTimer = null

function isDisabled (option) {
  return props.serious && option.key === 'humorous'
}

function remember (value) {
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch (e) { /* ignore */ }
}

async function select (option, { auto = false } = {}) {
  if (isDisabled(option) || current.value === option.key || saving.value) return
  const previous = current.value
  current.value = option.key
  remember(option.key)
  saving.value = true
  savedNote.value = '保存中…'
  try {
    // PUT /ai/config 要求 model 必填：先读回完整配置，只改 persona_style。
    if (!remoteConfig.value) {
      const { data: fresh } = await api.getAiConfig()
      remoteConfig.value = fresh
    }
    const base = remoteConfig.value
    if (!base?.model) throw new Error('missing model')
    const { data } = await api.saveAiConfig({
      provider: base.provider || 'zhipu',
      model: base.model,
      base_url: base.base_url || null,
      vision_provider: base.vision_provider || null,
      vision_model: base.vision_model || null,
      vision_base_url: base.vision_base_url || null,
      persona_style: option.key
    })
    remoteConfig.value = data
    emit('change', option.key)
    savedNote.value = auto ? '已自动切换为理性陪伴' : '已记住'
  } catch (e) {
    current.value = previous
    remember(previous)
    savedNote.value = '保存失败，稍后再试'
  } finally {
    saving.value = false
    if (savedTimer) clearTimeout(savedTimer)
    savedTimer = setTimeout(() => { savedNote.value = '' }, 2600)
  }
}

// 人设实际由服务端配置控制；只有真实进入 serious 时，才同步切换成理性陪伴。
async function maybeSwitchForSafety () {
  if (!props.serious || current.value !== 'humorous') return
  await select(options.find(option => option.key === 'clinical'), { auto: true })
}

watch(() => props.serious, (value) => {
  if (value) maybeSwitchForSafety()
})

onMounted(async () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'humorous' || saved === 'clinical') current.value = saved
  } catch (e) { /* ignore */ }

  try {
    const { data } = await api.getAiConfig()
    remoteConfig.value = data
    if (data?.persona_style === 'humorous' || data?.persona_style === 'clinical') {
      current.value = data.persona_style
      remember(data.persona_style)
    }
  } catch (e) { /* 没有配置时沿用本机偏好 */ }

  await maybeSwitchForSafety()
})

onUnmounted(() => {
  if (savedTimer) clearTimeout(savedTimer)
})
</script>

<style scoped>
.persona-card {
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.persona-compact {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.persona-compact-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.persona-compact-label {
  color: var(--muted);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.persona-options--compact {
  flex-direction: row;
  gap: 6px;
}

.persona-options--compact .persona-option {
  justify-content: center;
  min-height: 34px;
  padding: 5px 10px;
}

.persona-options--compact .persona-copy {
  flex: 0 1 auto;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.persona-options--compact .persona-name {
  font-size: 12px;
  white-space: nowrap;
}

.persona-options--compact .persona-current {
  font-size: 9px;
}

.persona-warn--compact {
  margin: 0;
  padding: 4px 0 0;
  background: transparent;
}

.persona-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.persona-head h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 18px;
  letter-spacing: -0.01em;
}

.persona-saved {
  min-height: 16px;
  color: var(--success);
  font-size: 11px;
}

.persona-intro {
  margin: 10px 0 12px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.65;
}

.persona-options {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.persona-option {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  padding: 12px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  text-align: left;
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out);
}

.persona-option:hover:not(:disabled) {
  border-color: var(--accent);
}

.persona-option.active {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.persona-option.disabled {
  opacity: 0.58;
  cursor: not-allowed;
}

.persona-radio {
  display: grid;
  place-items: center;
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
  margin-top: 2px;
  border: 1.5px solid var(--line-strong);
  border-radius: 50%;
  background: var(--surface);
}

.persona-radio i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: transparent;
}

.persona-option.active .persona-radio {
  border-color: var(--accent);
}

.persona-option.active .persona-radio i {
  background: var(--accent);
}

.persona-copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.persona-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
}

.persona-current {
  padding: 1px 5px;
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 9px;
  font-weight: 400;
}

.persona-desc {
  margin-top: 3px;
  color: var(--muted);
  font-size: 11.5px;
  line-height: 1.55;
}

.persona-quote {
  margin-top: 7px;
  padding: 7px 9px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: color-mix(in oklch, var(--surface-2) 74%, var(--surface));
  color: var(--muted);
  font-size: 11px;
  line-height: 1.6;
}

.persona-preview {
  margin-top: 10px;
  padding: 14px 16px;
  border-radius: var(--radius-sm);
  background: #141518;
  color: #fff;
}

.persona-preview-label {
  color: color-mix(in oklch, #fff 54%, transparent);
  font-family: var(--font-mono);
  font-size: 8px;
  letter-spacing: 0.12em;
}

.persona-preview p {
  margin: 6px 0 0;
  font-size: 12.5px;
  line-height: 1.7;
}

.persona-note,
.persona-warn {
  margin: 10px 0 0;
  font-size: 10px;
  line-height: 1.55;
}

.persona-note {
  color: var(--muted);
}

.persona-warn {
  padding: 7px 8px;
  border-radius: var(--radius-sm);
  background: var(--warn-soft);
  color: var(--muted);
}

@media (prefers-reduced-motion: reduce) {
  .persona-option {
    transition: none;
  }
}
</style>
