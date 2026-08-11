<template>
  <div class="health-reminder">

    <div class="content">
      <div class="section-header">
        <h1>🔔 健康提醒与目标</h1>
        <p>设定健康计划，养成良好习惯</p>
        <div class="mascot-companion mascot-nailong-companion">
          <MiniNailong />
        </div>
      </div>

      <div class="tabs">
        <button :class="{ active: activeTab === 'reminders' }" @click="activeTab = 'reminders'">
          ⏰ 我的提醒
        </button>
        <button :class="{ active: activeTab === 'goals' }" @click="activeTab = 'goals'">
          🎯 健康目标
        </button>
        <button :class="{ active: activeTab === 'warnings' }" @click="activeTab = 'warnings'">
          ⚠️ 健康预警
        </button>
      </div>

      <!-- 提醒列表 -->
      <div v-if="activeTab === 'reminders'" class="tab-content">
        <div class="action-bar">
          <button @click="showAddReminder = true" class="btn-primary">
            ➕ 添加提醒
          </button>
          <button @click="markAllRead" class="btn-secondary" v-if="unreadCount > 0">
            全部标为已读
          </button>
        </div>

        <div v-if="reminders.length === 0" class="no-data">
          <span class="no-data-icon">⏰</span>
          <p>暂无健康提醒</p>
          <div class="mascot-no-data">
            <MiniCat size="large" animation="wobble" />
            <MiniNailong size="large" />
          </div>
          <p class="hint">添加提醒来帮助您保持健康习惯</p>
        </div>
        <div v-else class="reminder-list">
          <div v-for="reminder in reminders" :key="reminder.id"
               :class="['reminder-card', { unread: !reminder.is_read, enabled: reminder.is_enabled }]">
            <div class="reminder-icon">{{ getReminderIcon(reminder.type) }}</div>
            <div class="reminder-info">
              <h3>{{ reminder.title }}</h3>
              <p>{{ reminder.description }}</p>
              <div class="reminder-meta">
                <span>⏱️ {{ reminder.remind_time }}</span>
                <span :class="['frequency-badge', reminder.frequency]">{{ getFrequencyText(reminder.frequency) }}</span>
                <span :class="['type-badge', reminder.type]">{{ getTypeText(reminder.type) }}</span>
              </div>
              <div class="reminder-methods" v-if="reminder.notify_methods && reminder.notify_methods.length">
                <span v-if="reminder.notify_methods.includes('sms')" class="method-tag">短信</span>
                <span v-if="reminder.notify_methods.includes('email')" class="method-tag">邮箱</span>
                <span v-if="reminder.notify_methods.includes('wechat')" class="method-tag">微信</span>
                <span v-if="reminder.notify_methods.includes('app')" class="method-tag">APP</span>
              </div>
            </div>
            <div class="reminder-actions">
              <label class="toggle-switch">
                <input type="checkbox" v-model="reminder.is_enabled" @change="toggleReminder(reminder)" />
                <span class="slider"></span>
              </label>
              <button @click="editReminder(reminder)" class="edit-btn">编辑</button>
              <button @click="deleteReminder(reminder.id)" class="delete-btn">删除</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 健康目标 -->
      <div v-if="activeTab === 'goals'" class="tab-content">
        <div class="action-bar">
          <button @click="showAddGoal = true" class="btn-primary">
            ➕ 设定新目标
          </button>
        </div>

        <!-- 目标概览卡片 -->
        <div class="goal-overview">
          <div class="overview-card">
            <h4>今日完成度</h4>
            <div class="progress-circle">
              <svg viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="45" fill="none" stroke="#e0e0e0" stroke-width="8"/>
                <circle cx="50" cy="50" r="45" fill="none" stroke="var(--accent)" stroke-width="8"
                        :stroke-dasharray="283" :stroke-dashoffset="283 * (1 - todayProgress / 100)"
                        transform="rotate(-90 50 50)"/>
              </svg>
              <span class="progress-text">{{ Math.round(todayProgress) }}%</span>
            </div>
          </div>
          <div class="stats-cards">
            <div class="stat-item">
              <span class="stat-value">{{ activeGoalsCount }}</span>
              <span class="stat-label">进行中</span>
            </div>
            <div class="stat-item">
              <span class="stat-value completed">{{ completedGoalsCount }}</span>
              <span class="stat-label">已完成</span>
            </div>
            <div class="stat-item">
              <span class="stat-value total">{{ goals.length }}</span>
              <span class="stat-label">总目标</span>
            </div>
          </div>
        </div>

        <div v-if="goals.length === 0" class="no-data">
          <span class="no-data-icon">🎯</span>
          <p>暂无健康目标</p>
          <div class="mascot-no-data">
            <MiniNailong size="large" />
            <MiniCat size="large" animation="wobble" />
          </div>
          <p class="hint">设定目标来追踪您的健康进度</p>
        </div>
        <div v-else class="goal-list">
          <div v-for="goal in goals" :key="goal.id" :class="['goal-card', goal.status]">
            <div class="goal-header">
              <div class="goal-icon">{{ getGoalIcon(goal.category) }}</div>
              <div class="goal-title-section">
                <h3>{{ goal.title }}</h3>
                <span class="goal-category">{{ getCategoryText(goal.category) }}</span>
              </div>
              <span :class="['status-badge', goal.status]">{{ getStatusText(goal.status) }}</span>
            </div>
            <p class="goal-description">{{ goal.description }}</p>
            <div class="goal-progress">
              <div class="progress-bar-container">
                <div class="progress-bar" :style="{ width: goal.progress + '%' }"></div>
              </div>
              <span class="progress-text">{{ goal.current_value || 0 }} / {{ goal.target_value || 100 }} {{ goal.unit || '' }}</span>
            </div>
            <div class="goal-footer">
              <span class="goal-deadline">截止：{{ formatDate(goal.deadline) }}</span>
              <div class="goal-actions">
                <button @click="updateProgress(goal)" class="update-btn" v-if="goal.status !== 'completed'">
                  更新进度
                </button>
                <button @click="deleteGoal(goal.id)" class="delete-btn">删除</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 健康预警 -->
      <div v-if="activeTab === 'warnings'" class="tab-content">
        <div class="warning-header">
          <div class="warning-stats">
            <div :class="['stat-box', { hasUnread: unreadWarnings > 0 }]">
              <span class="stat-number">{{ unreadWarnings }}</span>
              <span class="stat-text">未读预警</span>
            </div>
            <div class="stat-box">
              <span class="stat-number">{{ warnings.length }}</span>
              <span class="stat-text">总预警数</span>
            </div>
          </div>
          <button @click="checkHealthWarnings" class="btn-primary">
            🔍 立即检测
          </button>
        </div>

        <div v-if="warnings.length === 0" class="no-data">
          <span class="no-data-icon">✅</span>
          <p>暂无健康预警</p>
          <div class="mascot-no-data">
            <MiniCat size="large" animation="wobble" />
            <MiniNailong size="large" />
          </div>
          <p class="hint">您的健康状况良好！</p>
        </div>
        <div v-else class="warning-list">
          <div v-for="warning in warnings" :key="warning.id"
               :class="['warning-card', warning.level, { unread: !warning.is_read }]">
            <div class="warning-level-icon">
              {{ warning.level === 'high' ? '🔴' : warning.level === 'medium' ? '🟡' : '🟢' }}
            </div>
            <div class="warning-content">
              <div class="warning-header-row">
                <h4>{{ warning.title }}</h4>
                <span class="warning-time">{{ formatTime(warning.created_at) }}</span>
              </div>
              <p>{{ warning.message }}</p>
              <div class="warning-details" v-if="warning.details">
                <div v-for="(value, key) in warning.details" :key="key" class="detail-item">
                  <span class="detail-label">{{ key }}：</span>
                  <span :class="['detail-value', value.abnormal ? 'abnormal' : 'normal']">
                    {{ value.value }} {{ value.unit || '' }}
                    <span v-if="value.range" class="normal-range">(正常范围: {{ value.range }})</span>
                  </span>
                </div>
              </div>
              <div class="warning-suggestion" v-if="warning.suggestion">
                <strong>建议：</strong>{{ warning.suggestion }}
              </div>
            </div>
            <div class="warning-actions">
              <button v-if="!warning.is_read" @click="markAsRead(warning.id)" class="read-btn">
                标为已读
              </button>
              <button @click="viewWarningDetail(warning)" class="detail-btn">
                查看详情
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑提醒弹窗 -->
    <div v-if="showAddReminder" class="modal-overlay" @click="showAddReminder = false">
      <div class="modal" @click.stop>
        <h2>{{ editingReminder ? '编辑提醒' : '添加提醒' }}</h2>
        <form @submit.prevent="submitReminder" class="reminder-form">
          <div class="form-group">
            <label>提醒标题 *</label>
            <input type="text" v-model="reminderForm.title" required placeholder="例如：喝水提醒" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="reminderForm.description" rows="2" placeholder="提醒内容详情..."></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>提醒类型</label>
              <select v-model="reminderForm.type">
                <option value="water">喝水</option>
                <option value="exercise">运动</option>
                <option value="meal">用餐</option>
                <option value="medication">用药</option>
                <option value="sleep">睡眠</option>
                <option value="measure">测量指标</option>
                <option value="custom">自定义</option>
              </select>
            </div>
            <div class="form-group">
              <label>提醒时间</label>
              <input type="time" v-model="reminderForm.remind_time" required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>频率</label>
              <select v-model="reminderForm.frequency">
                <option value="once">仅一次</option>
                <option value="daily">每天</option>
                <option value="weekly">每周</option>
                <option value="weekday">工作日</option>
                <option value="weekend">周末</option>
              </select>
            </div>
            <div class="form-group">
              <label>通知方式</label>
              <div class="checkbox-group">
                <label><input type="checkbox" value="app" v-model="reminderForm.notify_methods" /> APP通知</label>
                <label><input type="checkbox" value="wechat" v-model="reminderForm.notify_methods" /> 微信</label>
                <label><input type="checkbox" value="sms" v-model="reminderForm.notify_methods" /> 短信</label>
                <label><input type="checkbox" value="email" v-model="reminderForm.notify_methods" /> 邮箱</label>
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" @click="showAddReminder = false" class="btn-cancel">取消</button>
            <button type="submit" class="btn-submit">保存</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 添加/编辑目标弹窗 -->
    <div v-if="showAddGoal" class="modal-overlay" @click="showAddGoal = false">
      <div class="modal" @click.stop>
        <h2>{{ editingGoal ? '编辑目标' : '设定新目标' }}</h2>
        <form @submit.prevent="submitGoal" class="goal-form">
          <div class="form-group">
            <label>目标标题 *</label>
            <input type="text" v-model="goalForm.title" required placeholder="例如：每天步行10000步" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="goalForm.description" rows="2" placeholder="详细描述您的目标..."></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>类别</label>
              <select v-model="goalForm.category">
                <option value="exercise">运动健身</option>
                <option value="diet">饮食控制</option>
                <option value="weight">体重管理</option>
                <option value="sleep">睡眠质量</option>
                <option value="water">饮水习惯</option>
                <option value="custom">其他</option>
              </select>
            </div>
            <div class="form-group">
              <label>截止日期</label>
              <input type="date" v-model="goalForm.deadline" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>目标值</label>
              <input type="number" v-model.number="goalForm.target_value" placeholder="100" />
            </div>
            <div class="form-group">
              <label>单位</label>
              <input type="text" v-model="goalForm.unit" placeholder="步/次/天等" />
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" @click="showAddGoal = false" class="btn-cancel">取消</button>
            <button type="submit" class="btn-submit">保存</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 更新进度弹窗 -->
    <div v-if="showUpdateProgress" class="modal-overlay" @click="showUpdateProgress = false">
      <div class="modal small" @click.stop>
        <h2>更新进度</h2>
        <form @submit.prevent="confirmUpdateProgress" class="progress-form">
          <div class="form-group">
            <label>当前值</label>
            <input type="number" v-model.number="progressValue" required :placeholder="'目标: ' + (currentGoal?.target_value || '') + ' ' + (currentGoal?.unit || '')" />
          </div>
          <div class="modal-actions">
            <button type="button" @click="showUpdateProgress = false" class="btn-cancel">取消</button>
            <button type="submit" class="btn-submit">更新</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'
