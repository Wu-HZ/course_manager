const STATUS_TEXT_MAP = {
  OPTIMAL: '最优解',
  FEASIBLE: '可行解',
  INFEASIBLE: '无可行解',
  MODEL_INVALID: '模型无效',
  UNKNOWN: '未知',
  FAILED_ALL_ATTEMPTS: '全部尝试失败'
}

const STATUS_TAG_TYPE_MAP = {
  OPTIMAL: 'success',
  FEASIBLE: 'warning',
  INFEASIBLE: 'danger',
  MODEL_INVALID: 'danger',
  UNKNOWN: 'info',
  FAILED_ALL_ATTEMPTS: 'danger'
}

export const getScheduleResultDisplayName = (result) => (
  result?.display_name || `课表 #${result?.id ?? ''}`
)

export const getScheduleResultStatusText = (status) => (
  STATUS_TEXT_MAP[status] || status || '未知'
)

export const getScheduleResultStatusType = (status) => (
  STATUS_TAG_TYPE_MAP[status] || 'info'
)

export const formatScheduleResultLabel = (result) => {
  if (!result) return ''
  return [
    getScheduleResultDisplayName(result),
    result.created_at,
    getScheduleResultStatusText(result.solve_status)
  ].filter(Boolean).join(' · ')
}

export const buildScheduleResultFileLabel = (result, fallback = '课表') => {
  const name = getScheduleResultDisplayName(result)
  const safeName = String(name || fallback).trim().replace(/[\\/:*?"<>|]/g, '-')
  return safeName || fallback
}
