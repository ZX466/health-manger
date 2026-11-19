<template>
  <div class="analysis-page">
    <PageHead
      folio="06"
      eyebrow="REVIEW / ARCHIVE"
      title="健康分析"
      deck="把体检数据翻译成人话：哪里稳住了，哪里需要盯一眼，下一步怎么做。"
    >
      <template #actions>
        <span class="status-chip" :class="latestAnalysis ? 'status-chip--accent' : ''">
          <span class="status-dot" :class="latestAnalysis ? 'status-dot--success' : ''"></span>
          {{ latestAnalysis ? '已生成' : '待体检' }}
        </span>
        <button
          class="btn btn-primary"
          :disabled="aiToolBusy || !latestAnalysis"
          :title="latestAnalysis ? '' : '请先添加一条含 BMI 的体检记录'"
          @click="generateAnalysis"
        >
          <AppIcon name="sparkles" :size="15" />
          {{ generating ? '生成中…' : '生成分析' }}
        </button>
        <button class="btn btn-ghost" @click="$router.push('/health-record')">
          <AppIcon name="plus" :size="15" />
          添加记录
        </button>
      </template>
    </PageHead>

    <template v-if="latestAnalysis">
      <section class="analysis-hero v21-panel">
        <div class="analysis-main">
          <p class="micro">SCORE / LATEST</p>
          <div class="analysis-figure">
            <span class="analysis-big">{{ displayScore }}</span>
            <span class="analysis-unit">/ 100</span>
          </div>
          <p class="analysis-rating" :class="ratingTone(latestAnalysis.health_rating)">
            {{ latestAnalysis.health_rating || '待评级' }}
          </p>
          <div class="analysis-bar" :class="ratingTone(latestAnalysis.health_rating)">
            <span :style="{ width: displayScore + '%' }"></span>
          </div>
          <p class="analysis-date micro">分析于 {{ formatDate(latestAnalysis.analysis_date) }}</p>
        </div>

        <div class="analysis-facts">
          <div class="analysis-fact">
            <span class="micro">BODY MASS / BMI</span>
            <div class="fact-line">
              <strong class="fact-label">BMI 体重指数</strong>
              <span class="fact-status" :class="statusTone(latestAnalysis.bmi_status)">
                {{ latestAnalysis.bmi_status || '未知' }}
              </span>
            </div>
            <p class="fact-advice">{{ latestAnalysis.bmi_advice || '暂无建议。' }}</p>
          </div>
          <div class="analysis-fact">
            <span class="micro">BLOOD PRESSURE</span>
            <div class="fact-line">
              <strong class="fact-label">血压状况</strong>
              <span class="fact-status" :class="statusTone(latestAnalysis.blood_pressure_status)">
                {{ latestAnalysis.blood_pressure_status || '未知' }}
              </span>
            </div>
            <p class="fact-advice">{{ latestAnalysis.blood_pressure_advice || '暂无建议。' }}</p>
          </div>
        </div>
      </section>

      <section class="overall-panel v21-panel">
        <div class="panel-head">
          <span class="micro">OVERALL / NOTE</span>
          <span class="micro">{{ latestAnalysis.overall_status || '未知' }}</span>
        </div>
        <h2>整体评估</h2>
        <p class="overall-advice">{{ latestAnalysis.overall_advice || '暂无整体建议。' }}</p>
      </section>

      <section class="ai-panel v21-panel">
        <div class="panel-head">
          <span class="micro">AI / INTERPRETATION</span>
          <span class="micro">{{ activeAi ? formatDateTime(activeAi.created_at) : 'NOT GENERATED' }}</span>
        </div>

        <div class="ai-head">
          <div>
            <h2>AI 深度解读</h2>
            <p class="ai-hint">
              基于最新体检记录生成，补充规则评分看不到的生活建议。内容仅供参考，不替代医生诊断。
            </p>
          </div>
          <button
            class="btn btn-ghost ai-refresh"
            :disabled="aiToolBusy"
            aria-describedby="ai-data-notice"
            @click="generateAnalysis"
          >
            <AppIcon name="sparkles" :size="15" />
            {{ generating ? '生成中…' : activeAi ? '重新生成' : '生成分析' }}
          </button>
        </div>

        <p id="ai-data-notice" class="ai-data-notice">
          <strong>发送前请知悉：</strong>
          生成时会将最新体检记录中的身高、体重、BMI、血压、心率、体温、睡眠、运动频率和饮食习惯，发送给你在「AI 设置」中选择的模型服务商（默认智谱 GLM），仅用于生成本次健康解读；不会发送姓名或账号信息。内容仅供参考，不替代医生诊断。
        </p>

        <div class="ai-tools">
          <div class="ai-tools-copy">
            <span class="micro">ANALYSIS / MODES</span>
            <p>快速结论、规则 + AI 综合评价，或提交后台任务稍后读取。</p>
          </div>
          <div class="ai-tools-actions">
            <button
              type="button"
              class="btn btn-ghost ai-tool"
              :disabled="aiToolBusy || !latestAnalysis"
              @click="runQuickAnalysis"
            >
              <AppIcon name="sparkles" :size="14" />
              {{ toolBusy === 'quick' ? '分析中…' : '快速分析' }}
            </button>
            <button
              type="button"
              class="btn btn-ghost ai-tool"
              :disabled="aiToolBusy || !latestAnalysis"
              @click="runHealthEvaluation"
            >
              <AppIcon name="chart" :size="14" />
              {{ toolBusy === 'evaluation' ? '评价中…' : '规则 + AI 评价' }}
            </button>
            <button
              type="button"
              class="btn btn-ghost ai-tool"
              :disabled="aiToolBusy || !latestAnalysis"
              @click="runAsyncAnalysis"
            >
              <AppIcon name="ai" :size="14" />
              {{ toolBusy === 'async' ? '后台处理中…' : '后台分析' }}
            </button>
          </div>
        </div>

        <div
          v-if="asyncTask"
          class="ai-task"
          :class="`is-${asyncTask.status}`"
          role="status"
          aria-live="polite"
        >
          <span class="ai-task-dot" aria-hidden="true"></span>
          <span>后台分析{{ asyncStatusText }}</span>
          <code v-if="asyncTask.task_id">{{ asyncTask.task_id }}</code>
        </div>

        <div v-if="aiError" class="ai-notice" :class="`is-${aiError.kind}`" role="alert">
          <AppIcon name="alert" :size="16" />
          <p>{{ aiError.message }}</p>
          <router-link
            v-if="aiError.action === 'settings'"
            class="ai-notice-action"
            to="/ai-settings"
          >
            去 AI 设置
          </router-link>
          <router-link
            v-else-if="aiError.action === 'record'"
            class="ai-notice-action"
            to="/health-record"
          >
            添加记录
          </router-link>
          <button
            v-else-if="aiError.action === 'retry'"
            type="button"
            class="ai-notice-action"
            @click="retryAi"
          >
            重试
          </button>
        </div>
        <p v-if="aiNotice" class="ai-success" role="status">{{ aiNotice }}</p>

        <div v-if="aiHistoryLoading" class="ai-loading" aria-live="polite">
          <span class="ai-loading-dot"></span>
          正在读取 AI 历史…
        </div>
        <article v-else-if="activeAi" class="ai-reading">
          <div class="ai-reading-meta">
            <span class="mini-tag mini-tag--score">{{ activeAi.analysis_type || '健康咨询' }}</span>
            <span v-if="activeAi.rule_score != null" class="mini-tag mini-tag--score">
              规则 {{ activeAi.rule_score }} · {{ activeAi.rule_rating || '—' }}
            </span>
            <span class="micro">
              {{ formatDateTime(activeAi.created_at) }}
              <span v-if="activeAi.tokens_used"> · {{ activeAi.tokens_used }} tokens</span>
            </span>
          </div>
          <p class="ai-reading-body">{{ activeAi.response_content }}</p>
        </article>
        <div v-else class="ai-empty">
          <span class="ai-empty-mark"><AppIcon name="sparkles" :size="22" /></span>
          <p>还没有 AI 解读。点“生成分析”，让 AI 把这次体检数据讲清楚。</p>
        </div>

        <div v-if="aiHistory.length" class="ai-history">
          <div class="panel-head ai-history-head">
            <span class="micro">AI HISTORY / {{ aiHistory.length }}</span>
            <span class="micro">点击查看</span>
          </div>
          <div class="ai-history-list">
            <div
              v-for="item in aiHistory"
              :key="item.id"
              class="ai-history-row"
              :class="{ 'is-active': activeAi && activeAi.id === item.id }"
            >
              <button
                type="button"
                class="ai-history-main"
                :disabled="aiDetailLoadingId === item.id"
                @click="openAiAnalysis(item.id)"
              >
                <span class="ai-history-date">{{ formatDateTime(item.created_at) }}</span>
                <span class="ai-history-excerpt">{{ excerpt(item.response_content) }}</span>
                <span v-if="aiDetailLoadingId === item.id" class="ai-history-state">读取中…</span>
              </button>
              <div class="ai-history-actions">
                <span class="micro ai-history-tokens">{{ item.tokens_used || '—' }} tok</span>
                <template v-if="deleteTargetId === item.id">
                  <button
                    type="button"
                    class="ai-delete ai-delete--confirm"
                    :disabled="aiDeletingId === item.id"
                    @click="confirmDelete(item)"
                  >
                    {{ aiDeletingId === item.id ? '删除中' : '确认删除' }}
                  </button>
                  <button
                    type="button"
                    class="ai-delete"
                    :disabled="aiDeletingId === item.id"
                    @click="deleteTargetId = null"
                  >
                    取消
                  </button>
                </template>
                <button
                  v-else
                  type="button"
                  class="ai-delete"
                  :aria-label="`删除 ${formatDateTime(item.created_at)} 的 AI 分析`"
                  @click="deleteTargetId = item.id"
                >
                  <AppIcon name="trash" :size="15" />
                </button>
              </div>
            </div>
          </div>
        </div>
        <p v-if="aiHistoryError" class="ai-history-error">{{ aiHistoryError }}</p>
      </section>

      <section class="history-panel v21-panel">
        <div class="panel-head">
          <span class="micro">HISTORY</span>
          <span class="micro">{{ analysisHistory.length }} 份报告</span>
        </div>
        <h2>历史分析</h2>
        <div class="history-list">
          <div v-for="analysis in analysisHistory" :key="analysis.id" class="history-row">
            <div class="history-date">
              <strong>{{ formatDate(analysis.analysis_date) }}</strong>
              <span class="micro">{{ formatTime(analysis.analysis_date) }}</span>
            </div>
            <div class="history-tags">
              <span class="mini-tag" :class="statusTone(analysis.bmi_status)">
                BMI · {{ analysis.bmi_status || '未知' }}
              </span>
              <span class="mini-tag" :class="statusTone(analysis.blood_pressure_status)">
                血压 · {{ analysis.blood_pressure_status || '未知' }}
              </span>
              <span class="mini-tag mini-tag--score">
                {{ analysis.health_score ?? '—' }} 分
              </span>
            </div>
            <span class="history-rating" :class="ratingTone(analysis.health_rating)">
              {{ analysis.health_rating || '—' }}
            </span>
          </div>
        </div>
      </section>
    </template>

    <section v-else class="empty-panel v21-panel">
      <div class="panel-head">
        <span class="micro">NO DATA</span>
        <span class="micro">0 份报告</span>
      </div>
      <div class="empty-body">
        <div class="empty-copy">
          <h2>还没有健康分析</h2>
          <p>先录入一次体检记录，系统会自动生成 BMI、血压和整体评估，之后每一次变化都会留在这里。</p>
          <button class="btn btn-primary" @click="$router.push('/health-record')">
            去添加体检记录
          </button>
        </div>
        <div v-if="!careMode" class="empty-mascots" aria-hidden="true">
          <MiniCat animation="wobble" />
          <MiniNailong />
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import api from '../api'
import PageHead from '../components/PageHead.vue'
import AppIcon from '../components/AppIcon.vue'
import MiniCat from '../components/mascots/MiniCat.vue'
import MiniNailong from '../components/mascots/MiniNailong.vue'
import { aiErrorInfo } from '../utils/aiError'
import { asyncStatusLabel, normalizeTaskResult } from '../utils/aiModes'
import { useWellnessStore } from '../stores/wellness'

