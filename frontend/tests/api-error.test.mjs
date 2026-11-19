// 422 校验错误必须渲染成可读文本，而不是「[object Object]」。
import test from 'node:test'
import assert from 'node:assert/strict'
import { readApiError } from '../src/utils/apiError.js'

test('422 detail 数组：拍平成「字段：原因」', () => {
  const message = readApiError({
    response: {
      status: 422,
      data: {
        detail: [
          { loc: ['body', 'model'], msg: 'Field required', type: 'missing' },
          { loc: ['body', 'vision_model'], msg: 'String should have at least 1 character' }
        ]
      }
    }
  })
  assert.equal(message, 'model：Field required；vision_model：String should have at least 1 character')
  assert.doesNotMatch(message, /\[object Object\]/)
})

test('字符串 detail 原样返回', () => {
  const message = readApiError({
    response: { status: 400, data: { detail: '自定义 Base URL 必须配置独立 API 密钥' } }
  })
  assert.equal(message, '自定义 Base URL 必须配置独立 API 密钥')
})

test('对象 detail 优先取 message', () => {
  const message = readApiError({
    response: { status: 500, data: { detail: { message: '上游返回异常' } } }
  })
  assert.equal(message, '上游返回异常')
})

test('无 detail 时回退到兜底文案', () => {
  assert.equal(readApiError({ message: 'Network Error' }, '连接失败'), '连接失败')
  assert.equal(readApiError(null, '连接失败'), '连接失败')
})
