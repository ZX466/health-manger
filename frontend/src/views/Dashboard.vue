<template>
  <div class="dashboard">
    <div class="dashboard-content">
      <div class="welcome-section">
        <div class="welcome-text">
          <h1>欢迎回来，{{ userName }}！</h1>
          <p>今天是 {{ currentDate }}，查看您的健康数据概览和分析建议</p>
        </div>
        <div class="welcome-mascots">
          <CharacterAvatar type="hajimi" :animated="true" style="width:70px;height:70px" />
          <CharacterAvatar type="nailong" :animated="true" style="width:70px;height:70px" />
        </div>
        <div class="health-score" v-if="latestRating">
          <div class="score-circle" :style="{ boxShadow: '0 0 20px ' + latestRating.bg_color }">
            <span class="score-emoji">{{ latestRating.emoji }}</span>
            <span class="score-value">{{ latestRating.score }}</span>
            <span class="score-label">{{ latestRating.rating }}</span>
          </div>
        </div>
      </div>

      <!-- 功能快捷入口 -->
      <div class="feature-grid">
        <div class="feature-card" @click="$router.push('/health-record')">
          <div class="feature-icon">📋</div>
          <div class="feature-info">
            <h3>健康记录</h3>
            <p>记录身体指标数据</p>
          </div>
        </div>
        <div class="feature-card" @click="$router.push('/diet-management')">
          <div class="feature-icon">🍎</div>
          <div class="feature-info">
            <h3>饮食管理</h3>
            <p>管理每日饮食摄入</p>
          </div>
        </div>
        <div class="feature-card" @click="$router.push('/sport-management')">
          <div class="feature-icon">🏃</div>
          <div class="feature-info">
            <h3>运动管理</h3>
            <p>追踪运动消耗</p>
          </div>
        </div>
        <div class="feature-card" @click="$router.push('/health-analysis')">
          <div class="feature-icon">📊</div>
          <div class="feature-info">
            <h3>健康分析</h3>
            <p>AI智能分析报告</p>
          </div>
        </div>
        <div class="feature-card" @click="$router.push('/health-knowledge')">
          <div class="feature-icon">📚</div>
          <div class="feature-info">
            <h3>健康知识</h3>
            <p>食谱与健康资讯</p>
          </div>
        </div>
        <div class="feature-card" @click="$router.push('/health-reminder')">
          <div class="feature-icon">🔔</div>
          <div class="feature-info">
            <h3>健康提醒</h3>
            <p>目标与提醒设置</p>
          </div>
        </div>
        <div class="feature-card" @click="$router.push('/tongue-diagnosis')">
          <div class="feature-icon">👅</div>
          <div class="feature-info">
            <h3>中医舌诊</h3>
            <p>AI舌象健康分析</p>
          </div>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📊</div>
          <div class="stat-info">
            <div class="stat-label">总记录数</div>
            <div class="stat-value">{{ stats.totalRecords }}</div>
          </div>
        </div>
        <div class="stat-card" v-if="latestRecord?.bmi">
          <div class="stat-icon">⚖️</div>
          <div class="stat-info">
            <div class="stat-label">最新BMI</div>
            <div class="stat-value">{{ latestRecord.bmi }}</div>
          </div>
        </div>
        <div class="stat-card" v-if="latestRecord?.blood_pressure_systolic">
          <div class="stat-icon">🩺</div>
          <div class="stat-info">
            <div class="stat-label">最新血压</div>
            <div class="stat-value small">
              {{ latestRecord.blood_pressure_systolic }}/{{ latestRecord.blood_pressure_diastolic }}
            </div>
          </div>
        </div>
        <div class="stat-card" v-if="latestRating">
          <div class="stat-icon">🏅</div>
          <div class="stat-info">
            <div class="stat-label">健康评级</div>
            <div class="stat-value rating-badge" :style="{ backgroundColor: latestRating.color + '20', color: latestRating.color }">
              {{ latestRating.emoji }} {{ latestRating.rating }}
            </div>
          </div>
        </div>
      </div>

      <!-- 今日任务/建议 -->
      <div class="today-section">
        <h2>📅 今日建议</h2>
        <div class="suggestion-list">
          <div class="suggestion-item" v-for="(suggestion, idx) in todaySuggestions" :key="idx">
            <span class="suggestion-icon">{{ suggestion.icon }}</span>
            <div class="suggestion-content">
              <strong>{{ suggestion.title }}</strong>
              <p>{{ suggestion.desc }}</p>
            </div>
            <button @click="$router.push(suggestion.link)" class="suggestion-btn">去完成</button>
          </div>
        </div>
      </div>

      <div class="latest-analysis" v-if="latestAnalysis">
        <h2>📈 最新健康分析</h2>
        <div class="analysis-card">
          <div class="analysis-grid">
            <div class="analysis-item bmi">
              <div class="analysis-icon">⚖️</div>
              <div class="analysis-detail">
                <h4>BMI指数</h4>
                <span :class="'status-' + latestAnalysis.bmi_status">{{ latestAnalysis.bmi_status }}</span>
                <p>{{ latestAnalysis.bmi_advice }}</p>
              </div>
            </div>
            <div class="analysis-item bp">
              <div class="analysis-icon">🩺</div>
              <div class="analysis-detail">
                <h4>血压状况</h4>
                <span :class="'status-' + latestAnalysis.blood_pressure_status">{{ latestAnalysis.blood_pressure_status }}</span>
                <p>{{ latestAnalysis.blood_pressure_advice }}</p>
              </div>
            </div>
          </div>
          <div class="overall-assessment">
            <h3>整体评估</h3>
            <p>{{ latestAnalysis.overall_advice }}</p>
            <button @click="$router.push('/health-analysis')" class="view-detail-btn">查看完整报告 →</button>
          </div>
        </div>
      </div>

      <!-- 趣图乐一乐 -->
      <div class="fun-section">
        <h2>🎉 趣图乐一乐</h2>
        <div class="fun-grid">
          <div class="fun-card">
            <MemeGallery source="memes" title="奶龙表情包" :count="3" :cols="3" />
          </div>
          <div class="fun-card">
            <h3 class="fun-card-title">🔊 开心音效</h3>
            <AudioPlayer />
          </div>
        </div>
      </div>

      <!-- 推荐内容 -->
      <div class="recommendations-section">
        <h2>✨ 为你推荐</h2>
        <div class="rec-cards">
          <div class="rec-card" v-for="rec in recommendations" :key="rec.id" @click="$router.push(rec.link)">
            <span class="rec-emoji">{{ rec.emoji }}</span>
            <div class="rec-text">
              <h4>{{ rec.title }}</h4>
              <p>{{ rec.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'
import CharacterAvatar from '../components/CharacterAvatar.vue'
import MemeGallery from '../components/MemeGallery.vue'
import AudioPlayer from '../components/AudioPlayer.vue'

export default {
  name: 'Dashboard',
  components: {
    CharacterAvatar,
    MemeGallery,
    AudioPlayer
  },
  data() {
    return {
      userName: '',
      currentDate: '',
      stats: {
        totalRecords: 0
      },
      latestRecord: null,
      latestAnalysis: null,
      latestRating: null,
      todaySuggestions: [
        { icon: '💧', title: '记得喝水', desc: '今日已饮水 2/8 杯', link: '/health-reminder' },
        { icon: '🏃', title: '运动目标', desc: '今日还需运动 30 分钟', link: '/sport-management' },
        { icon: '🍎', title: '饮食记录', desc: '还未记录午餐', link: '/diet-management' }
      ],
      recommendations: [
        { id: 1, emoji: '🥗', title: '低卡减脂餐谱', desc: '7天健康饮食计划', link: '/health-knowledge' },
        { id: 2, emoji: '🧘', title: '办公室拉伸指南', desc: '缓解久坐疲劳', link: '/health-knowledge' },
        { id: 3, emoji: '😴', title: '改善睡眠质量', desc: '10个助眠小技巧', link: '/health-knowledge' }
      ]
    }
  },
  async mounted() {
    this.currentDate = new Date().toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long'
    })
    await this.loadUserInfo()
    await this.loadStats()
  },
  methods: {
    async loadUserInfo() {
      try {
        const response = await api.getCurrentUser()
        this.userName = response.data.name
      } catch (err) {
        // 静默处理
      }
    },
    async loadStats() {
      try {
        const recordsResponse = await api.getHealthRecords()
        this.stats.totalRecords = recordsResponse.data.length
        if (recordsResponse.data.length > 0) {
          this.latestRecord = recordsResponse.data[0]
        }

        const analysisResponse = await api.getLatestAnalysis()
        this.latestAnalysis = analysisResponse.data

        const ratingResponse = await api.getLatestRating()
        this.latestRating = ratingResponse.data
      } catch (err) {
        // 静默处理
      }
    }
  }
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: var(--bg);
}
.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