const DEFAULT_AI_PROMPT =
  '请结合我最新的健康记录，给出整体健康解读、需要关注的风险点，以及 3 条可执行的改善建议，控制在 400 字以内。'

export default {
  name: 'HealthAnalysis',
  components: {
    PageHead,
    AppIcon,
    MiniCat,
    MiniNailong
  },
  setup() {
    return { wellness: useWellnessStore() }
  },
  data() {
    return {
      latestAnalysis: null,
      analysisHistory: [],
      generating: false,
      activeAi: null,
      aiHistory: [],
      aiHistoryLoading: false,
      aiHistoryError: '',
      aiDetailLoadingId: null,
      deleteTargetId: null,
      aiDeletingId: null,
      aiError: null,
      aiNotice: '',
      noticeTimer: null,
      toolBusy: '',
      asyncTask: null,
      asyncPollTimer: null,
      lastAiAction: 'deep'
    }
  },
  computed: {
    careMode() {
      return !!this.wellness?.isDanger
    },
    displayScore() {
      const score = Number(this.latestAnalysis?.health_score)
      return Number.isFinite(score) ? Math.max(0, Math.min(100, Math.round(score))) : 0
    },
    aiToolBusy() {
      return this.generating || Boolean(this.toolBusy)
    },
    asyncStatusText() {
      return asyncStatusLabel(this.asyncTask?.status)
    }
  },
  async mounted() {
    this.wellness.hydrateLocal()
    await Promise.all([this.loadAnalysis(), this.loadAiHistory(), this.wellness.load()])
  },
  beforeUnmount() {
    if (this.noticeTimer) clearTimeout(this.noticeTimer)
    this.clearAsyncPoll()
  },
  methods: {
    async loadAnalysis() {
      try {
        const latestResponse = await api.getLatestAnalysis()
        this.latestAnalysis = latestResponse.data
      } catch (err) {
        console.log('No analysis available yet')
      }

      try {
        const historyResponse = await api.getAnalysisHistory()
        this.analysisHistory = historyResponse.data
      } catch (err) {
        console.log('No history available')
      }
    },
    async generateAnalysis() {
      if (this.generating || this.toolBusy) return
      this.lastAiAction = 'deep'
      this.generating = true
      this.aiError = null
      this.aiNotice = ''
      try {
        const response = await api.createAIAnalysis({ request_content: DEFAULT_AI_PROMPT })
        this.activeAi = response.data
        await Promise.all([this.loadAnalysis(), this.loadAiHistory(response.data.id)])
        this.flashNotice('AI 分析已生成')
      } catch (err) {
        this.aiError = aiErrorInfo(err)
      } finally {
        this.generating = false
      }
    },
    async runQuickAnalysis() {
      if (this.aiToolBusy) return
      this.lastAiAction = 'quick'
      this.toolBusy = 'quick'
      this.aiError = null
      this.aiNotice = ''
      try {
        const { data } = await api.quickHealthAnalysis()
        const detail = await api.getAIAnalysis(data.analysis_id)
        this.activeAi = detail.data
        await this.loadAiHistory(data.analysis_id)
        this.flashNotice(data.cached ? '快速分析已生成（命中缓存）' : '快速分析已生成')
      } catch (err) {
        this.aiError = aiErrorInfo(err)
      } finally {
        this.toolBusy = ''
      }
    },
    async runHealthEvaluation() {
      if (this.aiToolBusy) return
      this.lastAiAction = 'evaluation'
      this.toolBusy = 'evaluation'
      this.aiError = null
      this.aiNotice = ''
      try {
        const { data } = await api.getHealthEvaluation()
        this.activeAi = {
          id: data.analysis_id,
          analysis_type: 'LLM 健康评价',
          response_content: data.llm_evaluation,
          tokens_used: data.tokens_used,
          created_at: new Date().toISOString(),
          rule_score: data.rule_score,
          rule_rating: data.rule_rating
        }
        await this.loadAiHistory(data.analysis_id)
        if (this.activeAi && this.activeAi.id === data.analysis_id) {
          this.activeAi = {
            ...this.activeAi,
            rule_score: data.rule_score,
            rule_rating: data.rule_rating
          }
        }
        this.flashNotice(data.cached ? '健康评价已生成（命中缓存）' : '健康评价已生成')
      } catch (err) {
        this.aiError = aiErrorInfo(err)
      } finally {
        this.toolBusy = ''
      }
    },
    async runAsyncAnalysis() {
      if (this.aiToolBusy) return
      this.lastAiAction = 'async'
      this.toolBusy = 'async'
      this.aiError = null
      this.aiNotice = ''
      this.clearAsyncPoll()
      this.asyncTask = { task_id: '', status: 'submitting' }
      try {
        const { data } = await api.asyncAIAnalysis({ request_content: DEFAULT_AI_PROMPT })
        this.asyncTask = { task_id: data.task_id, status: data.status || 'pending' }
        this.startAsyncPolling()
      } catch (err) {
        this.toolBusy = ''
        this.asyncTask = null
        this.aiError = aiErrorInfo(err)
      }
    },
    startAsyncPolling() {
      this.clearAsyncPoll()
      const startedAt = Date.now()
      const poll = async () => {
        const taskId = this.asyncTask?.task_id
        if (!taskId) return
        try {
          const { data } = await api.getTaskStatus(taskId)
          this.asyncTask = { ...this.asyncTask, ...data }
          if (data.status === 'completed') {
            await this.handleAsyncCompleted(data)
            return
          }
          if (data.status === 'failed') {
            this.toolBusy = ''
            this.aiError = {
              kind: 'server',
              message: data.error || '后台分析失败，请稍后重试。',
              action: 'retry'
            }
            return
          }
        } catch (err) {
          this.toolBusy = ''
          if (this.asyncTask) this.asyncTask = { ...this.asyncTask, status: 'failed' }
          this.aiError =
            err?.response?.status === 404
              ? { kind: 'server', message: '后台任务已过期，请重新提交。', action: 'retry' }
              : aiErrorInfo(err)
          return
        }
        if (Date.now() - startedAt > 120000) {
          this.toolBusy = ''
          if (this.asyncTask) this.asyncTask = { ...this.asyncTask, status: 'failed' }
          this.aiError = {
            kind: 'timeout',
            message: '后台分析超时，请稍后重试。',
            action: 'retry'
          }
          return
        }
        this.asyncPollTimer = setTimeout(poll, 1500)
      }
      this.asyncPollTimer = setTimeout(poll, 500)
    },
    async handleAsyncCompleted(data) {
      const parsed = normalizeTaskResult(data?.result)
      this.toolBusy = ''
      if (!parsed.content) {
        if (this.asyncTask) this.asyncTask = { ...this.asyncTask, status: 'failed' }
        this.aiError = {
          kind: 'server',
          message: '后台分析没有返回内容，请重试。',
          action: 'retry'
        }
        return
      }
      if (parsed.analysisId) {
        try {
          const detail = await api.getAIAnalysis(parsed.analysisId)
          this.activeAi = detail.data
        } catch (err) {
          this.activeAi = {
            id: parsed.analysisId,
            analysis_type: 'AI 异步分析',
            response_content: parsed.content,
            tokens_used: parsed.tokensUsed,
            created_at: new Date().toISOString()
          }
        }
        await this.loadAiHistory(parsed.analysisId)
      } else {
        this.activeAi = {
          id: null,
          analysis_type: 'AI 异步分析',
          response_content: parsed.content,
          tokens_used: parsed.tokensUsed,
          created_at: new Date().toISOString()
        }
      }
      this.flashNotice('后台分析已完成')
    },
    clearAsyncPoll() {
      if (this.asyncPollTimer) {
        clearTimeout(this.asyncPollTimer)
        this.asyncPollTimer = null
      }
    },
    retryAi() {
      if (this.lastAiAction === 'quick') this.runQuickAnalysis()
      else if (this.lastAiAction === 'evaluation') this.runHealthEvaluation()
      else if (this.lastAiAction === 'async') this.runAsyncAnalysis()
      else this.generateAnalysis()
    },
    async loadAiHistory(preserveId = null) {
      this.aiHistoryLoading = true
      this.aiHistoryError = ''
      try {
        const response = await api.getAIAnalysisHistory(20)
        this.aiHistory = Array.isArray(response.data) ? response.data : []
        if (preserveId) {
          const matched = this.aiHistory.find((item) => item.id === preserveId)
          if (matched) this.activeAi = matched
        } else if (!this.activeAi || !this.aiHistory.some((item) => item.id === this.activeAi.id)) {
          this.activeAi = this.aiHistory[0] || null
        }
      } catch (err) {
        this.aiHistoryError = 'AI 历史加载失败，稍后可刷新页面重试。'
        console.log('AI history unavailable', err)
      } finally {
        this.aiHistoryLoading = false
      }
    },
    async openAiAnalysis(id) {
      if (this.aiDetailLoadingId) return
      this.aiDetailLoadingId = id
      this.aiError = null
      try {
        const response = await api.getAIAnalysis(id)
        this.activeAi = response.data
      } catch (err) {
        this.aiError = aiErrorInfo(err)
      } finally {
        this.aiDetailLoadingId = null
      }
    },
    async confirmDelete(item) {
      if (this.aiDeletingId) return
      this.aiDeletingId = item.id
      this.aiError = null
      try {
        await api.deleteAIAnalysis(item.id)
        if (this.activeAi && this.activeAi.id === item.id) this.activeAi = null
        this.deleteTargetId = null
        await this.loadAiHistory()
        this.flashNotice('已删除这条 AI 分析')
      } catch (err) {
        this.aiError = aiErrorInfo(err)
      } finally {
        this.aiDeletingId = null
      }
    },
    flashNotice(message) {
      if (this.noticeTimer) clearTimeout(this.noticeTimer)
      this.aiNotice = message
      this.noticeTimer = setTimeout(() => {
        this.aiNotice = ''
      }, 4000)
    },
    excerpt(text) {
      const normalized = String(text || '').replace(/\s+/g, ' ').trim()
      if (!normalized) return '无内容'
      return normalized.length > 72 ? `${normalized.slice(0, 72)}…` : normalized
    },
    formatDateTime(dateStr) {
      const date = this.parseDate(dateStr)
      if (!date) return '—'
      return `${this.formatDate(dateStr)} ${this.formatTime(dateStr)}`
    },
    parseDate(dateStr) {
      if (!dateStr) return null
      const date = new Date(dateStr)
      return Number.isNaN(date.getTime()) ? null : date
    },
    formatDate(dateStr) {
      const date = this.parseDate(dateStr)
      if (!date) return '—'
      const pad = (value) => String(value).padStart(2, '0')
      return `${date.getFullYear()}.${pad(date.getMonth() + 1)}.${pad(date.getDate())}`
    },
    formatTime(dateStr) {
      const date = this.parseDate(dateStr)
      if (!date) return ''
      const pad = (value) => String(value).padStart(2, '0')
      return `${pad(date.getHours())}:${pad(date.getMinutes())}`
    },
    statusTone(status) {
      if (!status) return 'is-muted'
      if (status === '正常') return 'is-success'
      if (['肥胖', '高血压'].includes(status)) return 'is-danger'
      return 'is-warn'
    },
    ratingTone(rating) {
      if (!rating) return 'is-muted'
      if (['优秀', '良好'].includes(rating)) return 'is-success'
      if (rating === '中等') return 'is-warn'
      return 'is-danger'
    }
  }
}
</script>

