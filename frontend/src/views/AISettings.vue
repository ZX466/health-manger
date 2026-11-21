<template>
  <div class="ai-settings">
    <PageHead
      folio="08"
      eyebrow="SETTINGS / PERSONA"
      title="设置"
      deck="决定 AI 用什么画风陪你唠嗑，以及它几点该识相地闭嘴。"
    >
      <template #actions>
        <span class="status-chip" :class="seriousMode ? 'status-chip--warn' : 'status-chip--accent'">
          <span class="status-dot" :class="seriousMode ? 'status-dot--danger' : 'status-dot--success'"></span>
          {{ seriousMode ? '关怀模式优先' : '配置可用' }}
        </span>
      </template>
    </PageHead>

    <div class="settings-grid">
      <!-- 对话风格 -->
      <section class="persona-settings v21-panel">
        <div class="panel-head">
          <span class="micro">ASSISTANT TONE</span>
          <span class="micro">二选一</span>
        </div>
        <h2>AI 说话风格</h2>
        <PersonaCard :serious="seriousMode" />
      </section>

      <!-- 提醒 -->
      <section class="reminder-settings v21-panel">
        <div class="panel-head">
          <span class="micro">REMINDERS</span>
          <span class="micro">轻提醒</span>
        </div>
        <h2>提醒</h2>
        <label class="switch-row">
          <span><strong>早八保命提醒</strong><small>前一天 23:30 准时催你放下手机睡觉</small></span>
          <input type="checkbox" :checked="reminders.morning" @change="setReminder('morning', $event.target.checked)" />
          <i class="switch" aria-hidden="true"></i>
        </label>
        <label class="switch-row">
          <span><strong>喝水续命提醒</strong><small>每 2 小时戳你一次，考试周自动静音不添乱</small></span>
          <input type="checkbox" :checked="reminders.water" @change="setReminder('water', $event.target.checked)" />
          <i class="switch" aria-hidden="true"></i>
        </label>
        <label class="switch-row">
          <span><strong>睡前关机呼吸</strong><small>睡前 10 分钟，拉你做一轮 4-7-8 放空仪式</small></span>
          <input type="checkbox" :checked="reminders.breath" @change="setReminder('breath', $event.target.checked)" />
          <i class="switch" aria-hidden="true"></i>
        </label>
        <label class="switch-row">
          <span><strong>高危关怀</strong><small>检测到风险时优先展示热线与校医院</small></span>
          <input type="checkbox" checked disabled />
          <i class="switch" aria-hidden="true"></i>
        </label>
        <p class="fineprint">浏览器推送尚未接入，提醒偏好只保存在本机；高危关怀始终强制开启。</p>
      </section>

      <!-- 健康目标 -->
      <section class="goal-settings v21-panel">
        <div class="panel-head">
          <span class="micro">GOALS</span>
          <span class="micro">可随时改</span>
        </div>
        <h2>健康目标</h2>
        <div class="goal-grid">
          <label class="field">
            <span>每日睡眠 <em>小时</em></span>
            <input v-model.number="goals.sleep" type="number" min="4" max="12" step="0.5" @change="saveGoals" />
          </label>
          <label class="field">
            <span>每日步数</span>
            <input v-model.number="goals.steps" type="number" min="1000" step="500" @change="saveGoals" />
          </label>
          <label class="field">
            <span>每日热量 <em>kcal</em></span>
            <input v-model.number="goals.calories" type="number" min="800" step="50" @change="saveGoals" />
          </label>
        </div>
        <p class="fineprint">保存后用于总览睡眠目标与饮食热量目标；步数等待设备接入后生效。</p>
      </section>

      <MediaSettings :serious="seriousMode" />

      <aside class="privacy-panel v21-panel">
        <div class="panel-head">
          <span class="micro">PRIVACY</span>
          <span class="micro">最小必要</span>
        </div>
        <h2>你的数据</h2>
        <p>健康记录、心情与对话只存放在你的账号下。高危状态优先展示求助入口，识别结果需要你确认后才会入库。</p>
        <ul class="check-list">
          <li><AppIcon name="check" :size="14" />高危状态优先展示求助入口</li>
          <li><AppIcon name="check" :size="14" />不把玩梗文案用于风险状态</li>
          <li><AppIcon name="check" :size="14" />识别结果需人工确认后保存</li>
        </ul>
      </aside>
    </div>

    <section class="models-section">
      <div class="section-head">
        <div>
          <p class="micro">SYSTEM / MODELS</p>
          <h2>模型与安全边界</h2>
        </div>
        <span class="pill" :class="seriousMode ? 'pill--warn' : 'pill--ok'">
          {{ seriousMode ? '关怀模式优先' : '高危状态优先于任何玩梗设置' }}
        </span>
      </div>
      <div class="models-grid">
        <section class="card v21-panel model-card">
          <div class="section-head">
            <h2>聊天 / 分析模型</h2>
            <span class="pill" :class="chatSaved ? 'pill--ok' : 'pill--warn'">{{ chatSaved ? '已配置' : '默认' }}</span>
          </div>
          <p class="hint">用于 AI 对话、健康分析、快速评估。请选择文本对话模型（如 GLM-4.5 / GPT-4o / Doubao）。</p>
          <AiModelForm :providers="providers" :form="chatForm" :saved="chatSaved"
            :testing="chatTesting" :saving="chatSaving" :result="chatResult" uid="chat"
            @update:form="chatForm = $event" @test="testChat" @save="saveChat" @reset="resetChat" />
        </section>

        <section class="card v21-panel model-card">
          <div class="section-head">
            <h2>舌诊视觉模型</h2>
            <span class="pill" :class="visionSaved ? 'pill--ok' : 'pill--warn'">{{ visionSaved ? '已配置' : '默认 ARK' }}</span>
          </div>
          <p class="hint">用于舌诊、拍照识餐与体检 OCR。<strong>必须选择支持图像输入的视觉模型</strong>（如 glm-4v-plus / GPT-4o / Doubao-Vision）；纯文本模型会拒绝图片请求。</p>
          <AiModelForm :providers="visionProviders" :form="visionForm" :saved="visionSaved"
            :testing="visionTesting" :saving="visionSaving" :result="visionResult" uid="vision"
            @update:form="visionForm = $event" @test="testVision" @save="saveVision" @reset="resetVision" />
        </section>
      </div>
    </section>
  </div>
