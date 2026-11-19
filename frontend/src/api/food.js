import http from './http'

export function getFoods (params) {
  return http.get('/food/foods', { params })
}

export function getFood (id) {
  return http.get(`/food/foods/${id}`)
}

export function createFood (data) {
  return http.post('/food/foods', data)
}

export function updateFood (id, data) {
  return http.put(`/food/foods/${id}`, data)
}

export function deleteFood (id) {
  return http.delete(`/food/foods/${id}`)
}

export function createFoodRecord (data) {
  return http.post('/food/records', data)
}

export function getFoodRecords (params) {
  return http.get('/food/records', { params })
}

export function getFoodStats (params) {
  return http.get('/food/records/stats', { params })
}

export function deleteFoodRecord (id) {
  return http.delete(`/food/records/${id}`)
}

/**
 * 拍照识餐。后端真实路径是 /food/recognize，接收 multipart 字段 file。
 * 返回 items[{name, grams, calories}] 与 needs_confirm，不直接入库。
 */
export function recognizeFoodImage (formData) {
  return http.post('/food/recognize', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000
  })
}

export function createCustomFood (data) {
  return http.post('/food/custom', data)
}

export default {
  getFoods,
  getFood,
  createFood,
  updateFood,
  deleteFood,
  createFoodRecord,
  getFoodRecords,
  getFoodStats,
  deleteFoodRecord,
  recognizeFoodImage,
  createCustomFood
}
