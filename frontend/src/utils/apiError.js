/**
 * 把后端错误统一成可读文本。
 *
 * FastAPI 的 422 会把 detail 返回成数组（每项含 loc / msg），直接拼进字符串
 * 会得到「[object Object]」。这里把数组拍平成「字段：原因」，其余情况回退
 * 到字符串 detail 或给定兜底文案。
 */
export function readApiError (error, fallback = '操作失败，请稍后重试。') {
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string' && detail.trim()) return detail.trim()

  if (Array.isArray(detail)) {
    const text = detail
      .map((item) => {
        if (typeof item === 'string') return item
        const field = Array.isArray(item?.loc)
          ? item.loc.filter((part) => part !== 'body').join('.')
          : ''
        const message = item?.msg || ''
        if (!message) return ''
        return field ? `${field}：${message}` : message
      })
      .filter(Boolean)
      .join('；')
    if (text) return text
  }

  if (detail && typeof detail === 'object' && typeof detail.message === 'string') {
    return detail.message
  }

  return fallback
}