/* 欢迎区域 */
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 36px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent) 100%);
  padding: 32px;
  border-radius: var(--radius-lg);
  color: white;
  box-shadow: 0 8px 32px rgba(255, 155, 113, 0.25);
}
.welcome-text h1 {
  font-size: 28px;
  margin-bottom: 8px;
}
.welcome-text p {
  opacity: 0.9;
  font-size: 15px;
}
.health-score {
  text-align: center;
}
.score-circle {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}
.score-emoji {
  font-size: 22px;
}
.score-value {
  font-size: 20px;
  font-weight: bold;
}
.score-label {
  font-size: 11px;
  opacity: 0.9;
}

/* 功能快捷入口 */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 36px;
}
.feature-card {
  background: var(--surface);
  padding: 20px;
  border-radius: var(--radius);
  cursor: pointer;
  transition: var(--transition);
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: var(--shadow-xs);
  border: 2px solid transparent;
}
.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-md);
  border-color: var(--accent-soft);
  animation: float 1.5s ease-in-out infinite;
}
.feature-icon {
  font-size: 32px;
}
.feature-info h3 {
  color: var(--fg);
  font-size: 15px;
  margin-bottom: 4px;
}
.feature-info p {
  color: var(--muted);
  font-size: 13px;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 18px;
  margin-bottom: 36px;
}
.stat-card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 22px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-md);
  border: 2px solid var(--accent-soft);
  transition: var(--transition);
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  animation: pulse-glow 1.5s ease-in-out infinite;
}
.stat-icon {
  font-size: 38px;
}
.stat-info {
  flex: 1;
}
.stat-label {
  color: var(--muted);
  font-size: 13px;
  margin-bottom: 6px;
}
.stat-value {
  font-size: 22px;
  font-weight: bold;
  color: var(--fg);
}
.stat-value.small {
  font-size: 17px;
}
.rating-badge {
  padding: 4px 14px;
  border-radius: 20px;
  font-size: 14px;
}

