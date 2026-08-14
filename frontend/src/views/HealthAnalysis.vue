<template>
  <div class="health-analysis">

    <div class="content">
      <div class="latest-analysis" v-if="latestAnalysis">
        <h2>最新健康分析报告</h2>
        <p class="analysis-date">分析时间：{{ formatDate(latestAnalysis.analysis_date) }}</p>

        <div class="analysis-cards">
          <div class="analysis-card bmi-card">
            <div class="card-header">
              <span class="card-icon"></span>
              <h3>BMI 体重指数</h3>
            </div>
            <div class="card-status" :class="'status-' + latestAnalysis.bmi_status">
              {{ latestAnalysis.bmi_status }}
            </div>
            <p class="card-advice">{{ latestAnalysis.bmi_advice }}</p>
          </div>

          <div class="analysis-card bp-card">
            <div class="card-header">
              <span class="card-icon"></span>
              <h3>血压状况</h3>
            </div>
            <div class="card-status" :class="'status-' + latestAnalysis.blood_pressure_status">
              {{ latestAnalysis.blood_pressure_status }}
            </div>
            <p class="card-advice">{{ latestAnalysis.blood_pressure_advice }}</p>
          </div>

          <div class="analysis-card overall-card">
            <div class="card-header">
              <span class="card-icon"></span>
              <h3>整体健康评估</h3>
            </div>
            <div class="card-status overall" :class="'status-' + latestAnalysis.overall_status">
              {{ latestAnalysis.overall_status }}
            </div>
            <p class="card-advice">{{ latestAnalysis.overall_advice }}</p>
          </div>
        </div>
      </div>

      <div v-else class="no-analysis">
        <div class="no-data-icon"></div>
        <h2>暂无健康分析</h2>
          <div class="mascot-no-data">
            <MiniCat size="large" animation="wobble" />
            <MiniNailong size="large" />
          </div>
        <p>请先添加健康记录，系统将自动为您生成健康分析报告</p>
        <button @click="$router.push('/health-record')" class="action-btn primary">
           添加健康记录
        </button>
      </div>

      <div class="history-section" v-if="analysisHistory.length > 0">
        <h2>历史分析记录</h2>
        <div class="history-list">
          <div v-for="analysis in analysisHistory" :key="analysis.id" class="history-item">
            <div class="history-date">{{ formatDate(analysis.analysis_date) }}</div>
            <div class="history-status">
              <span class="status-tag" :class="'status-' + analysis.bmi_status">BMI: {{ analysis.bmi_status }}</span>
              <span class="status-tag" :class="'status-' + analysis.blood_pressure_status">血压: {{ analysis.blood_pressure_status }}</span>
              <span class="status-tag overall" :class="'status-' + analysis.overall_status">{{ analysis.overall_status }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'
import MiniCat from '../components/mascots/MiniCat.vue'
import MiniNailong from '../components/mascots/MiniNailong.vue'

export default {
  name: 'HealthAnalysis',
  components: {
    MiniCat,
    MiniNailong
  },
  data() {
    return {
      latestAnalysis: null,
      analysisHistory: []
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
    formatDate(dateStr) {
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.health-analysis {
  min-height: 100vh;
  background: var(--bg);
}
.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}
.latest-analysis h2 {
  color: var(--fg);
  margin-bottom: 10px;
}
.analysis-date {
  color: var(--muted);
  margin-bottom: 30px;
}
.analysis-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}
.analysis-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
  transition: transform 0.3s;
}
.analysis-card:hover {
  transform: translateY(-2px);
}
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.card-icon {
  font-size: 32px;
}
.card-header h3 {
  color: var(--fg);
  font-size: 18px;
}
.card-status {
  display: inline-block;
  padding: 8px 20px;
  border-radius: 25px;
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 16px;
}
.card-status.overall {
  font-size: 20px;
  padding: 12px 30px;
}
.status-正常 {
  background: var(--accent);
  color: white;
}
.status-偏瘦 {
  background: #fff3e0;
  color: var(--warning);
}
.status-偏低 {
  background: #e3f2fd;
  color: var(--info);
}
.status-偏胖 {
  background: #fff8e1;
  color: var(--warning);
}
.status-偏高 {
  background: #fff8e1;
  color: var(--warning);
}
.status-肥胖 {
  background: #ffebee;
  color: var(--danger);
}
.status-高血压 {
  background: #ffebee;
  color: var(--danger);
}
.card-advice {
  color: var(--muted);
  line-height: 1.8;
  font-size: 14px;
}
.bmi-card {
  border-left: 4px solid var(--accent);
}
.bp-card {
  border-left: 4px solid var(--danger);
}
.overall-card {
  border-left: 4px solid var(--success);
  background: var(--accent);
}
.overall-card .card-header h3 {
  color: white;
}
.overall-card .card-status {
  background: white;
  color: var(--accent);
}
.overall-card .card-advice {
  color: rgba(255, 255, 255, 0.95);
}
.no-analysis {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
}
.no-data-icon {
  font-size: 80px;
  margin-bottom: 20px;
}
.no-analysis h2 {
  color: var(--fg);
  margin-bottom: 10px;
}
.no-analysis p {
  color: var(--muted);
  margin-bottom: 30px;
}
.action-btn {
  padding: 14px 28px;
  border: none;
  border-radius: var(--radius);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}
.action-btn.primary {
  background: var(--accent);
  color: white;
}
.action-btn:hover {
  transform: translateY(-2px);
}
.history-section {
  background: white;
  border-radius: var(--radius-lg);
  padding: 30px;
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
}
.history-section h2 {
  color: var(--fg);
  margin-bottom: 20px;
}
.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 2px solid #FFE4D6;
  border-radius: var(--radius);
  transition: border-color 0.3s;
}
.history-item:hover {
  border-color: var(--accent);
}
.history-date {
  color: var(--accent);
  font-weight: 600;
}
.history-status {
  display: flex;
  gap: 10px;
}
.status-tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  background: #FFF0E8;
  color: var(--muted);
}
.status-tag.overall {
  background: var(--accent);
  color: white;
}
.mascot-no-data {
  display: flex; align-items: center; justify-content: center;
  gap: 20px; margin: 16px 0; padding: 12px;
}

</style>
