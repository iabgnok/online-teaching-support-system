import { createRouter, createWebHistory } from 'vue-router'

import Login from '../views/Login.vue'

import Dashboard from '../views/student/Dashboard.vue'

import CourseList from '../views/student/CourseList.vue'

import CourseDetail from '../views/student/CourseDetail.vue'

import Forum from '../views/Forum.vue'

import Messages from '../views/Messages.vue'

import Chat from '../views/Chat.vue'

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

import TeacherLiveClass from '../views/teacher/LiveClass.vue'



// Student Grade View

import MyGrades from '../views/student/MyGrades.vue'

import StudentLiveClass from '../views/student/LiveClass.vue'

import ActiveLiveClass from '../views/ActiveLiveClass.vue'



// Admin Views

import AdminDashboard from '../views/admin/AdminDashboard.vue'

import UserManagement from '../views/admin/UserManagement.vue'

import QueryPage from '../views/admin/QueryPage.vue'

import PermissionManagement from '../views/admin/PermissionManagement.vue'

import ForumManagement from '../views/admin/ForumManagement.vue'



// Common Views

import Profile from '../views/Profile.vue'
// 新版统一线上课堂组件
import LiveClassRoom from '../views/LiveClassRoom.vue'



const routes = [

  { path: '/login', component: Login },

  { path: '/profile', component: Profile },

 

  // Student / General Routes (Legacy Root)

  { path: '/', component: Dashboard, alias: '/dashboard' },

  { path: '/courses', component: CourseList },

  { path: '/course/:id', component: CourseDetail },

  { path: '/course/:id/grades', component: ClassGrades },

  { path: '/my-grades', component: MyGrades },

  { path: '/live-class/active', component: ActiveLiveClass },
  // 新版统一线上课堂路由
  { path: '/classroom/:lessonId', component: LiveClassRoom, props: true },

  { path: '/live-class/:lessonId', component: LiveClassRoom, props: true },

  { path: '/forum', component: Forum },

  { path: '/messages', component: Messages },

  { path: '/chat', component: Chat },

  { path: '/schedule', component: Schedule },

  { path: '/student/assignment/:assignmentId', component: SubmitAssignment },



  // Teacher Routes

  {

      path: '/teacher',

      children: [

          { path: 'dashboard', component: TeacherDashboard },

          { path: 'teaching-plan', component: TeachingPlan },

          { path: 'live-class/:lessonId', component: LiveClassRoom, props: true },

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

  const token = localStorage.getItem('user_token')

 

  // 鏈櫥褰曡烦杞埌鐧诲綍椤碉紙鎺掗櫎鐧诲綍椤垫湰韬級

  if (!token && to.path !== '/login') {

      next('/login')

      return

  }



  // 宸茬粡鐧诲綍杩樿闂櫥褰曢〉锛岃烦杞埌瀵瑰簲棣栭〉

  if (token && to.path === '/login') {

      if (role === 'teacher') {

          next('/teacher/dashboard')

      } else if (role === 'admin') {

          next('/admin/dashboard')

      } else {

          next('/')

      }

      return

  }



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