<style scoped>
.analysis-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.analysis-hero {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 0;
  padding: 0;
  overflow: hidden;
}

.analysis-main {
  padding: 24px 26px 26px;
  border-right: 1px solid var(--line);
}

.analysis-figure {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  margin-top: 6px;
}

.analysis-big {
  font-family: var(--font-display);
  font-size: 92px;
  font-weight: 760;
  line-height: 0.86;
  letter-spacing: -0.06em;
}

.analysis-unit {
  padding-bottom: 9px;
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted);
}

.analysis-rating {
  display: inline-block;
  margin-top: 14px;
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 730;
  letter-spacing: -0.02em;
}

.analysis-rating.is-success { color: var(--success); }
.analysis-rating.is-warn { color: var(--warn); }
.analysis-rating.is-danger { color: var(--danger); }
.analysis-rating.is-muted { color: var(--muted); }

.analysis-bar {
  height: 5px;
  margin-top: 16px;
  border-radius: 999px;
  background: var(--surface-3);
  overflow: hidden;
}

.analysis-bar span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--muted);
  transition: width 300ms var(--ease-out);
}

.analysis-bar.is-success span { background: var(--success); }
.analysis-bar.is-warn span { background: var(--warn); }
.analysis-bar.is-danger span { background: var(--danger); }
.analysis-bar.is-muted span { background: var(--muted-2); }

