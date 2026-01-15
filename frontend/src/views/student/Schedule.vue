<template>
  <div class="schedule-container">
    <h2>我的日程 (My Schedule)</h2>
    <el-card>
      <el-calendar v-model="currentDate">
        <template #date-cell="{ data }">
          <div class="date-cell-content" @click.stop>
            <p :class="{ 'is-today': data.isSelected }">
              {{ data.day.split('-').slice(2).join('') }}
              <span v-if="data.isSelected">📅</span>
            </p>
            <div class="events-list">
              <div 
                v-for="event in getEventsForDate(data.day)" 
                :key="event.id"
                class="event-item"
                :style="{ backgroundColor: event.color }"
                @click.stop="openEvent(event)"
                :title="event.title"
              >
                {{ event.title }}
              </div>
            </div>
          </div>
        </template>
      </el-calendar>
    </el-card>

    <el-dialog v-model="dialogVisible" title="事件详情" width="30%">
      <div v-if="selectedEvent">
        <h3 style="margin-top:0">{{ selectedEvent.title }}</h3>
        <p><strong>时间:</strong> {{ formatTime(selectedEvent.start) }}</p>
        <p v-if="selectedEvent.extendedProps?.description"><strong>描述:</strong> {{ selectedEvent.extendedProps.description }}</p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
          <!-- 假设后端返回的URL是前端路由兼容的，或者是一个有效的链接 -->
          <el-button type="primary" tag="a" :href="selectedEvent?.url" target="_blank" v-if="selectedEvent?.url">
            查看详情
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const currentDate = ref(new Date())
const events = ref([])
const dialogVisible = ref(false)
const selectedEvent = ref(null)

const fetchEvents = async () => {
  try {
    // 获取当前月份的事件
    // 这里暂时请求所有事件，也可以传递 currentMonth 参数优化
    const res = await api.get('/schedule/events')
    events.value = res.data
  } catch (err) {
    console.error('Failed to fetch events', err)
  }
}

const getEventsForDate = (dayStr) => {
  // dayStr is 'YYYY-MM-DD'
  return events.value.filter(e => {
    // 简单匹配日期部分
    return e.start.startsWith(dayStr)
  })
}

const openEvent = (event) => {
  selectedEvent.value = event
  dialogVisible.value = true
}

const formatTime = (isoStr) => {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleString()
}

onMounted(() => {
  fetchEvents()
})
</script>

<style scoped>
.schedule-container {
  padding: 20px;
}
.date-cell-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.date-cell-content p {
  margin: 0;
  font-size: 14px;
}
.events-list {
  margin-top: 5px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}
.event-item {
  font-size: 12px;
  color: white;
  padding: 2px 4px;
  margin-bottom: 2px;
  border-radius: 4px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}
.event-item:hover {
  opacity: 0.8;
}
</style>
