<template>
  <div class="chat-view">
    <div class="chat-layout">
      <!-- 会话列表 -->
      <aside class="chat-side card" aria-label="会话列表">
        <div class="section-head">
          <h2>会话</h2>
          <button class="btn btn--primary btn-sm" type="button" @click="createSession">＋ 新建</button>
        </div>
        <ul class="session-list">
          <li v-for="s in sessions" :key="s.id">
            <button
              class="session-item"
              :class="{ active: s.id === activeId }"
              type="button"
              @click="selectSession(s)"
            >
              <span class="session-title">{{ s.title || '新会话' }}</span>
              <span class="session-meta">{{ formatDate(s.updated_at) }}</span>
            </button>
          </li>
          <li v-if="!sessions.length" class="empty">
            <p class="empty-title">暂无会话</p>
            <p>点击「新建」开始对话</p>
          </li>
        </ul>
      </aside>

      <!-- 消息区 -->
      <section class="chat-main card">
        <div class="chat-top">
          <div class="chat-title">
            <span class="chat-dot" aria-hidden="true"></span>
            <span>和 AI 聊聊</span>
            <span v-if="safetyBadge" class="serious-pill">{{ safetyBadge }}</span>
          </div>
          <div class="chat-actions">
            <button
              class="btn btn--primary btn-sm chat-new-mobile"
              type="button"
              @click="createSession"
            >
              ＋ 新建
            </button>
            <button
              class="help-toggle"
              type="button"
              :aria-expanded="showHelp"
              @click="showHelp = !showHelp"
            >
              <AppIcon name="heart" :size="14" />
              需要帮助？
            </button>
          </div>
        </div>

        <div class="chat-persona">
          <PersonaCard compact :serious="personaSerious" />
        </div>

        <select
          v-if="sessions.length"
          class="session-select"
          :value="activeId"
          aria-label="切换会话"
          @change="onSelectChange"
        >
          <option v-for="s in sessions" :key="s.id" :value="s.id">
            {{ s.title || '新会话' }}
          </option>
        </select>

        <SafetyNotice
          v-if="showSafety"
          :level="safetyLevel"
          :crisis="currentSafety.crisis"
          :resources="currentSafety.resources"
          :serious="seriousMode"
          context="chat"
          :compact="!currentSafety.crisis"
        />

        <p v-if="seriousMode && !showSafety" class="serious-note" role="status">
          最近的状态值得被认真对待。不用急着组织语言；如果很难受，点右上角「需要帮助？」。
        </p>

        <p v-if="notice" class="chat-notice" role="status">{{ notice }}</p>

        <div
          ref="msgBox"
          class="messages"
          :aria-live="sending ? 'off' : 'polite'"
          :aria-busy="sending"
        >
          <div v-if="!messages.length" class="empty chat-empty">
            <p class="empty-title">{{ seriousMode ? '今天想从哪里开始？' : '开始聊点什么' }}</p>
            <p>{{ seriousMode ? '不用组织好语言，想到哪说到哪。' : '健康、睡眠、压力，或者只是今天有点累。' }}</p>
            <div class="prompt-chips">
              <button
                v-for="prompt in quickPrompts"
                :key="prompt"
                class="prompt-chip"
                type="button"
                @click="usePrompt(prompt)"
              >
                {{ prompt }}
              </button>
            </div>
          </div>
          <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
            <span class="msg-role">{{ m.role === 'assistant' ? 'AI' : '我' }}</span>
            <div class="msg-content">
              {{ m.content }}<span v-if="m.streaming" class="stream-cursor" aria-hidden="true"></span>
            </div>
          </div>
        </div>

        <form class="chat-input" @submit.prevent="send">
          <input
            v-model="input"
            class="field-input"
            :placeholder="activeId ? '输入你想说的…' : '直接说点什么，发送时自动新建会话'"
            :disabled="sending"
            maxlength="2000"
            aria-label="消息内容"
          />
          <button
            v-if="sending"
            class="btn btn-ghost"
            type="button"
            @click="stop"
          >
            停止
          </button>
          <button
            v-else
            class="btn btn--primary"
            type="submit"
            :disabled="!input.trim()"
          >
            发送
          </button>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import api from '../api'
import AppIcon from '../components/AppIcon.vue'
import PersonaCard from '../components/mental/PersonaCard.vue'
import SafetyNotice from '../components/mental/SafetyNotice.vue'
import { parseServerDate } from '../utils/date'

const sessions = ref([])
const activeId = ref(null)
const messages = ref([])
const input = ref('')
const sending = ref(false)
const notice = ref('')
const showHelp = ref(false)
const seriousMode = ref(false)
const msgBox = ref(null)
const currentSafety = ref({ level: 'normal', crisis: false, resources: [] })

let controller = null
let loadToken = 0
let streamToken = 0

const quickPrompts = computed(() => seriousMode.value
  ? ['我最近总是睡不好', '脑子里停不下来', '想找人说说']
  : ['最近总是睡不好', '压力有点大', '帮我看看今天的记录']
)

