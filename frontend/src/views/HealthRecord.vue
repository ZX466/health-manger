<template>
  <div class="health-record">

    <div class="page-header">
      <div class="header-left">
        <h1> 健康记录管理</h1>
        <p class="header-subtitle">记录你的身体状况，获取健康评级</p>
      </div>
      <div class="mascot-companion mascot-cat-companion">
        <CharacterAvatar type="hajimi" :animated="true" style="width:50px;height:50px" />
      </div>
      <div class="header-actions">
        <div class="selection-mode">
          <span class="mode-label">选择模式:</span>
          <button
            :class="['mode-btn', { active: selectionMode === 'single' }]"
            @click="setSelectionMode('single')"
          >
            单选
          </button>
          <button
            :class="['mode-btn', { active: selectionMode === 'multiple' }]"
            @click="setSelectionMode('multiple')"
          >
            多选
          </button>
        </div>
      </div>
    </div>

    <!-- 健康评级横幅 -->
    <div class="rating-banner" :class="ratingClass" v-if="latestRating">
      <div class="rating-left">
        <span class="rating-emoji">{{ latestRating.emoji || '' }}</span>
        <div class="rating-info">
          <span class="rating-label">当前健康评级</span>
          <span class="rating-level">{{ latestRating.rating }}</span>
        </div>
      </div>
      <div class="rating-score-wrap">
        <div class="rating-score-ring" :style="{ '--ring-color': latestRating.color || '#FF9B71' }">
          <span class="rating-score-num">{{ latestRating.score }}</span>
          <span class="rating-score-unit">分</span>
        </div>
      </div>
      <p class="rating-desc">{{ latestRating.overall_advice || '' }}</p>
    </div>

    <!-- 提交后的评级结果 -->
    <div v-if="showRatingResult" class="rating-result-overlay" @click="showRatingResult = false">
      <div class="rating-result-card" @click.stop>
        <button class="result-close" @click="showRatingResult = false">×</button>
        <div class="result-emoji">{{ latestRating?.emoji || '' }}</div>
        <div class="result-level" :class="ratingClass">{{ latestRating?.rating || '-' }}</div>
        <div class="result-score">{{ latestRating?.score || 0 }} <span>分</span></div>
        <p class="result-desc">{{ latestRating?.overall_advice || '' }}</p>
        <div class="result-mascot">
          <CharacterAvatar type="nailong" :animated="true" style="width:60px;height:60px" />
        </div>
        <button class="result-btn" @click="showRatingResult = false">知道了</button>
      </div>
    </div>

    <div class="content">
      <div class="form-section">
        <div class="form-header">
          <h2> 填写健康问卷</h2>
          <p class="form-hint">填写越多，评级越准确</p>
        </div>
        <form @submit.prevent="handleSubmit" class="record-form">

          <!-- 身体基本指标 -->
          <div class="survey-group">
            <h3 class="group-title"> 身体指标</h3>
            <div class="form-row">
              <div class="form-group">
                <label for="hr-height">你的身高大概是？</label>
                <div class="input-with-hint">
                  <input id="hr-height" v-model.number="form.height" type="number" step="0.1" placeholder="大概多高呢" />
                  <span class="input-hint">cm</span>
                </div>
              </div>
              <div class="form-group">
                <label for="hr-weight">体重大约多少？</label>
                <div class="input-with-hint">
                  <input id="hr-weight" v-model.number="form.weight" type="number" step="0.1" placeholder="大约多重" />
                  <span class="input-hint">kg</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 心血管健康 -->
          <div class="survey-group">
            <h3 class="group-title"> 心血管状况</h3>
            <div class="form-row triple">
              <div class="form-group">
                <label for="hr-systolic">心脏用力时血压</label>
                <div class="input-with-hint">
                  <input id="hr-systolic" v-model.number="form.blood_pressure_systolic" type="number" placeholder="高压" />
                  <span class="input-hint">mmHg</span>
                </div>
              </div>
              <div class="form-group">
                <label for="hr-diastolic">心脏放松时血压</label>
                <div class="input-with-hint">
                  <input id="hr-diastolic" v-model.number="form.blood_pressure_diastolic" type="number" placeholder="低压" />
                  <span class="input-hint">mmHg</span>
                </div>
              </div>
              <div class="form-group">
                <label for="hr-heartrate">安静时心跳感觉</label>
                <div class="input-with-hint">
                  <input id="hr-heartrate" v-model.number="form.heart_rate" type="number" placeholder="每分钟跳几次" />
                  <span class="input-hint">次/分</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 体温与视力 -->
          <div class="survey-group">
            <h3 class="group-title"> 其他指标</h3>
            <div class="form-row triple">
              <div class="form-group">
                <label for="hr-temp">最近体温正常吗？</label>
                <div class="input-with-hint">
                  <input id="hr-temp" v-model.number="form.temperature" type="number" step="0.1" placeholder="量一下" />
                  <span class="input-hint">℃</span>
                </div>
              </div>
              <div class="form-group">
                <label for="hr-vision-l">左眼视力如何？</label>
                <div class="input-with-hint">
                  <input id="hr-vision-l" v-model.number="form.vision_left" type="number" step="0.1" placeholder="5.0 正常" />
                  <span class="input-hint"></span>
                </div>
              </div>
              <div class="form-group">
                <label for="hr-vision-r">右眼视力如何？</label>
                <div class="input-with-hint">
                  <input id="hr-vision-r" v-model.number="form.vision_right" type="number" step="0.1" placeholder="5.0 正常" />
                  <span class="input-hint"></span>
                </div>
              </div>
            </div>
          </div>

          <!-- 生活习惯 -->
          <div class="survey-group">
            <h3 class="group-title"> 生活习惯</h3>
            <div class="form-row">
              <div class="form-group">
                <label for="hr-exercise">运动习惯怎么样？</label>
                <select id="hr-exercise" v-model="form.exercise_frequency">
                  <option value="">选一个最接近的</option>
                  <option value="daily">每天都会动一动</option>
                  <option value="regular">每周几次</option>
                  <option value="occasional">偶尔运动</option>
                  <option value="rare">不怎么动</option>
                  <option value="none">基本不动</option>
                </select>
              </div>
              <div class="form-group">
                <label for="hr-sleep">睡眠质量如何？</label>
                <div class="input-with-hint">
                  <input id="hr-sleep" v-model.number="form.sleep_hours" type="number" step="0.5" placeholder="每天睡几个小时" />
                  <span class="input-hint">小时/天</span>
                </div>
              </div>
            </div>
            <div class="form-group">
              <label for="hr-diet">饮食习惯</label>
              <textarea id="hr-diet" v-model="form.diet_habit" rows="3" placeholder="吃得健康吗？饮食有什么偏好或问题..."></textarea>
            </div>
          </div>

          <div v-if="message" :class="['message', messageType]">{{ message }}</div>

          <button type="submit" :disabled="loading" class="submit-btn">
            {{ loading ? '评估中...' : '提交并查看评级' }}
          </button>
        </form>
      </div>

      <div class="records-section">
        <div class="records-header">
          <h2>历史记录 ({{ records.length }})</h2>
          <div v-if="selectedRecords.length > 0" class="batch-actions">
            <span class="selected-count">已选择 {{ selectedRecords.length }} 条</span>
            <button class="action-btn export" @click="exportSelected">
               导出所选
            </button>
            <button class="action-btn delete" @click="confirmDeleteSelected">
               删除所选
            </button>
            <button class="action-btn clear" @click="clearSelection">
              清除选择
            </button>
          </div>
        </div>

        <div v-if="records.length === 0" class="no-data">
          <span class="no-data-icon"></span>
          <p>暂无健康记录</p>
          <div class="mascot-no-data">
            <MiniCat size="large" animation="wobble" />
            <MiniNailong size="large" />
          </div>
          <p class="no-data-hint">请在左侧添加您的第一条健康记录</p>
        </div>

        <div v-else class="records-list">
          <div 
            v-for="record in records" 
            :key="record.id" 
            :class="['record-card', { 
              selected: isSelected(record.id),
              'single-selected': isSelected(record.id) && selectionMode === 'single'
            }]"
            @click="toggleSelection(record.id)"
          >
            <div class="record-checkbox">
              <input 
                type="checkbox" 
                :checked="isSelected(record.id)"
                @click.stop
                @change="toggleSelection(record.id)"
              />
            </div>

            <div class="record-content">
              <div class="record-header">
                <div class="record-meta">
                  <span class="record-date">{{ formatDate(record.record_date) }}</span>
                  <span v-if="record.bmi" :class="['record-bmi', getBmiClass(record.bmi)]">
                    BMI: {{ record.bmi }}
                  </span>
                </div>
                <div class="record-status" v-if="record.health_rating">
                  <span :class="['status-badge', record.health_rating]">
                    {{ record.health_rating }}
                  </span>
                </div>
              </div>

              <div class="record-grid">
                <div class="grid-item">
                  <span class="grid-label">身高</span>
                  <span class="grid-value">{{ record.height || '-' }} cm</span>
                </div>
                <div class="grid-item">
                  <span class="grid-label">体重</span>
                  <span class="grid-value">{{ record.weight || '-' }} kg</span>
                </div>
                <div class="grid-item">
                  <span class="grid-label">血压</span>
                  <span class="grid-value">
                    {{ record.blood_pressure_systolic || '-' }}/{{ record.blood_pressure_diastolic || '-' }} 
                    <span class="unit">mmHg</span>
                  </span>
                </div>
                <div class="grid-item">
                  <span class="grid-label">心率</span>
                  <span class="grid-value">{{ record.heart_rate || '-' }} <span class="unit">次/分</span></span>
                </div>
                <div class="grid-item">
                  <span class="grid-label">体温</span>
                  <span class="grid-value">{{ record.temperature || '-' }} <span class="unit">℃</span></span>
                </div>
                <div class="grid-item">
                  <span class="grid-label">睡眠</span>
                  <span class="grid-value">{{ record.sleep_hours || '-' }} <span class="unit">小时</span></span>
                </div>
              </div>

              <div v-if="record.diet_habit" class="record-diet">
                <span class="diet-label">饮食习惯:</span>
                <span class="diet-text">{{ record.diet_habit }}</span>
              </div>
            </div>

            <div class="record-actions" @click.stop>
              <button class="icon-btn view" @click="viewDetail(record)" title="查看详情">
                
              </button>
              <button class="icon-btn export-single" @click="exportSingle(record)" title="导出">
                
              </button>
              <button class="icon-btn delete-single" @click="confirmDeleteSingle(record)" title="删除">
                
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="cancelDelete">
      <div class="modal-content delete-modal" @click.stop>
        <div class="modal-header">
          <span class="modal-icon warning"></span>
          <h3>确认删除</h3>
        </div>
        <div class="modal-body">
          <p v-if="deleteTarget === 'single'">
            确定要删除这条健康记录吗？<br/>
            <span class="delete-info">记录时间: {{ formatDate(singleDeleteRecord?.record_date) }}</span>
          </p>
          <p v-else>
            确定要删除选中的 <strong>{{ selectedRecords.length }} 条</strong> 健康记录吗？<br/>
            <span class="delete-warning">此操作不可恢复！</span>
          </p>
        </div>
        <div class="modal-footer">
          <button class="modal-btn cancel" @click="cancelDelete">取消</button>
          <button class="modal-btn confirm" @click="executeDelete">确认删除</button>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="showDetailModal" class="modal-overlay" @click="closeDetail">
      <div class="modal-content detail-modal" @click.stop>
        <div class="modal-header">
          <h3> 健康记录详情</h3>
          <button class="close-btn" @click="closeDetail">×</button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <div class="detail-row">
              <span class="detail-label">记录时间</span>
              <span class="detail-value">{{ formatDate(detailRecord?.record_date) }}</span>
            </div>
            <div class="detail-row" v-if="detailRecord?.bmi">
              <span class="detail-label">BMI</span>
              <span class="detail-value">{{ detailRecord?.bmi }} ({{ getBmiAdvice(detailRecord?.bmi) }})</span>
            </div>
          </div>

          <div class="detail-grid">
            <div class="detail-card">
              <span class="detail-card-icon"></span>
              <div class="detail-card-content">
                <span class="detail-card-label">身高</span>
                <span class="detail-card-value">{{ detailRecord?.height || '-' }} cm</span>
              </div>
            </div>
            <div class="detail-card">
              <span class="detail-card-icon"></span>
              <div class="detail-card-content">
                <span class="detail-card-label">体重</span>
                <span class="detail-card-value">{{ detailRecord?.weight || '-' }} kg</span>
              </div>
            </div>
            <div class="detail-card">
              <span class="detail-card-icon"></span>
              <div class="detail-card-content">
                <span class="detail-card-label">血压</span>
                <span class="detail-card-value">
                  {{ detailRecord?.blood_pressure_systolic || '-' }}/{{ detailRecord?.blood_pressure_diastolic || '-' }} mmHg
                </span>
              </div>
            </div>
            <div class="detail-card">
              <span class="detail-card-icon"></span>
              <div class="detail-card-content">
                <span class="detail-card-label">心率</span>
                <span class="detail-card-value">{{ detailRecord?.heart_rate || '-' }} 次/分</span>
              </div>
            </div>
            <div class="detail-card">
              <span class="detail-card-icon"></span>
              <div class="detail-card-content">
                <span class="detail-card-label">体温</span>
                <span class="detail-card-value">{{ detailRecord?.temperature || '-' }} ℃</span>
              </div>
            </div>
            <div class="detail-card">
              <span class="detail-card-icon"></span>
              <div class="detail-card-content">
                <span class="detail-card-label">睡眠</span>
                <span class="detail-card-value">{{ detailRecord?.sleep_hours || '-' }} 小时</span>
              </div>
            </div>
          </div>

          <div v-if="detailRecord?.diet_habit" class="detail-section">
            <span class="section-label">饮食习惯</span>
            <p class="diet-desc">{{ detailRecord?.diet_habit }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作日志 -->
    <div v-if="operationLogs.length > 0" class="logs-panel">
      <div class="logs-header">
        <h4> 操作日志</h4>
        <button class="clear-logs" @click="clearLogs">清空日志</button>
      </div>
      <div class="logs-list">
        <div v-for="(log, idx) in operationLogs.slice(-5).reverse()" :key="idx" class="log-item">
          <span class="log-time">{{ log.time }}</span>
          <span :class="['log-type', log.type]">{{ log.action }}</span>
          <span class="log-detail">{{ log.detail }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api'
import CharacterAvatar from '../components/CharacterAvatar.vue'
import MiniCat from '../components/mascots/MiniCat.vue'
import MiniNailong from '../components/mascots/MiniNailong.vue'

export default {
  name: 'HealthRecord',
  components: { CharacterAvatar, MiniCat, MiniNailong },
  data() {
    return {
      form: {
        height: null,
        weight: null,
        blood_pressure_systolic: null,
        blood_pressure_diastolic: null,
        heart_rate: null,
        temperature: null,
        vision_left: null,
        vision_right: null,
        exercise_frequency: '',
        sleep_hours: null,
        diet_habit: ''
      },
      records: [],
      loading: false,
      message: '',
      messageType: '',

      selectionMode: 'single',
      selectedRecords: [],
      showDeleteModal: false,
      deleteTarget: null,
      singleDeleteRecord: null,

      showDetailModal: false,
      detailRecord: null,

      latestRating: null,
      showRatingResult: false,

      operationLogs: []
    }
  },
  computed: {
    ratingClass() {
      if (!this.latestRating) return ''
      const rating = this.latestRating.rating
      if (rating === '优秀') return 'rating-top'
      if (rating === '良好') return 'rating-great'
      if (rating === '中等') return 'rating-ok'
      if (rating === '较差') return 'rating-meh'
      return 'rating-low'
    }
  },
  async mounted() {
    await Promise.all([this.loadRecords(), this.loadRating()])
  },
  methods: {
    async loadRecords() {
      try {
        const response = await api.getHealthRecords()
        this.records = response.data || []
        this.addLog('info', '加载', `成功加载 ${this.records.length} 条记录`)
      } catch (err) {
        this.addLog('error', '加载', '加载记录失败')
      }
    },

    async loadRating() {
      try {
        const response = await api.getLatestRating()
        this.latestRating = response.data
      } catch (err) {
        this.latestRating = null
      }
    },

    async handleSubmit() {
      this.loading = true
      this.message = ''
      try {
        const data = {}
        for (const key in this.form) {
          if (this.form[key] !== null && this.form[key] !== '') {
            data[key] = this.form[key]
          }
        }
        await api.createHealthRecord(data)
        this.message = '记录已保存，正在评估健康状况...'
        this.messageType = 'success'
        this.resetForm()
        await Promise.all([this.loadRecords(), this.loadRating()])
        if (this.latestRating) {
          this.showRatingResult = true
        }
        this.addLog('success', '添加', '新记录已保存并评级')
        setTimeout(() => { this.message = '' }, 3000)
      } catch (err) {
        this.message = this.extractErrorMessage(err) || '保存失败'
        this.messageType = 'error'
        this.addLog('error', '添加', '保存记录失败')
      } finally {
        this.loading = false
      }
    },

    extractErrorMessage(err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail) && detail.length) {
        // FastAPI 422 校验错误为数组 [{ loc, msg, type }, ...]
        return detail.map(d => d.msg || String(d)).join('；')
      }
      return ''
    },

    resetForm() {
      this.form = {
        height: null, weight: null, blood_pressure_systolic: null,
        blood_pressure_diastolic: null, heart_rate: null, temperature: null,
        vision_left: null, vision_right: null, exercise_frequency: '',
        sleep_hours: null, diet_habit: ''
      }
    },

    setSelectionMode(mode) {
      this.selectionMode = mode
      if (mode === 'single') {
        if (this.selectedRecords.length > 1) {
          this.selectedRecords = [this.selectedRecords[0]]
        }
      }
      this.addLog('info', '模式', `切换为${mode === 'single' ? '单选' : '多选'}模式`)
    },

    isSelected(id) {
      return this.selectedRecords.includes(id)
    },

    toggleSelection(id) {
      if (this.selectionMode === 'single') {
        this.selectedRecords = this.isSelected(id) ? [] : [id]
      } else {
        if (this.isSelected(id)) {
          this.selectedRecords = this.selectedRecords.filter(r => r !== id)
        } else {
          this.selectedRecords.push(id)
        }
      }
    },

    clearSelection() {
      this.selectedRecords = []
      this.addLog('info', '选择', '已清除所有选择')
    },

    viewDetail(record) {
      this.detailRecord = record
      this.showDetailModal = true
      this.addLog('info', '查看', `记录 #${record.id}`)
    },

    closeDetail() {
      this.showDetailModal = false
      this.detailRecord = null
    },

    confirmDeleteSingle(record) {
      this.deleteTarget = 'single'
      this.singleDeleteRecord = record
      this.showDeleteModal = true
    },

    confirmDeleteSelected() {
      if (this.selectedRecords.length === 0) return
      this.deleteTarget = 'batch'
      this.showDeleteModal = true
    },

    cancelDelete() {
      this.showDeleteModal = false
      this.deleteTarget = null
      this.singleDeleteRecord = null
    },

    async executeDelete() {
      try {
        if (this.deleteTarget === 'single') {
          const id = this.singleDeleteRecord.id
          await api.deleteHealthRecord(id)
          this.addLog('warn', '删除', `已删除记录 #${id}`)
        } else {
          for (const id of this.selectedRecords) {
            await api.deleteHealthRecord(id)
          }
          this.addLog('warn', '批量删除', `已删除 ${this.selectedRecords.length} 条记录`)
          this.selectedRecords = []
        }
        await this.loadRecords()
      } catch (err) {
        this.addLog('error', '删除', '删除失败')
        alert('删除失败，请重试')
      } finally {
        this.cancelDelete()
      }
    },

    exportSingle(record) {
      const content = this.generateRecordText([record])
      this.downloadFile(content, `健康记录_${record.id}.txt`)
      this.addLog('success', '导出', `已导出记录 #${record.id}`)
    },

    exportSelected() {
      if (this.selectedRecords.length === 0) return
      const selectedRecords = this.records.filter(r => this.selectedRecords.includes(r.id))
      const content = this.generateRecordText(selectedRecords)
      this.downloadFile(content, `健康记录_批量导出_${new Date().toLocaleDateString()}.txt`)
      this.addLog('success', '批量导出', `已导出 ${selectedRecords.length} 条记录`)
    },

    generateRecordText(records) {
      let content = '=================================\n'
      content += '       健康记录报告\n'
      content += '=================================\n'
      content += `导出时间: ${new Date().toLocaleString()}\n`
      content += `记录数量: ${records.length}\n`
      content += '=================================\n\n'

      for (const record of records) {
        content += `【记录 #${record.id}】\n`
        content += `时间: ${this.formatDate(record.record_date)}\n`
        content += `身高: ${record.height || '-'} cm\n`
        content += `体重: ${record.weight || '-'} kg\n`
        content += `BMI: ${record.bmi || '-'}\n`
        content += `血压: ${record.blood_pressure_systolic || '-'}/${record.blood_pressure_diastolic || '-'} mmHg\n`
        content += `心率: ${record.heart_rate || '-'} 次/分\n`
        content += `体温: ${record.temperature || '-'} ℃\n`
        content += `睡眠: ${record.sleep_hours || '-'} 小时\n`
        if (record.diet_habit) {
          content += `饮食习惯: ${record.diet_habit}\n`
        }
        content += '\n---------------------------------\n\n'
      }

      content += '=================================\n'
      content += '     报告生成完毕\n'
      content += '=================================\n'
      return content
    },

    downloadFile(content, filename) {
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    },

    formatDate(dateStr) {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    },

    getBmiClass(bmi) {
      if (!bmi) return ''
      if (bmi < 18.5) return 'bmi-low'
      if (bmi < 24) return 'bmi-normal'
      if (bmi < 28) return 'bmi-high'
      return 'bmi-obese'
    },

    getBmiAdvice(bmi) {
      if (!bmi) return ''
      if (bmi < 18.5) return '偏瘦'
      if (bmi < 24) return '正常'
      if (bmi < 28) return '偏胖'
      return '肥胖'
    },

    addLog(type, action, detail) {
      const now = new Date()
      this.operationLogs.push({
        time: `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`,
        type,
        action,
        detail
      })
    },

    clearLogs() {
      this.operationLogs = []
    }
  }
}
</script>

