import api from './index'

export const getLocations = () => api.get('/locations/')
export const getLocation = (id) => api.get(`/locations/${id}/`)
export const createLocation = (data) => api.post('/locations/', data)
export const updateLocation = (id, data) => api.put(`/locations/${id}/`, data)
export const deleteLocation = (id) => api.delete(`/locations/${id}/`)

export const getTravelGroups = () => api.get('/travel-groups/')
export const getTravelGroup = (id) => api.get(`/travel-groups/${id}/`)
export const createTravelGroup = (data) => api.post('/travel-groups/', data)
export const updateTravelGroup = (id, data) => api.put(`/travel-groups/${id}/`, data)
export const deleteTravelGroup = (id) => api.delete(`/travel-groups/${id}/`)

export const getAssignments = () => api.get('/class-subject-teachers/')
export const createAssignment = (data) => api.post('/class-subject-teachers/', data)
export const updateAssignment = (id, data) => api.put(`/class-subject-teachers/${id}/`, data)
export const deleteAssignment = (id) => api.delete(`/class-subject-teachers/${id}/`)

export const getCombinedGroups = () => api.get('/combined-class-groups/')
export const getCombinedGroup = (id) => api.get(`/combined-class-groups/${id}/`)
export const createCombinedGroup = (data) => api.post('/combined-class-groups/', data)
export const updateCombinedGroup = (id, data) => api.put(`/combined-class-groups/${id}/`, data)
export const deleteCombinedGroup = (id) => api.delete(`/combined-class-groups/${id}/`)
