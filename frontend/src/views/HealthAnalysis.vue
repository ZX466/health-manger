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
        <button class="btn btn-primary" @click="$router.push('/health-record')">
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
        <div class="empty-mascots" aria-hidden="true">
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

export default {
  name: 'HealthAnalysis',
  components: {
    PageHead,
    AppIcon,
    MiniCat,
    MiniNailong
  },
  data() {
    return {
      latestAnalysis: null,
      analysisHistory: []
    }
  },
  computed: {
    displayScore() {
      const score = Number(this.latestAnalysis?.health_score)
      return Number.isFinite(score) ? Math.max(0, Math.min(100, Math.round(score))) : 0
    }
  },
  async mounted() {
    await this.loadAnalysis()
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
}
</style>
