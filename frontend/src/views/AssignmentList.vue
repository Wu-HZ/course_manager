<template>
  <div class="page-container">
    <div class="page-header">
      <h2>授课分配</h2>
      <div class="header-buttons">
        <el-button type="danger" @click="handleClearAll" :disabled="assignments.length === 0">
          <el-icon><Delete /></el-icon> 一键清空
        </el-button>
        <el-button type="primary" @click="showDialog()">
          <el-icon><Plus /></el-icon> 手动指定
        </el-button>
      </div>
    </div>

    <el-alert type="info" :closable="false" style="margin-bottom: 20px">
      手动指定的分配优先于自动分配。自动分配的记录会在排课时根据教师资质自动生成。
    </el-alert>

    <el-table :data="assignments" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="school_class_name" label="班级" />
      <el-table-column prop="subject_name" label="课程" />
      <el-table-column prop="teacher_name" label="教师" />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_manual ? 'warning' : 'success'" size="small">
            {{ row.is_manual ? '手动' : '自动' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑分配' : '手动指定授课'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="班级" required>
          <el-select v-model="form.school_class" placeholder="请选择班级" filterable>
            <el-option v-for="c in classes" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程" required>
          <el-select v-model="form.subject" placeholder="请选择课程" filterable>
            <el-option v-for="s in subjects" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="教师" required>
          <el-select v-model="form.teacher" placeholder="请选择教师" filterable>
            <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="手动指定">
          <el-switch v-model="form.is_manual" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            手动指定的分配不会被自动分配覆盖
          </span>
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
import { getAssignments, createAssignment, updateAssignment, deleteAssignment } from '../api/resources'
import { getClasses } from '../api/classes'
import { getSubjects } from '../api/subjects'
import { getTeachers } from '../api/teachers'
import api from '../api'

const assignments = ref([])
const classes = ref([])
const subjects = ref([])
const teachers = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = ref({ school_class: null, subject: null, teacher: null, is_manual: true })

const loadData = async () => {
  [assignments.value, classes.value, subjects.value, teachers.value] = await Promise.all([
    getAssignments(), getClasses(), getSubjects(), getTeachers()
  ])
}

const showDialog = (row = null) => {
  if (row) {
    editingId.value = row.id
    form.value = {
      school_class: row.school_class,
      subject: row.subject,
      teacher: row.teacher,
      is_manual: row.is_manual
    }
  } else {
    editingId.value = null
    form.value = { school_class: null, subject: null, teacher: null, is_manual: true }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (editingId.value) {
      await updateAssignment(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createAssignment(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确定删除该分配?', '提示', { type: 'warning' })
  try {
    await deleteAssignment(row.id)
    ElMessage.success('删除成功')
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
</style>