/* 状态配色 */
.status-正常 {
  background: rgba(126, 200, 163, 0.15);
  color: var(--success);
}
.status-偏瘦, .status-偏低 {
  background: rgba(135, 206, 235, 0.15);
  color: var(--info);
}
.status-偏胖, .status-偏高 {
  background: rgba(255, 179, 102, 0.15);
  color: var(--warning);
}
.status-肥胖, .status-高血压 {
  background: rgba(255, 138, 138, 0.15);
  color: var(--danger);
}

/* 今日建议 */
.today-section {
  margin-bottom: 36px;
}
.today-section h2 {
  color: var(--fg);
  margin-bottom: 16px;
  font-size: 18px;
}
.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.suggestion-item {
  background: var(--surface);
  padding: 16px 20px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-xs);
  transition: var(--transition);
}
.suggestion-item:hover {
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
}
.suggestion-icon {
  font-size: 28px;
}
.suggestion-content {
  flex: 1;
}
.suggestion-content strong {
  color: var(--fg);
  display: block;
  margin-bottom: 4px;
}
.suggestion-content p {
  color: var(--muted);
  font-size: 13px;
}
.suggestion-btn {
  padding: 8px 18px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: var(--transition);
  box-shadow: 0 4px 12px rgba(255, 155, 113, 0.25);
}
.suggestion-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 18px rgba(255, 155, 113, 0.35);
}

