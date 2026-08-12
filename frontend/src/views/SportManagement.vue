<template>
  <div class="sport-management">

    <div class="content">
      <div class="section-header">
        <h1>🏃 运动管理</h1>
        <p>记录运动数据，追踪热量消耗</p>
        <div class="mascot-companion mascot-nailong-companion">
          <MiniNailong />
        </div>
      </div>

      <div class="tabs">
        <button :class="{ active: activeTab === 'records' }" @click="activeTab = 'records'">
          📝 运动记录
        </button>
        <button :class="{ active: activeTab === 'sports' }" @click="activeTab = 'sports'">
          🏋️ 运动库
        </button>
        <button :class="{ active: activeTab === 'stats' }" @click="activeTab = 'stats'">
          📊 统计分析
        </button>
      </div>

      <div v-if="activeTab === 'records'" class="tab-content">
        <div class="action-bar">
          <button @click="showAddRecord = true" class="btn-primary">
            ➕ 添加运动记录
          </button>
          <input 
            type="date" 
            v-model="filterDate" 
            @change="loadSportRecords"
            class="date-picker"
          />
        </div>

        <div class="records-list">
          <div v-for="record in sportRecords" :key="record.id" class="record-card">
            <div class="record-info">
              <div class="sport-name">{{ record.sport_name }}</div>
              <div class="record-meta">
                <span>⏱️ {{ record.duration_minutes }} 分钟</span>
                <span>🔥 {{ record.calories_burned }} kcal</span>
                <span>📅 {{ formatDate(record.record_date) }}</span>
              </div>
              <div v-if="record.notes" class="record-notes">{{ record.notes }}</div>
            </div>
            <button @click="deleteRecord(record.id)" class="btn-delete">删除</button>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'sports'" class="tab-content">
        <div class="action-bar">
          <button v-if="isAdmin" @click="showAddSport = true" class="btn-primary">
            ➕ 添加运动
          </button>
          <input 
            type="text" 
            v-model="sportSearch" 
            placeholder="搜索运动..."
            @input="searchSports"
            class="search-input"
          />
        </div>

        <div class="sports-grid">
          <div v-for="sport in sports" :key="sport.id" class="sport-card">
            <h3>{{ sport.name }}</h3>
            <p class="sport-category">{{ sport.category || '未分类' }}</p>
            <div class="sport-info">
              <span>🔥 {{ sport.calories_per_hour || 0 }} kcal/小时</span>
              <span>📊 {{ sport.intensity_level || '中等' }}</span>
            </div>
            <button @click="selectSport(sport)" class="btn-small">添加到记录</button>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'stats'" class="tab-content">
        <div class="stats-cards">
          <div class="stat-card">
            <h3>总消耗热量</h3>
            <div class="stat-value">{{ sportStats.total_calories }} kcal</div>
          </div>
          <div class="stat-card">
            <h3>总运动时长</h3>
            <div class="stat-value">{{ sportStats.total_duration_minutes }} 分钟</div>
          </div>
          <div class="stat-card">
            <h3>记录总数</h3>
            <div class="stat-value">{{ sportStats.total_records }}</div>
          </div>
        </div>
        <div class="sport-stats">
          <h3>各项运动统计</h3>
          <div v-for="(stats, sportName) in sportStats.sport_type_stats" :key="sportName" class="sport-stat">
            <div class="sport-stat-header">
              <span>{{ sportName }}</span>
              <span>{{ stats.count }} 次</span>
            </div>
            <div class="sport-stat-details">
              <span>🔥 {{ stats.calories }} kcal</span>
              <span>⏱️ {{ stats.duration }} 分钟</span>
            </div>
            <div class="progress-bar">
              <div class="progress" :style="{ width: getPercentage(stats.calories) + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showAddRecord" class="modal-overlay" @click="showAddRecord = false">
      <div class="modal" @click.stop>
        <h2>添加运动记录</h2>
        <form @submit.prevent="submitSportRecord">
          <div class="form-group">
            <label>运动项目</label>
            <select v-model="newRecord.sport_id" required>
              <option value="">选择运动</option>
              <option v-for="sport in sports" :key="sport.id" :value="sport.id">
                {{ sport.name }} ({{ sport.calories_per_hour || 0 }} kcal/小时)
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>运动时长 (分钟)</label>
            <input type="number" v-model.number="newRecord.duration_minutes" required min="1" />
          </div>
          <div class="form-group">
            <label>备注</label>
            <textarea v-model="newRecord.notes" rows="3" placeholder="可选，记录运动感受等"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" @click="showAddRecord = false" class="btn-cancel">取消</button>
            <button type="submit" class="btn-submit">确定</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showAddSport" class="modal-overlay" @click="showAddSport = false">
      <div class="modal" @click.stop>
        <h2>添加运动项目</h2>
        <form @submit.prevent="submitSport">
          <div class="form-group">
            <label>运动名称</label>
            <input type="text" v-model="newSport.name" required />
          </div>
          <div class="form-group">
            <label>分类</label>
            <select v-model="newSport.category">
              <option value="有氧运动">有氧运动</option>
              <option value="力量训练">力量训练</option>
              <option value="球类运动">球类运动</option>
              <option value="户外运动">户外运动</option>
              <option value="室内运动">室内运动</option>
            </select>
          </div>
          <div class="form-group">
            <label>热量消耗 (kcal/小时)</label>
            <input type="number" v-model.number="newSport.calories_per_hour" step="1" />
          </div>
          <div class="form-group">
            <label>强度等级</label>
            <select v-model="newSport.intensity_level">
              <option value="low">低强度</option>
              <option value="moderate">中等强度</option>
              <option value="high">高强度</option>
              <option value="extreme">极高强度</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="button" @click="showAddSport = false" class="btn-cancel">取消</button>
            <button type="submit" class="btn-submit">确定</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'