.analysis-date {
  margin-top: 12px;
}

.analysis-facts {
  display: flex;
  flex-direction: column;
}

.analysis-fact {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 22px 26px;
}

.analysis-fact + .analysis-fact {
  border-top: 1px solid var(--line);
}

.fact-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.fact-label {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.fact-status {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 650;
}

.fact-status.is-success {
  background: var(--success-soft);
  color: var(--success);
}

.fact-status.is-warn {
  background: var(--warn-soft);
  color: var(--warn);
}

.fact-status.is-danger {
  background: var(--danger-soft);
  color: var(--danger);
}

.fact-status.is-muted {
  background: var(--surface-2);
  color: var(--muted);
}

.fact-advice {
  max-width: 52ch;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--muted);
}

.overall-panel h2,
.ai-panel h2,
.history-panel h2,
.empty-panel h2 {
  margin-top: 4px;
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 730;
  letter-spacing: -0.035em;
}

.overall-advice {
  max-width: 74ch;
  margin-top: 12px;
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--muted);
}

.history-list {
  display: flex;
  flex-direction: column;
  margin-top: 14px;
}

.history-row {
  display: grid;
  grid-template-columns: minmax(140px, 0.8fr) minmax(0, 1.6fr) auto;
  align-items: center;
  gap: 18px;
  padding: 15px 2px;
  border-top: 1px solid var(--line);
}

