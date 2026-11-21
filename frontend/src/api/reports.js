import http from './http'

/**
 * 健康周报：只聚合既有记录，不新增存储。
 * end_date 缺省为今天，窗口为含当天的近 7 天。
 */
export function getWeeklyReport (params = {}) {
  return http.get('/reports/weekly', { params })
}

/** AI 解读通常 10–40s，单独放宽超时。 */
export function generateWeeklyReportAI (params = {}) {
  return http.post('/reports/weekly/ai', null, { params, timeout: 60000 })
}

export default {
  getWeeklyReport,
  generateWeeklyReportAI
}
