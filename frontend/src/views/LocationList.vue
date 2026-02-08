<template>
  <div class="page-container">
    <div class="page-header">
      <h2>场地管理</h2>
      <el-button type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon> 添加场地
      </el-button>
    </div>

    <el-table :data="locations" stripe border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="场地名称" />
      <el-table-column prop="location_type_display" label="场地类型" />
      <el-table-column prop="capacity" label="同时容纳班数" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑场地' : '添加场地'" width="500px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="场地名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="场地类型" required>
          <el-select v-model="form.location_type">
            <el-option label="普通教室" value="NORMAL" />
            <el-option label="操场" value="PLAYGROUND" />
            <el-option label="实验室" value="LAB" />
            <el-option label="家政室" value="HOME_EC" />
          </el-select>
        </el-form-item>
        <el-form-item label="同时容纳班数" required>
          <el-input-number v-model="form.capacity" :min="1" :max="10" />
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
import { getLocations, createLocation, updateLocation, deleteLocation } from '../api/resources'

const locations = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = ref({ name: '', location_type: 'NORMAL', capacity: 1 })

const loadData = async () => {
  locations.value = await getLocations()
}

const showDialog = (row = null) => {
  if (row) {
    editingId.value = row.id
    form.value = { name: row.name, location_type: row.location_type, capacity: row.capacity }
  } else {
    editingId.value = null
    form.value = { name: '', location_type: 'NORMAL', capacity: 1 }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (editingId.value) {
      await updateLocation(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createLocation(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确定删除该场地?', '提示', { type: 'warning' })
  try {
    await deleteLocation(row.id)
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
