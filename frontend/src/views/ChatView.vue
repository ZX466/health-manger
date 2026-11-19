<template>
  <div class="chat-view">
    <div class="chat-layout">
      <!-- 会话列表 -->
      <aside class="chat-side card" aria-label="会话列表">
        <div class="section-head">
          <h2>会话</h2>
          <button class="btn btn--primary btn-sm" type="button" :disabled="creating" @click="createSession">＋ 新建</button>
        </div>
        <ul class="session-list">
          <li v-for="s in sessions" :key="s.id" class="session-row">
            <button
              class="session-item"
              :class="{ active: s.id === activeId }"
              type="button"
              @click="selectSession(s)"
            >
              <span class="session-title">{{ s.title || '新会话' }}</span>
              <span class="session-meta">{{ formatDate(s.updated_at) }}</span>
            </button>
            <div class="session-actions">
              <template v-if="pendingDeleteId === s.id">
                <button
                  class="session-confirm"
                  type="button"
                  :disabled="deletingId === s.id"
                  @click.stop="deleteSession(s)"
                >
                  {{ deletingId === s.id ? '删除中' : '确认' }}
                </button>
                <button class="session-cancel" type="button" @click.stop="pendingDeleteId = null">取消</button>
              </template>
              <button
                v-else
                class="session-delete"
                type="button"
                :aria-label="`删除会话 ${s.title || '新会话'}`"
                title="删除会话"
                @click.stop="pendingDeleteId = s.id"
              >
                <AppIcon name="trash" :size="14" />
              </button>
            </div>
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
            <span>{{ modeMeta.label }}</span>
            <span v-if="safetyBadge" class="serious-pill">{{ safetyBadge }}</span>
          </div>
          <div class="chat-actions">
            <button
              class="btn btn--primary btn-sm chat-new-mobile"
              type="button"
              :disabled="creating"
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

        <div class="mode-switch" role="group" aria-label="对话模式">
          <button
            v-for="item in modeOptions"
            :key="item.key"
            class="mode-btn"
            :class="{ active: mode === item.key }"
            type="button"
            :aria-pressed="mode === item.key"
            @click="setMode(item.key)"
          >
            <AppIcon :name="item.icon" :size="15" />
            {{ item.label }}
          </button>
        </div>
        <p class="mode-hint">{{ modeMeta.hint }}</p>

        <div v-if="mode === 'body'" class="tongue-bar">
          <button
            class="tongue-btn"
            type="button"
            :disabled="tongueLoading || sending || creating"
            @click="useTongueContext"
          >
            <AppIcon name="tongue" :size="15" />
            {{ tongueLoading ? '读取舌诊…' : '引用最近舌诊' }}
          </button>
          <span>把最近一次舌象结果带进对话，让建议更贴近你的体质。</span>
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
        <button
          v-if="activeSession"
          class="session-delete-mobile"
          type="button"
          :aria-label="`删除当前会话 ${activeSession.title || '新会话'}`"
          @click="deleteSession(activeSession)"
        >
          <AppIcon name="trash" :size="14" />
          {{ pendingDeleteId === activeSession.id ? '确认删除' : '删除当前会话' }}
        </button>

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

        <p v-if="notice" class="chat-notice" role="status">
          {{ notice }}
          <router-link
            v-if="noticeLink && notice.includes('舌诊')"
            class="chat-notice-link"
            :to="noticeLink.to"
          >
            {{ noticeLink.label }}
          </router-link>
        </p>

        <div
          ref="msgBox"
          class="messages"
          :aria-live="sending ? 'off' : 'polite'"
          :aria-busy="sending"
        >
          <div v-if="!messages.length" class="empty chat-empty">
            <p class="empty-title">{{ personaSerious ? '今天想从哪里开始？' : modeMeta.emptyTitle }}</p>
            <p>{{ personaSerious ? '不用组织好语言，想到哪说到哪。' : modeMeta.emptyText }}</p>
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
            :placeholder="activeId ? modeMeta.placeholder : `${modeMeta.placeholder}，发送时自动新建会话`"
            :disabled="sending || creating"
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
            :disabled="!input.trim() || creating"
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
import { useRoute } from 'vue-router'
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
const creating = ref(false)
let disposed = false
const notice = ref('')
const noticeLink = ref(null)
const tongueLoading = ref(false)
const pendingDeleteId = ref(null)
const deletingId = ref(null)
const route = useRoute()
const showHelp = ref(false)
const seriousMode = ref(false)
const mode = ref(route.query.mode === 'mental' ? 'mental' : 'body')
const msgBox = ref(null)
const currentSafety = ref({ level: 'normal', crisis: false, resources: [] })

