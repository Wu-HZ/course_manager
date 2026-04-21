<template>
  <div class="page-container">
    <h2>课表查看</h2>

    <el-card class="filter-card">
      <div class="filter-row">
        <ScheduleResultPicker
          v-model="selectedResult"
          :current-result="currentResult"
          @refresh="onPickerRefresh"
        />
      </div>
      <el-form :inline="true" style="margin-top: 12px;">
        <el-form-item label="查看方式">
          <el-radio-group v-model="viewType" @change="loadAllTimetables">
            <el-radio-button value="class">按班级</el-radio-button>
            <el-radio-button value="teacher">按教师</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item>
          <el-button type="success" :disabled="!allTimetables.length" @click="exportToExcel">导出 Excel</el-button>
          <el-button type="primary" :disabled="!allTimetables.length" @click="exportToJSON">导出数据 (JSON)</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 教师课时柱状图 -->
    <el-card v-if="viewType === 'teacher' && allTimetables.length" class="chart-card">
      <template #header>
        <span>教师课时分布</span>
      </template>
      <v-chart :option="teacherChartOption" style="height: 300px; cursor: pointer;" autoresize @click="onChartClick" />
    </el-card>

    <!-- 所有课表 -->
    <template v-if="allTimetables.length">
      <el-card v-for="item in allTimetables" :key="item.id" :ref="el => setTimetableRef(item.id, el)" class="timetable-card">
        <template #header>
          <div class="timetable-header">
            <span>{{ item.name }} 课表</span>
            <span class="weekly-hours">
              周课时 {{ item.stats.total }}
              （普通课程 {{ item.stats.normal }} + 校本课程 {{ item.stats.combined }} + 班会课 {{ item.stats.meeting }}）
            </span>
          </div>
        </template>
        <TimetableGrid
          :entries="item.entries"
          :show-teacher="viewType === 'class'"
          :show-class="viewType === 'teacher'"
        />
      </el-card>
    </template>

    <el-empty v-else-if="selectedResult" description="暂无数据" />

    <!-- 校本课程分组分配表 -->
    <el-card v-if="combinedAssignments && Object.keys(combinedAssignments).length" class="combined-card">
      <template #header>
        <span>校本课程教师分组</span>
      </template>
      <el-table :data="combinedAssignmentsList" stripe border>
        <el-table-column prop="groupName" label="分组" width="120" />
        <el-table-column label="周二">
          <template #default="{ row }">
            <el-tag v-for="t in row.tuesday" :key="t" style="margin-right: 5px;">{{ t }}</el-tag>
            <span v-if="!row.tuesday.length" style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column label="周四">
          <template #default="{ row }">
            <el-tag v-for="t in row.thursday" :key="t" style="margin-right: 5px;">{{ t }}</el-tag>
            <span v-if="!row.thursday.length" style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column label="合计" width="80" align="center">
          <template #default="{ row }">
            {{ row.tuesday.length + row.thursday.length }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 送教分组表 -->
    <el-card v-if="travelGroupList.length" class="combined-card">
      <template #header>
        <span>送教分组</span>
      </template>
      <el-table :data="travelGroupList" stripe border>
        <el-table-column prop="name" label="分组" width="120" />
        <el-table-column prop="dayOffDisplay" label="禁排日" width="100" />
        <el-table-column label="教师">
          <template #default="{ row }">
            <el-tag v-for="t in row.teachers" :key="t" style="margin-right: 5px;">{{ t }}</el-tag>
            <span v-if="!row.teachers.length" style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column label="人数" width="80" align="center">
          <template #default="{ row }">
            {{ row.teachers.length }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import * as XLSX from 'xlsx'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import TimetableGrid from '../components/TimetableGrid.vue'
import ScheduleResultPicker from '../components/ScheduleResultPicker.vue'
import {
  getClassTimetable, getTeacherTimetable,
  getActiveSchedule, getScheduleResult
} from '../api/scheduler'
import { getClasses } from '../api/classes'
import { getTeachers } from '../api/teachers'
import { getTravelGroups, getAssignments } from '../api/resources'
import { getSubjects } from '../api/subjects'
import { buildScheduleResultFileLabel } from '../utils/scheduleResults'

// 注册 ECharts 组件
use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent])

