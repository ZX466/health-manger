/**
 * K-2 的日评分序列是连续的，缺失日的 score 为 null。
 * 仪表盘只对真实有分的日期求均值，并把覆盖天数一起带出来，避免把 0 当成“当天 0 分”。
 */
export function summarizeRatingHistory (points, days) {
  const list = Array.isArray(points) ? points : []
  const scores = list
    .map((point) => point?.score)
    .filter((score) => score !== null && score !== undefined && score !== '')
    .map((score) => Number(score))
    .filter((score) => Number.isFinite(score))

  if (scores.length === 0) {
    return { score: 0, hasScore: false, recorded: 0, days }
  }

  const average = Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
  return { score: average, hasScore: true, recorded: scores.length, days }
}
