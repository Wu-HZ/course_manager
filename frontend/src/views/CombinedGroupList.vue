<template>
  <div class="page-container">
    <div class="page-header">
      <h2>校本课程分组</h2>
      <div class="header-buttons">
        <el-button type="success" @click="handleAutoAssign">
          <el-icon><MagicStick /></el-icon> 自动分组
        </el-button>
        <el-button type="primary" @click="showDialog()">
          <el-icon><Plus /></el-icon> 添加分组
        </el-button>
      </div>
    </div>

    <el-alert
      title="说明：校本课程时段（周二/四下午），所有班级同时上课，由各分组内部自行安排教师。"
      type="info"
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>分组列表</span>
          </template>
          <el-table :data="groups" stripe border>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="分组名称" />
            <el-table-column label="教师数" width="80">
              <template #default="{ row }">
                {{ getGroupTeachers(row.id).length }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click="showDialog(row)">编辑</el-button>
                <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>各组教师分布</span>
          </template>
          <div v-for="group in groups" :key="group.id" class="group-section">
            <div class="group-title">{{ group.name }}</div>
            <div class="group-teachers">
              <el-tag
                v-for="teacher in getGroupTeachers(group.id)"
                :key="teacher.id"
                class="teacher-tag"
                closable
                @close="removeTeacherFromGroup(teacher)"
              >
                {{ teacher.name }}
              </el-tag>
              <span v-if="getGroupTeachers(group.id).length === 0" class="no-teacher">
                暂无教师
              </span>
            </div>
          </div>

          <el-divider />

          <div class="group-section">
            <div class="group-title">未分组教师</div>
            <div class="group-teachers">
              <el-tag
                v-for="teacher in unassignedTeachers"
                :key="teacher.id"
                class="teacher-tag"
                type="info"
              >
                {{ teacher.name }}
                <el-dropdown trigger="click" @command="(groupId) => assignTeacherToGroup(teacher, groupId)">
                  <el-icon class="assign-icon"><ArrowDown /></el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        v-for="g in groups"
                        :key="g.id"
                        :command="g.id"
                      >
                        {{ g.name }}
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </el-tag>
              <span v-if="unassignedTeachers.length === 0" class="no-teacher">
                全部已分组
              </span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑分组' : '添加分组'" width="400px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="分组名称" required>
          <el-input v-model="form.name" placeholder="如：校本课程第1组" />
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getCombinedGroups,
  createCombinedGroup,
  updateCombinedGroup,
  deleteCombinedGroup
} from '../api/resources'
import { getTeachers, updateTeacher } from '../api/teachers'
import api from '../api'

const groups = ref([])
const teachers = ref([])
const dialogVisible = ref(false)
const editingId = ref(null)
const form = ref({ name: '' })

const unassignedTeachers = computed(() => {
  return teachers.value.filter(t => !t.combined_class_group)
})

const getGroupTeachers = (groupId) => {
  return teachers.value.filter(t => t.combined_class_group === groupId)
}

const loadData = async () => {
  groups.value = await getCombinedGroups()
  teachers.value = await getTeachers()
}

const showDialog = (row = null) => {
  if (row) {
    editingId.value = row.id
    form.value = { name: row.name }
  } else {
    editingId.value = null
    form.value = { name: '' }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!form.value.name.trim()) {
    ElMessage.warning('请输入分组名称')
    return
  }
  try {
    if (editingId.value) {
      await updateCombinedGroup(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createCombinedGroup(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row) => {
  const teacherCount = getGroupTeachers(row.id).length
  if (teacherCount > 0) {
    await ElMessageBox.confirm(
      `该分组有 ${teacherCount} 位教师，删除后这些教师将变为未分组状态。确定删除?`,
      '提示',
      { type: 'warning' }
    )
  } else {
    await ElMessageBox.confirm('确定删除该分组?', '提示', { type: 'warning' })
  }
  try {
    await deleteCombinedGroup(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

const handleAutoAssign = async () => {
  if (groups.value.length === 0) {
    ElMessage.warning('请先创建分组')
    return
  }
  await ElMessageBox.confirm(
    '自动分组将把所有教师均匀分配到各分组，覆盖现有分配。确定继续?',
    '自动分组',
    { type: 'warning' }
  )
  try {
    await api.post('/combined-class-groups/auto-assign/')
    ElMessage.success('自动分组完成')
    loadData()
  } catch (e) {
    ElMessage.error(e.response?.data?.error || '自动分组失败')
  }
}

const assignTeacherToGroup = async (teacher, groupId) => {
  try {
    await updateTeacher(teacher.id, { ...teacher, combined_class_group: groupId })
    ElMessage.success(`已将 ${teacher.name} 分配到分组`)
    loadData()
  } catch (e) {
    ElMessage.error('分配失败')
  }
}

const removeTeacherFromGroup = async (teacher) => {
  try {
    await updateTeacher(teacher.id, { ...teacher, combined_class_group: null })
    ElMessage.success(`已将 ${teacher.name} 移出分组`)
    loadData()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-container { background: #fff; padding: 20px; border-radius: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; }
.header-buttons { display: flex; gap: 10px; }

.group-section { margin-bottom: 16px; }
.group-title {
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
  padding-left: 4px;
  border-left: 3px solid #409eff;
}
.group-teachers { display: flex; flex-wrap: wrap; gap: 8px; min-height: 32px; }
.teacher-tag { cursor: default; }
.no-teacher { color: #909399; font-size: 13px; }
.assign-icon { margin-left: 4px; cursor: pointer; }
</style>
