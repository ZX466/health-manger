// A-1 回归：AI 分析失败必须落到可操作的 UI 分支，而不是只弹一句“失败”。
import test from 'node:test'
import assert from 'node:assert/strict'
import { aiErrorInfo } from '../src/utils/aiError.js'

test('超时：给出重试入口', () => {
  const info = aiErrorInfo({ code: 'ECONNABORTED', message: 'timeout of 60000ms exceeded' })
  assert.equal(info.kind, 'timeout')
  assert.equal(info.action, 'retry')
  assert.match(info.message, /超时/)
})

test('无响应：网络错误提示重试', () => {
  const info = aiErrorInfo({ message: 'Network Error' })
  assert.equal(info.kind, 'network')
  assert.equal(info.action, 'retry')
})

test('503：缺 Key 指向 AI 设置', () => {
  const info = aiErrorInfo({
    response: { status: 503, data: { detail: '未配置 AI API 密钥，请在「AI 设置」中完善后重试' } }
  })
  assert.equal(info.kind, 'no-key')
  assert.equal(info.action, 'settings')
  assert.match(info.message, /AI 设置/)
})

test('400：无健康数据指向添加记录', () => {
  const info = aiErrorInfo({
    response: { status: 400, data: { detail: '暂无健康数据，请先添加健康记录' } }
  })
  assert.equal(info.kind, 'no-data')
  assert.equal(info.action, 'record')
})

test('400：非数据类校验错误不误导向添加记录', () => {
  const info = aiErrorInfo({
    response: { status: 400, data: { detail: '请求内容不能为空' } }
  })
  assert.equal(info.kind, 'no-data')
  assert.equal(info.action, 'retry')
})

test('429：限流提示重试', () => {
  const info = aiErrorInfo({ response: { status: 429, data: {} } })
  assert.equal(info.kind, 'rate-limit')
  assert.equal(info.action, 'retry')
})

test('500：保留后端 detail 并允许重试', () => {
  const info = aiErrorInfo({
    response: { status: 500, data: { detail: 'AI 分析失败，请稍后重试' } }
  })
  assert.equal(info.kind, 'server')
  assert.equal(info.action, 'retry')
  assert.match(info.message, /稍后重试/)
})

test('FastAPI 422 数组 detail 会拼接为可读文本', () => {
  const info = aiErrorInfo({
    response: {
      status: 422,
      data: {
        detail: [
          { msg: '字段不能为空', loc: ['body', 'request_content'] },
          { msg: '长度超出限制', loc: ['body', 'request_content'] }
        ]
      }
    }
  })
  assert.match(info.message, /字段不能为空；长度超出限制/)
})