</template>

<script>
import api from '../api'
import AiModelForm from '../components/AiModelForm.vue'
import AppIcon from '../components/AppIcon.vue'
import MediaSettings from '../components/MediaSettings.vue'
import PageHead from '../components/PageHead.vue'
import PersonaCard from '../components/mental/PersonaCard.vue'
import { useWellnessStore } from '../stores/wellness'
import { usePreferences } from '../composables/usePreferences'
import { readApiError } from '../utils/apiError'

const CHAT_PROVIDERS = [
  { key: 'zhipu', label: '智谱 GLM', defaultUrl: 'https://open.bigmodel.cn/api/paas/v4/chat/completions', defaultModel: 'glm-4.5-Air' },
  { key: 'openai', label: 'OpenAI 兼容', defaultUrl: 'https://api.openai.com/v1/chat/completions', defaultModel: 'gpt-4o-mini' },
  { key: 'ark', label: '火山引擎 Ark', defaultUrl: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', defaultModel: 'doubao-seed-1-6-vision-250815' }
]
const VISION_PROVIDERS = [
  { key: 'zhipu', label: '智谱 GLM-4V', defaultUrl: 'https://open.bigmodel.cn/api/paas/v4/chat/completions', defaultModel: 'glm-4v-plus' },
  { key: 'openai', label: 'OpenAI 兼容视觉', defaultUrl: 'https://api.openai.com/v1/chat/completions', defaultModel: 'gpt-4o' },
  { key: 'ark', label: '火山 Ark 视觉', defaultUrl: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', defaultModel: 'doubao-seed-1-6-vision-250815' }
]

export default {
  name: 'AISettings',
  components: { AiModelForm, AppIcon, MediaSettings, PageHead, PersonaCard },
  setup() {
    const { goals, reminders, saveGoals, saveReminders } = usePreferences()
    return { goals, reminders, saveGoals, saveReminders }
  },
  data() {
    return {
      providers: CHAT_PROVIDERS,
      visionProviders: VISION_PROVIDERS,
      localSerious: false,
      wellness: null,
      chatForm: { provider: 'zhipu', base_url: '', model: '', api_key: '' },
      visionForm: { provider: 'ark', base_url: '', model: '', api_key: '' },
      chatSaved: false, visionSaved: false,
      chatTesting: false, visionTesting: false,
      chatSaving: false, visionSaving: false,
      chatResult: null, visionResult: null
    }
  },
  computed: {
    seriousMode() {
      return !!this.wellness?.isDanger || this.localSerious
    }
  },
  created() {
    this.wellness = useWellnessStore()
  },
  async mounted() {
    await Promise.allSettled([this.loadConfig(), this.loadSeriousMode(), this.wellness?.load()])
  },
  methods: {
    setReminder(key, value) {
      this.saveReminders({ ...this.reminders, [key]: value })
    },
    async loadSeriousMode() {
      try {
        const { data } = await api.getMentalSummary()
        this.localSerious = !!data?.serious_mode
        if (data?.serious_mode) this.wellness?.markSerious()
      } catch (e) { /* 摘要不可用时不阻塞设置 */ }
    },
    async loadConfig() {
      try {
        const r = await api.getAiConfig()
        const d = r.data
        // 聊天
        this.chatForm.provider = d.provider || 'zhipu'
        this.chatForm.base_url = d.base_url || this.presetUrl(CHAT_PROVIDERS, d.provider)
        this.chatForm.model = d.model || this.presetModel(CHAT_PROVIDERS, d.provider)
        this.chatForm.api_key = ''
        this.chatSaved = !!d.has_api_key
        // 视觉
        this.visionForm.provider = d.vision_provider || 'ark'
        this.visionForm.base_url = d.vision_base_url || this.presetUrl(VISION_PROVIDERS, d.vision_provider)
        this.visionForm.model = d.vision_model || this.presetModel(VISION_PROVIDERS, d.vision_provider)
        this.visionForm.api_key = ''
        this.visionSaved = !!d.has_vision_api_key
      } catch (e) { /* silent */ }
    },
    presetUrl(list, key) {
      return (list.find(p => p.key === key) || {}).defaultUrl || ''
    },
    presetModel(list, key) {
      return (list.find(p => p.key === key) || {}).defaultModel || ''
    },
    async testChat() {
      this.chatTesting = true
      try {
        const r = await api.testAiConfig({
          provider: this.chatForm.provider, model: this.chatForm.model,
          base_url: this.chatForm.base_url, api_key: this.chatForm.api_key || undefined
        })
        this.chatResult = r.data
      } catch (e) { this.chatResult = { success: false, message: readApiError(e, '连接失败：网络或参数错误') } }
      finally { this.chatTesting = false }
    },
    async testVision() {
      this.visionTesting = true
      try {
        const r = await api.testAiConfig({
          provider: this.visionForm.provider, model: this.visionForm.model,
          base_url: this.visionForm.base_url, api_key: this.visionForm.api_key || undefined
        })
        this.visionResult = r.data
      } catch (e) { this.visionResult = { success: false, message: readApiError(e, '连接失败：网络或参数错误') } }
      finally { this.visionTesting = false }
    },
    async saveChat() {
      if (!this.chatForm.model) return alert('请填写聊天模型名称')
      this.chatSaving = true
      try {
        await api.saveAiConfig({
          provider: this.chatForm.provider, model: this.chatForm.model,
          base_url: this.chatForm.base_url, api_key: this.chatForm.api_key || undefined
        })
        this.chatSaved = true
        this.chatForm.api_key = ''
        this.chatResult = { success: true, message: '聊天模型已保存（API Key 加密存储）' }
      } catch (e) { this.chatResult = { success: false, message: '保存失败：' + readApiError(e) } }
      finally { this.chatSaving = false }
    },
    async saveVision() {
      if (!this.visionForm.model) return alert('请填写舌诊视觉模型名称')
      this.visionSaving = true
      try {
        await api.saveAiConfig({
          vision_provider: this.visionForm.provider, vision_model: this.visionForm.model,
          vision_base_url: this.visionForm.base_url, vision_api_key: this.visionForm.api_key || undefined
        })
        this.visionSaved = true
        this.visionForm.api_key = ''
        this.visionResult = { success: true, message: '舌诊视觉模型已保存' }
      } catch (e) { this.visionResult = { success: false, message: '保存失败：' + readApiError(e) } }
      finally { this.visionSaving = false }
    },
    async resetChat() {
      if (!confirm('确认恢复默认聊天模型？')) return
      try {
        await api.deleteAiConfig()
        this.chatSaved = false
        this.chatForm = { provider: 'zhipu', base_url: this.presetUrl(CHAT_PROVIDERS, 'zhipu'), model: this.presetModel(CHAT_PROVIDERS, 'zhipu'), api_key: '' }
        this.chatResult = { success: true, message: '已恢复默认' }
      } catch (e) { /* silent */ }
    },
    async resetVision() {
      if (!confirm('确认恢复默认舌诊视觉模型？')) return
      try {
        await api.saveAiConfig({ vision_provider: 'ark', vision_model: 'doubao-seed-1-6-vision-250815', vision_base_url: this.presetUrl(VISION_PROVIDERS, 'ark'), vision_api_key: '' })
        this.visionSaved = false
        this.visionForm = { provider: 'ark', base_url: this.presetUrl(VISION_PROVIDERS, 'ark'), model: this.presetModel(VISION_PROVIDERS, 'ark'), api_key: '' }
        this.visionResult = { success: true, message: '已恢复默认 ARK 视觉模型' }
      } catch (e) { /* silent */ }
    }
  }
}
</script>

<style scoped>
.ai-settings { display: flex; flex-direction: column; gap: 18px; }

.hint { font-size: 12px; color: var(--muted); line-height: 1.7; }

.settings-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.persona-settings,
.reminder-settings,
.goal-settings,
.privacy-panel {
  display: flex;
  flex-direction: column;
  padding: 20px 22px;
}

.persona-settings h2,
.reminder-settings h2,
.goal-settings h2,
.privacy-panel h2 {
  margin: 0 0 12px;
  font-family: var(--font-display);
  font-size: 20px;
  letter-spacing: -0.02em;
}

.persona-settings :deep(.persona-head) {
  justify-content: flex-end;
  margin-bottom: 8px;
}

.persona-settings :deep(.persona-head > div),
.persona-settings :deep(.persona-intro) {
  display: none;
}

.persona-settings :deep(.persona-card) {
  padding: 0;
  border: 0;
  background: transparent;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-top: 1px solid var(--line);
  cursor: pointer;
}

.switch-row:first-of-type { border-top: 0; }
.switch-row > span { display: flex; flex-direction: column; gap: 2px; }
.switch-row strong { font-size: 12.5px; }
.switch-row small { color: var(--muted); font-size: 10.5px; line-height: 1.55; }
.switch-row input { position: absolute; opacity: 0; pointer-events: none; }

.switch {
  position: relative;
  width: 36px;
  height: 20px;
  flex: 0 0 auto;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: var(--surface-2);
  transition: background var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out);
}

.switch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--surface);
  box-shadow: 0 1px 2px oklch(20% 0.02 250 / 0.18);
  transition: transform var(--duration-fast) var(--ease-out);
}