import MiniNailong from '../components/mascots/MiniNailong.vue'

export default {
  name: 'SportManagement',
  components: {
    MiniNailong
  },
  data() {
    return {
      activeTab: 'records',
      sportRecords: [],
      sports: [],
      sportStats: { total_calories: 0, total_duration_minutes: 0, total_records: 0, sport_type_stats: {} },
      filterDate: new Date().toISOString().split('T')[0],
      sportSearch: '',
      showAddRecord: false,
      showAddSport: false,
      isAdmin: false,
      newRecord: { sport_id: '', duration_minutes: '', notes: '' },
      newSport: { name: '', category: '', calories_per_hour: 0, intensity_level: 'moderate' }
    }
  },
  async mounted() {
    await this.loadCurrentUser()
    await this.loadSportRecords()
    await this.loadSports()
    await this.loadSportStats()
  },
  methods: {
    async loadCurrentUser() {
      try {
        const response = await api.getCurrentUser()
        this.isAdmin = !!response.data?.is_admin
      } catch (err) {
        this.isAdmin = false
      }
    },
    errMsg(err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail) && detail.length) {
        // FastAPI 422 校验错误为数组 [{ loc, msg, type }, ...]
        return detail.map(d => d.msg || String(d)).join('；')
      }
      return err.message || '未知错误'
    },
    async loadSportRecords() {
      try {
        const response = await api.getSportRecords({ start_date: this.filterDate, end_date: this.filterDate })
        this.sportRecords = response.data
      } catch (err) {
        console.error('加载运动记录失败:', err)
      }
    },
    async loadSports() {
      try {
        const response = await api.getSports({ search: this.sportSearch })
        this.sports = response.data
      } catch (err) {
        console.error('加载运动库失败:', err)
      }
    },
    async loadSportStats() {
      try {
        const response = await api.getSportStats({ start_date: this.filterDate, end_date: this.filterDate })
        this.sportStats = response.data
      } catch (err) {
        console.error('加载统计失败:', err)
      }
    },
    async searchSports() {
      await this.loadSports()
    },
    async submitSportRecord() {
      try {
        await api.createSportRecord(this.newRecord)
        this.showAddRecord = false
        this.newRecord = { sport_id: '', duration_minutes: '', notes: '' }
        await this.loadSportRecords()
        await this.loadSportStats()
        alert('添加成功')
      } catch (err) {
        alert('添加失败：' + this.errMsg(err))
      }
    },
    async submitSport() {
      try {
        await api.createSport(this.newSport)
        this.showAddSport = false
        this.newSport = { name: '', category: '', calories_per_hour: 0, intensity_level: 'moderate' }
        await this.loadSports()
        alert('添加成功')
      } catch (err) {
        alert('添加失败：' + this.errMsg(err))
      }
    },
    async deleteRecord(id) {
      if (confirm('确定要删除这条记录吗？')) {
        try {
          await api.deleteSportRecord(id)
          await this.loadSportRecords()
          await this.loadSportStats()
          alert('删除成功')
        } catch (err) {
          alert('删除失败')
        }
      }
    },
    selectSport(sport) {
      this.newRecord.sport_id = sport.id
      this.activeTab = 'records'
      this.showAddRecord = true
    },
    formatDate(dateStr) {
      return new Date(dateStr).toLocaleString('zh-CN')
    },
    getPercentage(calories) {
      const max = Math.max(...Object.values(this.sportStats.sport_type_stats).map(s => s.calories))
      return max > 0 ? (calories / max) * 100 : 0
    }
  }
}
</script>

