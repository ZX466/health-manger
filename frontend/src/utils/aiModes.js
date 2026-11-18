/** AI 快捷/异步分析的前端展示辅助。 */

const STATUS_LABELS = {
  submitting: '提交中…',
  pending: '排队中…',
  running: '分析中…',
  completed: '已完成',
  failed: '失败'
}

export function asyncStatusLabel (status) {
  return STATUS_LABELS[status] || '处理中…'
}

/**
 * 把 /api/ai/task/{id} 的 result 统一成可展示结构。
 * 兼容旧版 tuple（JSON 序列化后为数组）和新版 {content,tokens_used,analysis_id}。
 */
export function normalizeTaskResult (result) {
  if (Array.isArray(result) && result.length >= 2) {
    return {
      content: String(result[0] ?? ''),
      tokensUsed: Number(result[1]) || 0,
      analysisId: null
    }
  }

  if (result && typeof result === 'object') {
    return {
      content: String(result.content ?? ''),
      tokensUsed: Number(result.tokens_used) || 0,
      analysisId: result.analysis_id ?? null
    }
  }

  return { content: '', tokensUsed: 0, analysisId: null }
}
