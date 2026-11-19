<template>
  <div class="warning-page">
    <PageHead
      folio="08"
      eyebrow="MONITOR / SIGNALS"
      title="健康预警"
      deck="身体和情绪发来的信号，按轻重排好。先看最需要处理的那一条。"
    >
      <template #actions>
        <span
          class="status-chip"
          :class="stats.danger ? 'status-chip--warn' : unreadCount ? 'status-chip--accent' : ''"
        >
          <span
            class="status-dot"
            :class="stats.danger ? 'status-dot--danger' : unreadCount ? '' : 'status-dot--success'"
          ></span>
          {{ unreadCount ? `${unreadCount} 条未读` : '全部已读' }}
        </span>
        <button class="btn btn-ghost" type="button" :disabled="checking" @click="recheck">
          <AppIcon name="activity" :size="15" />
          {{ checking ? '检查中' : '重新检查' }}
        </button>
        <button
          class="btn btn-primary"
          type="button"
          :disabled="!unreadCount || markingAll"
          @click="markAll"
        >
          <AppIcon name="check" :size="15" />
          {{ markingAll ? '处理中' : '全部已读' }}
        </button>
      </template>
    </PageHead>

    <section class="warning-summary v21-panel" aria-label="预警统计">
      <article class="summary-cell summary-cell--lead">
        <span class="micro micro--inverse">TOTAL / ALL</span>
        <strong class="summary-value">{{ stats.total }}</strong>
        <span class="summary-label">累计提醒</span>
      </article>
      <article class="summary-cell summary-cell--unread">
        <span class="micro">UNREAD / NOW</span>
        <strong class="summary-value">{{ stats.unread }}</strong>
        <span class="summary-label">待查看</span>
      </article>
      <article class="summary-cell summary-cell--danger">
        <span class="micro">DANGER / UNREAD</span>
        <strong class="summary-value">{{ stats.danger }}</strong>
        <span class="summary-label">危险未读</span>
      </article>
    </section>

    <section class="warning-board v21-panel" aria-labelledby="warning-list-title">
      <div class="board-head">
        <div>
          <p class="micro">ALERTS / LIST</p>
          <h2 id="warning-list-title">提醒清单</h2>
        </div>
        <div class="filter-tabs" role="tablist" aria-label="预警筛选">
          <button
            class="filter-tab"
            :class="{ active: filter === 'unread' }"
            type="button"
            role="tab"
            :aria-selected="filter === 'unread'"
            @click="filter = 'unread'"
          >
            未读 <span>{{ unreadCount }}</span>
          </button>
          <button
            class="filter-tab"
            :class="{ active: filter === 'all' }"
            type="button"
            role="tab"
            :aria-selected="filter === 'all'"
            @click="filter = 'all'"
          >
            全部 <span>{{ warnings.length }}</span>
          </button>
        </div>
      </div>

      <div v-if="loading" class="warning-skeleton" aria-label="正在加载预警">
        <div v-for="n in 3" :key="n" class="skeleton-row">
          <span class="skeleton-dot"></span>
          <span class="skeleton-lines">
            <span class="skeleton-line skeleton-line--short"></span>
            <span class="skeleton-line"></span>
          </span>
        </div>
      </div>

      <div v-else-if="error" class="warning-empty" role="alert">
        <span class="empty-mark empty-mark--danger"><AppIcon name="alert" :size="21" /></span>
        <h3>提醒没有加载出来</h3>
        <p>{{ error }}</p>
        <button class="btn btn-ghost" type="button" @click="loadWarnings">重试</button>
      </div>

      <div v-else-if="!visibleWarnings.length" class="warning-empty">
        <span class="empty-mark"><AppIcon name="check" :size="21" /></span>
        <h3>{{ filter === 'unread' ? '没有未读提醒' : '还没有健康提醒' }}</h3>
        <p v-if="filter === 'unread'">
          已处理完当前所有提醒。新的信号出现时，会在这里第一时间排好。
        </p>
        <p v-else>
          记录一次体检数据或提交量表后，系统会自动检查并生成提醒。
        </p>
        <div class="empty-actions">
          <router-link class="btn btn-ghost" to="/health-record">去记录体检</router-link>
          <button class="btn btn-ghost" type="button" :disabled="checking" @click="recheck">
            手动检查
          </button>
        </div>
      </div>

      <ul v-else class="warning-list">
        <li
          v-for="item in visibleWarnings"
          :key="item.id"
          class="warning-item"
          :class="[`warning-item--${levelTone(item.warning_level)}`, { 'warning-item--unread': !item.is_read }]"
        >
          <span class="warning-mark" aria-hidden="true">
            <AppIcon name="alert" :size="17" />
          </span>
          <div class="warning-content">
            <div class="warning-meta">
              <span class="warning-level">{{ levelLabel(item.warning_level) }}</span>
              <span class="warning-type">{{ item.warning_type }}</span>
              <span class="warning-time micro">{{ formatScaleDate(item.created_at) }}</span>
              <span v-if="!item.is_read" class="warning-new">NEW</span>
            </div>
            <p class="warning-text">{{ item.warning_content }}</p>
          </div>
          <div class="warning-actions">
            <button
              v-if="!item.is_read"
              class="warning-action"
              type="button"
              :disabled="actionId === item.id"
              @click="markRead(item)"
            >
              标记已读
            </button>
            <button
              class="warning-action warning-action--danger"
              :class="{ 'is-confirming': pendingDelete === item.id }"
              type="button"
              :disabled="actionId === item.id"
              @click="remove(item)"
            >
              {{ pendingDelete === item.id ? '确认删除' : '删除' }}
            </button>
          </div>
        </li>
      </ul>

      <p v-if="notice" class="warning-notice" role="status">{{ notice }}</p>

      <footer class="board-foot">
        <span class="micro">AUTO / CHECK</span>
        <p>保存体检记录或提交量表后会自动检查；也可以点「重新检查」立即生成。</p>
      </footer>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import api from '../api'