.switch-row input:checked + .switch { border-color: var(--accent); background: var(--accent); }
.switch-row input:checked + .switch::after { transform: translateX(16px); }
.switch-row input:disabled + .switch { opacity: 0.55; }

.goal-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.field { display: flex; flex-direction: column; gap: 5px; }
.field > span { color: var(--muted); font-size: 10px; }
.field em { color: var(--muted-2); font-style: normal; }
.field input {
  width: 100%;
  min-height: 36px;
  padding: 0 9px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  font-family: var(--font-mono);
  font-size: 12px;
}

.field input:focus { outline: 2px solid var(--accent); outline-offset: 1px; }

.privacy-panel { background: var(--surface-2); }
.privacy-panel > p { margin: 0 0 10px; color: var(--muted); font-size: 12px; line-height: 1.7; }
.check-list { display: flex; flex-direction: column; gap: 6px; margin: 0; padding: 0; list-style: none; }
.check-list li { display: flex; align-items: center; gap: 6px; color: var(--muted); font-size: 11.5px; }
.check-list :deep(svg) { color: var(--success); }

.fineprint { margin: 8px 0 0; color: var(--muted-2); font-size: 10px; line-height: 1.6; }

.models-section { display: flex; flex-direction: column; gap: 12px; margin-top: 4px; }
.models-section .section-head { align-items: flex-end; }
.models-section .section-head h2 { margin: 2px 0 0; font-family: var(--font-display); font-size: 20px; }
.models-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; align-items: start; }
.model-card { display: flex; flex-direction: column; gap: 8px; }
.model-card .section-head { margin-bottom: 0; }
.model-card .hint { margin: 0; }
.model-card :deep(.ai-model-form) { margin-top: 4px; }

@media (max-width: 980px) {
  .settings-grid,
  .models-grid { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .persona-settings,
  .reminder-settings,
  .goal-settings,
  .privacy-panel { padding: 18px; }
  .goal-grid { grid-template-columns: 1fr; }
}
</style>
