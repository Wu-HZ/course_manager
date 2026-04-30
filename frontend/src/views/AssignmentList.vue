<template>
  <div class="page-container">
    <div class="page-header">
      <h2>授课分配</h2>
      <div class="header-buttons">
        <el-button type="danger" @click="handleClearAll" :disabled="assignments.length === 0">
          <el-icon><Delete /></el-icon> 一键清空
        </el-button>
      </div>
    </div>

    <el-alert type="info" :closable="false" style="margin-bottom: 20px">
      <div class="legend">
        <span>这里只分配普通课程；班会由班主任承担，不适用当前班级年级的课程不可分配：</span>
        <span class="legend-item"><span class="cell-demo manual"></span> 手动指定（固定）</span>
        <span class="legend-item"><span class="cell-demo auto"></span> 自动分配</span>
        <span class="legend-item"><span class="cell-demo empty"></span> 未分配</span>
        <span class="legend-item"><span class="cell-demo unavailable"></span> 不适用</span>
      </div>
    </el-alert>

    <div class="grid-container" v-if="classes.length && filteredSubjects.length">
      <table class="assignment-grid">
        <thead>
          <tr>
            <th class="subject-col">课程 \ 班级</th>
            <th v-for="c in classes" :key="c.id">{{ c.name }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="subject in filteredSubjects" :key="subject.id">
            <td class="subject-col">
              <span>{{ subject.name }}</span>
              <el-tag v-if="subject.is_main_subject" type="danger" size="small" style="margin-left: 5px">主</el-tag>
            </td>
            <td
              v-for="c in classes"
              :key="`${subject.id}-${c.id}`"
              :class="getCellClass(c, subject)"
              @click="handleCellClick(c, subject)"
            >
              <template v-if="!isSubjectApplicableToClass(subject, c)">
                <span class="unavailable-cell">—</span>
              </template>
              <template v-else-if="getAssignment(c.id, subject.id)">
                <div class="cell-content">
                  <span class="teacher-name">{{ getAssignment(c.id, subject.id).teacher_name }}</span>
                </div>
              </template>
              <template v-else>
                <span class="empty-cell">+</span>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <el-empty v-else description="请先添加班级和课程数据" />

    <!-- 分配对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="450px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="班级">
          <el-input :value="currentClassName" disabled />
        </el-form-item>
        <el-form-item label="课程">
          <el-input :value="currentSubjectName" disabled />
        </el-form-item>
        <el-form-item label="教师" required>
          <el-select v-model="form.teacher" placeholder="请选择教师" filterable style="width: 100%">
            <el-option
              v-for="t in qualifiedTeachers"
              :key="t.id"
              :label="t.name"
              :value="t.id"
            />
          </el-select>
          <div v-if="qualifiedTeachers.length === 0" style="color: #f56c6c; font-size: 12px; margin-top: 5px">
            没有教师有此课程的资质
          </div>
        </el-form-item>
        <el-form-item label="固定分配">
          <el-switch v-model="form.is_manual" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            固定后不会被自动分配覆盖
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button v-if="editingId" type="danger" @click="handleDelete" style="float: left">删除</el-button>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :disabled="!form.teacher">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAssignments, createAssignment, updateAssignment, deleteAssignment } from '../api/resources'
import { getClasses } from '../api/classes'
import { getSubjects } from '../api/subjects'
import { getTeachers } from '../api/teachers'
import api from '../api'

const assignments = ref([])
const classes = ref([])
const subjects = ref([])
const teachers = ref([])
const qualifications = ref([])
const classMeetingName = ref('班会')
const dialogVisible = ref(false)
const editingId = ref(null)
const currentClassId = ref(null)
const currentSubjectId = ref(null)
const form = ref({ teacher: null, is_manual: true })

const getApplicableGrades = (subject) => {
  if (!subject?.applicable_grades) return []
  return String(subject.applicable_grades)
    .split(',')
    .map(item => Number(item.trim()))
    .filter(Number.isInteger)
}

const isManagedAssignmentSubject = (subject) => (
  Boolean(subject) &&
  !subject.is_combined_class &&
  subject.name !== classMeetingName.value
)

const isSubjectApplicableToClass = (subject, schoolClass) => {
  if (!subject || !schoolClass) return false
  const grades = getApplicableGrades(subject)
  return grades.length === 0 || grades.includes(schoolClass.grade)
}

// 过滤掉班会课、校本课程和对当前所有班级都不适用的课程
const filteredSubjects = computed(() => {
  return subjects.value.filter(subject => (
    isManagedAssignmentSubject(subject) &&
    classes.value.some(schoolClass => isSubjectApplicableToClass(subject, schoolClass))
  ))
})

const classById = computed(() => Object.fromEntries(
  classes.value.map(schoolClass => [schoolClass.id, schoolClass])
))

const subjectById = computed(() => Object.fromEntries(
  subjects.value.map(subject => [subject.id, subject])
))

// 构建分配映射表
const assignmentMap = computed(() => {
  const map = {}
  for (const a of assignments.value) {
    const schoolClass = classById.value[a.school_class]
    const subject = subjectById.value[a.subject]
    if (!isManagedAssignmentSubject(subject) || !isSubjectApplicableToClass(subject, schoolClass)) {
      continue
    }
    map[`${a.school_class}-${a.subject}`] = a
  }
  return map
})

// 获取单元格的分配
const getAssignment = (classId, subjectId) => {
  return assignmentMap.value[`${classId}-${subjectId}`]
}