/* 分析区域 */
.latest-analysis {
  margin-bottom: 36px;
}
.latest-analysis h2 {
  margin-bottom: 20px;
  color: var(--fg);
  font-size: 18px;
}
.analysis-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 28px;
  box-shadow: var(--shadow-md);
  border: 2px solid var(--accent-soft);
}
.analysis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}
.analysis-item {
  padding: 20px;
  border-radius: var(--radius);
  display: flex;
  gap: 14px;
  align-items: flex-start;
}
.analysis-item.bmi {
  background: linear-gradient(135deg, rgba(126, 200, 163, 0.1) 0%, rgba(168, 216, 185, 0.1) 100%);
}
.analysis-item.bp {
  background: linear-gradient(135deg, rgba(135, 206, 235, 0.1) 0%, rgba(201, 177, 255, 0.1) 100%);
}
.analysis-icon {
  font-size: 32px;
}
.analysis-detail h4 {
  color: var(--fg);
  margin-bottom: 6px;
  font-size: 15px;
}
.analysis-detail span {
  font-weight: 600;
  font-size: 14px;
  padding: 2px 10px;
  border-radius: 12px;
}
.analysis-detail p {
  color: var(--muted);
  font-size: 13px;
  margin-top: 6px;
  line-height: 1.5;
}
.overall-assessment {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent) 100%);
  padding: 24px;
  border-radius: var(--radius);
  color: white;
}
.overall-assessment h3 {
  margin-bottom: 10px;
}
.overall-assessment p {
  opacity: 0.95;
  line-height: 1.7;
  margin-bottom: 16px;
}
.view-detail-btn {
  background: white;
  color: var(--accent-hover);
  border: none;
  padding: 10px 20px;
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 600;
  transition: var(--transition);
}
.view-detail-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 16px rgba(255, 255, 255, 0.3);
}

/* 推荐内容 */
.recommendations-section {
  margin-top: 36px;
}
.recommendations-section h2 {
  color: var(--fg);
  margin-bottom: 16px;
  font-size: 18px;
}
.rec-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}
.rec-card {
  background: var(--surface);
  padding: 18px;
  border-radius: var(--radius);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 14px;
  transition: var(--transition);
  box-shadow: var(--shadow-xs);
  border: 2px solid transparent;
}
.rec-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: var(--accent);
  animation: hold-belly-laugh 0.6s ease-in-out;
}
.rec-emoji {
  font-size: 36px;
}
.rec-text h4 {
  color: var(--fg);
  font-size: 15px;
  margin-bottom: 4px;
}
.rec-text p {
  color: var(--muted);
  font-size: 13px;
}

  .welcome-mascots {
    display: flex;
    gap: 16px;
    align-items: center;
  }
  .fun-section { margin-bottom: 36px; }
  .fun-section h2 { color: var(--fg); margin-bottom: 16px; font-size: 18px; }
  .fun-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
  }
  .fun-card {
    background: var(--surface);
    border-radius: var(--radius-lg);
    padding: 24px;
    box-shadow: var(--shadow-xs);
    border: 2px solid var(--accent-soft);
  }
  .fun-card-title {
    color: var(--accent-hover);
    margin-bottom: 16px;
    font-size: 16px;
    text-align: center;
  }
  @media (max-width: 768px) {
    .fun-grid { grid-template-columns: 1fr; }
    .welcome-mascots { display: none; }
  }
</style>
