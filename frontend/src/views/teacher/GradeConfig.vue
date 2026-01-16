<template>
  <div class="grade-config-container">
    <el-page-header @back="goBack" content="成绩配置" class="mb-4" />
    
    <!-- 使用说明 -->
    <el-alert
      title="💡 配置说明"
      type="info"
      :closable="false"
      class="mb-4"
    >
      <template #default>
        <div class="help-text">
          <p><strong>第一步：</strong>创建成绩分类（如：平时成绩30%、期中考试30%、期末考试40%），确保总权重为100%</p>
          <p><strong>第二步：</strong>在每个分类下添加具体的成绩项（如：考勤、作业、测验等）</p>
          <p><strong>第三步：</strong>配置每个成绩项的权重和满分</p>
          <p><strong>提示：</strong>录入成绩请在"班级管理 → 成绩管理"标签页中进行</p>
        </div>
      </template>
    </el-alert>
    
    <el-card class="mb-4">
      <template #header>
        <div class="flex justify-between items-center">
          <span>成绩结构配置</span>
          <el-button type="primary" @click="showAddCategoryDialog">+ 添加分类</el-button>
        </div>
      </template>
      
      <div v-if="loading" class="text-center p-4">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else>
        <el-alert
          v-if="totalWeight !== 100"
          type="warning"
          :closable="false"
          class="mb-4"
        >
          当前权重总和为 {{ totalWeight }}%，请确保总和为 100%
        </el-alert>
        
        <div v-for="category in categories" :key="category.id" class="category-block mb-4">
          <div class="category-header">
            <div class="flex items-center">
              <h3 class="m-0">{{ category.name }}</h3>
              <el-tag class="ml-2">{{ category.weight }}%</el-tag>
            </div>
            <div>
              <el-button size="small" @click="editCategory(category)">编辑</el-button>
              <el-button size="small" @click="addItem(category)">+ 添加成绩项</el-button>
              <el-button size="small" type="danger" @click="deleteCategory(category)">删除</el-button>
            </div>
          </div>
          
          <el-table :data="category.items" class="mt-2">
            <el-table-column prop="name" label="成绩项名称" />
            <el-table-column prop="type" label="类型" width="100">
              <template #default="scope">
                <el-tag :type="getItemTypeTag(scope.row.type)" size="small">
                  {{ getItemTypeName(scope.row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="weight" label="权重" width="80">
              <template #default="scope">{{ scope.row.weight }}%</template>
            </el-table-column>
            <el-table-column prop="max_score" label="满分" width="80" />
            <el-table-column label="自动计算" width="100" align="center">
              <template #default="scope">
                <el-icon v-if="scope.row.auto_calculate" color="#67C23A"><Check /></el-icon>
              </template>
            </el-table-column>
            <el-table-column label="已公开" width="80" align="center">
              <template #default="scope">
                <el-switch 
                  v-model="scope.row.is_published" 
                  @change="togglePublish(scope.row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button size="small" @click="editItem(scope.row)">编辑</el-button>
                <el-button size="small" type="danger" @click="deleteItem(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <div v-if="categories.length === 0" class="text-center text-secondary p-4">
          暂无成绩分类，请点击"添加分类"开始配置
        </div>
      </div>
    </el-card>
    
    <el-card>
      <div class="flex justify-between">
        <el-button @click="viewStatistics">查看统计</el-button>
        <div>
          <el-button type="success" @click="calculateFinalGrades" :loading="calculating">
            计算总评成绩
          </el-button>
          <el-button type="primary" @click="publishGrades">公开成绩</el-button>
        </div>
      </div>
    </el-card>
    
    <!-- 添加/编辑分类对话框 -->
    <el-dialog v-model="categoryDialogVisible" :title="editingCategory ? '编辑分类' : '添加分类'" width="500px">
      <el-form :model="categoryForm" label-width="80px">
        <el-form-item label="分类名称">
          <el-input v-model="categoryForm.name" placeholder="如：平时成绩" />
        </el-form-item>
        <el-form-item label="权重(%)">
          <el-input-number v-model="categoryForm.weight" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="categoryForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCategory">保存</el-button>
      </template>
    </el-dialog>
    
    <!-- 添加/编辑成绩项对话框 -->
    <el-dialog v-model="itemDialogVisible" :title="editingItem ? '编辑成绩项' : '添加成绩项'" width="500px">
      <el-form :model="itemForm" label-width="100px">
        <el-form-item label="成绩项名称">
          <el-input v-model="itemForm.name" placeholder="如：期中考试" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="itemForm.type" style="width: 100%">
            <el-option label="手动录入" value="manual" />
            <el-option label="关联作业" value="assignment" />
            <el-option label="关联考试" value="exam" />
            <el-option label="考勤自动" value="attendance" />
          </el-select>
        </el-form-item>
        <el-form-item label="权重(%)">
          <el-input-number v-model="itemForm.weight" :min="0" :max="100" />
        </el-form-item>
        <el-form-item label="满分">
          <el-input-number v-model="itemForm.max_score" :min="1" />
        </el-form-item>
        <el-form-item label="自动计算">
          <el-switch v-model="itemForm.auto_calculate" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="itemDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveItem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import api from '../../api'

const router = useRouter()
const route = useRoute()
const classId = ref(route.params.id)

const loading = ref(true)
const calculating = ref(false)
const categories = ref([])

const categoryDialogVisible = ref(false)
const itemDialogVisible = ref(false)
const editingCategory = ref(null)
const editingItem = ref(null)
const currentCategory = ref(null)

const categoryForm = ref({ name: '', weight: 0, description: '' })
const itemForm = ref({ 
  name: '', 
  type: 'manual', 
  weight: 0, 
  max_score: 100,
  auto_calculate: false 
})

const totalWeight = computed(() => {
  return categories.value.reduce((sum, cat) => sum + (cat.weight || 0), 0)
})

const fetchCategories = async () => {
  loading.value = true
  try {
    const res = await api.get(`/grades/class/${classId.value}/categories`)
    categories.value = res.data
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const showAddCategoryDialog = () => {
  editingCategory.value = null
  categoryForm.value = { name: '', weight: 0, description: '' }
  categoryDialogVisible.value = true
}

const editCategory = (category) => {
  editingCategory.value = category
  categoryForm.value = { ...category }
  categoryDialogVisible.value = true
}

const saveCategory = async () => {
  try {
    if (editingCategory.value) {
      await api.put(`/grades/categories/${editingCategory.value.id}`, categoryForm.value)
      ElMessage.success('更新成功')
    } else {
      await api.post(`/grades/class/${classId.value}/categories`, categoryForm.value)
      ElMessage.success('创建成功')
    }
    categoryDialogVisible.value = false
    fetchCategories()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '操作失败')
  }
}

const deleteCategory = async (category) => {
  try {
    await ElMessageBox.confirm('删除分类将同时删除其下所有成绩项，确定继续？', '警告', {
      type: 'warning'
    })
    await api.delete(`/grades/categories/${category.id}`)
    ElMessage.success('删除成功')
    fetchCategories()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const addItem = (category) => {
  currentCategory.value = category
  editingItem.value = null
  itemForm.value = { 
    name: '', 
    type: 'manual', 
    weight: 0, 
    max_score: 100,
    auto_calculate: false 
  }
  itemDialogVisible.value = true
}

const editItem = (item) => {
  editingItem.value = item
  itemForm.value = { ...item }
  itemDialogVisible.value = true
}

const saveItem = async () => {
  try {
    if (editingItem.value) {
      await api.put(`/grades/items/${editingItem.value.id}`, itemForm.value)
      ElMessage.success('更新成功')
    } else {
      await api.post(`/grades/categories/${currentCategory.value.id}/items`, itemForm.value)
      ElMessage.success('创建成功')
    }
    itemDialogVisible.value = false
    fetchCategories()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '操作失败')
  }
}

const deleteItem = async (item) => {
  try {
    await ElMessageBox.confirm('确定删除该成绩项？', '提示', { type: 'warning' })
    await api.delete(`/grades/items/${item.id}`)
    ElMessage.success('删除成功')
    fetchCategories()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const togglePublish = async (item) => {
  try {
    await api.put(`/grades/items/${item.id}`, { is_published: item.is_published })
    ElMessage.success(item.is_published ? '已公开' : '已隐藏')
  } catch (e) {
    ElMessage.error('操作失败')
    item.is_published = !item.is_published
  }
}

const calculateAttendance = async (item) => {
  try {
    const res = await api.post(`/grades/items/${item.id}/calculate-attendance`)
    ElMessage.success(`考勤成绩计算完成 (共${res.data.total_sessions}次考勤)`)
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '计算失败')
  }
}

const gradeItem = (item) => {
  router.push(`/teacher/class/${classId.value}/grade-item/${item.id}`)
}

const calculateFinalGrades = async () => {
  if (totalWeight.value !== 100) {
    ElMessage.warning('权重总和必须为100%才能计算总评')
    return
  }
  
  try {
    calculating.value = true
    const res = await api.post(`/grades/class/${classId.value}/calculate-final`)
    ElMessage.success(`总评成绩计算完成 (共${res.data.total_students}名学生)`)
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '计算失败')
  } finally {
    calculating.value = false
  }
}

const publishGrades = () => {
  router.push(`/teacher/class/${classId.value}/grade-publish`)
}

const viewStatistics = () => {
  router.push(`/teacher/class/${classId.value}/grade-statistics`)
}

const goBack = () => {
  router.back()
}

const getItemTypeName = (type) => {
  const map = {
    manual: '手动',
    assignment: '作业',
    exam: '考试',
    attendance: '考勤'
  }
  return map[type] || type
}

const getItemTypeTag = (type) => {
  const map = {
    manual: '',
    assignment: 'success',
    exam: 'warning',
    attendance: 'info'
  }
  return map[type] || ''
}

onMounted(() => {
  fetchCategories()
})
</script>

<style scoped>
.grade-config-container {
  padding: 20px;
}

.help-text {
  line-height: 1.8;
}

.help-text p {
  margin: 8px 0;
}

.help-text strong {
  color: #409EFF;
}

.category-block {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
  background: #fafafa;
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.justify-between {
  justify-content: space-between;
}

.mb-2 { margin-bottom: 8px; }
.mb-4 { margin-bottom: 16px; }
.ml-2 { margin-left: 8px; }
.m-0 { margin: 0; }
.mt-2 { margin-top: 8px; }
.p-4 { padding: 16px; }
.text-center { text-align: center; }
.text-secondary { color: #909399; }
</style>
