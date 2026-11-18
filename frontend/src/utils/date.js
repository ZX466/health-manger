/** 本地日期键，避免 toISOString() 的 UTC 偏移把“今天”算错。 */
export function localDateKey (date = new Date()) {
  const d = date instanceof Date ? date : new Date(date)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** 后端时间戳通常不带时区；补齐 Z 再按本地时区展示。 */
export function parseServerDate (value) {
  if (!value) return null
  if (typeof value === 'number' || value instanceof Date) {
    const d = new Date(value)
    return Number.isNaN(d.getTime()) ? null : d
  }
  let text = String(value)
  // 后端 DateTime 统一是 UTC；SQLite 丢掉 tzinfo 后序列化成 naive 字符串，
  // 因此带时间的字符串要补 Z。纯日期（如 mental record_date）保持本地日期语义。
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
    text += 'T00:00:00'
  } else if (/^\d{4}-\d{2}-\d{2}[ T]\d/.test(text)) {
    text = text.replace(' ', 'T')
    if (!/[zZ]|[+-]\d{2}:?\d{2}$/.test(text)) text += 'Z'
  }
  const d = new Date(text)
  return Number.isNaN(d.getTime()) ? null : d
}

export function formatScaleDate (value) {
  const d = parseServerDate(value)
  if (!d) return String(value || '')
  return d.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function formatShortDate (value) {
  const d = parseServerDate(value)
  if (!d) return String(value || '')
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}