const classes = ref([])
const teachers = ref([])
const selectedResult = ref(null)
const currentResult = ref(null)
const viewType = ref('class')
const allTimetables = ref([])
const travelGroups = ref([])
const timetableRefs = {}

const setTimetableRef = (id, el) => {
  if (el) {
    timetableRefs[id] = el
  } else {
    delete timetableRefs[id]
  }
}

const targets = computed(() => viewType.value === 'class' ? classes.value : teachers.value)
const combinedAssignments = computed(() => currentResult.value?.combined_class_assignments || {})

// 按课时量从大到小排序（图表用）
const sortedTimetables = computed(() =>
  [...allTimetables.value].sort((a, b) => b.stats.total - a.stats.total)
)

// 教师课时柱状图配置
const teacherChartOption = computed(() => {
  const sorted = sortedTimetables.value

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const data = params[0]
        const item = sorted[data.dataIndex]
        return `${item.name}<br/>
          普通课程: ${item.stats.normal} 节<br/>
          校本课程: ${item.stats.combined} 节<br/>
          班会课: ${item.stats.meeting} 节<br/>
          <strong>合计: ${item.stats.total} 节</strong>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: sorted.map(t => t.name),
      axisLabel: {
        rotate: 30,
        fontSize: 12
      }
    },
    yAxis: {
      type: 'value',
      name: '课时数',
      minInterval: 1
    },
    series: [
      {
        name: '普通课程',
        type: 'bar',
        stack: 'total',
        data: sorted.map(t => t.stats.normal),
        itemStyle: { color: '#409eff' }
      },
      {
        name: '校本课程',
        type: 'bar',
        stack: 'total',
        data: sorted.map(t => t.stats.combined),
        itemStyle: { color: '#67c23a' }
      },
      {
        name: '班会课',
        type: 'bar',
        stack: 'total',
        data: sorted.map(t => t.stats.meeting),
        itemStyle: { color: '#e6a23c' },
        label: {
          show: true,
          position: 'top',
          formatter: (params) => sorted[params.dataIndex].stats.total,
          fontSize: 12,
          color: '#606266'
        }
      }
    ],
    legend: {
      data: ['普通课程', '校本课程', '班会课'],
      top: 0
    }
  }
})

// 点击柱状图跳转到对应教师课表
const onChartClick = (params) => {
  const sorted = sortedTimetables.value
  const item = sorted[params.dataIndex]
  if (!item) return
  const el = timetableRefs[item.id]
  if (el?.$el) {
    el.$el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 转换为表格数据格式
const combinedAssignmentsList = computed(() => {
  // 新格式: {"分组名": {"周二": ["教师"], "周四": ["教师"]}, ...}
  return Object.entries(combinedAssignments.value).map(([groupName, dayData]) => {
    // 兼容新旧格式
    if (typeof dayData === 'object' && !Array.isArray(dayData)) {
      return {
        groupName,
        tuesday: dayData['周二'] || [],
        thursday: dayData['周四'] || []
      }
    }
    // 旧格式兼容（数组形式）
    return {
      groupName,
      tuesday: dayData || [],
      thursday: []
    }
  })
})

// 送教分组表格数据
const travelGroupList = computed(() => {
  const teachersByGroup = {}
  for (const t of teachers.value) {
    if (t.travel_group) {
      if (!teachersByGroup[t.travel_group]) {
        teachersByGroup[t.travel_group] = []
      }
      teachersByGroup[t.travel_group].push(t.name)
    }
  }
  return travelGroups.value.map(g => ({
    name: g.name,
    dayOffDisplay: g.day_off_display,
    teachers: teachersByGroup[g.id] || []
  }))
})

// 计算单个课表的周课时统计
const calcStats = (entries) => {
  const total = entries.length
  let meeting = 0
  let combined = 0

  for (const e of entries) {
    if (e.day === 4 && e.period === 3) {
      meeting++
    } else if (
      e.teacher === null ||
      e.teacher_name === null ||
      (e.subject_name && e.subject_name.startsWith('校本课程')) ||
      e.school_class_name === '(全年级)'
    ) {
      combined++
    }
  }

  const normal = total - meeting - combined
  return { total, normal, combined, meeting }
}

const loadData = async () => {
  const [classList, teacherList, travelGroupList] = await Promise.all([
    getClasses(), getTeachers(), getTravelGroups()
  ])
  classes.value = classList
  teachers.value = teacherList
  travelGroups.value = travelGroupList

  // 初始：尝试取当前激活的排课结果
  try {
    const active = await getActiveSchedule()
    currentResult.value = active
    selectedResult.value = active?.id ?? null
  } catch {
    currentResult.value = null
    selectedResult.value = null
  }
}

const loadCurrentResult = async (id) => {
  if (!id) {
    currentResult.value = null
    return
  }
  try {
    currentResult.value = await getScheduleResult(id)
  } catch {
    currentResult.value = null
  }
}

const onPickerRefresh = async () => {
  // 抽屉里做过改名/星标等操作 → 同步刷新摘要
  if (selectedResult.value) {
    await loadCurrentResult(selectedResult.value)
  }
}

watch(selectedResult, async (nextId, prevId) => {
  if (nextId === prevId) return
  await loadCurrentResult(nextId)
  await loadAllTimetables()
})

const loadAllTimetables = async () => {
  if (!selectedResult.value) {
    allTimetables.value = []
    return
  }

  const targetList = targets.value
  const fetchFn = viewType.value === 'class' ? getClassTimetable : getTeacherTimetable

  // 并行加载所有课表
  const promises = targetList.map(async (t) => {
    try {
      const entries = await fetchFn(selectedResult.value, t.id)
      return {
        id: t.id,
        name: t.name,
        entries,
        stats: calcStats(entries)
      }
    } catch (e) {
      return {
        id: t.id,
        name: t.name,
        entries: [],
        stats: { total: 0, normal: 0, combined: 0, meeting: 0 }
      }
    }
  })

  allTimetables.value = await Promise.all(promises)
}

const exportToExcel = () => {
  const wb = XLSX.utils.book_new()
  const dayLabels = ['周一', '周二', '周三', '周四', '周五']
  const periodsPerDay = { 0: 6, 1: 6, 2: 6, 3: 6, 4: 4 }
  const maxPeriods = 6
  const header = ['', '第1节', '第2节', '第3节', '第4节', '第5节', '第6节']

  for (const item of allTimetables.value) {
    const entryMap = {}
    for (const e of item.entries) {
      entryMap[`${e.day}-${e.period}`] = e
    }

    const rows = [header]
    for (let day = 0; day < 5; day++) {
      const row = [dayLabels[day]]
      for (let period = 0; period < maxPeriods; period++) {
        const entry = entryMap[`${day}-${period}`]
        if (entry) {
          const line1 = entry.subject_name || ''
          const line2 = viewType.value === 'class'
            ? (entry.teacher_name || '')
            : (entry.school_class_name || '')
          row.push(line2 ? `${line1}\n${line2}` : line1)
        } else if (period >= periodsPerDay[day]) {
          row.push('-')
        } else {
          row.push('')
        }
      }
      rows.push(row)
    }

    const ws = XLSX.utils.aoa_to_sheet(rows)
    // 设置列宽
    ws['!cols'] = [
      { wch: 6 },
      ...Array(maxPeriods).fill({ wch: 14 })
    ]
    const sheetName = item.name.substring(0, 31) // Excel sheet 名最长 31 字符
    XLSX.utils.book_append_sheet(wb, ws, sheetName)
  }

  const viewLabel = viewType.value === 'class' ? '按班级' : '按教师'
  const fileLabel = buildScheduleResultFileLabel(currentResult.value, `课表_${selectedResult.value}`)
  XLSX.writeFile(wb, `${fileLabel}_${viewLabel}.xlsx`)
}

const exportToJSON = async () => {
  const [subjects, assignments] = await Promise.all([
    getSubjects(),
    getAssignments()
  ])

  // 汇总所有班级的课表条目（按班级维度，去重完整）
  const classTimetables = viewType.value === 'class'
    ? allTimetables.value
    : await Promise.all(
        classes.value.map(async (c) => {
          try {
            const entries = await getClassTimetable(selectedResult.value, c.id)
            return { id: c.id, name: c.name, entries }
          } catch { return { id: c.id, name: c.name, entries: [] } }
        })
      )

  // 合并所有 entries，用 set 去重（同一个 entry 可能出现在班级和教师视图中）
  const allEntries = []
  const seen = new Set()
  for (const t of classTimetables) {
    for (const e of t.entries) {
      const key = `${e.day}-${e.period}-${e.school_class ?? t.id}`
      if (!seen.has(key)) {
        seen.add(key)
        allEntries.push({
          day: e.day,
          period: e.period,
          classId: e.school_class,
          className: e.school_class_name,
          teacherId: e.teacher,
          teacherName: e.teacher_name,
          subjectId: e.subject,
          subjectName: e.subject_name,
          isLocked: e.is_locked || false
        })
      }
    }
  }

  const data = {
    version: 1,
    exportedAt: new Date().toISOString(),
    resultId: selectedResult.value,
    classes: classes.value.map(c => ({
      id: c.id,
      name: c.name,
      grade: c.grade,
      homeroomTeacherId: c.homeroom_teacher,
      homeroomTeacherName: c.homeroom_teacher_name
    })),
    teachers: teachers.value.map(t => ({
      id: t.id,
      name: t.name,
      travelGroup: t.travel_group,
      travelGroupName: t.travel_group_name,
      combinedClassGroup: t.combined_class_group,
      combinedClassGroupName: t.combined_class_group_name,
      combinedClassDay: t.combined_class_day,
      excludeFromCombined: t.exclude_from_combined,
      minWeeklyHours: t.min_weekly_hours,
      maxWeeklyHours: t.max_weekly_hours
    })),
    subjects: subjects.map(s => ({
      id: s.id,
      name: s.name,
      weeklyHours: s.weekly_hours,
      isAmPreferred: s.is_am_preferred,
      allowConsecutive: s.allow_consecutive,
      maxDailyLimit: s.max_daily_limit,
      locationType: s.location_type,
      isCombinedClass: s.is_combined_class,
      applicableGrades: s.applicable_grades,
      avoidFirstPeriod: s.avoid_first_period,
      isMainSubject: s.is_main_subject,
      maxTeacherClasses: s.max_teacher_classes
    })),
    assignments: assignments.map(a => ({
      id: a.id,
      classId: a.school_class,
      className: a.school_class_name,
      subjectId: a.subject,
      subjectName: a.subject_name,
      teacherId: a.teacher,
      teacherName: a.teacher_name
    })),
    travelGroups: travelGroups.value.map(g => ({
      id: g.id,
      name: g.name,
      dayOff: g.day_off,
      dayOffDisplay: g.day_off_display
    })),
    combinedAssignments: combinedAssignments.value,
    entries: allEntries
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const fileLabel = buildScheduleResultFileLabel(currentResult.value, `课表_${selectedResult.value}`)
  a.download = `课表数据_${fileLabel}.json`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(loadData)
</script>

<style scoped>
.page-container { background: #fff; padding: 20px; border-radius: 4px; }
.page-container h2 { margin-bottom: 20px; }
.filter-card { margin-bottom: 20px; }
.chart-card { margin-bottom: 20px; }
.timetable-card { margin-top: 20px; }
.combined-card { margin-top: 20px; }
.timetable-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.weekly-hours {
  font-size: 14px;
  color: #606266;
  font-weight: normal;
}
.filter-row {
  margin-bottom: 4px;
}
</style>
