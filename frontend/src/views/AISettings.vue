<template>
  <div class="ai-settings">
    <section class="card">
      <div class="section-head">
        <h2>AI 模型配置</h2>
        <span class="pill" :class="saved ? 'pill--ok' : 'pill--warn'">{{ saved ? '已保存' : '默认' }}</span>
      </div>
      <p class="hint">选择你偏好的 AI 供应商与模型，之后 AI 健康分析 / 聊天将使用你的配置（每用户独立，API Key 加密存储）。</p>

      <div class="field" style="margin-top:16px">
        <label for="ai-provider">供应商</label>
        <select id="ai-provider" v-model="form.provider" class="field-input" @change="applyProviderPreset">
          <option v-for="p in providers" :key="p.key" :value="p.key">{{ p.label }}</option>
        </select>
      </div>

      <div class="field" style="margin-top:12px">
        <label for="ai-base-url">Base URL（OpenAI 兼容接口）</label>
        <input id="ai-base-url" v-model="form.base_url" class="field-input" placeholder="https://api.openai.com/v1/chat/completions" />
        <span class="hint">智谱/火山已预填，自定义时填写你自己的端点</span>
      </div>

      <div class="field" style="margin-top:12px">
        <label for="ai-model">模型名称</label>
        <input id="ai-model" v-model="form.model" class="field-input" placeholder="glm-4.5-Air / gpt-4o / doubao-seed..." />
      </div>

      <div class="field" style="margin-top:12px">
        <label for="ai-key">API Key{{ hasApiKey ? '（已配置，留空则不修改）' : '' }}</label>
        <input id="ai-key" v-model="form.api_key" class="field-input" type="password" :placeholder="hasApiKey ? '••••••••（已保存，留空保持原样）' : 'sk-...'" />
      </div>

      <div class="modal-actions" style="margin-top:20px">
        <button class="btn btn--ghost" type="button" @click="testConfig" :disabled="testing">
          {{ testing ? '测试中…' : '测试连接' }}
        </button>
        <button class="btn btn--primary" type="button" @click="saveConfig" :disabled="saving">
          {{ saving ? '保存中…' : '保存配置' }}
        </button>
        <button v-if="hasApiKey" class="btn btn--danger btn-sm" type="button" @click="resetConfig">恢复默认</button>
      </div>

      <div v-if="testResult" class="field" style="margin-top:16px" :class="{ 'field--error': !testResult.success }">
        <p class="hint" :style="{ color: testResult.success ? 'var(--success)' : 'var(--danger)' }">
          {{ testResult.message }}
        </p>
      </div>
    </section>
  </div>
</template>

<script>
import api from '../api'

const PROVIDERS = [
  { key: 'zhipu', label: '智谱 GLM', defaultUrl: 'https://open.bigmodel.cn/api/paas/v4/chat/completions', defaultModel: 'glm-4.5-Air' },
  { key: 'openai', label: 'OpenAI 兼容', defaultUrl: 'https://api.openai.com/v1/chat/completions', defaultModel: 'gpt-4o-mini' },
  { key: 'ark', label: '火山引擎 Ark', defaultUrl: 'https://ark.cn-beijing.volces.com/api/v3/chat/completions', defaultModel: 'doubao-seed-1-6-vision-250815' }
]

export default {
  name: 'AISettings',
  data() {
    return {
      providers: PROVIDERS,
      form: { provider: 'zhipu', base_url: '', model: '', api_key: '' },
      hasApiKey: false,
      saved: false,
      saving: false,
      testing: false,
      testResult: null
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
        this.form.provider = d.provider || 'zhipu'
        this.form.base_url = d.base_url || this.presetUrl(d.provider)
        this.form.model = d.model || this.presetModel(d.provider)
        this.form.api_key = ''
        this.hasApiKey = !!d.has_api_key
        this.saved = !!d.has_api_key
      } catch (e) { /* silent */ }
    },
    presetUrl(provider) {
      return (PROVIDERS.find(p => p.key === provider) || {}).defaultUrl || ''
    },
    presetModel(provider) {
      return (PROVIDERS.find(p => p.key === provider) || {}).defaultModel || ''
    },
    applyProviderPreset() {
      const url = this.presetUrl(this.form.provider)
      if (!this.form.base_url || this.form.base_url === this.presetUrl(this.oldProvider)) {
        this.form.base_url = url
      }
      this.oldProvider = this.form.provider
    },
    async testConfig() {
      this.testing = true
      this.testResult = null
      try {
        const r = await api.testAiConfig({
          provider: this.form.provider,
          model: this.form.model,
          base_url: this.form.base_url,
          api_key: this.form.api_key || undefined
        })
        this.testResult = r.data
      } catch (e) {
        this.testResult = { success: false, message: '连接失败：网络或参数错误' }
      } finally {
        this.testing = false
      }
    },
    async saveConfig() {
      if (!this.form.model) return alert('请填写模型名称')
      this.saving = true
      try {
        await api.saveAiConfig({
          provider: this.form.provider,
          model: this.form.model,
          base_url: this.form.base_url,
          api_key: this.form.api_key || undefined
        })
        this.saved = true
        this.hasApiKey = this.hasApiKey || !!this.form.api_key
        this.form.api_key = ''
        this.testResult = { success: true, message: '配置已保存（API Key 加密存储）' }
      } catch (e) {
        this.testResult = { success: false, message: '保存失败：' + (e.response?.data?.detail || e.message) }
      } finally {
        this.saving = false
      }
    },
    async resetConfig() {
      if (!confirm('确认恢复默认 AI 配置？')) return
      try {
        await api.deleteAiConfig()
        this.hasApiKey = false
        this.saved = false
        this.form = { provider: 'zhipu', base_url: this.presetUrl('zhipu'), model: this.presetModel('zhipu'), api_key: '' }
        this.testResult = { success: true, message: '已恢复默认智谱配置' }
      } catch (e) { /* silent */ }
    }
  }
}
</script>

<style scoped>
.ai-settings { max-width: 560px; }
.hint { font-size: 13px; color: var(--muted); line-height: 1.7; }
</style>
