<template>
  <div class="class-grades p-4">
     <el-page-header @back="$router.go(-1)" class="mb-4">
        <template #content>
            <span class="text-large font-600 mr-3"> 班级成绩单 </span>
        </template>
     </el-page-header>

     <el-alert
        title="提示：已启用新成绩系统"
        type="info"
        :closable="false"
        class="mb-4"
     >
        <template #default>
          <div>新成绩系统支持灵活配置分类、权重、自动考勤计算和排名功能。</div>
          <el-button type="primary" size="small" @click="goToNewGradeSystem" class="mt-2">
            前往新成绩配置
          </el-button>
        </template>
     </el-alert>

     <el-card shadow="never">
        <template #header>
            <div class="flex justify-between items-center">
                <span>旧成绩总览（仅显示作业成绩）</span>
                <el-button type="primary" size="small" @click="fetchGrades">刷新</el-button>
            </div>
        </template>
        
        <el-table :data="tableData" style="width: 100%" v-loading="loading" border height="600">
            <el-table-column fixed prop="student_no" label="学号" width="120" sortable />
            <el-table-column fixed prop="name" label="姓名" width="100" />
            
            <!-- Dynamic Assignment Columns -->
            <el-table-column 
                v-for="ass in assignments" 
                :key="ass.id" 
                :label="ass.title" 
                width="150"
                align="center"
            >
                <template #header>
                    <div class="truncate" :title="ass.title">{{ ass.title }}</div>
                    <div class="text-xs text-gray-500">满分: {{ ass.total }}</div>
                </template>
                <template #default="scope">
                    <span :class="getScoreClass(scope.row.scores[ass.id], ass.total)">
                        {{ scope.row.scores[ass.id] !== null && scope.row.scores[ass.id] !== undefined ? scope.row.scores[ass.id] : '-' }}
                    </span>
                </template>
            </el-table-column>
            
            <!-- Summary Columns -->
            <el-table-column label="平时分" align="center" width="100">
                 <template #default="scope">{{ scope.row.summary.homework_avg || '-' }}</template>
            </el-table-column>
            <el-table-column label="考试分" align="center" width="100">
                 <template #default="scope">{{ scope.row.summary.exam_avg || '-' }}</template>
            </el-table-column>
            <el-table-column label="总成绩" align="center" width="100" fixed="right">
                 <template #default="scope">
                     <strong class="text-lg" :class="getGradeClass(scope.row.summary.final)">
                         {{ scope.row.summary.final || '-' }}
                     </strong>
                 </template>
            </el-table-column>
        </el-table>
     </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../../api'

const route = useRoute()
const router = useRouter()
const classId = route.params.id
const loading = ref(false)
const tableData = ref([])
const assignments = ref([])

const fetchGrades = async () => {
    loading.value = true
    try {
        const res = await api.get(`/classes/${classId}/grades`)
        assignments.value = res.data.assignments
        tableData.value = res.data.students
    } catch (err) {
        console.error(err)
        // ElMessage.error('无法获取成绩数据')
    } finally {
        loading.value = false
    }
}

const goToNewGradeSystem = () => {
    router.push(`/teacher/class/${classId}/grade-config`)
}

onMounted(() => {
    fetchGrades()
})

const getScoreClass = (score, total) => {
    if (score === null || score === undefined) return 'text-gray-400'
    const ratio = score / total
    if (ratio < 0.6) return 'text-red-500 font-bold'
    if (ratio >= 0.9) return 'text-green-600 font-bold'
    return ''
}

const getGradeClass = (score) => {
    if (!score) return ''
    if (score < 60) return 'text-red-600'
    if (score >= 90) return 'text-green-600'
    return ''
}
</script>

<style scoped>
.truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>