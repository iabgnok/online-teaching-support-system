// src/api.js
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 5000, // 5秒超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add a response interceptor to handle errors
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // Not authenticated, redirect to login
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
