<template>
  <div class="ai-settings">
    <!-- 聊天/分析模型 -->
    <section class="card">
      <div class="section-head">
        <h2>聊天 / 分析模型</h2>
        <span class="pill" :class="chatSaved ? 'pill--ok' : 'pill--warn'">{{ chatSaved ? '已配置' : '默认' }}</span>
      </div>
      <p class="hint">用于 AI 对话、健康分析、快速评估。请选择文本对话模型（如 GLM-4.5 / GPT-4o / Doubao）。</p>
      <AiModelForm :providers="providers" :form="chatForm" :saved="chatSaved"
        :testing="chatTesting" :saving="chatSaving" :result="chatResult" uid="chat"
        @update:form="chatForm = $event" @test="testChat" @save="saveChat" @reset="resetChat" />
    </section>

    <!-- 舌诊视觉模型 -->
    <section class="card" style="margin-top:16px">
      <div class="section-head">
        <h2>舌诊视觉模型</h2>
        <span class="pill" :class="visionSaved ? 'pill--ok' : 'pill--warn'">{{ visionSaved ? '已配置' : '默认 ARK' }}</span>
      </div>
      <p class="hint">用于舌象图片分析。<strong>必须选择支持图像输入的视觉模型</strong>（如 GLM-4V / GPT-4o / Doubao-Vision），否则舌诊不可用。</p>
      <AiModelForm :providers="visionProviders" :form="visionForm" :saved="visionSaved"
        :testing="visionTesting" :saving="visionSaving" :result="visionResult" uid="vision"
        @update:form="visionForm = $event" @test="testVision" @save="saveVision" @reset="resetVision" />
    </section>
  </div>
</template>

<script>
import api from '../api'
import AiModelForm from '../components/AiModelForm.vue'

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
  components: { AiModelForm },
  data() {
    return {
      providers: CHAT_PROVIDERS,
      visionProviders: VISION_PROVIDERS,
      chatForm: { provider: 'zhipu', base_url: '', model: '', api_key: '' },
      visionForm: { provider: 'ark', base_url: '', model: '', api_key: '' },
      chatSaved: false, visionSaved: false,
      chatTesting: false, visionTesting: false,
      chatSaving: false, visionSaving: false,
      chatResult: null, visionResult: null
    }
  },
  async mounted() {
    await this.loadConfig()
  },
  methods: {
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
      } catch (e) { this.chatResult = { success: false, message: '连接失败：网络或参数错误' } }
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
      } catch (e) { this.visionResult = { success: false, message: '连接失败：网络或参数错误' } }
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
      } catch (e) { this.chatResult = { success: false, message: '保存失败：' + (e.response?.data?.detail || e.message) } }
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
      } catch (e) { this.visionResult = { success: false, message: '保存失败：' + (e.response?.data?.detail || e.message) } }
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
.ai-settings { max-width: 640px; }
.hint { font-size: 13px; color: var(--muted); line-height: 1.7; }
</style>
