<template>
  <div class="quick-commands">
    <el-dropdown @command="handleCommand" trigger="click">
      <el-button type="primary" :icon="Lightning">
        快捷指令
        <el-icon class="el-icon--right"><ArrowDown /></el-icon>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="attendance" :icon="UserFilled">
            /call - 发起签到
          </el-dropdown-item>
          <el-dropdown-item command="quiz" :icon="Edit">
            /quiz - 随堂测试
          </el-dropdown-item>
          <el-dropdown-item command="poll" :icon="DataLine">
            /poll - 课堂投票
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>

    <!-- 签到对话框 -->
    <el-dialog
      v-model="showAttendanceDialog"
      title="发起课堂签到"
      width="400px"
    >
      <el-form :model="attendanceForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="attendanceForm.title" placeholder="课堂签到" />
        </el-form-item>
        <el-form-item label="时长">
          <el-select v-model="attendanceForm.duration">
            <el-option label="3分钟" :value="180" />
            <el-option label="5分钟" :value="300" />
            <el-option label="10分钟" :value="600" />
            <el-option label="15分钟" :value="900" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAttendanceDialog = false">取消</el-button>
        <el-button type="primary" @click="startAttendance" :loading="loading">
          发起签到
        </el-button>
      </template>
    </el-dialog>

    <!-- 测试对话框 -->
    <el-dialog
      v-model="showQuizDialog"
      title="发起随堂测试"
      width="500px"
    >
      <el-form :model="quizForm" label-width="80px">
        <el-form-item label="问题" required>
          <el-input
            v-model="quizForm.question"
            type="textarea"
            :rows="3"
            placeholder="请输入测试问题..."
          />
        </el-form-item>
        <el-form-item label="选项">
          <div class="quiz-options">
            <div v-for="(option, index) in quizForm.options" :key="index" class="option-item">
              <el-input
                v-model="quizForm.options[index]"
                :placeholder="`选项 ${String.fromCharCode(65 + index)}`"
              >
                <template #prepend>{{ String.fromCharCode(65 + index) }}</template>
              </el-input>
              <el-radio v-model="quizForm.correct_answer" :label="index">
                正确
              </el-radio>
              <el-button
                v-if="quizForm.options.length > 2"
                :icon="Delete"
                circle
                size="small"
                @click="removeOption(index)"
              />
            </div>
            <el-button
              v-if="quizForm.options.length < 6"
              @click="addOption"
              :icon="Plus"
              size="small"
              text
            >
              添加选项
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="答题时长">
          <el-select v-model="quizForm.duration">
            <el-option label="30秒" :value="30" />
            <el-option label="60秒" :value="60" />
            <el-option label="90秒" :value="90" />
            <el-option label="120秒" :value="120" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showQuizDialog = false">取消</el-button>
        <el-button type="primary" @click="startQuiz" :loading="loading">
          发起测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import api from '../../api'
import { 
  Lightning, ArrowDown, UserFilled, Edit, DataLine, 
  Delete, Plus 
} from '@element-plus/icons-vue'

export default {
  name: 'QuickCommands',
  components: {
    Lightning,
    ArrowDown,
    UserFilled,
    Edit,
    DataLine,
    Delete,
    Plus
  },
  props: {
    liveClassId: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      loading: false,
      showAttendanceDialog: false,
      showQuizDialog: false,
      attendanceForm: {
        title: '课堂签到',
        duration: 300
      },
      quizForm: {
        question: '',
        options: ['', '', '', ''],
        correct_answer: 0,
        duration: 60
      }
    }
  },
  methods: {
    handleCommand(command) {
      if (command === 'attendance') {
        this.showAttendanceDialog = true
      } else if (command === 'quiz') {
        this.showQuizDialog = true
      } else if (command === 'poll') {
        this.$message.info('投票功能即将推出')
      }
    },
    async startAttendance() {
      this.loading = true
      try {
        const response = await api.post(
          `/chat/live/${this.liveClassId}/commands/attendance`,
          this.attendanceForm
        )
        
        if (response.data.code === 200) {
          this.$message.success('签到已发起')
          this.showAttendanceDialog = false
          this.$emit('command-issued', {
            type: 'attendance',
            data: response.data.data
          })
        }
      } catch (error) {
        this.$message.error('发起签到失败')
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    async startQuiz() {
      // 验证
      if (!this.quizForm.question.trim()) {
        this.$message.warning('请输入问题')
        return
      }
      
      const validOptions = this.quizForm.options.filter(o => o.trim())
      if (validOptions.length < 2) {
        this.$message.warning('至少需要2个选项')
        return
      }
      
      this.loading = true
      try {
        const response = await api.post(
          `/chat/live/${this.liveClassId}/commands/quiz`,
          {
            ...this.quizForm,
            options: validOptions
          }
        )
        
        if (response.data.code === 200) {
          this.$message.success('测试已发起')
          this.showQuizDialog = false
          this.$emit('command-issued', {
            type: 'quiz',
            data: response.data.data
          })
          
          // 重置表单
          this.quizForm = {
            question: '',
            options: ['', '', '', ''],
            correct_answer: 0,
            duration: 60
          }
        }
      } catch (error) {
        this.$message.error('发起测试失败')
        console.error(error)
      } finally {
        this.loading = false
      }
    },
    addOption() {
      this.quizForm.options.push('')
    },
    removeOption(index) {
      this.quizForm.options.splice(index, 1)
      // 调整正确答案索引
      if (this.quizForm.correct_answer >= this.quizForm.options.length) {
        this.quizForm.correct_answer = 0
      }
    }
  }
}
</script>

<style scoped>
.quick-commands {
  display: inline-block;
}

.quiz-options {
  width: 100%;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.option-item .el-input {
  flex: 1;
}
</style>
