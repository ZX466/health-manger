<template>
  <section
    v-if="loading"
    class="daily-action daily-action--skeleton"
    aria-busy="true"
    aria-label="今日一件小事加载中"
  >
    <span class="sk-mark" aria-hidden="true" />
    <div class="sk-copy" aria-hidden="true">
      <span class="sk-line sk-line--eyebrow" />
      <span class="sk-line sk-line--title" />
      <span class="sk-line sk-line--text" />
      <span class="sk-line sk-line--text sk-line--short" />
      <span class="sk-line sk-line--reason" />
    </div>
    <div class="daily-actions sk-actions" aria-hidden="true">
      <span class="sk-line sk-line--button" />
    </div>
  </section>

  <section
    v-else-if="visible"
    class="daily-action"
    :class="{ 'is-complete': action.completed, 'is-safety': isSafety }"
    aria-labelledby="daily-action-title"
  >
    <span class="daily-mark" aria-hidden="true">
      <AppIcon :name="iconName" :size="20" />
    </span>

    <div class="daily-copy">
      <div class="daily-head">
        <p class="daily-eyebrow">{{ eyebrow }}</p>
        <span v-if="!isSafety" class="daily-week" aria-live="polite">近 7 天完成 {{ weekCompleted }} 天</span>
      </div>
      <h2 id="daily-action-title">{{ action.title }}</h2>
      <p class="daily-desc">{{ action.description }}</p>
      <p class="daily-reason">
        <span class="daily-reason-label">依据</span>
        {{ action.reason }}
      </p>
      <p v-if="submitError" class="daily-error" role="alert">{{ submitError }}</p>
    </div>

    <div class="daily-actions">
      <router-link
        v-if="action.cta_path"
        class="btn btn-ghost daily-cta"
        :to="action.cta_path"
      >
        {{ action.cta_label || '去看看' }}
      </router-link>
      <button
        v-if="canComplete"
        class="btn daily-done"
        :class="action.completed ? 'is-done' : 'btn-primary'"
        type="button"
        :disabled="action.completed || submitting"
        @click="markDone"
      >
        <AppIcon v-if="action.completed" name="check" :size="15" :stroke="2.2" />
        {{ action.completed ? '已完成' : submitting ? '正在记下…' : '标记完成' }}
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import AppIcon from './AppIcon.vue'
import { completeDailyAction, getTodayAction } from '../api/dailyAction'

const ICONS = {
  care: 'heart',
  checkin: 'calendar',
  sleep: 'moon',
  move: 'activity',
  meal: 'meal',
  breathe: 'heart',
  rest: 'sparkles'
}

const action = ref(null)
const loading = ref(true)
const submitting = ref(false)
const submitError = ref('')

// Dashboard 进入严肃模式时整张卡不挂载，由求助横幅承担；否则安全行动也以关怀卡展示，
// 避免“近期危机 + 最新量表正常”时既没有行动卡也没有横幅。
const visible = computed(() => !!action.value)
const isSafety = computed(() => action.value?.kind === 'safety')
const eyebrow = computed(() => isSafety.value ? 'SUPPORT / 先照顾自己' : "TODAY'S ONE THING / 今日一件小事")
const iconName = computed(() => ICONS[action.value?.action_key] || 'sparkles')
const canComplete = computed(() => !!action.value?.can_complete)
const weekCompleted = computed(() => {
  const value = Number(action.value?.week_completed)
  return Number.isFinite(value) ? Math.max(0, Math.min(7, value)) : 0
})

async function load () {
  try {
    const res = await getTodayAction()
    const data = res?.data
    const valid = data &&
      typeof data === 'object' &&
      !Array.isArray(data) &&
      Number.isInteger(data.id) &&
      typeof data.title === 'string' &&
      data.title.trim()
    action.value = valid ? data : null
  } catch (e) {
    // 接口不可用时静默隐藏，不阻塞 Dashboard 其余内容。
    action.value = null
  } finally {
    loading.value = false
  }
}

