import api from './index'

export const runHeartbeat = () => api.post('/patrol/heartbeat')
export const runScreenshot = () => api.post('/patrol/screenshot')
export const getPatrolSettings = () => api.get('/patrol/settings')
export const updatePatrolSettings = (data) => api.put('/patrol/settings', data)
export const testFeishuApi = () => api.post('/patrol/test-feishu')
