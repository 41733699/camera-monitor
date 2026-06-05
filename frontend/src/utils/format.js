/**
 * 格式化工具函数
 */

/**
 * 格式化 ISO 时间字符串为本地可读格式
 */
export function formatTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  if (isNaN(d.getTime())) return isoStr
  return d.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
}

/**
 * 格式化 Unix 时间戳（秒）为本地可读格式
 */
export function formatTimestamp(ts) {
  if (!ts) return '-'
  return formatTime(new Date(ts * 1000).toISOString())
}
