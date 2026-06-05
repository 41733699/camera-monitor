import api from './index'

export const getAlerts = (params) => api.get('/alerts/', { params })
export const getAlert = (id) => api.get(`/alerts/${id}`)
export const deleteAlert = (id) => api.delete(`/alerts/${id}`)
export const clearAllAlerts = () => api.delete('/alerts/')
