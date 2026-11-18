// R2 回归：crisis 文案不能在“仅总分触发”时错误归因为自述念头。
import test from 'node:test'
import assert from 'node:assert/strict'
import { scaleRiskAdvice } from '../src/utils/scaleAdvice.js'

test('PHQ-9 仅总分触发：使用总分措辞', () => {
  const result = {
    scale_type: 'phq9',
    score: 20,
    max_score: 27,
    risk_level: 'severe',
    crisis_flag: true
  }
  const advice = scaleRiskAdvice(result, [3, 3, 3, 3, 3, 3, 2, 3, 0])
  assert.match(advice, /总分已达到需要立即关注/)
  assert.doesNotMatch(advice, /回答里提到了/)
})

test('PHQ-9 第 9 题阳性：保留自述措辞', () => {
  const result = {
    scale_type: 'phq9',
    score: 4,
    max_score: 27,
    risk_level: 'mild',
    crisis_flag: true
  }
  const advice = scaleRiskAdvice(result, [0, 0, 0, 0, 0, 0, 0, 0, 1])
  assert.match(advice, /回答里提到了/)
})

test('GAD-7 仅总分触发：使用总分措辞', () => {
  const result = {
    scale_type: 'gad7',
    score: 16,
    max_score: 21,
    risk_level: 'severe',
    crisis_flag: true
  }
  const advice = scaleRiskAdvice(result, [3, 3, 3, 3, 2, 2, 0])
  assert.match(advice, /总分已达到需要立即关注/)
  assert.doesNotMatch(advice, /回答里提到了/)
})

test('非危机分级文案保持原口径', () => {
  assert.match(
    scaleRiskAdvice({ scale_type: 'gad7', risk_level: 'moderate', crisis_flag: false }, []),
    /尽快预约学校心理咨询中心/
  )
})