<style scoped>
.health-record {
  min-height: 100vh;
  background: var(--bg);
}

/* ========== 健康评级横幅 ========== */
.rating-banner {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent) 100%);
  border-radius: var(--radius-lg);
  padding: 24px 32px;
  margin: 20px 30px 0;
  color: white;
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
  box-shadow: 0 8px 32px rgba(255, 155, 113, 0.25);
  position: relative;
  overflow: hidden;
}
.rating-banner::before {
  content: '';
  position: absolute;
  top: -30%;
  right: -5%;
  width: 200px;
  height: 200px;
  background: rgba(255,255,255,0.08);
  border-radius: 50%;
}
.rating-banner.rating-top {
  background: linear-gradient(135deg, #4CAF50 0%, #81C784 100%);
}
.rating-banner.rating-great {
  background: linear-gradient(135deg, #42A5F5 0%, #64B5F6 100%);
}
.rating-banner.rating-ok {
  background: linear-gradient(135deg, var(--accent) 0%, var(--warning) 100%);
}
.rating-banner.rating-meh {
  background: linear-gradient(135deg, #FF9800 0%, #FFB74D 100%);
}
.rating-banner.rating-low {
  background: linear-gradient(135deg, #F44336 0%, #EF5350 100%);
}
.rating-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.rating-emoji {
  font-size: 48px;
  animation: rating-bounce 2s ease-in-out infinite;
}
@keyframes rating-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
.rating-info {
  display: flex;
  flex-direction: column;
}
.rating-label {
  font-size: 13px;
  opacity: 0.85;
}
.rating-level {
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 2px;
}
.rating-score-wrap {
  margin-left: auto;
}
.rating-score-ring {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 3px solid rgba(255,255,255,0.4);
}
.rating-score-num {
  font-size: 24px;
  font-weight: 800;
  line-height: 1;
}
.rating-score-unit {
  font-size: 11px;
  opacity: 0.8;
}
.rating-desc {
  width: 100%;
  font-size: 13px;
  opacity: 0.9;
  margin: 0;
  padding-top: 4px;
  border-top: 1px solid rgba(255,255,255,0.2);
}

/* ========== 评级结果弹窗 ========== */
.rating-result-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fade-in 0.2s;
}
@keyframes fade-in {
  from { opacity: 0; } to { opacity: 1; }
}
.rating-result-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: 40px;
  text-align: center;
  width: 360px;
  max-width: 90vw;
  position: relative;
  animation: pop-in 0.3s cubic-bezier(0.34,1.56,0.64,1);
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}
@keyframes pop-in {
  from { transform: scale(0.7); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.result-close {
  position: absolute;
  top: 12px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  font-size: 24px;
  color: var(--muted);
  cursor: pointer;
}
.result-emoji {
  font-size: 64px;
  margin-bottom: 8px;
  animation: rating-bounce 1.5s ease-in-out infinite;
}
.result-level {
  font-size: 36px;
  font-weight: 800;
  letter-spacing: 3px;
  margin-bottom: 8px;
}
.result-level.rating-top { color: #4CAF50; }
.result-level.rating-great { color: #42A5F5; }
.result-level.rating-ok { color: var(--accent); }
.result-level.rating-meh { color: #FF9800; }
.result-level.rating-low { color: #F44336; }
.result-score {
  font-size: 48px;
  font-weight: 800;
  color: var(--fg);
  line-height: 1;
  margin-bottom: 12px;
}
.result-score span {
  font-size: 18px;
  font-weight: 400;
  color: var(--muted);
}
.result-desc {
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 16px;
}
.result-mascot {
  margin-bottom: 16px;
}
.result-btn {
  padding: 12px 32px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 15px rgba(255, 155, 113, 0.3);
}
.result-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 155, 113, 0.4);
}

/* ========== 问卷分组 ========== */
.form-header {
  margin-bottom: 24px;
}
.form-header h2 {
  margin-bottom: 4px;
}
.form-hint {
  color: var(--muted);
  font-size: 13px;
  margin: 0;
}
.survey-group {
  background: #FFFCFA;
  border: 1px solid #FFE8D6;
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 4px;
}
.group-title {
  font-size: 15px;
  color: var(--fg);
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #FFE4D6;
}
.input-with-hint {
  display: flex;
  align-items: center;
  gap: 0;
}
.input-with-hint input {
  flex: 1;
  border-radius: var(--radius) 0 0 var(--radius);
}
.input-hint {
  padding: 12px 12px;
  background: #FFF5EE;
  border: 2px solid #FFE4D6;
  border-left: none;
  border-radius: 0 var(--radius) var(--radius) 0;
  color: var(--muted);
  font-size: 12px;
  white-space: nowrap;
  min-width: 48px;
  text-align: center;
}
.input-hint:empty {
  display: none;
}
.input-with-hint input:has(+ .input-hint:empty) {
  border-radius: var(--radius);
}

.page-header {
  background: var(--accent);
  padding: 24px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px rgba(255, 155, 113, 0.3);
}

.header-left h1 {
  color: white;
  font-size: 24px;
  margin-bottom: 4px;
}

.header-subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.selection-mode {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-label {
  color: white;
  font-size: 14px;
}

.mode-btn {
  padding: 6px 16px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: transparent;
  color: white;
  border-radius: 20px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.mode-btn.active {
  background: white;
  color: var(--accent);
  border-color: white;
}

.mode-btn:hover:not(.active) {
  background: rgba(255, 255, 255, 0.2);
}

.content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 30px;
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 30px;
}

@media (max-width: 1100px) {
  .content {
    grid-template-columns: 1fr;
  }
}

.form-section, .records-section {
  background: white;
  border-radius: var(--radius-lg);
  padding: 28px;
  box-shadow: 0 4px 16px rgba(255, 155, 113, 0.12);
}

h2 {
  color: var(--fg);
  margin-bottom: 24px;
  font-size: 18px;
  font-weight: 600;
}

.record-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.form-row.triple {
  grid-template-columns: 1fr 1fr 1fr;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-weight: 500;
  color: var(--fg);
  font-size: 13px;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 12px 14px;
  border: 2px solid #FFE4D6;
  border-radius: var(--radius);
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.message {
  padding: 12px;
  border-radius: var(--radius);
  text-align: center;
  font-size: 14px;
}

.message.success {
  background: #f0f9f0;
  color: var(--success);
  border: 1px solid #c8e6c9;
}

.message.error {
  background: #fff5f5;
  color: var(--danger);
  border: 1px solid #ffcdd2;
}

.submit-btn {
  padding: 14px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 15px rgba(255, 155, 113, 0.3);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 155, 113, 0.4);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.records-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.batch-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.selected-count {
  background: var(--accent);
  color: white;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}

.action-btn {
  padding: 8px 16px;
  border: 1px solid #FFE4D6;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.action-btn.export {
  color: var(--success);
  border-color: var(--success);
}

.action-btn.export:hover {
  background: #f0f9f0;
}

.action-btn.delete {
  color: var(--danger);
  border-color: var(--danger);
}

.action-btn.delete:hover {
  background: #fff5f5;
}

.action-btn.clear {
  color: var(--muted);
}

.action-btn.clear:hover {
  background: #f5f5f5;
}

.no-data {
  text-align: center;
  padding: 60px 20px;
  color: var(--muted);
}

.no-data-icon {
  font-size: 64px;
  display: block;
  margin-bottom: 16px;
}

.no-data-hint {
  font-size: 13px;
  margin-top: 8px;
}
.mascot-no-data {
  display: flex; align-items: center; justify-content: center;
  gap: 20px; margin: 16px 0; padding: 12px;
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 700px;
  overflow-y: auto;
  padding-right: 4px;
}

.record-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  border: 2px solid #FFE4D6;
  border-radius: var(--radius);
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.record-card:hover {
  border-color: var(--accent);
  box-shadow: 0 4px 15px rgba(255, 155, 113, 0.15);
}

.record-card.selected {
  border-color: var(--accent);
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
}

.record-card.single-selected {
  box-shadow: 0 0 0 3px rgba(255, 155, 113, 0.3);
}

.record-checkbox {
  padding-top: 2px;
}

.record-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--accent);
}

.record-content {
  flex: 1;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.record-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.record-date {
  color: var(--accent);
  font-weight: 600;
  font-size: 13px;
}

.record-bmi {
  padding: 3px 10px;
  border-radius: var(--radius);
  font-size: 12px;
  font-weight: 600;
}

.record-bmi.bmi-low {
  background: #e3f2fd;
  color: var(--info);
}

.record-bmi.bmi-normal {
  background: #e8f5e9;
  color: var(--success);
}

.record-bmi.bmi-high {
  background: #fff8e1;
  color: var(--warning);
}

.record-bmi.bmi-obese {
  background: #ffebee;
  color: var(--danger);
}

.status-badge {
  padding: 3px 10px;
  border-radius: var(--radius);
  font-size: 11px;
  font-weight: 600;
}

.status-badge.夯 {
  background: #f6ffed;
  color: #52c41a;
}

.status-badge.顶级 {
  background: #e6f7ff;
  color: #1890ff;
}

.status-badge.人上人 {
  background: #fffbe6;
  color: #faad14;
}

.status-badge.NPC {
  background: #fff7e6;
  color: #fa8c16;
}

.status-badge.拉完了 {
  background: #fff1f0;
  color: #f5222d;
}

.record-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.grid-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.grid-label {
  font-size: 11px;
  color: var(--muted);
}

.grid-value {
  font-size: 13px;
  color: var(--fg);
  font-weight: 500;
}

.unit {
  color: var(--muted);
  font-size: 11px;
}

.record-diet {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #eee;
  font-size: 12px;
}

.diet-label {
  color: var(--muted);
}

.diet-text {
  color: var(--muted);
  margin-left: 4px;
}

.record-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #FFE4D6;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.icon-btn:hover {
  border-color: var(--accent);
  background: #FFF5EE;
}

.icon-btn.delete-single:hover {
  border-color: var(--danger);
  background: #fff5f5;
}

/* Modal */
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

.modal-content {
  background: white;
  border-radius: var(--radius-lg);
  max-width: 90%;
  animation: modalIn 0.2s ease;
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.delete-modal {
  width: 400px;
  padding: 28px;
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.modal-icon {
  font-size: 32px;
}

.modal-header h3 {
  font-size: 18px;
  color: var(--fg);
  margin: 0;
}

.modal-body {
  margin-bottom: 24px;
}

.modal-body p {
  color: var(--muted);
  line-height: 1.6;
  font-size: 14px;
}

.delete-info {
  display: block;
  margin-top: 8px;
  font-size: 13px;
  color: var(--muted);
}

.delete-warning {
  color: var(--danger);
  font-weight: 600;
}

.modal-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-btn {
  padding: 10px 24px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-btn.cancel {
  background: #f5f5f5;
  border: 1px solid #FFE4D6;
  color: var(--muted);
}

.modal-btn.cancel:hover {
  background: #eee;
}

.modal-btn.confirm {
  background: var(--danger);
  border: none;
  color: white;
}

.modal-btn.confirm:hover {
  background: #d32f2f;
}

.detail-modal {
  width: 560px;
  max-height: 80vh;
  overflow-y: auto;
}

.detail-modal .modal-header {
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.detail-modal .modal-header h3 {
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  font-size: 24px;
  color: var(--muted);
  cursor: pointer;
}

.close-btn:hover {
  color: var(--fg);
}

.detail-modal .modal-body {
  padding: 24px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-label {
  color: var(--muted);
  font-size: 13px;
}

.detail-value {
  color: var(--fg);
  font-weight: 500;
  font-size: 13px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}

.detail-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  background: #FFF5EE;
  border-radius: 10px;
}

.detail-card-icon {
  font-size: 24px;
}

.detail-card-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-card-label {
  font-size: 11px;
  color: var(--muted);
}

.detail-card-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--fg);
}

.section-label {
  display: block;
  color: var(--muted);
  font-size: 12px;
  margin-bottom: 8px;
}

.diet-desc {
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
  background: #FFF5EE;
  padding: 12px;
  border-radius: var(--radius);
}

/* Logs Panel */
.logs-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 360px;
  background: white;
  border-radius: var(--radius);
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.15);
  z-index: 100;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
}

.logs-header h4 {
  margin: 0;
  font-size: 13px;
  color: var(--fg);
}

.clear-logs {
  border: none;
  background: none;
  color: var(--muted);
  font-size: 12px;
  cursor: pointer;
}

.clear-logs:hover {
  color: var(--danger);
}

.logs-list {
  padding: 8px 16px 12px;
  max-height: 200px;
  overflow-y: auto;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 12px;
  border-bottom: 1px solid #f5f5f5;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: var(--muted);
  font-family: monospace;
}

.log-type {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.log-type.info {
  background: #e3f2fd;
  color: var(--info);
}

.log-type.success {
  background: #e8f5e9;
  color: var(--success);
}

.log-type.warn {
  background: #fff3e0;
  color: var(--warning);
}

.log-type.error {
  background: #ffebee;
  color: var(--danger);
}

.log-detail {
  color: var(--muted);
  flex: 1;
}
/* page-header mascot positioning */
.page-header { display: flex; align-items: center; flex-wrap: wrap; }
.page-header .mascot-companion {
  position: relative; top: auto; transform: none;
  margin-right: 8px; flex-shrink: 0;
}

</style>