.history-row:last-child {
  padding-bottom: 2px;
}

.history-date strong {
  display: block;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.history-date .micro {
  display: block;
  margin-top: 3px;
}

.history-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.mini-tag {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 9px;
  border-radius: 999px;
  font-size: 10.5px;
  font-weight: 600;
}

.mini-tag.is-success {
  background: var(--success-soft);
  color: var(--success);
}

.mini-tag.is-warn {
  background: var(--warn-soft);
  color: var(--warn);
}

.mini-tag.is-danger {
  background: var(--danger-soft);
  color: var(--danger);
}

.mini-tag.is-muted,
.mini-tag--score {
  background: var(--surface-2);
  color: var(--muted);
}

.history-rating {
  justify-self: end;
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
}

.history-rating.is-success { color: var(--success); }
.history-rating.is-warn { color: var(--warn); }
.history-rating.is-danger { color: var(--danger); }
.history-rating.is-muted { color: var(--muted-2); }

.empty-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 28px;
  padding-top: 18px;
}

.empty-copy p {
  max-width: 58ch;
  margin: 10px 0 20px;
  font-size: 13.5px;
  line-height: 1.75;
  color: var(--muted);
}

.empty-mascots {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-right: 8px;
  opacity: 0.9;
}

/* ── AI 深度解读 ─────────────────────────────────────── */
.ai-panel {
  display: flex;
  flex-direction: column;
}

