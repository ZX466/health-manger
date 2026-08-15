<template>
  <div>
    <div class="field" style="margin-top:16px">
      <label :for="uid + '-provider'">供应商</label>
      <select :id="uid + '-provider'" class="field-input" :value="form.provider" @change="changeProvider">
        <option v-for="p in providers" :key="p.key" :value="p.key">{{ p.label }}</option>
      </select>
    </div>

    <div class="field" style="margin-top:12px">
      <label :for="uid + '-url'">Base URL（OpenAI 兼容接口）</label>
      <input :id="uid + '-url'" class="field-input" :value="form.base_url" @input="set('base_url', $event.target.value)" placeholder="https://api.openai.com/v1/chat/completions" />
    </div>

    <div class="field" style="margin-top:12px">
      <label :for="uid + '-model'">模型名称</label>
      <input :id="uid + '-model'" class="field-input" :value="form.model" @input="set('model', $event.target.value)" placeholder="glm-4.5-Air / gpt-4o / doubao-seed..." />
    </div>

    <div class="field" style="margin-top:12px">
      <label :for="uid + '-key'">API Key{{ saved ? '（已配置，留空则不修改）' : '' }}</label>
      <input :id="uid + '-key'" class="field-input" type="password" :value="form.api_key" @input="set('api_key', $event.target.value)" :placeholder="saved ? '••••••••（已保存，留空保持原样）' : 'sk-...'" />
    </div>

    <div class="modal-actions" style="margin-top:20px">
      <button class="btn btn--ghost" type="button" @click="$emit('test')" :disabled="testing">
        {{ testing ? '测试中…' : '测试连接' }}
      </button>
      <button class="btn btn--primary" type="button" @click="$emit('save')" :disabled="saving">
        {{ saving ? '保存中…' : '保存配置' }}
      </button>
      <button v-if="saved" class="btn btn--danger btn-sm" type="button" @click="$emit('reset')">恢复默认</button>
    </div>

    <div v-if="result" class="field" style="margin-top:16px">
      <p class="hint" :style="{ color: result.success ? 'var(--success)' : 'var(--danger)' }">
        {{ result.message }}
      </p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AiModelForm',
  props: {
    providers: { type: Array, required: true },
    form: { type: Object, required: true },
    saved: { type: Boolean, default: false },
    testing: { type: Boolean, default: false },
    saving: { type: Boolean, default: false },
    result: { type: Object, default: null },
    uid: { type: String, default: 'ai' }
  },
  methods: {
    set(key, value) {
      this.$emit('update:form', { ...this.form, [key]: value })
    },
    changeProvider(e) {
      const key = e.target.value
      const p = (this.providers.find(x => x.key === key) || {})
      const next = { ...this.form, provider: key }
      if (!this.form.base_url || this.presetUrl(this.form.provider) === this.form.base_url) {
        next.base_url = p.defaultUrl || ''
      }
      if (!this.form.model || this.presetModel(this.form.provider) === this.form.model) {
        next.model = p.defaultModel || ''
      }
      this.$emit('update:form', next)
    },
    presetUrl(provider) {
      return (this.providers.find(p => p.key === provider) || {}).defaultUrl || ''
    },
    presetModel(provider) {
      return (this.providers.find(p => p.key === provider) || {}).defaultModel || ''
    }
  }
}
</script>

<style scoped>
.hint { font-size: 13px; color: var(--muted); line-height: 1.7; }
</style>