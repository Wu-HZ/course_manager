import api from './index'

export const runSchedule = (params = {}) => {
  const data = {
    time_limit_seconds: params.timeLimit || 300,
    max_attempts: params.maxAttempts || 50,
    total_timeout_seconds: params.totalTimeout || 600,
  }
  return api.post('/scheduler/run/', data)
}

export const getScheduleResults = (params = {}) =>
  api.get('/scheduler/results/', { params })
export const getScheduleResult = (id) => api.get(`/scheduler/results/${id}/`)
export const activateResult = (id) => api.post(`/scheduler/results/${id}/activate/`)
export const updateScheduleResult = (id, data) => api.patch(`/scheduler/results/${id}/`, data)
export const renameScheduleResult = (id, name) => updateScheduleResult(id, { name })
export const toggleFavoriteScheduleResult = (id, isFavorite) =>
  updateScheduleResult(id, { is_favorite: isFavorite })
export const deleteScheduleResult = (id) => api.delete(`/scheduler/results/${id}/`)
export const bulkDeleteScheduleResults = (ids) =>
  api.post('/scheduler/results/bulk_delete/', { ids })
export const getActiveSchedule = () => api.get('/scheduler/active/')

export const getClassTimetable = (resultId, classId) =>
  api.get(`/scheduler/results/${resultId}/class/${classId}/`)

export const getTeacherTimetable = (resultId, teacherId) =>
  api.get(`/scheduler/results/${resultId}/teacher/${teacherId}/`)
