import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/student/Dashboard.vue'
import CourseList from '../views/student/CourseList.vue'
import CourseDetail from '../views/student/CourseDetail.vue'
import Forum from '../views/Forum.vue'
import Messages from '../views/Messages.vue'
import Schedule from '../views/student/Schedule.vue'
import SubmitAssignment from '../views/student/SubmitAssignment.vue'

// Teacher Views
import TeacherDashboard from '../views/teacher/TeacherDashboard.vue'
import TeacherClassDetail from '../views/teacher/TeacherClassDetail.vue'
import TeacherGrading from '../views/teacher/TeacherGrading.vue'
import ClassGrades from '../views/teacher/ClassGrades.vue'

const routes = [
  { path: '/login', component: Login },
  
  // Student / General Routes (Legacy Root)
  { path: '/', component: Dashboard, alias: '/dashboard' },
  { path: '/courses', component: CourseList },
  { path: '/course/:id', component: CourseDetail },
  { path: '/course/:id/grades', component: ClassGrades },
  { path: '/forum', component: Forum },
  { path: '/messages', component: Messages },
  { path: '/schedule', component: Schedule },
  { path: '/student/assignment/:assignmentId', component: SubmitAssignment },

  // Teacher Routes
  { 
      path: '/teacher', 
      children: [
          { path: 'dashboard', component: TeacherDashboard },
          { path: 'class/:id', component: TeacherClassDetail },
          { path: 'class/:id/grades', component: ClassGrades },
          { path: 'grading/:assignmentId', component: TeacherGrading }
      ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation Guard
router.beforeEach((to, from, next) => {
  const role = localStorage.getItem('user_role')
  
  // Protect Student Routes from Teachers (Optional, but good for UX)
  if (to.path === '/' && role === 'teacher') {
      next('/teacher/dashboard')
      return
  }
  
  // Protect Teacher Routes from Students
  if (to.path.startsWith('/teacher') && role !== 'teacher') {
      next('/') // Redirect to student dashboard
      return
  }
  
  next()
})

export default router
