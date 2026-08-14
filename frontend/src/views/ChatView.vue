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
          <li
            v-for="s in sessions" :key="s.id"
            :class="['session-item', { active: s.id === activeId }]"
            @click="selectSession(s)"
          >
            <div class="session-title">{{ s.title || '新会话' }}</div>
            <div class="session-meta">{{ formatDate(s.updated_at) }}</div>
          </li>
          <li v-if="!sessions.length" class="empty">
            <p class="empty-title">暂无会话</p>
            <p>点击「新建」开始对话</p>
          </li>
        </ul>
      </aside>

      <!-- 消息区 -->
      <section class="chat-main card">
        <div ref="msgBox" class="messages" aria-live="polite">
          <div v-if="!messages.length" class="empty">
            <p class="empty-title">开始健康咨询</p>
            <p>可以问：我的血压正常吗？怎么改善睡眠？</p>
          </div>
          <div v-for="(m, i) in messages" :key="i" :class="['msg', m.role]">
            <span class="msg-role">{{ m.role === 'assistant' ? 'AI' : '我' }}</span>
            <div class="msg-content">{{ m.content }}</div>
          </div>
        </div>
        <form class="chat-input" @submit.prevent="send">
          <input
            v-model="input"
            class="field-input"
            placeholder="输入你的健康问题..."
            :disabled="!activeId || sending"
            aria-label="消息内容"
          />
          <button class="btn btn--primary" type="submit" :disabled="!activeId || !input.trim() || sending">
            {{ sending ? '思考中…' : '发送' }}
          </button>
        </form>
      </section>
    </div>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'ChatView',
  data() {
    return {
      sessions: [],
      activeId: null,
      messages: [],
      input: '',
      sending: false
    }
  },
  async mounted() {
    await this.loadSessions()
  },
  methods: {
    async loadSessions() {
      try {
        const r = await api.getChatSessions({ limit: 20 })
        this.sessions = r.data || []
      } catch (e) { /* silent */ }
    },
    async createSession() {
      try {
        const r = await api.createChatSession({ title: '新会话', context_type: 'general' })
        this.sessions.unshift(r.data)
        await this.selectSession(r.data)
      } catch (e) {
        alert('创建会话失败，请稍后重试')
      }
    },
    async selectSession(s) {
      this.activeId = s.id
      this.messages = []
      try {
        const r = await api.getChatMessages(s.id, { limit: 50 })
        this.messages = r.data || []
        this.$nextTick(() => this.scrollBottom())
      } catch (e) { /* silent */ }
    },
    async send() {
      const content = this.input.trim()
      if (!content || !this.activeId) return
      this.input = ''
      this.messages.push({ role: 'user', content })
      this.sending = true
      try {
        const r = await api.sendChatMessage(this.activeId, { content })
        this.messages.push({ role: 'assistant', content: r.data.response || '（无回复）' })
        this.$nextTick(() => this.scrollBottom())
      } catch (e) {
        this.messages.push({ role: 'assistant', content: '（发送失败，请稍后重试）' })
      } finally {
        this.sending = false
      }
    },
    scrollBottom() {
      if (this.$refs.msgBox) this.$refs.msgBox.scrollTop = this.$refs.msgBox.scrollHeight
    },
    formatDate(d) {
      if (!d) return ''
      const dt = new Date(d)
      return dt.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
    }
  }
}
</script>

<style scoped>
.chat-view { min-height: 60vh; }
.chat-layout { display: grid; grid-template-columns: 260px 1fr; gap: 16px; }
@media (max-width: 768px) { .chat-layout { grid-template-columns: 1fr; } .chat-side { display: none; } }
.chat-side { padding: 16px; }
.chat-main { display: flex; flex-direction: column; min-height: 60vh; padding: 0; overflow: hidden; }
.messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; max-height: 60vh; }
.msg { display: flex; gap: 8px; align-items: flex-start; max-width: 80%; }
.msg.user { align-self: flex-end; flex-direction: row-reverse; }
.msg-role { flex: 0 0 auto; padding: 2px 8px; border-radius: 999px; background: var(--accent-soft); color: var(--accent-strong); font-size: 12px; font-weight: 550; }
.msg.user .msg-role { background: var(--success-soft); color: var(--success); }
.msg-content { background: var(--bg); border: var(--border-hairline); border-radius: var(--radius-md); padding: 10px 14px; font-size: 14px; line-height: 1.75; }
.msg.user .msg-content { background: var(--accent-soft); border-color: transparent; }
.chat-input { display: flex; gap: 8px; padding: 12px 16px; border-top: var(--border-hairline); }
.chat-input input { flex: 1; }
.session-list { list-style: none; display: flex; flex-direction: column; gap: 4px; }
.session-item { padding: 10px 12px; border-radius: var(--radius-sm); cursor: pointer; border: var(--border-hairline); background: var(--surface); }
.session-item:hover { background: color-mix(in oklch, var(--bg), var(--fg) 4%); }
.session-item.active { background: var(--accent-soft); border-color: transparent; }
.session-title { font-size: 14px; font-weight: 550; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.session-meta { font-size: 11px; color: var(--muted); margin-top: 2px; }
</style>
