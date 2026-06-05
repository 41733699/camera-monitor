import api from './index'

export const exportConfig = () => api.get('/backup/export')
export const importConfig = (formData) => api.post('/backup/import', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