import MiniCat from '../components/mascots/MiniCat.vue'
import MiniNailong from '../components/mascots/MiniNailong.vue'

export default {
  name: 'HealthReminder',
  components: {
    MiniCat,
    MiniNailong
  },
  data() {
    return {
      activeTab: 'reminders',

      // 提醒相关
      reminders: [],
      showAddReminder: false,
      editingReminder: null,
      reminderForm: {
        title: '',
        description: '',
        type: 'water',
        remind_time: '09:00',
        frequency: 'daily',
        notify_methods: ['app']
      },

      // 目标相关
      goals: [],
      showAddGoal: false,
      editingGoal: null,
      goalForm: {
        title: '',
        description: '',
        category: 'exercise',
        deadline: '',
        target_value: 100,
        unit: ''
      },
      showUpdateProgress: false,
      currentGoal: null,
      progressValue: 0,

      // 预警相关
      warnings: [],
      unreadCount: 0
    }
  },
  computed: {
    unreadWarnings() {
      return this.warnings.filter(w => !w.is_read).length
    },
    activeGoalsCount() {
      return this.goals.filter(g => g.status === 'active').length
    },
    completedGoalsCount() {
      return this.goals.filter(g => g.status === 'completed').length
    },
    todayProgress() {
      if (this.goals.length === 0) return 0
      const total = this.goals.reduce((sum, g) => sum + (g.progress || 0), 0)
      return total / this.goals.length
    }
  },
  mounted() {
    this.loadReminders()
    this.loadGoals()
    this.loadWarnings()
  },
  methods: {
    async loadReminders() {
      try {
        const response = await api.getReminders()
        this.reminders = response.data || []
      } catch (err) {
        console.error('加载提醒失败:', err)
      }
    },

    async loadGoals() {
      try {
        const response = await api.getGoals()
        this.goals = response.data || []
      } catch (err) {
        console.error('加载目标失败:', err)
      }
    },

    async loadWarnings() {
      try {
        const response = await api.getWarnings()
        this.warnings = response.data || []
        try {
          const statsResponse = await api.getWarningStats()
          this.unreadCount = statsResponse.data?.unread || 0
        } catch (e) {}
      } catch (err) {
        console.error('加载预警失败:', err)
      }
    },

    async submitReminder() {
      try {
        if (this.editingReminder) {
          await api.updateReminder(this.editingReminder.id, this.reminderForm)
        } else {
          await api.createReminder(this.reminderForm)
        }
        this.showAddReminder = false
        this.resetReminderForm()
        await this.loadReminders()
        alert(this.editingReminder ? '更新成功！' : '添加成功！')
      } catch (err) {
        alert('操作失败：' + (err.response?.data?.detail || err.message))
      }
    },

    editReminder(reminder) {
      this.editingReminder = reminder
      this.reminderForm = { ...reminder }
      this.showAddReminder = true
    },

    resetReminderForm() {
      this.editingReminder = null
      this.reminderForm = {
        title: '',
        description: '',
        type: 'water',
        remind_time: '09:00',
        frequency: 'daily',
        notify_methods: ['app']
      }
    },

    async toggleReminder(reminder) {
      try {
        await api.toggleReminder(reminder.id, { is_enabled: reminder.is_enabled })
      } catch (err) {
        alert('操作失败')
        reminder.is_enabled = !reminder.is_enabled
      }
    },

    async deleteReminder(id) {
      if (!confirm('确定要删除这个提醒吗？')) return
      try {
        await api.deleteReminder(id)
        await this.loadReminders()
        alert('删除成功')
      } catch (err) {
        alert('删除失败')
      }
    },

    async markAllRead() {
      try {
        await api.markAllRemindersRead()
        this.reminders.forEach(r => r.is_read = true)
        this.unreadCount = 0
      } catch (err) {
        alert('操作失败')
      }
    },

    async submitGoal() {
      try {
        if (this.editingGoal) {
          await api.updateGoal(this.editingGoal.id, this.goalForm)
        } else {
          await api.createGoal(this.goalForm)
        }
        this.showAddGoal = false
        this.resetGoalForm()
        await this.loadGoals()
        alert(this.editingGoal ? '更新成功！' : '目标已设定！')
      } catch (err) {
        alert('操作失败：' + (err.response?.data?.detail || err.message))
      }
    },

    editGoal(goal) {
      this.editingGoal = goal
      this.goalForm = { ...goal }
      this.showAddGoal = true
    },

    resetGoalForm() {
      this.editingGoal = null
      this.goalForm = {
        title: '',
        description: '',
        category: 'exercise',
        deadline: '',
        target_value: 100,
        unit: ''
      }
    },

    updateProgress(goal) {
      this.currentGoal = goal
      this.progressValue = goal.current_value || 0
      this.showUpdateProgress = true
    },

    async confirmUpdateProgress() {
      try {
        await api.updateGoalProgress(this.currentGoal.id, { current_value: this.progressValue })
        this.showUpdateProgress = false
        await this.loadGoals()
        alert('进度已更新！')
      } catch (err) {
        alert('更新失败')
      }
    },

    async deleteGoal(id) {
      if (!confirm('确定要删除这个目标吗？')) return
      try {
        await api.deleteGoal(id)
        await this.loadGoals()
        alert('删除成功')
      } catch (err) {
        alert('删除失败')
      }
    },

    async checkHealthWarnings() {
      try {
        const response = await api.checkWarnings()
        if (response.data.new_warnings > 0) {
          alert(`检测到 ${response.data.new_warnings} 条新的健康预警！`)
        } else {
          alert('检测结果正常，未发现异常！')
        }
        await this.loadWarnings()
      } catch (err) {
        alert('检测失败：' + (err.response?.data?.detail || err.message))
      }
    },

    async markAsRead(id) {
      try {
        await api.markWarningAsRead(id)
        const warning = this.warnings.find(w => w.id === id)
        if (warning) warning.is_read = true
        this.unreadCount = Math.max(0, this.unreadCount - 1)
      } catch (err) {
        alert('操作失败')
      }
    },

    viewWarningDetail(warning) {
      alert(`${warning.title}\n\n${warning.message}\n\n建议：${warning.suggestion || '请保持良好的生活习惯'}`)
    },

    // 辅助方法
    getReminderIcon(type) {
      const icons = {
        water: '💧',
        exercise: '🏃',
        meal: '🍽️',
        medication: '💊',
        sleep: '😴',
        measure: '📏',
        custom: '📌'
      }
      return icons[type] || '📌'
    },

    getFrequencyText(freq) {
      const texts = {
        once: '仅一次',
        daily: '每天',
        weekly: '每周',
        weekday: '工作日',
        weekend: '周末'
      }
      return texts[freq] || freq
    },

    getTypeText(type) {
      const texts = {
        water: '喝水',
        exercise: '运动',
        meal: '用餐',
        medication: '用药',
        sleep: '睡眠',
        measure: '测量',
        custom: '自定义'
      }
      return texts[type] || type
    },

    getGoalIcon(category) {
      const icons = {
        exercise: '🏃',
        diet: '🥗',
        weight: '⚖️',
        sleep: '😴',
        water: '💧',
        custom: '🎯'
      }
      return icons[category] || '🎯'
    },

    getCategoryText(category) {
      const texts = {
        exercise: '运动健身',
        diet: '饮食控制',
        weight: '体重管理',
        sleep: '睡眠质量',
        water: '饮水习惯',
        custom: '其他'
      }
      return texts[category] || category
    },

    getStatusText(status) {
      const texts = {
        active: '进行中',
        completed: '已完成',
        expired: '已过期',
        paused: '已暂停'
      }
      return texts[status] || status
    },

    formatDate(dateStr) {
      if (!dateStr) return '未设置'
      return new Date(dateStr).toLocaleDateString('zh-CN')
    },

    formatTime(timeStr) {
      return new Date(timeStr).toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.health-reminder {
  min-height: 100vh;
  background: var(--bg);
}
.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}
.section-header {
  margin-bottom: 24px;
}
.section-header h1 {
  color: var(--fg);
  margin-bottom: 8px;
}
.section-header p {
  color: var(--muted);
}
.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 24px;
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
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
  color: white;
}
.action-bar {
  display: flex;
  gap: 12px;
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
.btn-secondary {
  padding: 12px 24px;
  background: white;
  color: var(--accent);
  border: 2px solid var(--accent);
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 500;
}

/* 提醒卡片 */
.reminder-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.reminder-card {
  background: white;
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.08);
  transition: all 0.3s;
  opacity: 0.6;
}
.reminder-card.enabled {
  opacity: 1;
}
.reminder-card.unread {
  border-left: 4px solid var(--accent);
}
.reminder-icon {
  font-size: 36px;
}
.reminder-info {
  flex: 1;
}
.reminder-info h3 {
  color: var(--fg);
  margin-bottom: 6px;
}
.reminder-info p {
  color: var(--muted);
  font-size: 14px;
  margin-bottom: 10px;
}
.reminder-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
}
.frequency-badge, .type-badge {
  padding: 3px 10px;
  border-radius: var(--radius);
  font-size: 12px;
}
.frequency-badge {
  background: #e8f5e9;
  color: var(--success);
}
.type-badge.water { background: #e3f2fd; color: var(--info); }
.type-badge.exercise { background: #fff3e0; color: var(--warning); }
.type-badge.meal { background: #fce4ec; color: #e91e63; }
.type-badge.medication { background: #f3e5f5; color: #9c27b0; }
.type-badge.sleep { background: #e8eaf6; color: #3f51b5; }
.reminder-methods {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}
.method-tag {
  background: #FFF0E8;
  color: var(--muted);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
}
.reminder-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

/* 开关 */
.toggle-switch {
  position: relative;
  width: 48px;
  height: 26px;
}
.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: 0.3s;
  border-radius: 26px;
}
.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: 0.3s;
  border-radius: 50%;
}
input:checked + .slider {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
}
input:checked + .slider:before {
  transform: translateX(22px);
}
.edit-btn, .delete-btn {
  padding: 6px 14px;
  border: 1px solid #FFE4D6;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.delete-btn {
  color: var(--danger);
  border-color: #fed7d7;
}

/* 目标区域 */
.goal-overview {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  background: white;
  padding: 24px;
  border-radius: var(--radius);
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.08);
}
.overview-card {
  text-align: center;
}
.overview-card h4 {
  color: var(--muted);
  margin-bottom: 16px;
}
.progress-circle {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto;
}
.progress-circle svg {
  width: 100%;
  height: 100%;
}
.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 22px;
  font-weight: bold;
  color: var(--accent);
}
.stats-cards {
  display: flex;
  gap: 24px;
  justify-content: center;
  align-items: center;
  flex: 1;
}
.stat-item {
  text-align: center;
}
.stat-value {
  display: block;
  font-size: 32px;
  font-weight: bold;
  color: var(--fg);
}
.stat-value.completed {
  color: var(--success);
}
.stat-value.total {
  color: var(--accent);
}
.stat-label {
  color: var(--muted);
  font-size: 14px;
}

/* 目标列表 */
.goal-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.goal-card {
  background: white;
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.08);
}
.goal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.goal-icon {
  font-size: 32px;
}
.goal-title-section {
  flex: 1;
}
.goal-title-section h3 {
  color: var(--fg);
  margin-bottom: 4px;
}
.goal-category {
  font-size: 12px;
  color: var(--muted);
  background: #FFF0E8;
  padding: 2px 10px;
  border-radius: 10px;
}
.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}
.status-badge.active {
  background: #e8f5e9;
  color: var(--success);
}
.status-badge.completed {
  background: #e3f2fd;
  color: var(--info);
}
.status-badge.expired {
  background: #ffebee;
  color: var(--danger);
}
.goal-description {
  color: var(--muted);
  margin-bottom: 16px;
}
.goal-progress {
  margin-bottom: 16px;
}
.progress-bar-container {
  height: 10px;
  background: #e0e0e0;
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 8px;
}
.progress-bar {
  height: 100%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
  transition: width 0.3s;
}
.progress-text {
  font-size: 13px;
  color: var(--muted);
}
.goal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.goal-deadline {
  color: var(--muted);
  font-size: 13px;
}
.goal-actions {
  display: flex;
  gap: 8px;
}
.update-btn {
  padding: 8px 16px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

/* 预警区域 */
.warning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: white;
  padding: 20px;
  border-radius: var(--radius);
}
.warning-stats {
  display: flex;
  gap: 20px;
}
.stat-box {
  text-align: center;
  padding: 12px 24px;
  background: #FFF8F5;
  border-radius: var(--radius);
}
.stat-box.hasUnread {
  background: #fff5f5;
  border: 2px solid #fed7d7;
}
.stat-number {
  display: block;
  font-size: 28px;
  font-weight: bold;
  color: var(--fg);
}
.stat-box.hasUnread .stat-number {
  color: var(--danger);
}
.stat-text {
  color: var(--muted);
  font-size: 13px;
}

