<template>
  <div class="page-container">
    <div class="page-header">
      <h2>教师禁排日管理</h2>
      <el-button type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon> 添加禁排时段
      </el-button>
    </div>

    <el-table :data="blockedTimes" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="teacher_name" label="教师姓名" />
      <el-table-column prop="day_display" label="星期" />
      <el-table-column prop="period_type_display" label="时段" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑禁排时段' : '添加禁排时段'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="教师" required>
          <el-select v-model="form.teacher" filterable placeholder="请选择教师">
            <el-option
              v-for="t in teachers"
              :key="t.id"
              :label="t.name"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="星期" required>
          <el-select v-model="form.day">
            <el-option label="周一" :value="0" />
            <el-option label="周二" :value="1" />
            <el-option label="周三" :value="2" />
            <el-option label="周四" :value="3" />
            <el-option label="周五" :value="4" />
          </el-select>
        </el-form-item>
        <el-form-item label="时段" required>
          <el-select v-model="form.period_type">
            <el-option label="上午" value="am" />
            <el-option label="下午" value="pm" />
            <el-option label="全天" value="all" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getBlockedTimes, createBlockedTime, updateBlockedTime, deleteBlockedTime } from '../api/resources'
import { getTeachers } from '../api/teachers'

const blockedTimes = ref([])
const teachers = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = ref({ teacher: null, day: 0, period_type: 'am' })

const loadData = async () => {
  blockedTimes.value = await getBlockedTimes()
}

const loadTeachers = async () => {
  teachers.value = await getTeachers()
}

const showDialog = (row = null) => {
  if (row) {
    editingId.value = row.id
    form.value = { teacher: row.teacher, day: row.day, period_type: row.period_type }
  } else {
    editingId.value = null
    form.value = { teacher: null, day: 0, period_type: 'am' }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!form.value.teacher) {
    ElMessage.warning('请选择教师')
    return
  }
  try {
    if (editingId.value) {
      await updateBlockedTime(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createBlockedTime(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确定删除该禁排时段?', '提示', { type: 'warning' })
  try {
    await deleteBlockedTime(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadData()
  loadTeachers()
})
</script>

<style scoped>
.page-container { background: #fff; padding: 20px; border-radius: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; }
</style>
