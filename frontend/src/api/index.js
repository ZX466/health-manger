import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userName')
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default {
  register(data) {
    return api.post('/auth/register', data)
  },
  login(username, password) {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    return api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  },
  getCurrentUser() {
    return api.get('/auth/me')
  },
  createHealthRecord(data) {
    return api.post('/health/records', data)
  },
  getHealthRecords() {
    return api.get('/health/records')
  },
  getHealthRecord(id) {
    return api.get(`/health/records/${id}`)
  },
  deleteHealthRecord(id) {
    return api.delete(`/health/records/${id}`)
  },
  getLatestAnalysis() {
    return api.get('/health/analysis/latest')
  },
  getAnalysisHistory() {
    return api.get('/health/analysis/history')
  },
  
  // 食物管理
  getFoods(params) {
    return api.get('/food/foods', { params })
  },
  getFood(id) {
    return api.get(`/food/foods/${id}`)
  },
  createFood(data) {
    return api.post('/food/foods', data)
  },
  updateFood(id, data) {
    return api.put(`/food/foods/${id}`, data)
  },

  // 饮食记录
  createFoodRecord(data) {
    return api.post('/food/records', data)
  },
  getFoodRecords(params) {
    return api.get('/food/records', { params })
  },
  getFoodStats(params) {
    return api.get('/food/records/stats', { params })
  },
  deleteFoodRecord(id) {
    return api.delete(`/food/records/${id}`)
  },
  
  // 运动管理
  getSports(params) {
    return api.get('/sport/sports', { params })
  },
  getSport(id) {
    return api.get(`/sport/sports/${id}`)
  },
  createSport(data) {
    return api.post('/sport/sports', data)
  },
  updateSport(id, data) {
    return api.put(`/sport/sports/${id}`, data)
  },

  // 运动记录
  createSportRecord(data) {
    return api.post('/sport/records', data)
  },
  getSportRecords(params) {
    return api.get('/sport/records', { params })
  },
  getSportStats(params) {
    return api.get('/sport/records/stats', { params })
  },
  deleteSportRecord(id) {
    return api.delete(`/sport/records/${id}`)
  },
  
  // AI 健康分析
  createAIAnalysis(data) {
    return api.post('/ai/analysis', data)
  },
  getAIAnalysisHistory(limit = 10) {
    return api.get('/ai/analysis/history', { params: { limit } })
  },
  getAIAnalysis(id) {
    return api.get(`/ai/analysis/${id}`)
  },
  deleteAIAnalysis(id) {
    return api.delete(`/ai/analysis/${id}`)
  },
  quickHealthAnalysis() {
    return api.post('/ai/quick-analysis')
  },
  
  // 健康预警
  checkWarnings() {
    return api.post('/warning/check')
  },
  getWarnings(params) {
    return api.get('/warning/list', { params })
  },
  markWarningAsRead(id) {
    return api.put(`/warning/read/${id}`)
  },
  markAllWarningsAsRead() {
    return api.put('/warning/read-all')
  },
  deleteWarning(id) {
    return api.delete(`/warning/${id}`)
  },

  // 健康评级
  getLatestRating() {
    return api.get('/health/rating/latest')
  },

  // 舌诊分析
  uploadTongueImage(formData) {
    return api.post('/tongue/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getTongueList(params) {
    return api.get('/tongue/list', { params })
  },
  getTongueDetail(id) {
    return api.get(`/tongue/${id}`)
  },
  getTongueImage(id) {
    return api.get(`/tongue/image/${id}`, { responseType: 'blob' })
  },
  getLatestTongueResult() {
    return api.get('/tongue/latest/result')
  },
  deleteTongueRecord(id) {
    return api.delete(`/tongue/${id}`)
  },
  getTongueStats() {
    return api.get('/tongue/stats/summary')
  },

// AI 健康分析（kilo I-N1 补齐）
  getHealthEvaluation() {
    return api.post('/ai/health-evaluation')
  },
  asyncAIAnalysis(data) {
    return api.post('/ai/async-analysis', data)
  },
  getTaskStatus(taskId) {
    return api.get(`/ai/task/${taskId}`)
  },
  getWarningStats() {
    return api.get('/warning/stats')
  },

  // AI 对话（Claude F-N1）
  createChatSession(data) {
    return api.post('/chat/session', data)
  },
  getChatSessions(params) {
    return api.get('/chat/sessions', { params })
  },
  getChatMessages(sessionId, params) {
    return api.get(`/chat/session/${sessionId}/messages`, { params })
  },
  sendChatMessage(sessionId, data) {
    return api.post(`/chat/session/${sessionId}/message`, data)
  },
  addTongueContext(sessionId) {
    return api.post(`/chat/session/${sessionId}/tongue-context`)
  },
  deleteChatSession(sessionId) {
    return api.delete(`/chat/session/${sessionId}`)
  }
}
