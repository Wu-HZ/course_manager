<template>
  <div class="page-container">
    <div class="page-header">
      <h2>课表锁定</h2>
      <div style="display: flex; align-items: center; gap: 10px;">
        <el-select v-model="selectedClassId" placeholder="选择班级" @change="loadLocks" style="width: 200px;">
          <el-option
            v-for="c in classes"
            :key="c.id"
            :label="c.name"
            :value="c.id"
          />
        </el-select>
        <el-button type="danger" @click="handleClearAll" :disabled="!selectedClassId">
          清空全部锁定
        </el-button>
      </div>
    </div>

    <div v-if="selectedClassId" class="schedule-grid">
      <table border="1" cellspacing="0">
        <thead>
          <tr>
            <th class="period-col">节次</th>
            <th v-for="(dayName, dayIdx) in dayNames" :key="dayIdx" class="day-col">{{ dayName }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="period in maxPeriods" :key="period">
            <td class="period-col">第{{ period }}节</td>
            <td
              v-for="(dayName, dayIdx) in dayNames"
              :key="dayIdx"
              class="cell"
              :class="getCellClass(dayIdx, period - 1)"
              @click="handleCellClick(dayIdx, period - 1)"
            >
              <template v-if="isSpecialSlot(dayIdx, period - 1)">
                <span class="special">{{ getSpecialLabel(dayIdx, period - 1) }}</span>
              </template>
              <template v-else-if="getLock(dayIdx, period - 1)">
                <div class="locked-cell">
                  <div class="subject-name">{{ getLock(dayIdx, period - 1).subject_name }}</div>
                  <div class="teacher-name" v-if="getLock(dayIdx, period - 1).teacher_name">
                    {{ getLock(dayIdx, period - 1).teacher_name }}
                  </div>
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
    <div v-else class="empty-tip">
      请先选择一个班级
    </div>

    <!-- 锁定设置弹窗 -->
    <el-dialog v-model="dialogVisible" title="设置课表锁定" width="400px">
      <el-form label-width="80px">
        <el-form-item label="时间">
          {{ dayNames[editDay] }} 第{{ editPeriod + 1 }}节
        </el-form-item>
        <el-form-item label="课程" required>
          <el-select v-model="editSubjectId" placeholder="选择课程" style="width: 100%;">
            <el-option
              v-for="s in subjects"
              :key="s.id"
              :label="s.name"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="教师">
          <el-select v-model="editTeacherId" clearable placeholder="留空使用授课分配" style="width: 100%;">
            <el-option
              v-for="t in teachers"
              :key="t.id"
              :label="t.name"
              :value="t.id"
            />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px">
            留空则自动使用授课分配中该班该课的教师
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button v-if="hasExistingLock" type="danger" @click="handleDeleteLock">删除锁定</el-button>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveLock">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const classes = ref([])
const subjects = ref([])
const teachers = ref([])
const selectedClassId = ref(null)
const locks = ref([])  // 当前班级的锁定列表

const dayNames = ['周一', '周二', '周三', '周四', '周五']
const periodsPerDay = { 0: 6, 1: 6, 2: 6, 3: 6, 4: 4 }
const maxPeriods = 6

// 特殊时段
const fridayClassMeeting = { day: 4, period: 3 }  // 周五第4节班会
const combinedSlots = [  // 校本课程时段
  { day: 1, period: 4 }, { day: 1, period: 5 },
  { day: 3, period: 4 }, { day: 3, period: 5 }
]

// 弹窗状态
const dialogVisible = ref(false)
const editDay = ref(0)
const editPeriod = ref(0)
const editSubjectId = ref(null)
const editTeacherId = ref(null)
const hasExistingLock = ref(false)

const loadBase = async () => {
  classes.value = await api.get('/classes/')
  subjects.value = await api.get('/subjects/')
  teachers.value = await api.get('/teachers/')
}

const loadLocks = async () => {
  if (!selectedClassId.value) {
    locks.value = []
    return
  }
  locks.value = await api.get(`/classes/${selectedClassId.value}/locks/`)
}

const getLock = (day, period) => {
  return locks.value.find(l => l.day === day && l.period === period)
}

const isSpecialSlot = (day, period) => {
  if (day === fridayClassMeeting.day && period === fridayClassMeeting.period) return true
  if (combinedSlots.some(s => s.day === day && s.period === period)) return true
  if (day === 4 && period >= 4) return true  // 周五无5、6节
  return false
}

const getSpecialLabel = (day, period) => {
  if (day === fridayClassMeeting.day && period === fridayClassMeeting.period) return '班会'
  if (combinedSlots.some(s => s.day === day && s.period === period)) return '校本课程'
  if (day === 4 && period >= 4) return '-'
  return ''
}

const getCellClass = (day, period) => {
  if (isSpecialSlot(day, period)) return 'special-cell'
  if (getLock(day, period)) return 'has-lock'
  return ''
}

const handleCellClick = (day, period) => {
  if (isSpecialSlot(day, period)) return
  const existing = getLock(day, period)
  editDay.value = day
  editPeriod.value = period
  if (existing) {
    editSubjectId.value = existing.subject
    editTeacherId.value = existing.teacher
    hasExistingLock.value = true
  } else {
    editSubjectId.value = null
    editTeacherId.value = null
    hasExistingLock.value = false
  }
  dialogVisible.value = true
}

const handleSaveLock = async () => {
  if (!editSubjectId.value) {
    ElMessage.warning('请选择课程')
    return
  }
  try {
    await api.post('/schedule-locks/set/', {
      school_class: selectedClassId.value,
      day: editDay.value,
      period: editPeriod.value,
      subject: editSubjectId.value,
      teacher: editTeacherId.value || null,
    })
    ElMessage.success('锁定成功')
    dialogVisible.value = false
    loadLocks()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleDeleteLock = async () => {
  try {
    await api.delete('/schedule-locks/delete/', {
      data: {
        school_class: selectedClassId.value,
        day: editDay.value,
        period: editPeriod.value,
      }
    })
    ElMessage.success('已取消锁定')
    dialogVisible.value = false
    loadLocks()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleClearAll = async () => {
  await ElMessageBox.confirm('确定清空所有班级的课表锁定?', '提示', { type: 'warning' })
  try {
    await api.delete('/schedule-locks/clear-all/')
    ElMessage.success('已清空')
    loadLocks()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(loadBase)
</script>

<style scoped>
.page-container { background: #fff; padding: 20px; border-radius: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; }

.schedule-grid { overflow-x: auto; }
.schedule-grid table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.schedule-grid th, .schedule-grid td {
  padding: 8px;
  text-align: center;
  border: 1px solid #dcdfe6;
  height: 60px;
}
.schedule-grid th { background: #f5f7fa; font-weight: bold; }

.period-col { width: 70px; background: #f5f7fa; font-weight: bold; }
.day-col { width: 18%; }

.cell { cursor: pointer; transition: background 0.2s; }
.cell:hover { background: #ecf5ff; }

.special-cell {
  background: #f0f0f0;
  color: #909399;
  cursor: default;
}
.special-cell:hover { background: #f0f0f0; }

.has-lock { background: #e1f3d8; }
.has-lock:hover { background: #d1ebc8; }

.locked-cell .subject-name { font-weight: bold; color: #67c23a; font-size: 14px; }
.locked-cell .teacher-name { color: #909399; font-size: 12px; margin-top: 2px; }

.empty-cell { color: #dcdfe6; font-size: 20px; }
.special { color: #909399; font-size: 12px; }

.empty-tip { text-align: center; color: #909399; padding: 60px 0; font-size: 16px; }
</style>
