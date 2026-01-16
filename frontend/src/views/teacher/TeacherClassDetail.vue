<template>
  <div class="class-manage-container">
    <el-page-header @back="goBack" content="班级管理" class="mb-4" />
    
    <!-- Header Info -->
    <el-card shadow="never" class="mb-4" v-if="courseInfo">
        <template #header>
            <div class="flex justify-between items-center">
                <div>
                   <span class="text-lg font-bold mr-2">{{ courseInfo.course_name }}</span>
                   <el-tag>{{ courseInfo.class_name }}</el-tag>
                </div>
                <div class="text-secondary text-sm">
                    {{ courseInfo.semester }} | {{ courseInfo.student_count }} 人
                </div>
            </div>
        </template>
        <div class="info-row">
            <span class="mr-4"><el-icon><Location /></el-icon> {{ courseInfo.classroom || '未排课' }}</span>
            <span><el-icon><Clock /></el-icon> {{ courseInfo.time || '时间未定' }}</span>
        </div>
    </el-card>

    <el-tabs v-model="activeTab" class="manage-tabs" type="border-card">
        <!-- Tab 1: Student Roster -->
        <el-tab-pane label="学生名册" name="students">
            <div class="tab-actions mb-2">
                <el-button type="success" size="small" plain @click="exportStudentList">导出名单</el-button>
            </div>
            <el-table :data="students" stripe style="width: 100%" v-loading="loadingStudents">
                <el-table-column prop="student_no" label="学号" width="120" sortable />
                <el-table-column prop="name" label="姓名" width="120" />
                <el-table-column prop="major" label="专业" />
                <el-table-column prop="dept_name" label="学院" />
                <el-table-column label="操作" width="150" align="center">
                    <template #default="scope">
                        <el-button link type="primary" size="small" @click="viewStudentDetail(scope.row.student_id)">详情</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-tab-pane>

        <!-- Tab 2: Assignments -->
        <el-tab-pane label="作业管理" name="assignments">
             <div class="tab-actions mb-3 flex justify-between">
                <span>共 {{ assignments.length }} 次作业</span>
                <el-button type="primary" size="small" @click="createAssignment">+ 发布作业</el-button>
            </div>
            <el-table :data="assignments" style="width: 100%" v-loading="loadingAssignments">
                <el-table-column prop="title" label="作业标题" min-width="200" />
                <el-table-column prop="deadline" label="截止时间" width="180">
                    <template #default="scope">{{ formatTime(scope.row.deadline) }}</template>
                </el-table-column>
                <el-table-column label="提交统计" width="250">
                    <template #default="scope">
                         <div class="stats-tags">
                             <el-tag type="success" size="small" effect="plain">已批: {{ scope.row.stats?.graded || 0 }}</el-tag>
                             <el-tag type="warning" size="small" effect="plain" class="ml-2">待批: {{ scope.row.stats?.pending || 0 }}</el-tag>
                             <el-tag type="info" size="small" effect="plain" class="ml-2">未交: {{ (scope.row.stats?.total || 0) - (scope.row.stats?.submitted || 0) - (scope.row.stats?.graded || 0) }}</el-tag>
                         </div>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="120" align="center">
                    <template #default="scope">
                        <el-button type="primary" size="small" @click="goToGrading(scope.row.id)">批改</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-tab-pane>

        <!-- Tab 3: Materials -->
        <el-tab-pane label="课件资料" name="materials">
             <div class="tab-actions mb-3 flex justify-between">
                <span></span>
                <el-button type="primary" size="small" @click="uploadMaterial">+ 上传资料</el-button>
            </div>
            <el-table :data="materials" style="width: 100%" v-loading="loadingMaterials">
                <el-table-column prop="title" label="名称" />
                <el-table-column prop="file_size" label="大小" width="100">
                     <template #default="scope">{{ formatSize(scope.row.file_size) }}</template>
                </el-table-column>
                <el-table-column prop="publish_time" label="发布时间" width="180">
                     <template #default="scope">{{ formatDate(scope.row.publish_time) }}</template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                    <template #default="scope">
                        <el-button link type="danger" size="small" @click="deleteMaterial(scope.row.id)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>
        </el-tab-pane>
        
        <!-- Tab 4: Attendance -->
        <el-tab-pane label="考勤记录" name="attendance">
            <div class="tab-actions mb-3 flex justify-between">
                <span>共 {{ attendanceList.length }} 次考勤</span>
                <el-button type="primary" size="small" @click="createAttendance">+ 发起考勤</el-button>
            </div>
            
            <!-- Attendance History Table -->
            <el-table :data="attendanceList" style="width: 100%" v-if="!currentAttendanceId">
                <el-table-column prop="date" label="日期" width="150" sortable />
                <el-table-column label="出勤统计">
                     <template #default="scope">
                         <div class="stats-mini">
                             <el-tag type="success" size="small">出勤: {{ scope.row.stats.present }}</el-tag>
                             <el-tag type="danger" size="small" class="ml-2">缺勤: {{ scope.row.stats.absent }}</el-tag>
                             <el-tag type="warning" size="small" class="ml-2">迟到: {{ scope.row.stats.late }}</el-tag>
                             <el-tag type="info" size="small" class="ml-2">请假: {{ scope.row.stats.leave }}</el-tag>
                         </div>
                     </template>
                </el-table-column>
                <el-table-column label="操作" width="200" align="center">
                    <template #default="scope">
                        <el-button link type="primary" @click="viewAttendance(scope.row.attendance_id)">详情/修改</el-button>
                        <el-button link type="danger" @click="deleteAttendance(scope.row.attendance_id)">删除</el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- Active Attendance Detail (Inline Edit) -->
            <div v-else class="attendance-detail-view">
                 <div class="detail-header mb-4 flex justify-between items-center bg-gray-50 p-3 rounded">
                     <span class="font-bold">📅 {{ currentAttendanceDate }} 考勤表</span>
                     <div>
                         <el-button size="small" @click="closeAttendanceDetail">返回列表</el-button>
                         <el-button type="primary" size="small" @click="saveAttendanceChanges" :loading="savingAttendance">保存更改</el-button>
                     </div>
                 </div>
                 
                 <el-table :data="currentAttendanceRecords" height="500" border>
                     <el-table-column prop="student_no" label="学号" width="120" sortable />
                     <el-table-column prop="name" label="姓名" width="120" />
                     <el-table-column label="状态" width="300">
                         <template #default="scope">
                             <el-radio-group v-model="scope.row.status" size="small">
                                <el-radio-button label="present">出勤</el-radio-button>
                                <el-radio-button label="late">迟到</el-radio-button>
                                <el-radio-button label="leave">请假</el-radio-button>
                                <el-radio-button label="absent">缺勤</el-radio-button>
                              </el-radio-group>
                         </template>
                     </el-table-column>
                     <el-table-column label="备注">
                         <template #default="scope">
                             <el-input v-model="scope.row.remarks" size="small" placeholder="备注..." />
                         </template>
                     </el-table-column>
                 </el-table>
            </div>
        </el-tab-pane>

        <!-- Tab 5: Gradebook -->
        <el-tab-pane label="成绩管理" name="grades">
            <!-- 筛选工具栏 -->
            <div class="grade-toolbar mb-3">
                <el-radio-group v-model="gradeViewMode" size="small" @change="onGradeViewModeChange">
                    <el-radio-button value="by_item">按作业/考试查看</el-radio-button>
                    <el-radio-button value="by_student">按学生查看总成绩</el-radio-button>
                </el-radio-group>
                
                <div class="toolbar-right">
                    <el-button type="primary" size="small" @click="goToGradeConfig">成绩配置</el-button>
                </div>
            </div>

            <!-- 按作业/考试查看模式 -->
            <div v-if="gradeViewMode === 'by_item'">
                <div class="mb-3 flex items-center gap-3">
                    <span class="text-sm text-gray-600">选择作业/考试：</span>
                    <el-select 
                        v-model="selectedGradeItem" 
                        placeholder="请选择" 
                        style="width: 300px"
                        @change="onGradeItemChange"
                    >
                        <el-option-group label="作业">
                            <el-option
                                v-for="item in homeworkItems"
                                :key="item.id"
                                :label="item.title"
                                :value="item.id"
                            />
                        </el-option-group>
                        <el-option-group label="考试">
                            <el-option
                                v-for="item in examItems"
                                :key="item.id"
                                :label="item.title"
                                :value="item.id"
                            />
                        </el-option-group>
                        <el-option-group label="其他成绩项">
                            <el-option
                                v-for="item in otherGradeItems"
                                :key="item.id"
                                :label="item.name"
                                :value="item.id"
                            />
                        </el-option-group>
                    </el-select>
                    
                    <el-button 
                        v-if="selectedGradeItem" 
                        type="primary" 
                        size="small"
                        @click="openGradeInputDialog"
                    >
                        录入/修改成绩
                    </el-button>
                    
                    <el-button 
                        v-if="selectedGradeItem" 
                        size="small"
                        @click="exportGrades"
                    >
                        导出成绩
                    </el-button>
                </div>

                <el-card v-if="!selectedGradeItem" class="empty-state">
                    <div class="text-center text-gray-400 py-8">
                        <el-icon size="48"><Document /></el-icon>
                        <p class="mt-2">请选择一个作业或考试查看成绩</p>
                    </div>
                </el-card>

                <el-table 
                    v-else
                    :data="currentItemGrades" 
                    style="width: 100%" 
                    v-loading="loadingItemGrades"
                    border
                    stripe
                >
                    <el-table-column type="index" label="#" width="50" />
                    <el-table-column prop="student_no" label="学号" width="120" sortable />
                    <el-table-column prop="student_name" label="姓名" width="100" />
                    <el-table-column label="成绩" width="150" align="center">
                        <template #default="scope">
                            <el-tag 
                                v-if="scope.row.score !== null && scope.row.score !== undefined"
                                :type="getScoreTagType(scope.row.score, currentItemInfo.max_score)"
                                size="large"
                            >
                                {{ scope.row.score }} / {{ currentItemInfo.max_score }}
                            </el-tag>
                            <span v-else class="text-gray-400">未录入</span>
                        </template>
                    </el-table-column>
                    <el-table-column prop="submitted_at" label="提交时间" width="160">
                        <template #default="scope">
                            {{ scope.row.submitted_at ? formatDateTime(scope.row.submitted_at) : '-' }}
                        </template>
                    </el-table-column>
                    <el-table-column prop="graded_at" label="批改时间" width="160">
                        <template #default="scope">
                            {{ scope.row.graded_at ? formatDateTime(scope.row.graded_at) : '-' }}
                        </template>
                    </el-table-column>
                    <el-table-column prop="feedback" label="评语" min-width="200" show-overflow-tooltip />
                    <el-table-column label="操作" width="100" align="center" fixed="right">
                        <template #default="scope">
                            <el-button 
                                link 
                                type="primary" 
                                size="small"
                                @click="quickEditGrade(scope.row)"
                            >
                                编辑
                            </el-button>
                        </template>
                    </el-table-column>
                </el-table>

                <!-- 统计信息 -->
                <el-card v-if="selectedGradeItem && currentItemGrades.length > 0" class="mt-3">
                    <div class="flex gap-6">
                        <div class="stat-item">
                            <span class="label">已录入：</span>
                            <span class="value text-success">{{ itemGradeStats.graded }} / {{ itemGradeStats.total }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">平均分：</span>
                            <span class="value text-primary">{{ itemGradeStats.avg.toFixed(1) }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">最高分：</span>
                            <span class="value text-warning">{{ itemGradeStats.max }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">最低分：</span>
                            <span class="value">{{ itemGradeStats.min }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">及格率：</span>
                            <span class="value">{{ itemGradeStats.passRate }}%</span>
                        </div>
                    </div>
                </el-card>
            </div>

            <!-- 按学生查看总成绩模式 -->
            <div v-else-if="gradeViewMode === 'by_student'">
                <div class="mb-3 flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <el-tag>总成绩统计</el-tag>
                        <span class="text-sm text-gray-500">基于成绩配置自动计算</span>
                    </div>
                    <div>
                        <el-button size="small" @click="calculateFinalGrades">计算总成绩</el-button>
                        <el-button size="small" @click="exportFinalGrades">导出总成绩</el-button>
                    </div>
                </div>

                <el-table 
                    :data="finalGradesData" 
                    style="width: 100%" 
                    v-loading="loadingFinalGrades"
                    border
                    stripe
                >
                    <el-table-column type="index" label="排名" width="60" />
                    <el-table-column prop="student_no" label="学号" width="120" sortable />
                    <el-table-column prop="student_name" label="姓名" width="100" />
                    
                    <!-- 各分类成绩 -->
                    <el-table-column 
                        v-for="cat in gradeCategories" 
                        :key="cat.id"
                        :label="`${cat.name}(${cat.weight}%)`"
                        width="120"
                        align="center"
                    >
                        <template #default="scope">
                            {{ scope.row.category_scores?.[cat.id]?.toFixed(1) || '-' }}
                        </template>
                    </el-table-column>
                    
                    <el-table-column label="总成绩" width="120" align="center" fixed="right">
                        <template #default="scope">
                            <strong 
                                class="text-lg" 
                                :class="getFinalGradeClass(scope.row.final_score)"
                            >
                                {{ scope.row.final_score?.toFixed(1) || '-' }}
                            </strong>
                        </template>
                    </el-table-column>
                    
                    <el-table-column label="等级" width="80" align="center" fixed="right">
                        <template #default="scope">
                            <el-tag :type="getGradeLevelType(scope.row.grade_level)">
                                {{ scope.row.grade_level || '-' }}
                            </el-tag>
                        </template>
                    </el-table-column>
                    
                    <el-table-column label="操作" width="100" align="center" fixed="right">
                        <template #default="scope">
                            <el-button 
                                link 
                                type="primary" 
                                size="small"
                                @click="viewStudentGradeDetail(scope.row)"
                            >
                                详情
                            </el-button>
                        </template>
                    </el-table-column>
                </el-table>

                <!-- 总成绩统计 -->
                <el-card v-if="finalGradesData.length > 0" class="mt-3">
                    <div class="flex gap-6">
                        <div class="stat-item">
                            <span class="label">班级人数：</span>
                            <span class="value">{{ finalGradeStats.total }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">平均分：</span>
                            <span class="value text-primary">{{ finalGradeStats.avg.toFixed(1) }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">最高分：</span>
                            <span class="value text-warning">{{ finalGradeStats.max }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">最低分：</span>
                            <span class="value">{{ finalGradeStats.min }}</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">及格率：</span>
                            <span class="value text-success">{{ finalGradeStats.passRate }}%</span>
                        </div>
                        <div class="stat-item">
                            <span class="label">优秀率：</span>
                            <span class="value text-success">{{ finalGradeStats.excellentRate }}%</span>
                        </div>
                    </div>
                </el-card>
            </div>
        </el-tab-pane>
        
        <!-- Tab 6: Teaching Statistics -->
        <el-tab-pane label="教学统计" name="statistics">
            <el-row :gutter="20" class="mb-4">
                <el-col :span="8">
                    <el-card shadow="hover">
                        <div class="stat-card">
                            <div class="stat-icon" style="background: #E6F7FF; color: #1890FF;">
                                <el-icon size="24"><Document /></el-icon>
                            </div>
                            <div class="stat-info">
                                <div class="stat-value">{{ teachingStats.total_assignments || 0 }}</div>
                                <div class="stat-label">已发布作业</div>
                            </div>
                        </div>
                    </el-card>
                </el-col>
                <el-col :span="8">
                    <el-card shadow="hover">
                        <div class="stat-card">
                            <div class="stat-icon" style="background: #F0F9FF; color: #52C41A;">
                                <el-icon size="24"><Check /></el-icon>
                            </div>
                            <div class="stat-info">
                                <div class="stat-value">{{ teachingStats.avg_submission_rate || 0 }}%</div>
                                <div class="stat-label">平均提交率</div>
                            </div>
                        </div>
                    </el-card>
                </el-col>
                <el-col :span="8">
                    <el-card shadow="hover">
                        <div class="stat-card">
                            <div class="stat-icon" style="background: #FFF7E6; color: #FA8C16;">
                                <el-icon size="24"><Calendar /></el-icon>
                            </div>
                            <div class="stat-info">
                                <div class="stat-value">{{ teachingStats.total_attendance || 0 }}</div>
                                <div class="stat-label">考勤次数</div>
                            </div>
                        </div>
                    </el-card>
                </el-col>
            </el-row>
            
            <el-row :gutter="20" class="mb-4">
                <el-col :span="12">
                    <el-card>
                        <template #header>
                            <div class="flex justify-between items-center">
                                <span>作业完成情况</span>
                                <el-button size="small" @click="viewGradeStatistics">查看成绩统计</el-button>
                            </div>
                        </template>
                        <el-table :data="assignmentStats" max-height="400">
                            <el-table-column prop="title" label="作业名称" show-overflow-tooltip />
                            <el-table-column label="提交率" width="120" align="center">
                                <template #default="scope">
                                    <el-progress 
                                        :percentage="scope.row.submission_rate" 
                                        :color="getProgressColor(scope.row.submission_rate)"
                                        :status="scope.row.submission_rate === 100 ? 'success' : ''"
                                    />
                                </template>
                            </el-table-column>
                            <el-table-column label="已批改" width="100" align="center">
                                <template #default="scope">
                                    <el-tag :type="scope.row.graded === scope.row.submitted ? 'success' : 'warning'" size="small">
                                        {{ scope.row.graded }}/{{ scope.row.submitted }}
                                    </el-tag>
                                </template>
                            </el-table-column>
                        </el-table>
                        <div v-if="assignmentStats.length === 0" class="empty-hint">暂无作业数据</div>
                    </el-card>
                </el-col>
                
                <el-col :span="12">
                    <el-card>
                        <template #header>考勤统计</template>
                        <div class="attendance-summary">
                            <div class="summary-item">
                                <span class="summary-label">总出勤率：</span>
                                <span class="summary-value text-success">{{ teachingStats.avg_attendance_rate || 0 }}%</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">平均出勤：</span>
                                <span class="summary-value">{{ teachingStats.avg_present || 0 }} 人</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">平均缺勤：</span>
                                <span class="summary-value text-danger">{{ teachingStats.avg_absent || 0 }} 人</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">平均迟到：</span>
                                <span class="summary-value text-warning">{{ teachingStats.avg_late || 0 }} 人</span>
                            </div>
                        </div>
                        
                        <el-divider />
                        
                        <div class="attendance-chart">
                            <div class="chart-title">出勤趋势</div>
                            <el-table :data="attendanceHistory" size="small" max-height="300">
                                <el-table-column prop="date" label="日期" width="120" />
                                <el-table-column label="出勤率" align="center">
                                    <template #default="scope">
                                        <el-tag :type="scope.row.rate >= 90 ? 'success' : scope.row.rate >= 80 ? '' : 'danger'" size="small">
                                            {{ scope.row.rate }}%
                                        </el-tag>
                                    </template>
                                </el-table-column>
                            </el-table>
                            <div v-if="attendanceHistory.length === 0" class="empty-hint">暂无考勤数据</div>
                        </div>
                    </el-card>
                </el-col>
            </el-row>
        </el-tab-pane>
    </el-tabs>

    <!-- Create Assignment Dialog -->
    <el-dialog v-model="dialogVisible" title="发布新作业" width="500px">
        <el-form :model="form" label-width="80px">
            <el-form-item label="标题">
                <el-input v-model="form.title" placeholder="如: 期中大作业" />
            </el-form-item>
            <el-form-item label="截止时间">
                <el-date-picker 
                    v-model="form.deadline" 
                    type="datetime" 
                    placeholder="选择截止日期" 
                    style="width: 100%" 
                    value-format="YYYY-MM-DD HH:mm:ss"
                />
            </el-form-item>
             <el-form-item label="满分">
                <el-input-number v-model="form.total_score" :min="1" :max="100" />
            </el-form-item>
            <el-form-item label="类型">
                <el-radio-group v-model="form.type">
                  <el-radio label="homework">普通作业</el-radio>
                  <el-radio label="exam">考试测验</el-radio>
                </el-radio-group>
            </el-form-item>
            <el-form-item label="说明">
                <el-input v-model="form.description" type="textarea" rows="3" />
            </el-form-item>
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="dialogVisible = false">取消</el-button>
                <el-button type="primary" @click="submitAssignment" :loading="submitting">发布</el-button>
            </span>
        </template>
    </el-dialog>

    <!-- Upload Material Dialog -->
    <el-dialog v-model="uploadDialogVisible" title="上传课件资料" width="500px">
        <el-form label-width="80px">
            <el-form-item label="文件">
                <el-upload
                    class="upload-demo"
                    drag
                    action=""
                    :auto-upload="false"
                    :on-change="handleFileChange"
                    :limit="1"
                    style="width: 100%"
                >
                    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                    <div class="el-upload__text">
                         拖拽文件到此处或 <em>点击上传</em>
                    </div>
                </el-upload>
            </el-form-item>
             <el-form-item label="标题">
                <el-input v-model="uploadForm.title" placeholder="如果不填则使用文件名" />
            </el-form-item>
             <el-form-item label="描述">
                <el-input v-model="uploadForm.description" type="textarea" />
            </el-form-item>
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="uploadDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="submitUpload" :loading="uploading">开始上传</el-button>
            </span>
        </template>
    </el-dialog>

    <!-- Create Attendance Dialog -->
    <el-dialog v-model="attendanceDialogVisible" title="发起考勤" width="500px">
        <el-form :model="attendanceForm" label-width="100px">
            <el-form-item label="考勤日期">
                <el-date-picker 
                    v-model="attendanceForm.date" 
                    type="date"
                    placeholder="选择日期"
                    style="width: 100%"
                    :disabled-date="disabledDate"
                />
            </el-form-item>
            <el-form-item label="考勤方式">
                <el-radio-group v-model="attendanceForm.type">
                    <el-radio value="manual">教师点名</el-radio>
                    <el-radio value="self">学生自助签到</el-radio>
                </el-radio-group>
                <div class="text-xs text-gray-500 mt-2">
                    <div v-if="attendanceForm.type === 'manual'">教师手动记录每位学生的出勤状态</div>
                    <div v-else>学生通过系统自助签到，教师可后续修改</div>
                </div>
            </el-form-item>
            <el-form-item label="默认状态" v-if="attendanceForm.type === 'manual'">
                <el-select v-model="attendanceForm.defaultStatus" style="width: 100%">
                    <el-option label="默认出勤" value="present" />
                    <el-option label="默认缺勤" value="absent" />
                </el-select>
            </el-form-item>
        </el-form>
        <template #footer>
            <el-button @click="attendanceDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitAttendance" :loading="creatingAttendance">发起</el-button>
        </template>
    </el-dialog>

    <!-- Batch Grade Input Dialog -->
    <el-dialog 
        v-model="gradeInputDialogVisible" 
        :title="`批量录入成绩 - ${currentItemInfo.name}`" 
        width="900px"
        :close-on-click-modal="false"
    >
        <div class="mb-3 flex justify-between items-center">
            <div class="text-sm text-gray-600">
                满分：{{ currentItemInfo.max_score }} 分
            </div>
            <div>
                <el-button size="small" @click="fillAllScores">一键填充</el-button>
                <el-button size="small" @click="clearAllScores">清空全部</el-button>
            </div>
        </div>

        <el-table 
            :data="batchGradeData" 
            style="width: 100%" 
            max-height="500"
            border
        >
            <el-table-column type="index" label="#" width="50" />
            <el-table-column prop="student_no" label="学号" width="120" />
            <el-table-column prop="student_name" label="姓名" width="100" />
            <el-table-column label="成绩" width="150">
                <template #default="scope">
                    <el-input-number
                        v-model="scope.row.score"
                        :min="0"
                        :max="currentItemInfo.max_score"
                        :precision="1"
                        size="small"
                        style="width: 120px"
                    />
                </template>
            </el-table-column>
            <el-table-column label="评语" min-width="200">
                <template #default="scope">
                    <el-input
                        v-model="scope.row.feedback"
                        placeholder="选填"
                        size="small"
                    />
                </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
                <template #default="scope">
                    <el-tag v-if="scope.row.originalScore !== null" type="success" size="small">
                        已录入
                    </el-tag>
                    <el-tag v-else type="info" size="small">未录入</el-tag>
                </template>
            </el-table-column>
        </el-table>

        <template #footer>
            <div class="flex justify-between items-center">
                <span class="text-sm text-gray-500">
                    已录入：{{ batchGradeData.filter(g => g.score !== null).length }} / {{ batchGradeData.length }}
                </span>
                <div>
                    <el-button @click="gradeInputDialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="submitBatchGrades" :loading="savingBatchGrades">
                        保存全部
                    </el-button>
                </div>
            </div>
        </template>
    </el-dialog>

    <!-- Student Grade Detail Dialog -->
    <el-dialog 
        v-model="studentGradeDetailVisible" 
        :title="`学生成绩详情 - ${currentStudentGradeDetail.student_name}`" 
        width="800px"
    >
        <div v-if="loadingStudentDetail" class="text-center py-8">
            <el-skeleton :rows="5" animated />
        </div>
        <div v-else>
            <!-- 学生基本信息 -->
            <el-descriptions :column="3" border class="mb-4">
                <el-descriptions-item label="学号">{{ currentStudentGradeDetail.student_no }}</el-descriptions-item>
                <el-descriptions-item label="姓名">{{ currentStudentGradeDetail.student_name }}</el-descriptions-item>
                <el-descriptions-item label="总成绩">
                    <el-tag :type="getGradeLevelType(currentStudentGradeDetail.grade_level)" size="large">
                        {{ currentStudentGradeDetail.final_score?.toFixed(1) || '-' }} 分 ({{ currentStudentGradeDetail.grade_level || '-' }})
                    </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="班级排名" :span="3">
                    第 {{ currentStudentGradeDetail.rank || '-' }} 名
                </el-descriptions-item>
            </el-descriptions>

            <!-- 各分类成绩 -->
            <el-card class="mb-3" v-for="category in studentGradeCategories" :key="category.id">
                <template #header>
                    <div class="flex justify-between items-center">
                        <span class="font-bold">{{ category.name }}</span>
                        <el-tag>权重: {{ category.weight }}%</el-tag>
                    </div>
                </template>
                
                <div class="mb-2">
                    <span class="text-sm text-gray-600">分类得分：</span>
                    <span class="text-lg font-bold text-primary">
                        {{ studentGradeDetail.category_scores?.[category.id]?.toFixed(1) || '-' }} 分
                    </span>
                </div>

                <el-table :data="category.items" size="small" stripe>
                    <el-table-column prop="name" label="成绩项" width="150" />
                    <el-table-column prop="type" label="类型" width="100">
                        <template #default="scope">
                            <el-tag size="small" :type="getItemTypeTagType(scope.row.type)">
                                {{ getItemTypeName(scope.row.type) }}
                            </el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column label="权重" width="80">
                        <template #default="scope">{{ scope.row.weight }}%</template>
                    </el-table-column>
                    <el-table-column label="满分" width="80">
                        <template #default="scope">{{ scope.row.max_score }}</template>
                    </el-table-column>
                    <el-table-column label="得分" width="100" align="center">
                        <template #default="scope">
                            <span v-if="scope.row.score !== null && scope.row.score !== undefined" 
                                  :class="getScoreColorClass(scope.row.score, scope.row.max_score)">
                                <strong>{{ scope.row.score }}</strong>
                            </span>
                            <span v-else class="text-gray-400">未录入</span>
                        </template>
                    </el-table-column>
                    <el-table-column label="得分率" width="100" align="center">
                        <template #default="scope">
                            <span v-if="scope.row.score !== null && scope.row.score !== undefined">
                                {{ ((scope.row.score / scope.row.max_score) * 100).toFixed(1) }}%
                            </span>
                            <span v-else>-</span>
                        </template>
                    </el-table-column>
                    <el-table-column prop="remarks" label="备注" show-overflow-tooltip />
                </el-table>
            </el-card>

            <!-- 统计信息 -->
            <el-card>
                <template #header>
                    <span class="font-bold">成绩统计</span>
                </template>
                <el-row :gutter="20">
                    <el-col :span="8">
                        <div class="stat-box">
                            <div class="stat-label">已录入项</div>
                            <div class="stat-value">{{ studentGradeStats.recorded }} / {{ studentGradeStats.total }}</div>
                        </div>
                    </el-col>
                    <el-col :span="8">
                        <div class="stat-box">
                            <div class="stat-label">平均得分率</div>
                            <div class="stat-value text-primary">{{ studentGradeStats.avgRate }}%</div>
                        </div>
                    </el-col>
                    <el-col :span="8">
                        <div class="stat-box">
                            <div class="stat-label">录入进度</div>
                            <el-progress :percentage="studentGradeStats.progress" />
                        </div>
                    </el-col>
                </el-row>
            </el-card>
        </div>

        <template #footer>
            <el-button @click="studentGradeDetailVisible = false">关闭</el-button>
        </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Location, Clock, UploadFilled, Document, Check, Calendar } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api'

const route = useRoute()
const router = useRouter()
const classId = route.params.id

const courseInfo = ref(null)
const students = ref([])
const assignments = ref([])
const materials = ref([])
const activeTab = ref('students')

const loadingStudents = ref(false)
const loadingAssignments = ref(false)
const loadingMaterials = ref(false)

// Dialog State
const dialogVisible = ref(false)
const submitting = ref(false)
const form = ref({
    title: '',
    deadline: '',
    total_score: 100,
    description: '',
    type: 'homework'
})

// Upload Dialog State
const uploadDialogVisible = ref(false)
const uploading = ref(false)
const uploadForm = ref({
    title: '',
    description: '',
    file: null
})

// Attendance Dialog State
const attendanceDialogVisible = ref(false)
const creatingAttendance = ref(false)
const attendanceForm = ref({
    date: new Date(),
    type: 'manual',
    defaultStatus: 'present'
})

// Teaching Statistics State
const teachingStats = ref({})
const assignmentStats = ref([])
const attendanceHistory = ref([])

// Student Grade Detail Dialog State
const studentGradeDetailVisible = ref(false)
const currentStudentGradeDetail = ref({})
const studentGradeDetail = ref({})
const studentGradeCategories = ref([])
const loadingStudentDetail = ref(false)
const studentGradeStats = computed(() => {
    if (!studentGradeCategories.value.length) {
        return { total: 0, recorded: 0, avgRate: 0, progress: 0 }
    }
    
    let totalItems = 0
    let recordedItems = 0
    let totalRate = 0
    let ratedItems = 0
    
    studentGradeCategories.value.forEach(cat => {
        cat.items.forEach(item => {
            totalItems++
            if (item.score !== null && item.score !== undefined) {
                recordedItems++
                if (item.max_score > 0) {
                    totalRate += (item.score / item.max_score) * 100
                    ratedItems++
                }
            }
        })
    })
    
    return {
        total: totalItems,
        recorded: recordedItems,
        avgRate: ratedItems > 0 ? (totalRate / ratedItems).toFixed(1) : 0,
        progress: totalItems > 0 ? Math.round((recordedItems / totalItems) * 100) : 0
    }
})

const fetchClassInfo = async () => {
    try {
        // Reuse my classes to get info (optimized would be single get)
        const res = await api.get('/classes/my')
        courseInfo.value = res.data.find(c => c.class_id == classId)
    } catch(e) {}
}

const fetchStudents = async () => {
    loadingStudents.value = true
    try {
        const res = await api.get(`/classes/${classId}/students`)
        students.value = res.data
    } catch(e) {}
    finally { loadingStudents.value = false }
}

const fetchAssignments = async () => {
    loadingAssignments.value = true
    try {
        const res = await api.get(`/classes/${classId}/assignments`)
        assignments.value = res.data
    } catch(e) {}
    finally { loadingAssignments.value = false }
}

const fetchMaterials = async () => {
    loadingMaterials.value = true
    try {
        const res = await api.get(`/classes/${classId}/materials`)
        materials.value = res.data
    } catch(e) {}
    finally { loadingMaterials.value = false }
}

const createAssignment = () => {
    form.value = { title: '', deadline: '', total_score: 100, description: '', type: 'homework' }
    dialogVisible.value = true
}

const submitAssignment = async () => {
    if(!form.value.title || !form.value.deadline) {
        ElMessage.warning('请填写完整信息')
        return
    }
    submitting.value = true
    try {
        await api.post('/assignments/', {
            ...form.value,
            class_id: classId
        })
        ElMessage.success('发布成功')
        dialogVisible.value = false
        fetchAssignments() // Refresh list
    } catch(e) {
        ElMessage.error('发布失败: ' + (e.response?.data?.error || '未知错误'))
    } finally {
        submitting.value = false
    }
}

const goToGrading = (assignmentId) => {
    // alert(`跳转到批改界面 (ID: ${assignmentId})`)
    router.push(`/teacher/grading/${assignmentId}`)
}

const goBack = () => {
    router.push('/teacher/dashboard')
}

const exportStudentList = () => {
    if (!students.value.length) {
        ElMessage.warning('没有可导出的学生')
        return
    }
    
    const headers = ['学号', '姓名', '专业', '学院']
    const rows = students.value.map(s => [
        s.student_no,
        s.name,
        s.major || '',
        s.dept_name || ''
    ])
    
    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')
    
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${courseInfo.value?.class_name || '班级'}_学生名单.csv`
    link.click()
    URL.revokeObjectURL(link.href)
    
    ElMessage.success('导出成功')
}

const uploadMaterial = () => {
    uploadDialogVisible.value = true
    uploadForm.value = { title: '', description: '', file: null }
}

const handleFileChange = (uploadFile) => {
    uploadForm.value.file = uploadFile.raw
}

const submitUpload = async () => {
    if (!uploadForm.value.file) {
        ElMessage.warning('请选择文件')
        return
    }
    
    uploading.value = true
    const formData = new FormData()
    formData.append('file', uploadForm.value.file)
    formData.append('title', uploadForm.value.title || uploadForm.value.file.name)
    formData.append('description', uploadForm.value.description)
    
    try {
        await api.post(`/classes/${classId}/materials`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
        ElMessage.success('上传成功')
        uploadDialogVisible.value = false
        fetchMaterials()
    } catch(e) {
        ElMessage.error('上传失败: ' + (e.response?.data?.error || '未知错误'))
    } finally {
        uploading.value = false
    }
}

const deleteMaterial = async (materialId) => {
    try {
        await ElMessageBox.confirm('确定删除这个资料吗？', '提示', {
            type: 'warning'
        })
        
        await api.delete(`/materials/${materialId}`)
        ElMessage.success('删除成功')
        fetchMaterials()
    } catch (e) {
        if (e !== 'cancel') {
            ElMessage.error('删除失败: ' + (e.response?.data?.error || '未知错误'))
        }
    }
}

const viewStudentDetail = (studentId) => {
    ElMessage.info('学生详情功能开发中')
    // TODO: 可以跳转到学生详情页或显示对话框
    // router.push(`/teacher/student/${studentId}`)
}

// Attendance Logic
const attendanceList = ref([])
const currentAttendanceId = ref(null)
const currentAttendanceDate = ref('')
const currentAttendanceRecords = ref([])
const savingAttendance = ref(false)

const fetchAttendanceList = async () => {
    try {
        const res = await api.get(`/attendance/class/${classId}`)
        attendanceList.value = res.data
    } catch(e) { console.error(e) }
}

const createAttendance = () => {
    attendanceForm.value = {
        date: new Date(),
        type: 'manual',
        defaultStatus: 'present'
    }
    attendanceDialogVisible.value = true
}

const submitAttendance = async () => {
    creatingAttendance.value = true
    try {
        const isSelfCheckin = attendanceForm.value.type === 'self'
        const payload = {
            date: attendanceForm.value.date,
            is_self_checkin: isSelfCheckin,
            // 如果是自助签到，默认状态应该是 'absent'，让学生自己签到
            default_status: isSelfCheckin ? 'absent' : attendanceForm.value.defaultStatus
        }
        await api.post(`/attendance/class/${classId}`, payload)
        ElMessage.success('考勤已发起')
        attendanceDialogVisible.value = false
        fetchAttendanceList()
    } catch(e) {
        ElMessage.error('发起失败: ' + (e.response?.data?.error || '未知错误'))
    } finally {
        creatingAttendance.value = false
    }
}

const deleteAttendance = async (attendanceId) => {
    try {
        await ElMessageBox.confirm('确定删除这次考勤记录？', '提示', {
            type: 'warning'
        })
        await api.delete(`/attendance/${attendanceId}`)
        ElMessage.success('删除成功')
        fetchAttendanceList()
    } catch(e) {
        if (e !== 'cancel') {
            ElMessage.error('删除失败')
        }
    }
}

const disabledDate = (date) => {
    // 禁用未来的日期
    return date.getTime() > Date.now()
}

// Teaching Statistics Logic
const fetchTeachingStats = async () => {
    try {
        // 获取作业统计
        const assignmentsRes = await api.get(`/classes/${classId}/assignments`)
        const allAssignments = assignmentsRes.data
        
        let totalSubmissions = 0
        let totalPossible = 0
        
        const stats = allAssignments.map(a => {
            const submitted = (a.stats?.submitted || 0) + (a.stats?.graded || 0)
            const total = a.stats?.total || 0
            const rate = total > 0 ? Math.round((submitted / total) * 100) : 0
            
            totalSubmissions += submitted
            totalPossible += total
            
            return {
                title: a.title,
                submission_rate: rate,
                submitted: submitted,
                graded: a.stats?.graded || 0,
                total: total
            }
        })
        
        assignmentStats.value = stats
        
        // 获取考勤统计
        const attendanceRes = await api.get(`/attendance/class/${classId}`)
        const attendances = attendanceRes.data
        
        let totalPresent = 0
        let totalAbsent = 0
        let totalLate = 0
        let totalCount = 0
        
        const history = attendances.map(a => {
            const total = a.stats.total
            const present = a.stats.present
            const rate = total > 0 ? Math.round((present / total) * 100) : 0
            
            totalPresent += present
            totalAbsent += a.stats.absent
            totalLate += a.stats.late
            totalCount += 1
            
            return {
                date: new Date(a.date).toLocaleDateString('zh-CN'),
                rate: rate,
                present: present,
                total: total
            }
        })
        
        attendanceHistory.value = history.slice(0, 10) // 最近10次
        
        // 计算总体统计
        const avgSubmissionRate = totalPossible > 0 
            ? Math.round((totalSubmissions / totalPossible) * 100) 
            : 0
        
        const avgAttendanceRate = attendances.length > 0
            ? Math.round(attendances.reduce((sum, a) => {
                const rate = a.stats.total > 0 ? (a.stats.present / a.stats.total) * 100 : 0
                return sum + rate
            }, 0) / attendances.length)
            : 0
        
        teachingStats.value = {
            total_assignments: allAssignments.length,
            avg_submission_rate: avgSubmissionRate,
            total_attendance: attendances.length,
            avg_attendance_rate: avgAttendanceRate,
            avg_present: totalCount > 0 ? Math.round(totalPresent / totalCount) : 0,
            avg_absent: totalCount > 0 ? Math.round(totalAbsent / totalCount) : 0,
            avg_late: totalCount > 0 ? Math.round(totalLate / totalCount) : 0
        }
    } catch(e) {
        console.error('Failed to fetch teaching stats:', e)
    }
}

const viewGradeStatistics = () => {
    router.push(`/teacher/class/${classId}/grade-statistics`)
}

const getProgressColor = (percentage) => {
    if (percentage >= 90) return '#67C23A'
    if (percentage >= 70) return '#409EFF'
    if (percentage >= 50) return '#E6A23C'
    return '#F56C6C'
}

const viewAttendance = async (id) => {
    try {
        const res = await api.get(`/attendance/${id}`)
        currentAttendanceId.value = id
        currentAttendanceDate.value = formatDate(res.data.date)
        currentAttendanceRecords.value = res.data.records
    } catch(e) {
        ElMessage.error('无法加载详情')
    }
}

const closeAttendanceDetail = () => {
    currentAttendanceId.value = null
    currentAttendanceRecords.value = []
    fetchAttendanceList() // Refresh stats
}

const saveAttendanceChanges = async () => {
    savingAttendance.value = true
    try {
        const payload = {
            records: currentAttendanceRecords.value.map(r => ({
                record_id: r.record_id,
                status: r.status,
                remarks: r.remarks
            }))
        }
        await api.put(`/attendance/${currentAttendanceId.value}/records`, payload)
        ElMessage.success('保存成功')
    } catch(e) {
        ElMessage.error('保存失败')
    } finally {
        savingAttendance.value = false
    }
}

// Grades Logic - 新版本
const gradeViewMode = ref('by_item') // 'by_item' 或 'by_student'
const selectedGradeItem = ref(null)
const currentItemGrades = ref([])
const currentItemInfo = ref({ max_score: 100 })
const loadingItemGrades = ref(false)
const homeworkItems = ref([])
const examItems = ref([])
const otherGradeItems = ref([])
const finalGradesData = ref([])
const loadingFinalGrades = ref(false)
const gradeCategories = ref([])

// 批量录入成绩相关
const gradeInputDialogVisible = ref(false)
const batchGradeData = ref([])
const savingBatchGrades = ref(false)

const itemGradeStats = computed(() => {
    if (currentItemGrades.value.length === 0) {
        return { total: 0, graded: 0, avg: 0, max: 0, min: 0, passRate: 0 }
    }
    
    const gradedItems = currentItemGrades.value.filter(g => g.score !== null && g.score !== undefined)
    const scores = gradedItems.map(g => g.score)
    const passCount = scores.filter(s => s >= currentItemInfo.value.max_score * 0.6).length
    
    return {
        total: currentItemGrades.value.length,
        graded: gradedItems.length,
        avg: scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0,
        max: scores.length > 0 ? Math.max(...scores) : 0,
        min: scores.length > 0 ? Math.min(...scores) : 0,
        passRate: gradedItems.length > 0 ? Math.round((passCount / gradedItems.length) * 100) : 0
    }
})

const finalGradeStats = computed(() => {
    if (finalGradesData.value.length === 0) {
        return { total: 0, avg: 0, max: 0, min: 0, passRate: 0, excellentRate: 0 }
    }
    
    const scores = finalGradesData.value.map(s => s.final_score).filter(s => s !== null && s !== undefined)
    const passCount = scores.filter(s => s >= 60).length
    const excellentCount = scores.filter(s => s >= 90).length
    
    return {
        total: finalGradesData.value.length,
        avg: scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0,
        max: scores.length > 0 ? Math.max(...scores) : 0,
        min: scores.length > 0 ? Math.min(...scores) : 0,
        passRate: scores.length > 0 ? Math.round((passCount / scores.length) * 100) : 0,
        excellentRate: scores.length > 0 ? Math.round((excellentCount / scores.length) * 100) : 0
    }
})

const onGradeViewModeChange = async (mode) => {
    if (mode === 'by_item') {
        await fetchGradeItems()
    } else {
        await fetchFinalGrades()
    }
}

const fetchGradeItems = async () => {
    try {
        // 获取作业和考试列表
        const resAssignments = await api.get(`/classes/${classId}/assignments`)
        const assignments = resAssignments.data || []
        
        homeworkItems.value = assignments.filter(a => a.type === 'homework')
        examItems.value = assignments.filter(a => a.type === 'exam')
        
        // 获取其他成绩项（从成绩配置）
        const resGradeItems = await api.get(`/grades/class/${classId}/items`)
        otherGradeItems.value = resGradeItems.data || []
    } catch (e) {
        console.error('获取成绩项失败:', e)
    }
}

const onGradeItemChange = async (itemId) => {
    if (!itemId) return
    
    loadingItemGrades.value = true
    try {
        // 判断是作业/考试还是其他成绩项
        const homework = homeworkItems.value.find(h => h.id === itemId)
        const exam = examItems.value.find(e => e.id === itemId)
        const otherItem = otherGradeItems.value.find(o => o.id === itemId)
        
        if (homework || exam) {
            // 作业或考试，从assignment API获取
            const res = await api.get(`/assignments/${itemId}/grades`)
            currentItemGrades.value = res.data || []
            currentItemInfo.value = {
                id: itemId,
                name: homework?.title || exam?.title,
                max_score: homework?.total_score || exam?.total_score || 100,
                type: homework ? 'homework' : 'exam'
            }
        } else if (otherItem) {
            // 其他成绩项，从grade API获取
            const res = await api.get(`/grades/item/${itemId}/scores`)
            currentItemGrades.value = res.data || []
            currentItemInfo.value = {
                id: itemId,
                name: otherItem.name,
                max_score: otherItem.max_score || 100,
                type: 'other'
            }
        }
    } catch (e) {
        ElMessage.error('获取成绩失败: ' + (e.response?.data?.error || '未知错误'))
    } finally {
        loadingItemGrades.value = false
    }
}

const fetchFinalGrades = async () => {
    loadingFinalGrades.value = true
    try {
        const res = await api.get(`/grades/class/${classId}/final`)
        finalGradesData.value = res.data.students || []
        gradeCategories.value = res.data.categories || []
    } catch (e) {
        console.error('获取总成绩失败:', e)
        ElMessage.error('获取总成绩失败')
    } finally {
        loadingFinalGrades.value = false
    }
}

const openGradeInputDialog = async () => {
    if (!selectedGradeItem.value || !currentItemGrades.value.length) {
        ElMessage.warning('请先选择成绩项并加载数据')
        return
    }
    
    // 准备批量录入数据
    batchGradeData.value = currentItemGrades.value.map(g => ({
        student_id: g.student_id,
        student_no: g.student_no,
        student_name: g.student_name,
        score: g.score,
        originalScore: g.score, // 保存原始值用于判断是否已录入
        feedback: g.feedback || ''
    }))
    
    gradeInputDialogVisible.value = true
}

const fillAllScores = () => {
    ElMessageBox.prompt('请输入统一分数', '一键填充', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^\d+(\.\d+)?$/,
        inputErrorMessage: '请输入有效的数字'
    }).then(({ value }) => {
        const score = parseFloat(value)
        if (score > currentItemInfo.value.max_score) {
            ElMessage.warning(`分数不能超过满分${currentItemInfo.value.max_score}`)
            return
        }
        batchGradeData.value.forEach(item => {
            item.score = score
        })
        ElMessage.success('已填充全部学生成绩')
    }).catch(() => {})
}

const clearAllScores = () => {
    ElMessageBox.confirm('确定清空所有成绩吗？', '提示', {
        type: 'warning'
    }).then(() => {
        batchGradeData.value.forEach(item => {
            item.score = null
            item.feedback = ''
        })
        ElMessage.success('已清空')
    }).catch(() => {})
}

const submitBatchGrades = async () => {
    savingBatchGrades.value = true
    try {
        // 批量提交成绩
        const updates = batchGradeData.value
            .filter(g => g.score !== null && g.score !== undefined)
            .map(g => ({
                student_id: g.student_id,
                score: g.score,
                feedback: g.feedback
            }))
        
        if (updates.length === 0) {
            ElMessage.warning('请至少录入一个学生的成绩')
            savingBatchGrades.value = false
            return
        }
        
        // 使用现有的批量录入API
        await api.post(`/grades/items/${currentItemInfo.value.id}/scores`, {
            scores: updates
        })
        
        ElMessage.success(`成功保存 ${updates.length} 个学生的成绩`)
        gradeInputDialogVisible.value = false
        
        // 刷新成绩列表
        await onGradeItemChange(selectedGradeItem.value)
    } catch (e) {
        ElMessage.error('保存失败: ' + (e.response?.data?.error || '未知错误'))
    } finally {
        savingBatchGrades.value = false
    }
}

const quickEditGrade = (row) => {
    ElMessageBox.prompt('请输入成绩', `修改 ${row.student_name} 的成绩`, {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^\d+(\.\d+)?$/,
        inputErrorMessage: '请输入有效的数字'
    }).then(async ({ value }) => {
        try {
            await api.post(`/grades/item/${currentItemInfo.value.id}/score`, {
                student_id: row.student_id,
                score: parseFloat(value)
            })
            ElMessage.success('成绩已更新')
            onGradeItemChange(selectedGradeItem.value)
        } catch (e) {
            ElMessage.error('更新失败: ' + (e.response?.data?.error || '未知错误'))
        }
    }).catch(() => {})
}

const calculateFinalGrades = async () => {
    try {
        await ElMessageBox.confirm('确定重新计算所有学生的总成绩吗？', '提示', {
            type: 'warning'
        })
        
        const res = await api.post(`/grades/class/${classId}/calculate-final`)
        ElMessage.success(`计算成功！已计算 ${res.data.count} 名学生的成绩`)
        await fetchFinalGrades()
    } catch (e) {
        if (e !== 'cancel') {
            ElMessage.error('计算失败: ' + (e.response?.data?.error || '未知错误'))
        }
    }
}

const viewStudentGradeDetail = async (row) => {
    currentStudentGradeDetail.value = {
        student_id: row.student_id,
        student_no: row.student_no,
        student_name: row.student_name,
        final_score: row.final_score,
        grade_level: row.grade_level,
        rank: row.rank
    }
    
    studentGradeDetail.value = { category_scores: row.category_scores }
    studentGradeDetailVisible.value = true
    loadingStudentDetail.value = true
    
    try {
        // 获取所有分类和成绩项（一次性获取）
        const resCategories = await api.get(`/grades/class/${classId}/categories`)
        const categories = resCategories.data || []
        
        // 获取学生所有成绩项的分数
        const resScores = await api.get(`/grades/class/${classId}/student/${row.student_id}/scores`)
        const scores = resScores.data || [] // 格式: [{ grade_item_id, score, ... }]
        
        // 组装数据 - categories已经包含了items
        studentGradeCategories.value = categories.map(category => {
            // 为每个item附加学生成绩
            const itemsWithScores = (category.items || []).map(item => {
                const scoreData = scores.find(s => s.grade_item_id === item.id)
                return {
                    ...item,
                    score: scoreData?.score
                }
            })
            
            return {
                ...category,
                items: itemsWithScores
            }
        })
    } catch (e) {
        ElMessage.error('加载学生成绩详情失败: ' + (e.response?.data?.error || '未知错误'))
    } finally {
        loadingStudentDetail.value = false
    }
}

const exportGrades = () => {
    if (!selectedGradeItem.value || !currentItemGrades.value.length) {
        ElMessage.warning('没有可导出的数据')
        return
    }
    
    // 生成CSV内容
    const headers = ['学号', '姓名', '成绩', '提交时间', '批改时间', '评语']
    const rows = currentItemGrades.value.map(g => [
        g.student_no,
        g.student_name,
        g.score !== null ? g.score : '',
        g.submitted_at || '',
        g.graded_at || '',
        g.feedback || ''
    ])
    
    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')
    
    // 添加BOM以支持中文
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${currentItemInfo.value.name}_成绩.csv`
    link.click()
    URL.revokeObjectURL(link.href)
    
    ElMessage.success('导出成功')
}

const exportFinalGrades = () => {
    if (!finalGradesData.value.length) {
        ElMessage.warning('没有可导出的数据')
        return
    }
    
    // 生成CSV内容
    const headers = ['排名', '学号', '姓名', ...gradeCategories.value.map(c => c.name), '总成绩', '等级']
    const rows = finalGradesData.value.map((s, index) => [
        index + 1,
        s.student_no,
        s.student_name,
        ...gradeCategories.value.map(c => s.category_scores?.[c.id]?.toFixed(1) || ''),
        s.final_score?.toFixed(1) || '',
        s.grade_level || ''
    ])
    
    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n')
    
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${courseInfo.value?.class_name || '班级'}_总成绩.csv`
    link.click()
    URL.revokeObjectURL(link.href)
    
    ElMessage.success('导出成功')
}

const getScoreTagType = (score, maxScore) => {
    const ratio = score / maxScore
    if (ratio >= 0.9) return 'success'
    if (ratio >= 0.8) return ''
    if (ratio >= 0.6) return 'warning'
    return 'danger'
}

const getFinalGradeClass = (score) => {
    if (!score) return ''
    if (score >= 90) return 'text-green-600'
    if (score >= 80) return 'text-blue-600'
    if (score >= 60) return ''
    return 'text-red-600'
}

const getGradeLevelType = (level) => {
    if (level === 'A' || level === 'A+') return 'success'
    if (level === 'B' || level === 'B+') return ''
    if (level === 'C') return 'warning'
    return 'danger'
}

const formatDateTime = (iso) => {
    if (!iso) return '-'
    return new Date(iso).toLocaleString('zh-CN')
}

const goToGradeConfig = () => {
    router.push(`/teacher/class/${classId}/grade-config`)
}

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

const formatTime = (iso) => new Date(iso).toLocaleString('zh-CN', { month:'numeric', day:'numeric', hour:'2-digit', minute:'2-digit' })
const formatDate = (iso) => new Date(iso).toLocaleDateString('zh-CN')

const getItemTypeName = (type) => {
    const typeMap = {
        'homework': '作业',
        'exam': '考试',
        'quiz': '测验',
        'project': '项目',
        'participation': '参与度',
        'other': '其他'
    }
    return typeMap[type] || type
}

const getItemTypeTagType = (type) => {
    const typeMap = {
        'homework': '',
        'exam': 'danger',
        'quiz': 'warning',
        'project': 'success',
        'participation': 'info',
        'other': ''
    }
    return typeMap[type] || ''
}

const getScoreColorClass = (score, maxScore) => {
    if (score === null || score === undefined) return ''
    const ratio = score / maxScore
    if (ratio >= 0.9) return 'text-green-600 font-bold'
    if (ratio >= 0.8) return 'text-blue-600'
    if (ratio >= 0.6) return 'text-gray-700'
    return 'text-red-500 font-bold'
}

const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

onMounted(() => {
    fetchClassInfo()
    fetchStudents()
    fetchAssignments()
    fetchMaterials()
    fetchAttendanceList()
    fetchGradeItems() // 初始加载成绩项列表
})

// 监听标签页切换
watch(activeTab, (newTab) => {
    if (newTab === 'statistics') {
        fetchTeachingStats()
    } else if (newTab === 'grades') {
        // 切换到成绩管理标签时，根据当前模式加载数据
        if (gradeViewMode.value === 'by_item') {
            fetchGradeItems()
        } else {
            fetchFinalGrades()
        }
    }
})
</script>

<style scoped>
.class-manage-container {
    padding: 20px;
}
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.text-lg { font-size: 18px; }
.font-bold { font-weight: bold; }
.text-secondary { color: #909399; }
.text-sm { font-size: 13px; }
.mr-2 { margin-right: 8px; }
.mr-4 { margin-right: 16px; }
.ml-2 { margin-left: 8px; }
.mb-2 { margin-bottom: 8px; }
.mb-3 { margin-bottom: 12px; }
.mb-4 { margin-bottom: 16px; }

.info-row {
    margin-top: 10px;
    color: #606266;
    font-size: 14px;
}

.stat-card {
    display: flex;
    align-items: center;
    gap: 16px;
}

.stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.stat-info {
    flex: 1;
}

.stat-value {
    font-size: 28px;
    font-weight: bold;
    color: #303133;
    line-height: 1;
    margin-bottom: 4px;
}

.stat-label {
    font-size: 14px;
    color: #909399;
}

.attendance-summary {
    padding: 10px;
}

.summary-item {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #EBEEF5;
}

.summary-item:last-child {
    border-bottom: none;
}

.summary-label {
    color: #606266;
    font-size: 14px;
}

.summary-value {
    font-weight: bold;
    font-size: 16px;
}

.attendance-chart {
    margin-top: 10px;
}

.chart-title {
    font-weight: 500;
    margin-bottom: 10px;
    color: #303133;
}

.empty-hint {
    text-align: center;
    color: #909399;
    padding: 40px 0;
}

.text-success { color: #67C23A; }
.text-danger { color: #F56C6C; }
.text-warning { color: #E6A23C; }

/* 成绩管理样式 */
.grade-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    background: #f5f7fa;
    border-radius: 4px;
}

.toolbar-right {
    display: flex;
    gap: 8px;
}

.empty-state {
    min-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.stat-item {
    display: flex;
    align-items: center;
    gap: 8px;
}

.stat-box {
    text-align: center;
    padding: 16px;
    background-color: #f5f7fa;
    border-radius: 8px;
}

.stat-box .stat-label {
    font-size: 14px;
    color: #909399;
    margin-bottom: 8px;
}

.stat-box .stat-value {
    font-size: 24px;
    font-weight: bold;
    color: #303133;
}

.stat-item .label {
    color: #606266;
    font-size: 14px;
}

.stat-item .value {
    font-weight: bold;
    font-size: 16px;
    color: #303133;
}

.text-primary { color: #409EFF; }
.text-gray-400 { color: #909399; }
.text-gray-500 { color: #909399; }
.text-gray-600 { color: #606266; }
.text-blue-600 { color: #409EFF; }
.text-green-600 { color: #67C23A; }
.text-red-600 { color: #F56C6C; }
.gap-3 { gap: 12px; }
.gap-6 { gap: 24px; }
.py-8 { padding-top: 32px; padding-bottom: 32px; }
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }

.truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
</style>