let controller = null
let loadToken = 0
let streamToken = 0
let messageSeq = 0

const modeOptions = [
  { key: 'body', label: '身体问诊', icon: 'activity' },
  { key: 'mental', label: '心理树洞', icon: 'mood' }
]

const MODE_META = {
  body: {
    label: '身体问诊',
    hint: '说清楚哪里不舒服、多久了；AI 会结合你的健康记录给建议，不替代医生诊断。',
    emptyTitle: '身体哪里不太对劲？',
    emptyText: '睡眠、肠胃、头疼、体检单上的箭头，都可以直接说。',
    placeholder: '描述一下身体的不舒服…'
  },
  mental: {
    label: '心理树洞',
    hint: '这里不评判、不催你振作。想骂人、想哭、想沉默一会儿都可以。',
    emptyTitle: '今天心里堵着什么？',
    emptyText: '不用组织好语言，想到哪说到哪。有风险时，安全支持会先接管。',
    placeholder: '想说什么就说什么…'
  }
}

const activeSession = computed(() =>
  sessions.value.find(s => String(s.id) === String(activeId.value)) || null
)

const modeMeta = computed(() => {
  if (personaSerious.value) {
    return {
      ...MODE_META[mode.value],
      hint: '最近的状态值得被认真对待。这里不玩梗，也不用一个人扛。',
      emptyTitle: '今天想从哪里开始？',
      emptyText: '不用组织好语言，想到哪说到哪。'
    }
  }
  return MODE_META[mode.value]
})

const quickPrompts = computed(() => {
  // 与人设使用同一有效安全状态：摘要失败但 SSE 已报 high/crisis 时也不能出现玩梗快捷词。
  if (mode.value === 'mental') {
    return personaSerious.value
      ? ['我最近总是睡不好', '脑子里停不下来', '想找人说说']
      : ['今天有点破防', '压力大到不想说话', '想找个地方倒垃圾']
  }
  return personaSerious.value
    ? ['我最近总是睡不好', '身体一直不太舒服', '想找人说说']
    : ['最近总是睡不好', '吃完饭胃不舒服', '帮我看看今天的记录']
})

const isCrisis = computed(() => currentSafety.value.crisis || currentSafety.value.level === 'crisis')
const safetyLevel = computed(() => {
  if (isCrisis.value) return 'crisis'
  if (currentSafety.value.level === 'high') return 'serious'
  if (currentSafety.value.level === 'elevated') return 'elevated'
  return 'info'
})

