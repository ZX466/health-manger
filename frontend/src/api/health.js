import http from './http'

export function createHealthRecord (data) {
  return http.post('/health/records', data)
}

export function getHealthRecords () {
  return http.get('/health/records')
}

export function getHealthRecord (id) {
  return http.get(`/health/records/${id}`)
}

export function deleteHealthRecord (id) {
  return http.delete(`/health/records/${id}`)
}

export function getLatestAnalysis () {
  return http.get('/health/analysis/latest')
}

export function getAnalysisHistory () {
  return http.get('/health/analysis/history')
}

export function getLatestRating () {
  return http.get('/health/rating/latest')
}

export function getRatingHistory (days = 7) {
  return http.get('/health/rating/history', { params: { days } })
}

/**
 * 体检单 OCR。后端真实路径是 /health/reports/ocr，接收 multipart 字段 file。
 * 只返回草稿字段，确认后仍走 v1 的 POST /health/records 入库。
 */
export function ocrHealthReport (formData) {
  return http.post('/health/reports/ocr', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000
  })
}

export default {
  createHealthRecord,
  getHealthRecords,
  getHealthRecord,
  deleteHealthRecord,
  getLatestAnalysis,
  getAnalysisHistory,
  getLatestRating,
  getRatingHistory,
  ocrHealthReport
}
