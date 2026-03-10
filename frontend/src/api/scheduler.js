import api from './index'

export const runSchedule = (params = {}) => {
  const data = {
    time_limit_seconds: params.timeLimit || 300,
    max_attempts: params.maxAttempts || 50,
    total_timeout_seconds: params.totalTimeout || 600,
  }
  return api.post('/scheduler/run/', data)
}

export const getScheduleResults = () => api.get('/scheduler/results/')
export const getScheduleResult = (id) => api.get(`/scheduler/results/${id}/`)
export const activateResult = (id) => api.post(`/scheduler/results/${id}/activate/`)
export const getActiveSchedule = () => api.get('/scheduler/active/')

export const getClassTimetable = (resultId, classId) =>
  api.get(`/scheduler/results/${resultId}/class/${classId}/`)

export const getTeacherTimetable = (resultId, teacherId) =>
  api.get(`/scheduler/results/${resultId}/teacher/${teacherId}/`)
