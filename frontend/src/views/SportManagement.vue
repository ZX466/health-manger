<template>
  <div class="sport-page">
    <PageHead
      folio="04"
      eyebrow="MOVE / TODAY"
      title="运动记录"
      deck="今日活动轨迹：床 → 拿外卖 → 床。现在下楼走十分钟，还来得及改写结局。"
    >
      <template #actions>
        <span class="status-chip" :class="sportRecords.length ? 'status-chip--accent' : ''">
          <span class="status-dot" :class="sportRecords.length ? 'status-dot--success' : ''"></span>
          {{ sportRecords.length ? '已打卡' : (isToday ? '待运动' : '无记录') }}
        </span>
        <button class="btn btn-primary" @click="showAddRecord = true">
          <AppIcon name="plus" :size="15" />
          添加记录
        </button>
      </template>
    </PageHead>

    <section class="sport-hero v21-panel">
      <div class="sport-main">
        <p class="micro">{{ isToday ? "BURN / TODAY" : 'BURN / DAY' }}</p>
        <div class="sport-figure">
          <span class="sport-big">{{ Math.round(Number(sportStats.total_calories) || 0) }}</span>
          <span class="sport-unit">/ {{ goalCalories }} kcal</span>
        </div>
        <p class="sport-note">已消耗 · {{ isToday ? '今天' : '这一天' }}的运动</p>
        <div class="progress sport-progress">
          <span :style="{ width: goalPercent + '%' }"></span>
        </div>
      </div>
      <div class="sport-facts">
        <div>
          <span>活跃时长</span>
          <strong>{{ sportStats.total_duration_minutes || 0 }}</strong>
          <em>min</em>
        </div>
        <div>
          <span>运动次数</span>
          <strong>{{ sportStats.total_records || 0 }}</strong>
          <em>次</em>
        </div>
        <div>
          <span>平均每次</span>
          <strong>{{ avgDuration }}</strong>
          <em>min</em>
        </div>
      </div>
    </section>

    <div class="sport-toolbar">
      <div class="sport-tabs">
        <button :class="{ active: activeTab === 'records' }" @click="activeTab = 'records'">运动记录</button>
        <button :class="{ active: activeTab === 'sports' }" @click="activeTab = 'sports'">运动库</button>
        <button :class="{ active: activeTab === 'stats' }" @click="activeTab = 'stats'">统计分析</button>
      </div>
      <label class="sport-date">
        <input
          type="date"
          v-model="filterDate"
          @change="reloadForDate"
        />
      </label>
    </div>

    <template v-if="activeTab === 'records'">
      <div class="sport-grid">
        <section class="week-panel v21-panel">
          <div class="panel-head">
            <span class="micro">LAST 7 DAYS</span>
            <span class="micro">周均 {{ weekAverage }} kcal</span>
          </div>
          <h2>近 7 天消耗</h2>
          <div class="bar-chart" role="img" aria-label="近七天运动消耗柱状图">
            <div
              v-for="day in weekDays"
              :key="day.key"
              class="bar-col"
              :class="{ 'is-today': day.isSelected }"
              :title="`${day.key} · ${day.kcal} kcal`"
            >
              <span :style="{ height: day.height + '%' }"></span>
              <em>{{ day.day }}</em>
            </div>
          </div>
        </section>

        <section class="quick-panel v21-panel">
          <div class="panel-head">
            <span class="micro">QUICK ADD</span>
            <span class="micro">20 MIN</span>
          </div>
          <h2>补记一次活动</h2>
          <div class="quick-add-list">
            <button
              v-for="sport in quickSports"
              :key="sport.id"
              type="button"
              @click="quickAdd(sport)"
            >
              <span>{{ sport.name }} 20 分钟</span>
              <em>{{ estimateCalories(sport) }} kcal · 估算</em>
              <AppIcon name="plus" :size="14" />
            </button>
          </div>
          <p v-if="!quickSports.length" class="empty-hint">运动库还是空的，先去添加一项运动。</p>
        </section>
      </div>

      <section class="activity-panel v21-panel">
        <div class="panel-head">
          <span class="micro">ACTIVITY LOG</span>
          <span class="micro">{{ sportRecords.length }} 条</span>
        </div>
        <h2>{{ isToday ? '今天的活动' : '这一天的活动' }}</h2>
        <div v-if="sportRecords.length" class="activity-list">
          <div v-for="record in sportRecords" :key="record.id" class="activity-row">
            <span class="activity-icon"><AppIcon name="activity" :size="16" /></span>
            <div class="activity-copy">
              <strong>{{ record.sport_name }}</strong>
              <p>{{ recordMeta(record) }}<template v-if="record.notes"> · {{ record.notes }}</template></p>
            </div>
            <span class="activity-kcal">{{ Math.round(Number(record.calories_burned) || 0) }} kcal</span>
            <button class="icon-btn" title="删除记录" @click="deleteRecord(record.id)">
              <AppIcon name="trash" :size="15" />
            </button>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>{{ isToday ? '今天还没有活动记录。先走到楼下便利店，也算运动。' : '这一天没有运动记录。补一笔也算数。' }}</p>
        </div>
      </section>
    </template>

    <section v-else-if="activeTab === 'sports'" class="library-panel v21-panel">
      <div class="panel-head">
        <span class="micro">SPORT LIBRARY</span>
        <span class="micro">{{ sports.length }} 项运动</span>
      </div>
      <h2>运动库</h2>
      <div class="library-tools">
        <input
          type="text"
          v-model="sportSearch"
          placeholder="搜索运动..."
          @input="searchSports"
          class="search-input"
        />
        <button v-if="isAdmin" class="btn btn-primary" @click="openAddSport">
          <AppIcon name="plus" :size="15" />
          添加运动
        </button>
      </div>
      <div v-if="sports.length" class="sports-grid">
        <div v-for="sport in sports" :key="sport.id" class="sport-card">
          <div class="sport-card-top">
            <h3>{{ sport.name }}</h3>
            <span class="tag">{{ sport.category || '未分类' }}</span>
          </div>
          <div class="sport-card-meta">
            <span>{{ sport.calories_per_hour || 0 }} kcal/小时</span>
            <span>{{ intensityLabel(sport.intensity_level) }}</span>
          </div>
          <button @click="selectSport(sport)" class="btn-small">
            添加到记录
            <AppIcon name="arrow" :size="14" />
          </button>
          <div v-if="isAdmin" class="sport-admin-actions">
            <button type="button" class="sport-admin-btn" @click="openEditSport(sport)">编辑</button>
            <button type="button" class="sport-admin-btn sport-admin-btn--danger" @click="confirmDeleteSport(sport)">删除</button>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <p>没有找到匹配的运动。换个关键词试试。</p>
      </div>
    </section>

    <section v-else class="stats-panel v21-panel">
      <div class="panel-head">
        <span class="micro">SUMMARY</span>
        <span class="micro">{{ filterDate }}</span>
      </div>
      <h2>运动分布</h2>
      <div class="stats-cells">
        <div>
          <span>总消耗</span>
          <strong>{{ Math.round(Number(sportStats.total_calories) || 0) }}</strong>
          <em>kcal</em>
        </div>
        <div>
          <span>总时长</span>
          <strong>{{ sportStats.total_duration_minutes || 0 }}</strong>
          <em>min</em>
        </div>
        <div>
          <span>记录数</span>
          <strong>{{ sportStats.total_records || 0 }}</strong>
          <em>条</em>
        </div>
      </div>
      <div v-if="hasDistribution" class="distribution">
        <div v-for="(stats, sportName) in sportStats.sport_type_stats" :key="sportName" class="distribution-row">
          <div class="distribution-head">
            <span>{{ sportName }}</span>
            <span>{{ stats.count }} 次</span>
          </div>
          <div class="distribution-meta">
            <span>{{ Math.round(Number(stats.calories) || 0) }} kcal</span>
            <span>{{ stats.duration }} 分钟</span>
          </div>
          <div class="progress">
            <div class="progress-fill" :style="{ width: getPercentage(stats.calories) + '%' }"></div>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <p>还没有可统计的运动。先去记录一笔。</p>
      </div>
    </section>

    <div v-if="showAddRecord" class="modal-overlay" @click.self="showAddRecord = false">
      <div class="modal sport-modal">
        <div class="modal-head">
          <span class="micro">NEW ACTIVITY</span>
          <h2>添加运动记录</h2>
        </div>
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
            <button type="button" @click="showAddRecord = false" class="btn btn-ghost">取消</button>
            <button type="submit" class="btn btn-primary">确定</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showAddSport" class="modal-overlay" @click.self="closeSportModal">
      <div class="modal sport-modal">
        <div class="modal-head">
          <span class="micro">{{ editingSportId ? 'EDIT SPORT' : 'NEW SPORT' }}</span>
          <h2>{{ editingSportId ? '编辑运动项目' : '添加运动项目' }}</h2>
        </div>
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
            <button type="button" @click="closeSportModal" class="btn btn-ghost">取消</button>
            <button type="submit" class="btn btn-primary">{{ editingSportId ? '保存' : '确定' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'
import PageHead from '../components/PageHead.vue'
import AppIcon from '../components/AppIcon.vue'
import { localDateKey, parseServerDate } from '../utils/date'

export default {
  name: 'SportManagement',
  components: {
    PageHead,
    AppIcon
  },
  data() {
    return {
      activeTab: 'records',
      sportRecords: [],
      weekRecords: [],
      sports: [],
      sportStats: { total_calories: 0, total_duration_minutes: 0, total_records: 0, sport_type_stats: {} },
      filterDate: localDateKey(),
      sportSearch: '',
      goalCalories: 400,
      showAddRecord: false,
      showAddSport: false,
      editingSportId: null,
      deletingSportId: null,
      isAdmin: false,
      newRecord: { sport_id: '', duration_minutes: '', notes: '' },
      newSport: { name: '', category: '', calories_per_hour: 0, intensity_level: 'moderate' }
    }
  },
  computed: {
    isToday() {
      return this.filterDate === localDateKey()
    },
    goalPercent() {
      return Math.min(100, Math.round(((Number(this.sportStats.total_calories) || 0) / this.goalCalories) * 100))
    },
    avgDuration() {
      const count = Number(this.sportStats.total_records) || 0
      if (!count) return 0
      return Math.round((Number(this.sportStats.total_duration_minutes) || 0) / count)
    },
    quickSports() {
      const preferred = ['快走', '瑜伽', '力量训练']
      const picked = preferred
        .map(name => this.sports.find(sport => sport.name === name))
        .filter(Boolean)
      if (picked.length < 3) {
        for (const sport of this.sports) {
          if (picked.length >= 3) break
          if (!picked.includes(sport)) picked.push(sport)
        }
      }
      return picked.slice(0, 3)
    },
    weekDays() {
      const end = new Date(`${this.filterDate}T00:00:00`)
      if (Number.isNaN(end.getTime())) return []
      const days = []
      for (let i = 6; i >= 0; i -= 1) {
        const date = new Date(end)
        date.setDate(end.getDate() - i)
        const key = localDateKey(date)
        const kcal = this.weekRecords
          .filter(record => String(record.record_date || '').slice(0, 10) === key)
          .reduce((sum, record) => sum + (Number(record.calories_burned) || 0), 0)
        days.push({ key, day: date.getDate(), kcal: Math.round(kcal), isSelected: key === this.filterDate })
      }
      const max = Math.max(...days.map(day => day.kcal), 1)
      return days.map(day => ({
        ...day,
        height: day.kcal ? Math.max(8, Math.round((day.kcal / max) * 100)) : 4
      }))
    },
    weekAverage() {
      if (!this.weekDays.length) return 0
      const total = this.weekDays.reduce((sum, day) => sum + day.kcal, 0)
      return Math.round(total / this.weekDays.length)
    },
    hasDistribution() {
      return Object.keys(this.sportStats.sport_type_stats || {}).length > 0
    }
  },
  async mounted() {
    await this.loadCurrentUser()
    await this.loadSportData()
    await this.loadSports()
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
        return detail.map(d => d.msg || String(d)).join('；')
      }
      return err.message || '未知错误'
    },
    intensityLabel(level) {
      const labels = { low: '低强度', moderate: '中等强度', high: '高强度', extreme: '极高强度' }
      return labels[level] || level || '中等强度'
    },
    async loadSportData() {
      await Promise.all([
        this.loadSportRecords(),
        this.loadSportStats(),
        this.loadWeekRecords()
      ])
    },
    async reloadForDate() {
      await this.loadSportData()
    },
    async loadSportRecords() {
      try {
        const response = await api.getSportRecords({ start_date: this.filterDate, end_date: this.filterDate })
        this.sportRecords = response.data
      } catch (err) {
        console.error('加载运动记录失败:', err)
      }
    },
    async loadWeekRecords() {
      const end = new Date(`${this.filterDate}T00:00:00`)
      if (Number.isNaN(end.getTime())) {
        this.weekRecords = []
        return
      }
      const start = new Date(end)
      start.setDate(end.getDate() - 6)
      try {
        const response = await api.getSportRecords({
          start_date: localDateKey(start),
          end_date: this.filterDate
        })
        this.weekRecords = response.data
      } catch (err) {
        this.weekRecords = []
        console.error('加载近 7 天运动失败:', err)
      }
    },
    async loadSports() {
      try {
        const response = await api.getSports({ search: this.sportSearch || undefined })
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
        await this.loadSportData()
        alert('添加成功')
      } catch (err) {
        alert('添加失败：' + this.errMsg(err))
      }
    },
    openAddSport() {
      this.editingSportId = null
      this.newSport = { name: '', category: '', calories_per_hour: 0, intensity_level: 'moderate' }
      this.showAddSport = true
    },
    async openEditSport(sport) {
      this.editingSportId = sport.id
      this.newSport = {
        name: sport.name,
        category: sport.category || '',
        calories_per_hour: sport.calories_per_hour || 0,
        intensity_level: sport.intensity_level || 'moderate'
      }
      this.showAddSport = true
      try {
        const { data } = await api.getSport(sport.id)
        if (data && this.editingSportId === sport.id) {
          this.newSport = {
            name: data.name,
            category: data.category || '',
            calories_per_hour: data.calories_per_hour || 0,
            intensity_level: data.intensity_level || 'moderate'
          }
        }
      } catch (err) {
        // 详情接口失败时保留列表快照，仍可编辑。
      }
    },
    closeSportModal() {
      this.showAddSport = false
      this.editingSportId = null
    },
    async submitSport() {
      const isEdit = !!this.editingSportId
      try {
        if (isEdit) {
          await api.updateSport(this.editingSportId, this.newSport)
        } else {
          await api.createSport(this.newSport)
        }
        this.closeSportModal()
        this.newSport = { name: '', category: '', calories_per_hour: 0, intensity_level: 'moderate' }
        await this.loadSports()
        alert(isEdit ? '更新成功' : '添加成功')
      } catch (err) {
        alert((isEdit ? '更新失败：' : '添加失败：') + this.errMsg(err))
      }
    },
    async confirmDeleteSport(sport) {
      if (this.deletingSportId) return
      if (!confirm(`确定删除「${sport.name}」吗？该运动会从运动库移除，已有记录不受影响。`)) return
      this.deletingSportId = sport.id
      try {
        await api.deleteSport(sport.id)
        this.sports = this.sports.filter(item => item.id !== sport.id)
        await this.loadSportData()
        alert('删除成功')
      } catch (err) {
        alert('删除失败：' + this.errMsg(err))
      } finally {
        this.deletingSportId = null
      }
    },
    async deleteRecord(id) {
      if (confirm('确定要删除这条记录吗？')) {
        try {
          await api.deleteSportRecord(id)
          await this.loadSportData()
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
    quickAdd(sport) {
      this.newRecord = { sport_id: sport.id, duration_minutes: 20, notes: '' }
      this.showAddRecord = true
    },
    estimateCalories(sport) {
      return Math.round(((Number(sport.calories_per_hour) || 0) / 60) * 20)
    },
    recordMeta(record) {
      const parts = []
      const time = this.formatTime(record.record_date)
      if (time) parts.push(time)
      parts.push(`${record.duration_minutes} 分钟`)
      return parts.join(' · ')
    },
    formatTime(value) {
      const date = parseServerDate(value)
      if (!date) return ''
      return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    },
    getPercentage(calories) {
      const max = Math.max(...Object.values(this.sportStats.sport_type_stats).map(s => Number(s.calories) || 0))
      return max > 0 ? (Number(calories) / max) * 100 : 0
    }
  }
}
</script>

<style scoped>
.sport-admin-actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}
.sport-admin-btn {
  flex: 1;
  padding: 6px 8px;
  border: var(--border-hairline);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--muted);
  font-size: 12px;
  cursor: pointer;
}
.sport-admin-btn:hover { color: var(--fg); }
.sport-admin-btn--danger { color: var(--danger); border-color: currentColor; }
</style>
