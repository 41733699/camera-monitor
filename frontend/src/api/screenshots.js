import api from './index'

export const getScreenshots = (cameraId) => api.get(`/screenshots/${cameraId}`)
export const deleteScreenshot = (cameraId, filename) => api.delete(`/screenshots/${cameraId}/${filename}`)
export const deleteAllScreenshots = (cameraId) => api.delete(`/screenshots/${cameraId}`)