async function markDone () {
  const current = action.value
  // 同步置位 submitting，双击/回车连按在请求返回前不会重复提交。
  if (!current || current.completed || !current.can_complete || submitting.value) return
  submitting.value = true
  submitError.value = ''
  try {
    const res = await completeDailyAction(current.id)
    const data = res?.data && typeof res.data === 'object' ? res.data : {}
    const merged = { ...current, ...data }
    merged.completed = data.completed ?? true
    if (merged.week_completed == null) {
      merged.week_completed = Math.min(7, (Number(current.week_completed) || 0) + 1)
    }
    if (!merged.completed_at && merged.completed) {
      merged.completed_at = new Date().toISOString()
    }
    action.value = merged
  } catch (e) {
    submitError.value = '刚才没记上，稍后再试一次。'
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.daily-action {
  display: grid;
  grid-template-columns: 44px minmax(0, 1fr) auto;
  align-items: start;
  gap: 16px;
  padding: 20px 22px;
  margin-bottom: 20px;
  border: var(--border-hairline);
  border-radius: var(--radius-lg);
  background:
    linear-gradient(118deg, var(--accent-soft) 0%, transparent 54%),
    var(--surface);
  overflow: hidden;
}

.daily-action.is-safety {
  border-color: color-mix(in oklch, var(--danger) 24%, var(--line));
  background:
    linear-gradient(118deg, var(--danger-soft) 0%, transparent 54%),
    var(--surface);
}

.daily-action.is-safety .daily-eyebrow,
.daily-action.is-safety .daily-mark {
  color: var(--danger);
}

.daily-action.is-safety .daily-mark {
  border-color: color-mix(in oklch, var(--danger) 24%, var(--line));
}

.daily-action.is-safety .daily-reason-label {
  background: var(--danger-soft);
  color: var(--danger);
}

.daily-mark {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border: 1px solid color-mix(in oklch, var(--accent) 20%, var(--line));
  border-radius: 50%;
  background: var(--surface);
  color: var(--accent-strong);
}

.daily-copy {
  min-width: 0;
}

.daily-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 4px 12px;
}

.daily-eyebrow {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.12em;
  line-height: 1.4;
  text-transform: uppercase;
  color: var(--muted);
}

.daily-week {
  color: var(--muted-2);
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.daily-copy h2 {
  margin: 5px 0 6px;
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 740;
  line-height: 1.25;
  letter-spacing: -0.025em;
  overflow-wrap: anywhere;
}

.daily-desc {
  max-width: 68ch;
  margin: 0;
  color: var(--muted);
  font-size: 13.5px;
  line-height: 1.65;
}

.daily-reason {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px;
  margin: 8px 0 0;
  color: var(--muted-2);
  font-size: 11.5px;
  line-height: 1.55;
}

.daily-reason-label {
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.08em;
  white-space: nowrap;
}

.daily-error {
  margin: 8px 0 0;
  color: var(--danger);
  font-size: 12px;
}

.daily-actions {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 8px;
  min-width: 132px;
  padding-top: 2px;
}

.daily-actions .btn {
  width: 100%;
}

.daily-done.is-done,
.daily-done.is-done:disabled {
  border-color: color-mix(in oklch, var(--success) 28%, var(--line));
  background: var(--success-soft);
  color: var(--success);
  opacity: 1;
  cursor: default;
}

.daily-action a:focus-visible,
.daily-action button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

/* 加载占位：与成卡同一栅格与行高节奏，避免数据到达时明显跳动。 */
.daily-action--skeleton {
  pointer-events: none;
}

.sk-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  min-height: 94px;
}

.sk-mark,
.sk-line {
  display: block;
  border-radius: 6px;
  background: linear-gradient(90deg, var(--surface-2) 20%, var(--surface-3) 46%, var(--surface-2) 72%);
  background-size: 220% 100%;
  animation: daily-shimmer 1.5s linear infinite;
}

.sk-mark {
  width: 44px;
  height: 44px;
  border-radius: 50%;
}

.sk-line--eyebrow { width: 52%; height: 10px; }
.sk-line--title { width: 70%; height: 22px; }
.sk-line--text { width: 100%; height: 12px; }
.sk-line--short { width: 86%; }
.sk-line--reason { width: 58%; height: 11px; }
.sk-line--button { width: 100%; height: 40px; border-radius: var(--radius-sm); }

@keyframes daily-shimmer {
  from { background-position: 120% 0; }
  to { background-position: -120% 0; }
}

@media (max-width: 700px) {
  .daily-action {
    grid-template-columns: 40px minmax(0, 1fr);
    gap: 12px;
    padding: 16px;
  }

  .daily-mark,
  .sk-mark {
    width: 40px;
    height: 40px;
  }

  .daily-actions {
    grid-column: 1 / -1;
    flex-direction: row;
    flex-wrap: wrap;
    min-width: 0;
    padding-top: 0;
  }

  .daily-actions .btn {
    flex: 1 1 128px;
    width: auto;
  }

  .sk-actions .sk-line--button {
    flex: 1 1 128px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sk-mark,
  .sk-line {
    animation: none;
  }
}
</style>
