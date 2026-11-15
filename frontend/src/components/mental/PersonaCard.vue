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
        <span v-if="!compact" class="persona-avatar" aria-hidden="true">
          <CharacterAvatar
            v-if="option.key === 'humorous'"
            type="nailong"
            :animated="false"
          />
          <svg v-else viewBox="0 0 24 24" class="persona-leaf">
            <path d="M12 21V10" />
            <path d="M12 13c-3.5 0-6-2.2-6-5.5C9.5 7.5 12 9.7 12 13Z" />
            <path d="M12 9c0-3.2 2.5-5.5 6-5.5C18 6.8 15.5 9 12 9Z" />
          </svg>
        </span>

        <span class="persona-copy">
          <span class="persona-name">
            {{ option.name }}
            <span v-if="current === option.key" class="persona-current">当前</span>
            <span v-else-if="isDisabled(option)" class="persona-current">暂不可选</span>
          </span>
          <span v-if="!compact" class="persona-desc">{{ option.description }}</span>
        </span>

        <span v-if="!compact" class="persona-dot" aria-hidden="true"></span>
      </button>
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
import { onMounted, onUnmounted, ref, watch } from 'vue'
import api from '../../api'
import CharacterAvatar from '../CharacterAvatar.vue'

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
    description: '接梗、吐槽、偶尔发疯，但不拿你的痛苦开玩笑。'
  },
  {
    key: 'clinical',
    name: '理性陪伴',
    description: '不玩梗，先接住情绪，再一起把问题拆小一点。'
  }
]

const current = ref('humorous')
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
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 10px;
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

.persona-avatar {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
  background: var(--bg);
}

.persona-avatar :deep(.character-avatar) {
  width: 36px;
  height: 36px;
  box-shadow: none;
  cursor: default;
}

.persona-leaf {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: var(--success);
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
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
  color: var(--muted);
  font-size: 11px;
  line-height: 1.5;
}

.persona-dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border: 1px solid var(--border);
  border-radius: 50%;
}

.persona-option.active .persona-dot {
  border-color: var(--accent);
  background: var(--accent);
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