<style scoped>
.sport-management {
  min-height: 100vh;
  background: var(--bg);
}
.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.section-header {
  margin-bottom: 30px;
}
.section-header h1 {
  color: var(--fg);
  margin-bottom: 10px;
}
.section-header p {
  color: var(--muted);
}
.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.tabs button {
  padding: 12px 24px;
  border: none;
  background: white;
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}
.tabs button.active {
  background: var(--accent);
  color: white;
}
.action-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}
.btn-primary {
  padding: 12px 24px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 600;
}
.date-picker, .search-input {
  padding: 12px;
  border: 1px solid #FFE4D6;
  border-radius: var(--radius);
  font-size: 14px;
}
.search-input {
  flex: 1;
}
.record-card {
  background: white;
  padding: 20px;
  border-radius: var(--radius);
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
}
.sport-name {
  font-size: 18px;
  font-weight: bold;
  color: var(--fg);
  margin-bottom: 8px;
}
.record-meta {
  display: flex;
  gap: 15px;
  color: var(--muted);
  font-size: 14px;
  margin-bottom: 5px;
}
.record-notes {
  color: var(--muted);
  font-size: 14px;
  font-style: italic;
}
.btn-delete {
  padding: 8px 16px;
  background: #fee;
  color: var(--danger);
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
}
.sports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}
.sport-card {
  background: white;
  padding: 20px;
  border-radius: var(--radius);
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
}
.sport-card h3 {
  color: var(--fg);
  margin-bottom: 8px;
}
.sport-category {
  color: var(--muted);
  font-size: 14px;
  margin-bottom: 12px;
}
.sport-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 15px;
  font-size: 14px;
  color: var(--muted);
}
.btn-small {
  padding: 8px 16px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  width: 100%;
}
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}
.stat-card {
  background: white;
  padding: 24px;
  border-radius: var(--radius);
  text-align: center;
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
}
.stat-card h3 {
  color: var(--muted);
  font-size: 14px;
  margin-bottom: 10px;
}
.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: var(--accent);
}
.sport-stats {
  background: white;
  padding: 24px;
  border-radius: var(--radius);
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
}
.sport-stat {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}
.sport-stat:last-child {
  border-bottom: none;
}
.sport-stat-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-weight: 600;
  color: var(--fg);
}
.sport-stat-details {
  display: flex;
  gap: 20px;
  margin-bottom: 10px;
  font-size: 14px;
  color: var(--muted);
}
.progress-bar {
  height: 20px;
  background: #FFF0E8;
  border-radius: 10px;
  overflow: hidden;
}
.progress {
  height: 100%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
  transition: width 0.3s;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.modal {
  background: white;
  padding: 30px;
  border-radius: var(--radius);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}
.modal h2 {
  margin-bottom: 20px;
  color: var(--fg);
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--muted);
  font-weight: 500;
}
.form-group input, .form-group select, .form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #FFE4D6;
  border-radius: var(--radius);
  font-size: 14px;
}
.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
.btn-cancel {
  padding: 12px 24px;
  background: #FFF0E8;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
}
.btn-submit {
  padding: 12px 24px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
}

/* section-header mascot positioning */
.section-header { position: relative; }
.mascot-companion {
  position: absolute; top: 50%; transform: translateY(-50%);
  z-index: 2; pointer-events: none;
}
.mascot-nailong-companion { right: 15px; }

</style>
