import api from './index'

export const getCameras = (params) => api.get('/cameras/', { params })
export const getCamera = (id) => api.get(`/cameras/${id}`)
export const createCamera = (data) => api.post('/cameras/', data)
export const updateCamera = (id, data) => api.put(`/cameras/${id}`, data)
export const deleteCamera = (id) => api.delete(`/cameras/${id}`)
export const checkCamera = (id) => api.post(`/cameras/${id}/check`)
export const getStats = () => api.get('/cameras/stats')
export const getCameraStream = (id) => api.get(`/cameras/${id}/stream`)
export const getCameraSnapshot = (id) => api.get(`/cameras/${id}/snapshot`, { responseType: 'blob' })
