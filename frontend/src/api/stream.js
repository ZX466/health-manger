/**
 * POST + SSE 流式读取。
 *
 * 后端事件契约（routers/chat.py）：safety? → delta* → done | error。
 * 未知事件不抛错，交给调用方忽略，方便后端后续扩展。
 */
export async function streamChatMessage (sessionId, content, { signal, onEvent } = {}) {
  const token = localStorage.getItem('token')
  const response = await fetch(`/api/chat/session/${sessionId}/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({ content }),
    signal
  })

  if (!response.ok) {
    let detail = `请求失败（${response.status}）`
    try {
      const body = await response.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch (e) { /* ignore */ }

    if (response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userName')
      if (!window.location.pathname.includes('/login')) window.location.href = '/login'
    }

    const error = new Error(detail)
    error.status = response.status
    error.detail = detail
    throw error
  }

  if (!response.body) {
    throw new Error('浏览器不支持流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let eventName = 'message'
  let dataLines = []
  let sawTerminal = false

  const isValidTerminal = (name, data) => {
    if (!data || typeof data !== 'object' || Array.isArray(data)) return false
    if (name === 'done') {
      // 契约：done = {message_id:int, tokens_used:int}
      return Number.isInteger(data.message_id) && Number.isFinite(data.tokens_used)
    }
    // 契约：error = {detail:string}
    return typeof data.detail === 'string' && data.detail.length > 0
  }

  const dispatch = () => {
    if (!dataLines.length) {
      eventName = 'message'
      return
    }
    const raw = dataLines.join('\n')
    dataLines = []
    const name = eventName || 'message'
    eventName = 'message'
    let data = raw
    let parsed = false
    try {
      data = JSON.parse(raw)
      parsed = true
    } catch (e) {
      // 非 JSON 的 data 也交给调用方；后端当前全部是 JSON。
    }
    if (name === 'done' || name === 'error') {
      // 终态帧必须完整解析且符合契约；截断/缺字段的帧不回调，按未收到终态处理。
      if (!parsed || !isValidTerminal(name, data)) return
      sawTerminal = true
    }
    if (typeof onEvent === 'function') onEvent(name, data)
  }

  const processLines = (text) => {
    buffer += text
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const rawLine of lines) {
      const line = rawLine.replace(/\r$/, '')
      if (line === '') {
        // 仅在空行（帧结束）时派发；EOF 时未以空行结束的残余帧按规范丢弃。
        dispatch()
        continue
      }
      if (line.startsWith(':')) continue
      if (line.startsWith('event:')) {
        eventName = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).replace(/^ /, ''))
      }
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    processLines(decoder.decode(value, { stream: true }))
  }
  // 冲掉解码器尾部；未构成完整帧的 buffer 不派发（SSE 规范要求空行结束）。
  processLines(decoder.decode())

  if (!sawTerminal) {
    const error = new Error('连接中断，未收到完整回复')
    error.name = 'StreamIncompleteError'
    error.code = 'STREAM_INCOMPLETE'
    throw error
  }
}
