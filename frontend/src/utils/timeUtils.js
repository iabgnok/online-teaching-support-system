/**
 * 时间工具函数
 * 用于统一处理时间显示，修正时区问题
 */

/**
 * 解析后端返回的时间戳
 * 后端保存的是北京时间但标记为UTC(+00:00)，需要修正
 * @param {string|Date} timestamp - ISO格式的时间戳
 * @returns {Date} - 修正后的Date对象
 */
export function parseBackendTime(timestamp) {
  if (!timestamp) return null
  
  try {
    let dateStr = timestamp
    
    // 如果是ISO格式字符串，移除时区标记并当作本地时间解析
    if (typeof timestamp === 'string' && timestamp.includes('+00:00')) {
      // 后端返回的时间实际上是北京时间，但被错误标记为UTC
      // 我们需要去掉时区标记，按本地时间解析
      dateStr = timestamp.replace('+00:00', '').replace('T', ' ')
    } else if (typeof timestamp === 'string' && timestamp.includes('Z')) {
      // 也去掉Z标记
      dateStr = timestamp.replace('Z', '').replace('T', ' ')
    } else if (typeof timestamp === 'string' && timestamp.includes('T')) {
      // 标准ISO格式但没有时区标记
      dateStr = timestamp.replace('T', ' ')
    }
    
    // 创建Date对象
    const date = new Date(dateStr)
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.error('Invalid timestamp:', timestamp)
      return null
    }
    
    return date
  } catch (error) {
    console.error('Error parsing timestamp:', timestamp, error)
    return null
  }
}

/**
 * 格式化时间为 HH:MM 格式
 * @param {string|Date} timestamp - 时间戳
 * @returns {string} - 格式化后的时间字符串
 */
export function formatTime(timestamp) {
  if (!timestamp) return ''
  
  const date = parseBackendTime(timestamp)
  if (!date) return '--:--'
  
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  
  return `${hours}:${minutes}`
}

/**
 * 格式化完整时间
 * @param {string|Date} timestamp - 时间戳
 * @returns {string} - 格式化后的完整时间字符串
 */
export function formatFullTime(timestamp) {
  if (!timestamp) return ''
  
  const date = parseBackendTime(timestamp)
  if (!date) return ''
  
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

/**
 * 格式化日期分隔线（今天、昨天或具体日期）
 * @param {string|Date} timestamp - 时间戳
 * @returns {string} - 格式化后的日期字符串
 */
export function formatDateDivider(timestamp) {
  if (!timestamp) return ''
  
  const date = parseBackendTime(timestamp)
  if (!date) return ''
  
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  
  // 比较日期（只比较年月日）
  const dateStr = date.toDateString()
  const todayStr = today.toDateString()
  const yesterdayStr = yesterday.toDateString()
  
  if (dateStr === todayStr) {
    return '今天'
  } else if (dateStr === yesterdayStr) {
    return '昨天'
  } else {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}年${month}月${day}日`
  }
}

/**
 * 格式化相对时间（几分钟前、几小时前等）
 * @param {string|Date} timestamp - 时间戳
 * @returns {string} - 格式化后的相对时间字符串
 */
export function formatRelativeTime(timestamp) {
  if (!timestamp) return ''
  
  const date = parseBackendTime(timestamp)
  if (!date) return ''
  
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  // 如果时间差为负数（未来时间），显示为"刚刚"
  if (diffMs < 0) {
    console.warn('Future timestamp detected:', timestamp, 'Current time:', now.toISOString())
    return '刚刚'
  }
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  
  // 超过一周显示日期
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  
  if (year === now.getFullYear()) {
    return `${month}/${day}`
  }
  
  return `${year}/${month}/${day}`
}

/**
 * 检查两条消息之间是否需要显示日期分隔线
 * @param {Object} currentMessage - 当前消息
 * @param {Object} prevMessage - 上一条消息
 * @returns {boolean} - 是否需要显示分隔线
 */
export function shouldShowDateDivider(currentMessage, prevMessage) {
  if (!prevMessage) return true
  
  const currentDate = parseBackendTime(currentMessage.created_at)
  const prevDate = parseBackendTime(prevMessage.created_at)
  
  if (!currentDate || !prevDate) return false
  
  // 如果日期不同，显示分隔线
  return currentDate.toDateString() !== prevDate.toDateString()
}
