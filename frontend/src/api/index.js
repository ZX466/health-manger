import http from './http'
import foodApi from './food'
import healthApi from './health'
import chatApi from './chat'
import mentalApi from './mental'

export default {
  // 认证
  register(data) {
    return http.post('/auth/register', data)
  },
  login(username, password) {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    return http.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  },
  getCurrentUser() {
    return http.get('/auth/me')
  },

  // 饮食 / 健康 / 心理 / 对话（模块化）
  ...foodApi,
  ...healthApi,
  ...chatApi,
  ...mentalApi,

  // 运动管理
  getSports(params) {
    return http.get('/sport/sports', { params })
  },
  getSport(id) {
    return http.get(`/sport/sports/${id}`)
  },
  createSport(data) {
    return http.post('/sport/sports', data)
  },
  updateSport(id, data) {
    return http.put(`/sport/sports/${id}`, data)
  },
  createSportRecord(data) {
    return http.post('/sport/records', data)
  },
  getSportRecords(params) {
    return http.get('/sport/records', { params })
  },
  getSportStats(params) {
    return http.get('/sport/records/stats', { params })
  },
  deleteSportRecord(id) {
    return http.delete(`/sport/records/${id}`)
  },

  // AI 健康分析
  createAIAnalysis(data) {
    // LLM 生成通常 10–40s，默认 30s 容易误报超时。
    return http.post('/ai/analysis', data, { timeout: 60000 })
  },
  getAIAnalysisHistory(limit = 10) {
    return http.get('/ai/analysis/history', { params: { limit } })
  },
  getAIAnalysis(id) {
    return http.get(`/ai/analysis/${id}`)
  },
  deleteAIAnalysis(id) {
    return http.delete(`/ai/analysis/${id}`)
  },
  quickHealthAnalysis() {
    return http.post('/ai/quick-analysis', null, { timeout: 60000 })
  },
  getHealthEvaluation() {
    return http.post('/ai/health-evaluation', null, { timeout: 60000 })
  },
  asyncAIAnalysis(data) {
    return http.post('/ai/async-analysis', data)
  },
  getTaskStatus(taskId) {
    return http.get(`/ai/task/${taskId}`)
  },

  // 健康预警
  checkWarnings() {
    return http.post('/warning/check')
  },
  getWarnings(params) {
    return http.get('/warning/list', { params })
  },
  markWarningAsRead(id) {
    return http.put(`/warning/read/${id}`)
  },
  markAllWarningsAsRead() {
    return http.put('/warning/read-all')
  },
  deleteWarning(id) {
    return http.delete(`/warning/${id}`)
  },
  getWarningStats() {
    return http.get('/warning/stats')
  },

  // 舌诊分析
  uploadTongueImage(formData) {
    return http.post('/tongue/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getTongueList(params) {
    return http.get('/tongue/list', { params })
  },
  getTongueDetail(id) {
    return http.get(`/tongue/${id}`)
  },
  getTongueImage(id) {
    return http.get(`/tongue/image/${id}`, { responseType: 'blob' })
  },
  getLatestTongueResult() {
    return http.get('/tongue/latest/result')
  },
  deleteTongueRecord(id) {
    return http.delete(`/tongue/${id}`)
  },
  getTongueStats() {
    return http.get('/tongue/stats/summary')
  },

  // AI 配置（自定义供应商/模型）
  getAiConfig() {
    return http.get('/ai/config')
  },
  saveAiConfig(data) {
    return http.put('/ai/config', data)
  },
  deleteAiConfig() {
    return http.delete('/ai/config')
  },
  testAiConfig(data) {
    return http.post('/ai/config/test', data)
  }
}