import AppIcon from '../components/AppIcon.vue'
import PageHead from '../components/PageHead.vue'
import { formatScaleDate } from '../utils/date'
import { useWarningStore } from '../stores/warnings'

const warningStore = useWarningStore()
const stats = computed(() => warningStore.stats)

const warnings = ref([])
const loading = ref(true)
const checking = ref(false)
const markingAll = ref(false)
const actionId = ref(null)
const pendingDelete = ref(null)
const filter = ref('unread')
const error = ref('')
const notice = ref('')
let noticeTimer = null
let deleteTimer = null

const unreadCount = computed(() => warnings.value.filter(item => !item.is_read).length)
const visibleWarnings = computed(() =>
  filter.value === 'unread' ? warnings.value.filter(item => !item.is_read) : warnings.value
)

const LEVELS = {
  info: { label: '提示', tone: 'info' },
  warning: { label: '关注', tone: 'warning' },
  danger: { label: '危险', tone: 'danger' },
  critical: { label: '紧急', tone: 'critical' }
}

function levelLabel (level) {
  return LEVELS[level]?.label || '提醒'
}

function levelTone (level) {
  return LEVELS[level]?.tone || 'info'
}

function applyStats () {
  warningStore.setStats({
    total: warnings.value.length,
    unread: unreadCount.value,
    danger: warnings.value.filter(
      item => !item.is_read && ['danger', 'critical'].includes(item.warning_level)
    ).length
  })
}

function flash (message) {
  notice.value = message
  if (noticeTimer) window.clearTimeout(noticeTimer)
  noticeTimer = window.setTimeout(() => {
    notice.value = ''
  }, 4200)
}

async function loadWarnings () {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.getWarnings()
    warnings.value = Array.isArray(data) ? data : []
    applyStats()
  } catch (err) {
    error.value = err.response?.data?.detail || '网络或服务暂时不可用，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function recheck () {
  if (checking.value) return
  checking.value = true
  try {
    const { data } = await api.checkWarnings()
    await loadWarnings()
    const added = Number(data?.new_warnings) || 0
    flash(added > 0 ? `检查完成，新增 ${added} 条提醒。` : '检查完成，暂未发现新的提醒。')
  } catch (err) {
    flash(err.response?.data?.detail || '检查失败，请稍后重试。')
  } finally {
    checking.value = false
  }
}

