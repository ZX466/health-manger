// DASH-1 回归：K-2 的缺失日是 null，不能被当成 0 分拉低均值。
import test from 'node:test'
import assert from 'node:assert/strict'
import { summarizeRatingHistory } from '../src/utils/ratingHistory.js'

test('只对有分的日期求均值', () => {
  const summary = summarizeRatingHistory(
    [
      { date: '2026-11-12', score: 80, level: '良好' },
      { date: '2026-11-13', score: null, level: null },
      { date: '2026-11-14', score: 90, level: '优秀' }
    ],
    7
  )
  assert.equal(summary.score, 85)
  assert.equal(summary.recorded, 2)
  assert.equal(summary.hasScore, true)
})

test('全为缺失日时保持空态', () => {
  const summary = summarizeRatingHistory([{ date: '2026-11-18', score: null, level: null }], 7)
  assert.equal(summary.score, 0)
  assert.equal(summary.hasScore, false)
  assert.equal(summary.recorded, 0)
})

test('容忍空响应与非数组', () => {
  assert.deepEqual(summarizeRatingHistory(null, 30), {
    score: 0,
    hasScore: false,
    recorded: 0,
    days: 30
  })
})

test('0 分是有效评分，不会被过滤', () => {
  const summary = summarizeRatingHistory([{ score: 0 }, { score: 10 }], 7)
  assert.equal(summary.score, 5)
  assert.equal(summary.recorded, 2)
})
