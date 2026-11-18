import http from './http'
import { streamChatMessage as openStream } from './stream'

export function createChatSession (data) {
  return http.post('/chat/session', data)
}

export function getChatSessions (params) {
  return http.get('/chat/sessions', { params })
}

export function getChatMessages (sessionId, params) {
  return http.get(`/chat/session/${sessionId}/messages`, { params })
}

export function sendChatMessage (sessionId, data) {
  return http.post(`/chat/session/${sessionId}/message`, data)
}

export function addTongueContext (sessionId) {
  return http.post(`/chat/session/${sessionId}/tongue-context`)
}

export function deleteChatSession (sessionId) {
  return http.delete(`/chat/session/${sessionId}`)
}

/**
 * SSE 流式对话。
 * 支持两种调用方式：
 * 1. streamChatMessage(id, content, onChunk, onDone, onError)
 * 2. streamChatMessage(id, content, { signal, onEvent }) —— 兼容既有 ChatView
 * 后端事件：safety → delta({content})* → done | error
 */
export function streamChatMessage (sessionId, content, onChunk, onDone, onError) {
  if (onChunk && typeof onChunk === 'object') {
    return openStream(sessionId, content, onChunk)
  }

  return openStream(sessionId, content, {
    onEvent: (event, data) => {
      if (event === 'delta') {
        if (typeof onChunk === 'function') onChunk(data?.content ?? data?.delta ?? '', data)
      } else if (event === 'done') {
        if (typeof onDone === 'function') onDone(data)
      } else if (event === 'error') {
        if (typeof onError === 'function') onError(data)
      }
    }
  }).catch(error => {
    if (typeof onError === 'function') {
      onError(error)
      return
    }
    throw error
  })
}

export default {
  createChatSession,
  getChatSessions,
  getChatMessages,
  sendChatMessage,
  streamChatMessage,
  addTongueContext,
  deleteChatSession
}