.ai-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.ai-hint {
  max-width: 62ch;
  margin-top: 8px;
  font-size: 12.5px;
  line-height: 1.7;
  color: var(--muted);
}

.ai-refresh {
  flex: 0 0 auto;
}

.ai-data-notice {
  max-width: 76ch;
  margin-top: 14px;
  padding: 10px 12px;
  border-left: 2px solid var(--line-strong, var(--line));
  background: var(--surface-2);
  font-size: 11.5px;
  line-height: 1.65;
  color: var(--muted);
}

.ai-data-notice strong {
  color: var(--fg);
  font-weight: 650;
}

.ai-tools {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}

.ai-tools-copy p {
  max-width: 52ch;
  margin-top: 4px;
  font-size: 11.5px;
  line-height: 1.6;
  color: var(--muted);
}

.ai-tools-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ai-tool {
  min-height: 34px;
  padding: 0 12px;
  font-size: 12px;
}

.ai-task {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--muted);
}

.ai-task-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--muted);
}

.ai-task.is-submitting .ai-task-dot,
.ai-task.is-pending .ai-task-dot,
.ai-task.is-running .ai-task-dot {
  background: var(--accent);
  animation: ai-pulse 900ms ease-in-out infinite alternate;
}

.ai-task.is-completed .ai-task-dot { background: var(--success); }
.ai-task.is-failed .ai-task-dot { background: var(--danger); }

