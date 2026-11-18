import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

const STALE_MS = 15000

/**
 * 预警统计（侧栏 / 顶栏 / 总览共用一个未读数）。
 * 统计失败保持旧值：徽标不应因为一次网络抖动而消失。
 */
export const useWarningStore = defineStore('warnings', () => {
  const stats = ref({ total: 0, unread: 0, danger: 0 })
  let lastFetched = 0
  // S-1：账号切换时递增；旧会话晚到的响应按 epoch 丢弃，避免串号显示未读数。
  let sessionEpoch = 0

  async function refreshStats(force = false) {
    if (!force && Date.now() - lastFetched < STALE_MS) return stats.value
    const epoch = sessionEpoch
    try {
      const { data } = await api.getWarningStats()
      if (epoch !== sessionEpoch) return stats.value
      stats.value = {
        total: Number(data?.total) || 0,
        unread: Number(data?.unread) || 0,
        danger: Number(data?.danger) || 0
      }
      lastFetched = Date.now()
    } catch {
      // 静默：徽标是辅助信息，不阻塞页面
    }
    return stats.value
  }

  function resetStats() {
    sessionEpoch += 1
    stats.value = { total: 0, unread: 0, danger: 0 }
    lastFetched = 0
  }

  function setStats(next) {
    stats.value = {
      total: Math.max(0, Number(next?.total) || 0),
      unread: Math.max(0, Number(next?.unread) || 0),
      danger: Math.max(0, Number(next?.danger) || 0)
    }
    lastFetched = Date.now()
  }

  return { stats, refreshStats, resetStats, setStats }
})