const isCrisis = computed(() => currentSafety.value.crisis || currentSafety.value.level === 'crisis')
const safetyLevel = computed(() => {
  if (isCrisis.value) return 'crisis'
  if (currentSafety.value.level === 'high') return 'serious'
  if (currentSafety.value.level === 'elevated') return 'elevated'
  return 'info'
})

const showSafety = computed(() =>
  showHelp.value ||
  isCrisis.value ||
  currentSafety.value.level === 'high' ||
  currentSafety.value.level === 'elevated'
)
const personaSerious = computed(() => seriousMode.value || isCrisis.value || currentSafety.value.level === 'high')
const safetyBadge = computed(() => {
  if (isCrisis.value || currentSafety.value.level === 'high') return '安全模式已接管'
  return seriousMode.value ? '慢一点也没关系' : ''
})

function resetSafety () {
  // 危机状态必须一直保留到新的 safety 事件覆盖，不能被会话切换静默清掉。
  if (currentSafety.value.crisis) {
    showHelp.value = true
    return
  }
  currentSafety.value = { level: 'normal', crisis: false, resources: [] }
  showHelp.value = false
}

async function loadSessions () {
  try {
    const { data } = await api.getChatSessions({ limit: 20 })
    sessions.value = Array.isArray(data) ? data : []
    if (!activeId.value && sessions.value.length) {
      await selectSession(sessions.value[0])
    }
  } catch (e) {
    notice.value = '会话列表没加载出来，稍后刷新试试'
  }
}

async function loadSeriousMode () {
  try {
    const { data } = await api.getMentalSummary()
    seriousMode.value = !!data?.serious_mode
  } catch (e) { /* 摘要失败不阻塞聊天 */ }
}

function detachStream () {
  streamToken += 1
  if (controller) controller.abort()
  controller = null
  sending.value = false
}

async function createSession () {
  if (sending.value) detachStream()
  loadToken += 1
  try {
    const { data } = await api.createChatSession({ title: '新会话', context_type: 'general' })
    loadToken += 1
    sessions.value = [data, ...sessions.value]
    activeId.value = data.id
    messages.value = []
    notice.value = ''
    resetSafety()
    await nextTick()
    scrollBottom(true)
  } catch (e) {
    notice.value = '创建会话失败，请稍后重试'
  }
}

function onSelectChange (event) {
  const session = sessions.value.find(s => String(s.id) === String(event.target.value))
  if (session) selectSession(session)
}

async function selectSession (session) {
  if (sending.value) detachStream()
  resetSafety()
  activeId.value = session.id
  messages.value = []
  const token = ++loadToken
  try {
    const { data } = await api.getChatMessages(session.id, { limit: 50 })
    if (token !== loadToken) return
    messages.value = (Array.isArray(data) ? data : []).filter(m => m.role !== 'system')
    await nextTick()
    scrollBottom(true)
  } catch (e) {
    if (token === loadToken) notice.value = '消息没加载出来，稍后重试'
  }
}

function usePrompt (prompt) {
  input.value = prompt
  send()
}

function stop () {
  if (controller) controller.abort()
}

function scrollBottom (force = false) {
  const box = msgBox.value
  if (!box) return
  const nearBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 90
  if (force || nearBottom) box.scrollTop = box.scrollHeight
}

async function send () {
  const content = input.value.trim()
  if (!content || sending.value) return

  if (!activeId.value) {
    await createSession()
    if (!activeId.value) return
  }

  input.value = ''
  notice.value = ''
  const token = ++streamToken
  messages.value.push({ role: 'user', content })
  messages.value.push({ role: 'assistant', content: '', streaming: true })
  sending.value = true
  // 不在每次发送时清空安全状态：上一轮的高风险/危机提示要保留到新事件覆盖。
  controller = new AbortController()
  await nextTick()
  scrollBottom(true)

  try {
    await api.streamChatMessage(activeId.value, content, {
      signal: controller.signal,
      onEvent: (event, data) => {
        if (token !== streamToken) return
        if (event === 'safety') {
          currentSafety.value = {
            level: data?.level || 'normal',
            crisis: !!data?.crisis,
            resources: Array.isArray(data?.resources) ? data.resources : []
          }
          if (data?.crisis) showHelp.value = true
        } else if (event === 'delta') {
          const last = messages.value[messages.value.length - 1]
          if (last?.role === 'assistant') last.content += data?.content || ''
          scrollBottom()
        } else if (event === 'done') {
          const last = messages.value[messages.value.length - 1]
          if (last?.role === 'assistant') {
            last.streaming = false
            if (!last.content) last.content = '（没有收到内容，再试一次吧）'
          }
        } else if (event === 'error') {
          const last = messages.value[messages.value.length - 1]
          if (last?.role === 'assistant') {
            last.streaming = false
            last.content = data?.detail || 'AI 响应失败，请稍后重试'
          }
          notice.value = data?.detail || 'AI 响应失败，请稍后重试'
        }
      }
    })
  } catch (e) {
    if (token !== streamToken) return
    const last = messages.value[messages.value.length - 1]
    if (e?.name === 'AbortError') {
      if (last?.role === 'assistant') {
        last.streaming = false
        if (last.content) last.content += '\n\n（已停止生成，本次回复未保存）'
        else last.content = '（已停止生成，本次回复未保存）'
      }
    } else {
      if (last?.role === 'assistant') {
        last.streaming = false
        last.content = e?.detail || e?.message || '发送失败，请稍后重试'
      }
      notice.value = e?.detail || e?.message || '发送失败，请稍后重试'
    }
  } finally {
    if (token === streamToken) {
      const last = messages.value[messages.value.length - 1]
      if (last?.role === 'assistant') last.streaming = false
      sending.value = false
      controller = null
      await nextTick()
      scrollBottom()
    }
  }
}

