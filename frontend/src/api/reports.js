import api from './index'

export const getStatusHistory = (params) => api.get('/reports/history', { params })
export const getCameraStats = (params) => api.get('/reports/camera-stats', { params })
export const getHourlyStats = (params) => api.get('/reports/hourly', { params })
export const clearStatusRecords = (params) => api.delete('/reports/records', { params })