async function markRead (item) {
  if (item.is_read || actionId.value) return
  actionId.value = item.id
  try {
    const { data } = await api.markWarningAsRead(item.id)
    Object.assign(item, data || { is_read: true })
    if (item.is_read !== true) item.is_read = true
    applyStats()
  } catch (err) {
    flash(err.response?.data?.detail || '标记失败，请稍后重试。')
  } finally {
    actionId.value = null
  }
}

async function markAll () {
  if (!unreadCount.value || markingAll.value) return
  markingAll.value = true
  try {
    await api.markAllWarningsAsRead()
    warnings.value = warnings.value.map(item => ({ ...item, is_read: true }))
    applyStats()
    flash('已全部标记为已读。')
  } catch (err) {
    flash(err.response?.data?.detail || '操作失败，请稍后重试。')
  } finally {
    markingAll.value = false
  }
}

function clearDeleteTimer () {
  if (deleteTimer) {
    window.clearTimeout(deleteTimer)
    deleteTimer = null
  }
}

async function remove (item) {
  if (actionId.value) return
  if (pendingDelete.value !== item.id) {
    pendingDelete.value = item.id
    clearDeleteTimer()
    deleteTimer = window.setTimeout(() => {
      pendingDelete.value = null
      deleteTimer = null
    }, 4000)
    return
  }

  clearDeleteTimer()
  pendingDelete.value = null
  actionId.value = item.id
  try {
    await api.deleteWarning(item.id)
    warnings.value = warnings.value.filter(entry => entry.id !== item.id)
    applyStats()
    flash('提醒已删除。')
  } catch (err) {
    flash(err.response?.data?.detail || '删除失败，请稍后重试。')
  } finally {
    actionId.value = null
  }
}

onMounted(loadWarnings)

onBeforeUnmount(() => {
  if (noticeTimer) window.clearTimeout(noticeTimer)
  clearDeleteTimer()
})
</script>

<style scoped>
.warning-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ── 统计条 ─────────────────────────────────────────── */
.warning-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 0;
  overflow: hidden;
}

.summary-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 132px;
  padding: 20px 24px;
  border-right: 1px solid var(--line);
}

.summary-cell:last-child {
  border-right: 0;
}

.summary-cell--lead {
  background: var(--ink);
  color: var(--surface);
}

.summary-cell--lead .micro {
  color: color-mix(in oklch, var(--surface) 58%, transparent);
}

.summary-cell--unread {
  background: var(--accent-soft);
}

.summary-cell--danger {
  background: var(--danger-soft);
}

.summary-value {
  font-family: var(--font-display);
  font-size: 42px;
  font-weight: 760;
  line-height: 1;
  letter-spacing: -0.05em;
}

.summary-cell--unread .summary-value {
  color: var(--accent-strong);
}

.summary-cell--danger .summary-value {
  color: var(--danger);
}

.summary-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
}

.summary-cell--lead .summary-label {
  color: color-mix(in oklch, var(--surface) 76%, transparent);
}

/* ── 清单面板 ───────────────────────────────────────── */
.warning-board {
  padding: 0;
  overflow: hidden;
}

.board-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  padding: 22px 24px 18px;
  border-bottom: 1px solid var(--line);
}

.board-head h2 {
  margin-top: 4px;
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 740;
  letter-spacing: -0.04em;
}

.filter-tabs {
  display: inline-flex;
  gap: 4px;
  padding: 3px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface-2);
}

.filter-tab {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 30px;
  padding: 0 12px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 11px;
  font-weight: 650;
  white-space: nowrap;
}

.filter-tab span {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--muted-2);
}

.filter-tab.active {
  background: var(--surface);
  color: var(--fg);
  box-shadow: 0 1px 2px color-mix(in oklch, var(--ink) 8%, transparent);
}

.filter-tab.active span {
  color: var(--accent-strong);
}

.warning-list {
  margin: 0;
  padding: 0 24px;
  list-style: none;
}

