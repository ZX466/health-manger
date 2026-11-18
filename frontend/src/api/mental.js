import http from './http'

/**
 * 心理健康接口。
 * 说明：需求文档中的 /mental/records、/mental/assessments 在当前后端不存在，
 * 这里保留同名能力函数，实际请求落到已实现的 /mental/mood 与 /mental/scales。
 */

export function getMentalRecords (params) {
  return http.get('/mental/mood', { params })
}

export function createMentalRecord (data) {
  return http.post('/mental/mood', data)
}

export function getMentalTrend (params) {
  return http.get('/mental/trend', { params })
}

export function getMentalAssessments (params) {
  return http.get('/mental/scales/history', { params })
}

export function createMentalAssessment (scaleType, data) {
  return http.post(`/mental/scales/${scaleType}/submit`, data)
}

export function getMentalScales () {
  return http.get('/mental/scales')
}

export function getMentalSummary () {
  return http.get('/mental/summary')
}

// v1 命名保留，避免既有页面回归。
export const getMentalMood = getMentalRecords
export const saveMentalMood = createMentalRecord
export const getMentalScaleHistory = getMentalAssessments
export const submitMentalScale = createMentalAssessment

export default {
  getMentalRecords,
  createMentalRecord,
  getMentalTrend,
  getMentalAssessments,
  createMentalAssessment,
  getMentalScales,
  getMentalSummary,
  getMentalMood,
  saveMentalMood,
  getMentalScaleHistory,
  submitMentalScale
}
