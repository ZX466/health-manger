import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useTongueStore = defineStore('tongue', () => {
  const historyList = ref([])
  const result = ref(null)
  const realtimeResult = ref(null)
  const realtimeHistory = ref([])
  const analyzing = ref(false)

  async function loadHistory() {
    try {
      const response = await api.getTongueList({ limit: 10 })
      historyList.value = response.data || []
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Failed to load history')
    }
  }

  async function uploadAndAnalyze(file, mode, captureFn) {
    analyzing.value = true
    try {
      if (mode === 'upload') {
        const formData = new FormData()
        formData.append('file', file)

        await api.uploadTongueImage(formData)
        // 用 /tongue/latest/result（返回 {name,color,desc} 对象结构）而非 getTongueDetail（字符串字段），
        // 修复 M3：舌色/苔色恒显示 "-"
        const detailResponse = await api.getLatestTongueResult()
        result.value = detailResponse.data
      } else if (captureFn) {
        const blob = await captureFn()
        const formData = new FormData()
        formData.append('file', blob, 'frame.jpg')

        await api.uploadTongueImage(formData)
        const detailResponse = await api.getLatestTongueResult()
        realtimeResult.value = detailResponse.data

        const now = new Date()
        const newEntry = {
          time: `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`,
          syndrome: detailResponse.data.tcm_syndrome,
          overall_type: detailResponse.data.overall_type,
          confidence: detailResponse.data.confidence_score
        }
        realtimeHistory.value = [...realtimeHistory.value, newEntry].slice(-20)
      }

      await loadHistory()
    } finally {
      analyzing.value = false
    }
  }

  function clearResult() {
    result.value = null
    realtimeResult.value = null
  }

  return {
    historyList,
    result,
    realtimeResult,
    realtimeHistory,
    analyzing,
    loadHistory,
    uploadAndAnalyze,
    clearResult
  }
})
