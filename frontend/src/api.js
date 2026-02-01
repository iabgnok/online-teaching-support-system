// src/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 5000, // 5秒超时
  withCredentials: false, // 暂时禁用Cookie，只使用Token验证
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加token到Authorization头
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('user_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      // 调试信息：记录token状态
      console.log('📤 发送请求:', config.url)
      console.log('   Token存在:', !!token, '| 长度:', token.length)
      console.log('   Token前20字符:', token.substring(0, 20) + '...')
    } else {
      console.warn('⚠️ 发送请求但没有Token:', config.url)
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理401错误
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // 关键：只有当报错的不是非核心接口时，才清空存储并跳转
      // 非核心接口包括：未读消息查询等不影响主流程的接口
      const isCriticalError = !error.config.url.includes('/chat/conversations')
      
      console.log('401错误 - URL:', error.config.url, '| 是否关键接口:', isCriticalError)
      
      if (isCriticalError) {
        // 只有关键接口401才清空所有用户信息
        console.warn('关键接口401，清空登录信息')
        localStorage.removeItem('user_token')
        localStorage.removeItem('user_role')
        localStorage.removeItem('user_id')
        localStorage.removeItem('user_name')
        localStorage.removeItem('username')
        localStorage.removeItem('real_name')
        
        // 只有当前不在登录页时才重定向
        if (window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      } else {
        console.log('非核心接口401，不执行闪退跳转')
      }
    }
    return Promise.reject(error)
  }
)

export default api