function formatDate (value) {
  const date = parseServerDate(value)
  if (!date) return ''
  return date.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(async () => {
  await Promise.allSettled([loadSessions(), loadSeriousMode()])
})

onUnmounted(() => {
  if (controller) controller.abort()
})
</script>

<style scoped>
.chat-view { min-height: 60vh; }
.chat-layout { display: grid; grid-template-columns: 260px 1fr; gap: 16px; }
.chat-side { padding: 16px; }
.chat-main { display: flex; flex-direction: column; min-height: 60vh; padding: 0; overflow: hidden; }

.chat-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: var(--border-hairline);
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 600;
}

.chat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--success);
}

.chat-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.chat-new-mobile { display: none; }

.serious-pill {
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--warn-soft);
  color: var(--warn);
  font-size: 9px;
  font-weight: 400;
}

.help-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border: var(--border-hairline);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 11px;
  cursor: pointer;
}

.help-toggle:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.chat-persona {
  padding: 7px 16px;
  border-bottom: var(--border-hairline);
}

.chat-main :deep(.safety-notice) {
  margin: 10px 16px 0;
}

.serious-note {
  margin: 10px 16px 0;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--warn-soft);
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

.session-select {
  display: none;
  width: calc(100% - 32px);
  margin: 10px 16px 0;
}

.chat-notice {
  margin: 10px 16px 0;
  padding: 7px 10px;
  border-radius: var(--radius-sm);
  background: var(--warn-soft);
  color: var(--muted);
  font-size: 12px;
}

.messages {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 58vh;
  padding: 20px;
  overflow-y: auto;
}

.msg { display: flex; gap: 8px; align-items: flex-start; max-width: 82%; }
.msg.user { align-self: flex-end; flex-direction: row-reverse; }

.msg-role {
  flex: 0 0 auto;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-size: 11px;
  font-weight: 550;
}

.msg.user .msg-role { background: var(--success-soft); color: var(--success); }

.msg-content {
  padding: 10px 14px;
  border: var(--border-hairline);
  border-radius: var(--radius-md);
  background: var(--bg);
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.msg.user .msg-content { background: var(--accent-soft); border-color: transparent; }

.stream-cursor {
  display: inline-block;
  width: 5px;
  height: 14px;
  margin-left: 2px;
  border-radius: 1px;
  background: var(--accent);
  vertical-align: -2px;
  animation: cursor-blink 900ms step-end infinite;
}

@keyframes cursor-blink {
  50% { opacity: 0; }
}

.chat-empty {
  margin: auto;
  text-align: center;
}

.prompt-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
  margin-top: 12px;
}

.prompt-chip {
  padding: 5px 10px;
  border: var(--border-hairline);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 11px;
  cursor: pointer;
}

.prompt-chip:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.chat-input { display: flex; gap: 8px; padding: 12px 16px; border-top: var(--border-hairline); }
.chat-input input { flex: 1; min-width: 0; }

.session-list { list-style: none; display: flex; flex-direction: column; gap: 4px; }

.session-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  width: 100%;
  padding: 10px 12px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  text-align: left;
  cursor: pointer;
}

.session-item:hover { background: color-mix(in oklch, var(--bg), var(--fg) 4%); }
.session-item.active { background: var(--accent-soft); border-color: transparent; }
.session-title { max-width: 100%; overflow: hidden; font-size: 14px; font-weight: 550; text-overflow: ellipsis; white-space: nowrap; }
.session-meta { color: var(--muted); font-size: 11px; }

@media (max-width: 768px) {
  .chat-layout { grid-template-columns: 1fr; }
  .chat-side { display: none; }
  .session-select { display: block; }
  .chat-new-mobile { display: inline-flex; }
  .chat-main { min-height: 62vh; }
  .messages { max-height: 52vh; padding: 16px; }
  .msg { max-width: 92%; }
}

@media (prefers-reduced-motion: reduce) {
  .stream-cursor { animation: none; }
}
</style>