.ai-task code {
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--surface-2);
  font-size: 10px;
  letter-spacing: 0.04em;
}

.ai-notice {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 16px;
  padding: 11px 13px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  font-size: 12px;
  line-height: 1.6;
  color: var(--muted);
}

.ai-notice.is-no-key,
.ai-notice.is-no-data,
.ai-notice.is-rate-limit {
  border-color: color-mix(in oklch, var(--warn) 24%, var(--line));
  background: var(--warn-soft);
  color: var(--warn);
}

.ai-notice.is-timeout,
.ai-notice.is-network,
.ai-notice.is-server {
  border-color: color-mix(in oklch, var(--danger) 20%, var(--line));
  background: var(--danger-soft);
  color: var(--danger);
}

.ai-notice p {
  flex: 1;
  min-width: 0;
}

.ai-notice-action {
  flex: 0 0 auto;
  align-self: center;
  padding: 0;
  border: 0;
  background: none;
  color: inherit;
  font-size: 11px;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
  cursor: pointer;
}

.ai-success {
  margin-top: 12px;
  font-size: 11.5px;
  font-weight: 650;
  color: var(--success);
}

.ai-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 18px;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-md);
  font-size: 12px;
  color: var(--muted);
}

.ai-loading-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: ai-pulse 900ms ease-in-out infinite alternate;
}