.warning-item {
  --level: var(--accent);
  --level-soft: var(--accent-soft);
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) auto;
  gap: 14px;
  align-items: start;
  padding: 18px 0;
  border-top: 1px solid var(--line);
  border-left: 2px solid transparent;
  transition: background var(--duration-fast) var(--ease-out);
}

.warning-item:first-child {
  border-top: 0;
}

.warning-item--warning {
  --level: var(--warn);
  --level-soft: var(--warn-soft);
}

.warning-item--danger,
.warning-item--critical {
  --level: var(--danger);
  --level-soft: var(--danger-soft);
}

.warning-item--unread {
  border-left-color: var(--level);
}

.warning-item:hover {
  background: color-mix(in oklch, var(--surface-2) 55%, transparent);
}

.warning-mark {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--level-soft);
  color: var(--level);
}

.warning-content {
  min-width: 0;
}

.warning-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}

.warning-level {
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--level-soft);
  color: var(--level);
  font-family: var(--font-mono);
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.warning-type {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.warning-time {
  color: var(--muted-2);
}

.warning-new {
  font-family: var(--font-mono);
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--accent-strong);
}

.warning-text {
  max-width: 72ch;
  margin: 0;
  color: var(--muted);
  font-size: 12.5px;
  line-height: 1.6;
}

.warning-item--unread .warning-text {
  color: var(--fg);
}

.warning-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 2px;
}

.warning-action {
  min-height: 28px;
  padding: 0 9px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 10.5px;
  font-weight: 650;
  white-space: nowrap;
}

.warning-action:hover {
  border-color: var(--line-strong);
  color: var(--fg);
}

.warning-action:disabled {
  opacity: 0.45;
}

.warning-action--danger:hover,
.warning-action.is-confirming {
  border-color: color-mix(in oklch, var(--danger) 35%, var(--line));
  background: var(--danger-soft);
  color: var(--danger);
}

/* ── 空态 / 加载 / 错误 ─────────────────────────────── */
.warning-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  padding: 54px 24px 58px;
  text-align: center;
}

.empty-mark {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  margin-bottom: 4px;
  border-radius: 50%;
  background: var(--success-soft);
  color: var(--success);
}

.empty-mark--danger {
  background: var(--danger-soft);
  color: var(--danger);
}

.warning-empty h3 {
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 720;
  letter-spacing: -0.025em;
}

.warning-empty p {
  max-width: 44ch;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.65;
}

.empty-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
}

.warning-skeleton {
  padding: 8px 24px 16px;
}

.skeleton-row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  padding: 18px 0;
  border-bottom: 1px solid var(--line);
}

.skeleton-row:last-child {
  border-bottom: 0;
}

.skeleton-dot,
.skeleton-line {
  display: block;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--surface-2), var(--surface-3), var(--surface-2));
  background-size: 200% 100%;
  animation: warning-shimmer 1.4s ease-in-out infinite;
}

.skeleton-dot {
  width: 36px;
  height: 36px;
}

.skeleton-lines {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-line {
  width: 78%;
  height: 10px;
}

.skeleton-line--short {
  width: 32%;
  height: 8px;
}

@keyframes warning-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.warning-notice {
  margin: 0 24px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-size: 11.5px;
  font-weight: 600;
}

.board-foot {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 15px 24px;
  border-top: 1px solid var(--line);
  background: var(--surface-2);
}

.board-foot p {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.5;
}

@media (max-width: 820px) {
  .board-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
  }

  .warning-item {
    grid-template-columns: 36px minmax(0, 1fr);
  }

  .warning-actions {
    grid-column: 2;
    padding-top: 0;
  }
}

@media (max-width: 640px) {
  .summary-cell {
    min-height: 112px;
    padding: 16px 14px;
    gap: 4px;
  }

  .summary-value {
    font-size: 32px;
  }

  .summary-label {
    font-size: 10.5px;
  }

  .board-head,
  .warning-skeleton {
    padding-left: 16px;
    padding-right: 16px;
  }

  .warning-list {
    padding: 0 16px;
  }

  .warning-notice {
    margin: 0 16px;
  }

  .board-foot {
    padding-left: 16px;
    padding-right: 16px;
  }
}
</style>