const showSafety = computed(() =>
  showHelp.value ||
  seriousMode.value ||
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

function setMode (next) {
  if (mode.value === next) return
  mode.value = next
  notice.value = next === 'mental'
    ? '已切到心理树洞。新会话会套用树洞引导，当前会话内容不会丢。'
    : '已切到身体问诊。新会话会优先结合健康记录。'
}

function detachStream () {
  streamToken += 1
  if (controller) controller.abort()
  controller = null
  sending.value = false
}

async function createSession () {
  if (creating.value) return
  creating.value = true
  if (sending.value) detachStream()
  loadToken += 1
  try {
    const contextType = mode.value === 'body' ? 'health' : 'general'
    const title = mode.value === 'body' ? '身体问诊 · 新会话' : '心理树洞 · 新会话'
    const { data } = await api.createChatSession({ title, context_type: contextType })
    if (disposed) return
    loadToken += 1
    sessions.value = [data, ...sessions.value]
    activeId.value = data.id
    messages.value = []
    pendingDeleteId.value = null
    notice.value = ''
    resetSafety()
    await nextTick()
    scrollBottom(true)
  } catch (e) {
    notice.value = '创建会话失败，请稍后重试'
  } finally {
    creating.value = false
  }
}

function onSelectChange (event) {
  const session = sessions.value.find(s => String(s.id) === String(event.target.value))
  if (session) selectSession(session)
}

async function selectSession (session) {
  if (sending.value) detachStream()
  pendingDeleteId.value = null
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

async function deleteSession (session) {
  if (!session || deletingId.value) return
  if (pendingDeleteId.value !== session.id) {
    pendingDeleteId.value = session.id
    return
  }
  deletingId.value = session.id
  try {
    // 删除一开始就取消同会话的在途流，避免 DELETE 响应前仍有助手消息写入。
    if (String(activeId.value) === String(session.id) && sending.value) detachStream()
    await api.deleteChatSession(session.id)
    sessions.value = sessions.value.filter(s => String(s.id) !== String(session.id))
    notice.value = '会话已删除'
    // 删除完成时按「当前」activeId 判断：等待期间用户可能已切换会话。
    if (String(activeId.value) === String(session.id)) {
      if (sending.value) detachStream()
      loadToken += 1 // 作废被删会话的在途历史请求，避免晚到响应回填
      activeId.value = null
      messages.value = []
      pendingDeleteId.value = null
      if (sessions.value.length) {
        await selectSession(sessions.value[0])
      } else {
        resetSafety()
      }
    }
  } catch (e) {
    notice.value = e?.response?.data?.detail || '删除会话失败，请稍后重试'
  } finally {
    deletingId.value = null
    pendingDeleteId.value = null
  }
}

function usePrompt (prompt) {
  input.value = prompt
  send()
}

async function useTongueContext () {
  if (tongueLoading.value || sending.value || creating.value) return
  tongueLoading.value = true
  notice.value = ''
  noticeLink.value = null
  try {
    if (!activeId.value) await createSession()
    if (!activeId.value) return
    await api.addTongueContext(activeId.value)
    input.value = '请结合我的舌诊结果，分析我的体质特点，并给出 3 条可执行的调理建议。'
    tongueLoading.value = false
    send()
  } catch (e) {
    const status = e?.response?.status
    const detail = e?.response?.data?.detail
    if (status === 404) {
      // 全局 404 处理器会统一返回“请求的资源不存在”，这里按场景给可操作文案。
      notice.value = '暂无舌诊记录，请先上传一张舌象图片'
      noticeLink.value = { to: '/tongue-diagnosis', label: '去舌诊' }
    } else {
      notice.value = detail || '舌诊上下文添加失败，请稍后重试'
    }
  } finally {
    tongueLoading.value = false
  }
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
  if (!content || sending.value || creating.value) return

  if (!activeId.value) {
    await createSession()
    // 等待建会话期间已离开页面：本次发送作废，不能继续发起流式请求。
    if (disposed || !activeId.value) return
  }

  // 发送会接管当前会话：作废尚未返回的历史请求，避免它覆盖刚发出的消息。
  loadToken += 1
  input.value = ''
  notice.value = ''
  noticeLink.value = null
  const token = ++streamToken
  const replyId = `local-${++messageSeq}`
  messages.value.push({ role: 'user', content })
  messages.value.push({ role: 'assistant', content: '', streaming: true, id: replyId })
  sending.value = true
  // 不在每次发送时清空安全状态：上一轮的高风险/危机提示要保留到新事件覆盖。
  const requestController = new AbortController()
  controller = requestController
  await nextTick()
  scrollBottom(true)

  const findReply = () => messages.value.find(m => m.id === replyId)

  try {
    await api.streamChatMessage(activeId.value, content, {
      signal: requestController.signal,
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
          const reply = findReply()
          if (reply) {
            reply.content += data?.content || ''
            scrollBottom()
          }
        } else if (event === 'done') {
          const reply = findReply()
          if (reply) {
            reply.streaming = false
            if (!reply.content) reply.content = '（没有收到内容，再试一次吧）'
          }
        } else if (event === 'error') {
          const reply = findReply()
          if (reply) {
            reply.streaming = false
            reply.content = data?.detail || 'AI 响应失败，请稍后重试'
          }
          notice.value = data?.detail || 'AI 响应失败，请稍后重试'
        }
      }
    })
  } catch (e) {
    if (token !== streamToken) return
    const reply = findReply()
    if (e?.name === 'AbortError') {
      if (reply) {
        reply.streaming = false
        if (reply.content) reply.content += '\n\n（已停止生成，本次回复未保存）'
        else reply.content = '（已停止生成，本次回复未保存）'
      }
    } else if (e?.code === 'STREAM_INCOMPLETE' || e?.name === 'StreamIncompleteError') {
      if (reply) {
        reply.streaming = false
        if (reply.content) reply.content += '\n\n（连接中断，本次回复未保存）'
        else reply.content = '连接中断，未收到完整回复，请再试一次。'
      }
      notice.value = '连接中断，未收到完整回复'
    } else {
      if (reply) {
        reply.streaming = false
        reply.content = e?.detail || e?.message || '发送失败，请稍后重试'
      }
      notice.value = e?.detail || e?.message || '发送失败，请稍后重试'
    }
  } finally {
    if (token === streamToken) {
      const reply = findReply()
      if (reply) reply.streaming = false
      sending.value = false
      if (controller === requestController) controller = null
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
  disposed = true
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

.mode-switch {
  display: flex;
  gap: 6px;
  margin: 10px 16px 0;
  padding: 4px;
  border: var(--border-hairline);
  border-radius: 999px;
  background: var(--bg);
}

.mode-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  flex: 1;
  min-height: 34px;
  padding: 0 10px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}

.mode-btn:hover { color: var(--fg); }

.mode-btn.active {
  background: var(--surface);
  color: var(--accent-strong);
  box-shadow: var(--shadow-sm);
}

.mode-hint {
  margin: 6px 18px 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.6;
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

.tongue-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 7px;
  margin: 8px 16px 0;
}

.tongue-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 30px;
  padding: 0 10px;
  border: 1px dashed color-mix(in oklch, var(--accent) 38%, var(--line));
  border-radius: 999px;
  background: var(--surface);
  color: var(--accent-strong);
  font-size: 11px;
  font-weight: 650;
  cursor: pointer;
}

.tongue-btn:hover {
  background: var(--accent-soft);
  border-style: solid;
}

.tongue-btn:disabled {
  cursor: wait;
  opacity: 0.52;
}

.tongue-bar span {
  color: var(--muted);
  font-size: 10.5px;
  line-height: 1.5;
}

.chat-notice {
  margin: 10px 16px 0;
  padding: 7px 10px;
  border-radius: var(--radius-sm);
  background: var(--warn-soft);
  color: var(--muted);
  font-size: 12px;
}

.chat-notice-link {
  margin-left: 6px;
  color: var(--accent-strong);
  font-weight: 650;
  text-decoration: underline;
  text-underline-offset: 2px;
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
.session-row { display: flex; align-items: stretch; gap: 4px; }
.session-actions { display: flex; align-items: center; gap: 2px; }
.session-delete,
.session-confirm,
.session-cancel {
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--muted);
  cursor: pointer;
}
.session-delete { display: inline-flex; align-items: center; justify-content: center; width: 30px; }
.session-delete:hover { color: var(--danger, #c0392b); border-color: currentColor; }
.session-confirm,
.session-cancel { padding: 4px 6px; font-size: 12px; }
.session-confirm { color: var(--danger, #c0392b); border-color: currentColor; }
.session-cancel:hover { color: var(--fg); }
.session-delete-mobile { display: none; }

.session-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  flex: 1;
  min-width: 0;
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
  .session-delete-mobile {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin: 6px 16px 0;
    padding: 6px 10px;
    border: var(--border-hairline);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--muted);
    font-size: 12px;
    cursor: pointer;
  }
  .chat-new-mobile { display: inline-flex; }
  .chat-main { min-height: 62vh; }
  .messages { max-height: 52vh; padding: 16px; }
  .msg { max-width: 92%; }
}

@media (prefers-reduced-motion: reduce) {
  .stream-cursor { animation: none; }
}
</style>
