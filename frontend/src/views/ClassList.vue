<template>
  <div class="page-container">
    <div class="page-header">
      <h2>班级管理</h2>
      <el-button type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon> 添加班级
      </el-button>
    </div>

    <el-table :data="classes" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="班级名称" />
      <el-table-column prop="grade" label="年级" />
      <el-table-column prop="homeroom_teacher_name" label="班主任" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑班级' : '添加班级'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="班级名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="年级" required>
          <el-input-number v-model="form.grade" :min="1" :max="9" />
        </el-form-item>
        <el-form-item label="班主任">
          <el-select v-model="form.homeroom_teacher" clearable placeholder="请选择">
            <el-option
              v-for="t in teachers"
              :key="t.id"
              :label="t.name"
              :value="t.id"
            />
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
import { getClasses, createClass, updateClass, deleteClass } from '../api/classes'
import { getTeachers } from '../api/teachers'

const classes = ref([])
const teachers = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = ref({ name: '', grade: 1, homeroom_teacher: null })

const loadData = async () => {
  classes.value = await getClasses()
  teachers.value = await getTeachers()
}

const showDialog = (row = null) => {
  if (row) {
    editingId.value = row.id
    form.value = { name: row.name, grade: row.grade, homeroom_teacher: row.homeroom_teacher }
  } else {
    editingId.value = null
    form.value = { name: '', grade: 1, homeroom_teacher: null }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (editingId.value) {
      await updateClass(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createClass(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确定删除该班级?', '提示', { type: 'warning' })
  try {
    await deleteClass(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-container { background: #fff; padding: 20px; border-radius: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; }
</style>
