/**
 * 量表结果的安抚/求助文案。
 *
 * crisis_flag 可能来自两个通道：PHQ-9 第 9 题阳性，或总分达到高风险阈值。
 * 只有前者可以在文案里陈述“回答中提到”，否则会把总分触发误说成自述念头。
 */
const SELF_HARM_ADVICE =
  '你的回答里提到了伤害自己的念头。请先不要独处，联系身边信任的人、学校心理咨询中心，或拨打 120 / 110。你不需要一个人扛。'

const SCORE_CRISIS_ADVICE =
  '这次测评的总分已达到需要立即关注的区间。请先不要独处，联系身边信任的人、学校心理咨询中心，或拨打 120 / 110。你不需要一个人扛。'

export function scaleRiskAdvice (result, answers) {
  if (!result) return ''

  if (result.crisis_flag) {
    const fromQ9 = result.scale_type === 'phq9' && Number(answers?.[8]) > 0
    return fromQ9 ? SELF_HARM_ADVICE : SCORE_CRISIS_ADVICE
  }

  switch (result.risk_level) {
    case 'minimal':
      return '目前没有明显症状。继续保持规律作息；如果之后状态变化，可以再测一次。'
    case 'mild':
      return '有一些轻度困扰。先从睡眠、运动和和人聊聊开始；如果持续两周以上，建议预约咨询。'
    case 'moderate':
      return '困扰已经比较明显。建议尽快预约学校心理咨询中心，和专业人员聊一聊。'
    case 'moderately_severe':
    case 'severe':
      return '建议尽快联系学校心理咨询中心或医疗机构。如果出现伤害自己的念头，请立刻寻求紧急帮助。'
    default:
      return '结果仅供参考，不构成诊断。'
  }
}