@keyframes ai-pulse {
  from { opacity: 0.25; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}

.ai-reading {
  margin-top: 16px;
  padding: 18px 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--surface-2);
}

.ai-reading-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.ai-reading-body {
  margin-top: 14px;
  font-size: 13.5px;
  line-height: 1.9;
  color: var(--fg);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.ai-empty {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  padding: 18px;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-md);
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--muted);
}

.ai-empty-mark {
  display: inline-grid;
  place-items: center;
  width: 38px;
  height: 38px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--surface-2);
  color: var(--accent);
}

.ai-history {
  margin-top: 22px;
}

.ai-history-head {
  margin-bottom: 0;
}

.ai-history-list {
  display: flex;
  flex-direction: column;
}

.ai-history-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 9px 8px;
  border-bottom: 1px solid var(--line);
  border-radius: var(--radius-sm);
}

.ai-history-row:last-child {
  border-bottom: 0;
}

.ai-history-row.is-active {
  background: var(--surface-2);
}

.ai-history-main {
  display: grid;
  grid-template-columns: 118px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  min-width: 0;
  padding: 0;
  border: 0;
  background: none;
  text-align: left;
  cursor: pointer;
}

.ai-history-main:disabled {
  cursor: wait;
  opacity: 0.55;
}

.ai-history-date {
  font-family: var(--font-mono);
  font-size: 10.5px;
  color: var(--muted);
  white-space: nowrap;
}

.ai-history-excerpt {
  overflow: hidden;
  font-size: 12px;
  color: var(--fg);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ai-history-state {
  grid-column: 1 / -1;
  font-size: 10px;
  color: var(--muted);
}

.ai-history-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.ai-history-tokens {
  white-space: nowrap;
}

.ai-delete {
  display: inline-grid;
  place-items: center;
  min-width: 30px;
  min-height: 30px;
  padding: 0 7px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--muted);
  font-size: 10.5px;
  font-weight: 650;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}

.ai-delete:hover {
  background: var(--danger-soft);
  color: var(--danger);
}

.ai-delete--confirm {
  background: var(--danger);
  color: var(--surface);
}

.ai-delete--confirm:hover {
  background: var(--danger);
  color: var(--surface);
}

.ai-delete:disabled {
  cursor: wait;
  opacity: 0.55;
}

.ai-history-error {
  margin-top: 10px;
  font-size: 11.5px;
  color: var(--danger);
}

@media (max-width: 900px) {
  .analysis-hero {
    grid-template-columns: minmax(0, 1fr);
  }

  .analysis-main {
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .analysis-big {
    font-size: 76px;
  }

  .history-row {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .history-tags {
    grid-column: 1 / -1;
    grid-row: 2;
  }
}

@media (max-width: 640px) {
  .analysis-main,
  .analysis-fact {
    padding: 20px;
  }

  .empty-body {
    grid-template-columns: minmax(0, 1fr);
  }

  .empty-mascots {
    justify-content: flex-start;
    padding-right: 0;
  }

  .ai-head {
    flex-direction: column;
    gap: 14px;
  }

  .ai-refresh {
    width: 100%;
  }

  .ai-tools {
    align-items: stretch;
    flex-direction: column;
    gap: 12px;
  }

  .ai-tools-actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  .ai-tool {
    width: 100%;
  }

  .ai-notice {
    flex-wrap: wrap;
  }

  .ai-notice-action {
    margin-left: 24px;
  }

  .ai-history-row {
    grid-template-columns: minmax(0, 1fr);
    align-items: start;
    gap: 6px;
  }

  .ai-history-main {
    grid-template-columns: minmax(0, 1fr);
    gap: 4px;
  }

  .ai-history-actions {
    justify-content: flex-end;
  }
}
</style>
