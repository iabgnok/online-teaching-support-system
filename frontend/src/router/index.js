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
import GradeConfig from '../views/teacher/GradeConfig.vue'
import GradeInput from '../views/teacher/GradeInput.vue'
import GradeStatistics from '../views/teacher/GradeStatistics.vue'
import TeachingPlan from '../views/teacher/TeachingPlan.vue'

// Student Grade View
import MyGrades from '../views/student/MyGrades.vue'

// Admin Views
import AdminDashboard from '../views/admin/AdminDashboard.vue'
import UserManagement from '../views/admin/UserManagement.vue'
import QueryPage from '../views/admin/QueryPage.vue'
import PermissionManagement from '../views/admin/PermissionManagement.vue'
import ForumManagement from '../views/admin/ForumManagement.vue'

// Common Views
import Profile from '../views/Profile.vue'

const routes = [
  { path: '/login', component: Login },
  { path: '/profile', component: Profile },
  
  // Student / General Routes (Legacy Root)
  { path: '/', component: Dashboard, alias: '/dashboard' },
  { path: '/courses', component: CourseList },
  { path: '/course/:id', component: CourseDetail },
  { path: '/course/:id/grades', component: ClassGrades },
  { path: '/my-grades', component: MyGrades },
  { path: '/forum', component: Forum },
  { path: '/messages', component: Messages },
  { path: '/schedule', component: Schedule },
  { path: '/student/assignment/:assignmentId', component: SubmitAssignment },

  // Teacher Routes
  { 
      path: '/teacher', 
      children: [
          { path: 'dashboard', component: TeacherDashboard },
          { path: 'teaching-plan', component: TeachingPlan },
          { path: 'class/:id', component: TeacherClassDetail },
          { path: 'class/:id/grades', component: ClassGrades },
          { path: 'class/:id/grade-config', component: GradeConfig },
          { path: 'class/:id/grade-item/:itemId', component: GradeInput },
          { path: 'class/:id/grade-statistics', component: GradeStatistics },
          { path: 'grading/:assignmentId', component: TeacherGrading }
      ]
  },

  // Admin Routes
  { 
      path: '/admin', 
      children: [
          { path: 'dashboard', component: AdminDashboard },
          { path: 'users', component: UserManagement },
          { path: 'query', component: QueryPage },
          { path: 'permissions', component: PermissionManagement },
          { path: 'forum-management', component: ForumManagement }
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
  
  // Redirect to appropriate dashboard based on role
  if (to.path === '/') {
      if (role === 'teacher') {
          next('/teacher/dashboard')
          return
      } else if (role === 'admin') {
          next('/admin/dashboard')
          return
      }
  }
  
  // Protect Teacher Routes
  if (to.path.startsWith('/teacher') && role !== 'teacher') {
      next('/')
      return
  }
  
  // Protect Admin Routes
  if (to.path.startsWith('/admin') && role !== 'admin') {
      next('/')
      return
  }
  
  next()
})

export default router