/* 预警列表 */
.warning-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.warning-card {
  background: white;
  border-radius: var(--radius);
  padding: 20px;
  display: flex;
  gap: 16px;
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.08);
  border-left: 4px solid transparent;
}
.warning-card.high {
  border-left-color: var(--danger);
}
.warning-card.medium {
  border-left-color: var(--warning);
}
.warning-card.low {
  border-left-color: #48bb78;
}
.warning-card.unread {
  background: linear-gradient(to right, rgba(255, 155, 113, 0.05), white);
}
.warning-level-icon {
  font-size: 32px;
}
.warning-content {
  flex: 1;
}
.warning-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.warning-header-row h4 {
  color: var(--fg);
}
.warning-time {
  color: var(--muted);
  font-size: 13px;
}
.warning-content p {
  color: var(--muted);
  line-height: 1.6;
  margin-bottom: 12px;
}
.warning-details {
  background: #FFF8F5;
  padding: 12px;
  border-radius: var(--radius);
  margin-bottom: 12px;
}
.detail-item {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 14px;
}
.detail-label {
  color: var(--muted);
  font-weight: 500;
}
.detail-value.abnormal {
  color: var(--danger);
  font-weight: bold;
}
.normal-range {
  color: var(--muted);
  font-size: 12px;
}
.warning-suggestion {
  background: #e8f5e9;
  padding: 12px;
  border-radius: var(--radius);
  color: var(--success);
  font-size: 14px;
}
.warning-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.read-btn, .detail-btn {
  padding: 8px 16px;
  border: 1px solid #FFE4D6;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
.read-btn:hover {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

/* 弹窗样式 */
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
  max-width: 550px;
  max-height: 90vh;
  overflow-y: auto;
}
.modal.small {
  max-width: 400px;
}
.modal h2 {
  color: var(--fg);
  margin-bottom: 20px;
}
.form-group {
  margin-bottom: 18px;
}
.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--muted);
  font-weight: 500;
}
.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #FFE4D6;
  border-radius: var(--radius);
  font-size: 14px;
  box-sizing: border-box;
}
.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent);
}
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 14px;
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
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
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-weight: 500;
}

/* 无数据状态 */
.no-data {
  text-align: center;
  padding: 60px 20px;
  background: white;
  border-radius: var(--radius);
}
.no-data-icon {
  font-size: 60px;
  display: block;
  margin-bottom: 16px;
}
.no-data p {
  color: var(--muted);
  margin-bottom: 8px;
}
.no-data .hint {
  color: var(--muted);
  font-size: 14px;
}
.mascot-no-data {
  display: flex; align-items: center; justify-content: center;
  gap: 20px; margin: 16px 0; padding: 12px;
}

/* section-header mascot positioning */
.section-header { position: relative; }
.mascot-companion {
  position: absolute; top: 50%; transform: translateY(-50%);
  z-index: 2; pointer-events: none;
}
.mascot-nailong-companion { right: 15px; }

</style>
