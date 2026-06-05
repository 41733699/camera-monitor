/**
 * 摄像头相关工具函数
 */

/**
 * 状态文本映射
 */
export const STATUS_MAP = {
  online: { text: '在线', type: 'success' },
  offline: { text: '离线', type: 'danger' },
  unknown: { text: '未知', type: 'info' },
}

/**
 * 获取状态对应的 Element Plus Tag 类型
 */
export function getStatusType(status) {
  return STATUS_MAP[status]?.type || 'info'
}

/**
 * 获取状态文本
 */
export function getStatusText(status) {
  return STATUS_MAP[status]?.text || status
}
