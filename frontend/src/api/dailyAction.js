import http from './http'

/**
 * 今日一件小事：后端每天规则生成一条行动，当天重复打开返回同一条。
 * 返回字段见 docs/plans/daily-action.md，GET 与 POST 结构一致。
 */
export function getTodayAction () {
  return http.get('/daily-action/today')
}

/** 标记完成；重复调用幂等，返回同一结果。 */
export function completeDailyAction (id) {
  return http.post(`/daily-action/${id}/complete`)
}

export default {
  getTodayAction,
  completeDailyAction
}
