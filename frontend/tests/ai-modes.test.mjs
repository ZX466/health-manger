// P1 异步分析：result 契约与状态文案回归。
import test from 'node:test'
import assert from 'node:assert/strict'
import { asyncStatusLabel, normalizeTaskResult } from '../src/utils/aiModes.js'

test('新版 dict result 保留内容、token 与 analysis_id', () => {
  assert.deepEqual(
    normalizeTaskResult({
      content: '异步建议',
      tokens_used: 12,
      analysis_id: 88
    }),
    { content: '异步建议', tokensUsed: 12, analysisId: 88 }
  )
})

test('兼容旧版 tuple/数组 result', () => {
  assert.deepEqual(normalizeTaskResult(['旧结果', 7]), {
    content: '旧结果',
    tokensUsed: 7,
    analysisId: null
  })
})

test('空 result 不产生误导内容', () => {
  assert.deepEqual(normalizeTaskResult(null), {
    content: '',
    tokensUsed: 0,
    analysisId: null
  })
  assert.deepEqual(normalizeTaskResult('unexpected'), {
    content: '',
    tokensUsed: 0,
    analysisId: null
  })
})

test('状态文案覆盖完整生命周期', () => {
  assert.equal(asyncStatusLabel('pending'), '排队中…')
  assert.equal(asyncStatusLabel('running'), '分析中…')
  assert.equal(asyncStatusLabel('completed'), '已完成')
  assert.equal(asyncStatusLabel('failed'), '失败')
  assert.equal(asyncStatusLabel('unknown'), '处理中…')
})