// 获取单元格样式
const getCellClass = (schoolClass, subject) => {
  if (!isSubjectApplicableToClass(subject, schoolClass)) {
    return 'cell unavailable'
  }
  const a = getAssignment(schoolClass.id, subject.id)
  if (!a) return 'cell empty'
  return a.is_manual ? 'cell manual' : 'cell auto'
}

// 当前选中的班级名称
const currentClassName = computed(() => {
  const c = classes.value.find(c => c.id === currentClassId.value)
  return c ? c.name : ''
})

// 当前选中的课程名称
const currentSubjectName = computed(() => {
  const s = subjects.value.find(s => s.id === currentSubjectId.value)
  return s ? s.name : ''
})

// 对话框标题
const dialogTitle = computed(() => {
  return editingId.value ? '编辑授课分配' : '指定授课教师'
})

// 获取有当前课程资质的教师
const qualifiedTeachers = computed(() => {
  if (!currentSubjectId.value) return []
  const qualified = qualifications.value
    .filter(q => q.subject === currentSubjectId.value)
    .map(q => q.teacher)
  return teachers.value.filter(t => qualified.includes(t.id))
})

const loadData = async () => {
  try {
    const [assignmentList, classList, subjectList, teacherList, qualificationList, settings] = await Promise.all([
      getAssignments(),
      getClasses(),
      getSubjects(),
      getTeachers(),
      api.get('/teacher-qualifications/'),
      api.get('/scheduler-settings/'),
    ])
    assignments.value = assignmentList
    classes.value = classList
    subjects.value = subjectList
    teachers.value = teacherList
    qualifications.value = qualificationList
    classMeetingName.value = settings.class_meeting_name || '班会'
  } catch (e) {
    console.error('加载数据失败:', e)
    ElMessage.error('加载数据失败')
  }
}

// 点击单元格
const handleCellClick = (schoolClass, subject) => {
  if (!isManagedAssignmentSubject(subject) || !isSubjectApplicableToClass(subject, schoolClass)) {
    return
  }

  currentClassId.value = schoolClass.id
  currentSubjectId.value = subject.id

  const existing = getAssignment(schoolClass.id, subject.id)
  if (existing) {
    editingId.value = existing.id
    form.value = {
      teacher: existing.teacher,
      is_manual: existing.is_manual
    }
  } else {
    editingId.value = null
    form.value = { teacher: null, is_manual: true }
  }

  dialogVisible.value = true
}

const handleSave = async () => {
  const data = {
    school_class: currentClassId.value,
    subject: currentSubjectId.value,
    teacher: form.value.teacher,
    is_manual: form.value.is_manual
  }

  try {
    if (editingId.value) {
      await updateAssignment(editingId.value, data)
      ElMessage.success('更新成功')
    } else {
      await createAssignment(data)
      ElMessage.success('分配成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    const detail = e.response?.data?.subject?.[0] || e.response?.data?.detail
    ElMessage.error(detail || '操作失败')
  }
}

const handleDelete = async () => {
  await ElMessageBox.confirm('确定删除该分配?', '提示', { type: 'warning' })
  try {
    await deleteAssignment(editingId.value)
    ElMessage.success('删除成功')
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

const handleClearAll = async () => {
  await ElMessageBox.confirm(
    `确定清空全部 ${assignments.value.length} 条授课分配记录？此操作不可恢复！`,
    '一键清空',
    { type: 'warning', confirmButtonText: '确定清空', cancelButtonText: '取消' }
  )
  try {
    const res = await api.delete('/class-subject-teachers/clear-all/')
    ElMessage.success(`已清空 ${res.deleted} 条记录`)
    loadData()
  } catch (e) {
    ElMessage.error('清空失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-container { background: #fff; padding: 20px; border-radius: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; }
.header-buttons { display: flex; gap: 10px; }

.legend {
  display: flex;
  align-items: center;
  gap: 20px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}
.cell-demo {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 3px;
  border: 1px solid #dcdfe6;
}
.cell-demo.manual { background: #409eff; }
.cell-demo.auto { background: #67c23a; }
.cell-demo.empty { background: #f5f7fa; }
.cell-demo.unavailable { background: #eef1f5; }

.grid-container {
  overflow-x: auto;
}

.assignment-grid {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.assignment-grid th,
.assignment-grid td {
  border: 1px solid #dcdfe6;
  padding: 8px;
  text-align: center;
  min-width: 80px;
}

.assignment-grid th {
  background: #f5f7fa;
  font-weight: bold;
  position: sticky;
  top: 0;
}

.subject-col {
  min-width: 120px !important;
  text-align: left !important;
  background: #f5f7fa;
  position: sticky;
  left: 0;
  z-index: 1;
}

.cell {
  cursor: pointer;
  transition: all 0.2s;
  height: 50px;
  vertical-align: middle;
}

.cell:hover {
  opacity: 0.8;
  box-shadow: inset 0 0 0 2px #409eff;
}

.cell.empty {
  background: #fafafa;
}

.cell.manual {
  background: #409eff;
  color: #fff;
}

.cell.auto {
  background: #67c23a;
  color: #fff;
}

.cell.unavailable {
  background: #f2f4f7;
  color: #c0c4cc;
  cursor: not-allowed;
}

.cell.unavailable:hover {
  opacity: 1;
  box-shadow: none;
}

.cell-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.teacher-name {
  font-size: 13px;
  font-weight: 500;
}

.empty-cell {
  color: #c0c4cc;
  font-size: 20px;
}

.unavailable-cell {
  color: #c0c4cc;
  font-size: 18px;
}
</style>
