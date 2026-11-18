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

  async function refreshStats(force = false) {
    if (!force && Date.now() - lastFetched < STALE_MS) return stats.value
    try {
      const { data } = await api.getWarningStats()
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

  function setStats(next) {
    stats.value = {
      total: Math.max(0, Number(next?.total) || 0),
      unread: Math.max(0, Number(next?.unread) || 0),
      danger: Math.max(0, Number(next?.danger) || 0)
    }
    lastFetched = Date.now()
  }

  return { stats, refreshStats, setStats }
})
