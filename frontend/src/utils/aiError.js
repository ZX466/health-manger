/**
 * 把 AI 分析接口的失败统一成 UI 可操作的信息。
 *
 * 后端约定：缺 Key → 503，无健康数据 → 400，限流 → 429，其余 → 500。
 * action 决定提示条旁边显示哪个入口：设置 / 添加记录 / 重试。
 */
const NO_KEY_MESSAGE = '未配置 AI API 密钥，请先在「AI 设置」中填写后重试。'
const NO_DATA_MESSAGE = '暂无健康数据，请先添加一条体检记录。'
const TIMEOUT_MESSAGE = 'AI 分析超时，尚未生成结果。请稍后重试，或在 AI 设置中换一个更快的模型。'

function readDetail (error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail.trim()
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === 'string' ? item : item?.msg || ''))
      .filter(Boolean)
      .join('；')
  }
  return ''
}

export function aiErrorInfo (error) {
  const status = error?.response?.status
  const detail = readDetail(error)
  const rawMessage = String(error?.message || '')

  if (
    error?.code === 'ECONNABORTED' ||
    error?.code === 'ETIMEDOUT' ||
    /timeout/i.test(rawMessage)
  ) {
    return { kind: 'timeout', message: TIMEOUT_MESSAGE, action: 'retry' }
  }

  if (!error?.response) {
    return {
      kind: 'network',
      message: '无法连接服务器，请检查网络后重试。',
      action: 'retry'
    }
  }

  if (status === 503) {
    return { kind: 'no-key', message: detail || NO_KEY_MESSAGE, action: 'settings' }
  }

  if (status === 429) {
    return {
      kind: 'rate-limit',
      message: detail || '请求太频繁，请等一分钟再试。',
      action: 'retry'
    }
  }

  if (status === 400) {
    return {
      kind: 'no-data',
      message: detail || NO_DATA_MESSAGE,
      action: /健康数据|体检记录|记录/.test(detail) ? 'record' : 'retry'
    }
  }

  if (status === 401) {
    return { kind: 'auth', message: '登录已过期，请重新登录。', action: null }
  }

  return {
    kind: 'server',
    message: detail || 'AI 分析失败，请稍后重试。',
    action: 'retry'
  }
}
