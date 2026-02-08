import api from './index'

export const getSubjects = () => api.get('/subjects/')
export const getSubject = (id) => api.get(`/subjects/${id}/`)
export const createSubject = (data) => api.post('/subjects/', data)
export const updateSubject = (id, data) => api.put(`/subjects/${id}/`, data)
export const deleteSubject = (id) => api.delete(`/subjects/${id}/`)
