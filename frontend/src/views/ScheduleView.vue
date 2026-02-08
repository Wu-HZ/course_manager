<template>
  <div class="page-container">
    <h2>课表查看</h2>

    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="排课结果">
          <el-select v-model="selectedResult" placeholder="选择排课结果" @change="loadTimetable">
            <el-option
              v-for="r in results"
              :key="r.id"
              :label="`#${r.id} - ${r.created_at} (${r.solve_status})`"
              :value="r.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="查看方式">
          <el-radio-group v-model="viewType" @change="loadTimetable">
            <el-radio-button value="class">按班级</el-radio-button>
            <el-radio-button value="teacher">按教师</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="viewType === 'class' ? '班级' : '教师'">
          <el-select v-model="selectedTarget" placeholder="请选择" @change="loadTimetable">
            <el-option
              v-for="t in targets"
              :key="t.id"
              :label="t.name"
              :value="t.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="entries.length" class="timetable-card">
      <template #header>
        <span>{{ currentTargetName }} 课表</span>
      </template>
      <TimetableGrid
        :entries="entries"
        :show-teacher="viewType === 'class'"
        :show-class="viewType === 'teacher'"
      />
    </el-card>

    <el-empty v-else-if="selectedResult && selectedTarget" description="暂无数据" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import TimetableGrid from '../components/TimetableGrid.vue'
import { getScheduleResults, getClassTimetable, getTeacherTimetable } from '../api/scheduler'
import { getClasses } from '../api/classes'
import { getTeachers } from '../api/teachers'

const results = ref([])
const classes = ref([])
const teachers = ref([])
const selectedResult = ref(null)
const viewType = ref('class')
const selectedTarget = ref(null)
const entries = ref([])

const targets = computed(() => viewType.value === 'class' ? classes.value : teachers.value)
const currentTargetName = computed(() => {
  const list = viewType.value === 'class' ? classes.value : teachers.value
  return list.find(t => t.id === selectedTarget.value)?.name || ''
})

const loadData = async () => {
  [results.value, classes.value, teachers.value] = await Promise.all([
    getScheduleResults(), getClasses(), getTeachers()
  ])
  // 自动选择最新激活的结果
  const active = results.value.find(r => r.is_active)
  if (active) selectedResult.value = active.id
  else if (results.value.length) selectedResult.value = results.value[0].id
}

const loadTimetable = async () => {
  if (!selectedResult.value || !selectedTarget.value) {
    entries.value = []
    return
  }
  try {
    if (viewType.value === 'class') {
      entries.value = await getClassTimetable(selectedResult.value, selectedTarget.value)
    } else {
      entries.value = await getTeacherTimetable(selectedResult.value, selectedTarget.value)
    }
  } catch (e) {
    entries.value = []
  }
}

watch(viewType, () => {
  selectedTarget.value = targets.value[0]?.id || null
})

watch(targets, (newTargets) => {
  if (newTargets.length && !selectedTarget.value) {
    selectedTarget.value = newTargets[0].id
  }
}, { immediate: true })

onMounted(async () => {
  await loadData()
  if (targets.value.length) {
    selectedTarget.value = targets.value[0].id
    loadTimetable()
  }
})
</script>

<style scoped>
.page-container { background: #fff; padding: 20px; border-radius: 4px; }
.page-container h2 { margin-bottom: 20px; }
.filter-card { margin-bottom: 20px; }
.timetable-card { margin-top: 20px; }
</style>
