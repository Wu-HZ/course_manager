<template>
  <div class="timetable-grid">
    <table>
      <thead>
        <tr>
          <th class="day-col"></th>
          <th v-for="period in maxPeriods" :key="period">第{{ period }}节</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="day in days" :key="day.key">
          <td class="day-col">{{ day.label }}</td>
          <td
            v-for="period in maxPeriods"
            :key="`${day.key}-${period}`"
            :class="getCellClass(day.index, period - 1)"
          >
            <div v-if="getEntry(day.index, period - 1)" class="cell-content">
              <div class="subject">{{ getEntry(day.index, period - 1).subject_name }}</div>
              <div class="teacher" v-if="showTeacher">{{ getEntry(day.index, period - 1).teacher_name }}</div>
              <div class="class" v-if="showClass">{{ getEntry(day.index, period - 1).school_class_name }}</div>
            </div>
            <div v-else-if="isDisabled(day.index, period - 1)" class="disabled">-</div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  entries: { type: Array, default: () => [] },
  showTeacher: { type: Boolean, default: true },
  showClass: { type: Boolean, default: false }
})

const days = [
  { key: 'mon', label: '周一', index: 0 },
  { key: 'tue', label: '周二', index: 1 },
  { key: 'wed', label: '周三', index: 2 },
  { key: 'thu', label: '周四', index: 3 },
  { key: 'fri', label: '周五', index: 4 }
]

const periodsPerDay = { 0: 6, 1: 6, 2: 6, 3: 6, 4: 4 }
const maxPeriods = 6

const entryMap = computed(() => {
  const map = {}
  props.entries.forEach(e => {
    map[`${e.day}-${e.period}`] = e
  })
  return map
})

const getEntry = (day, period) => entryMap.value[`${day}-${period}`]

const isDisabled = (day, period) => period >= periodsPerDay[day]

const getCellClass = (day, period) => {
  const entry = getEntry(day, period)
  if (entry?.is_locked) return 'locked'
  if (isDisabled(day, period)) return 'disabled-cell'
  if (period < 4) return 'am'
  return 'pm'
}
</script>

<style scoped>
.timetable-grid table {
  width: 100%;
  border-collapse: collapse;
}

.timetable-grid th,
.timetable-grid td {
  border: 1px solid #dcdfe6;
  padding: 8px;
  text-align: center;
  min-width: 90px;
  height: 70px;
}

.timetable-grid th {
  background: #f5f7fa;
  font-weight: bold;
}

.day-col {
  width: 60px;
  background: #f5f7fa !important;
  font-weight: bold;
}

.cell-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.subject {
  font-weight: bold;
  color: #303133;
}

.teacher, .class {
  font-size: 12px;
  color: #909399;
}

.am { background: #f0f9eb; }
.pm { background: #fdf6ec; }
.locked { background: #fef0f0; }
.disabled-cell { background: #f5f5f5; }
.disabled { color: #c0c4cc; }
</style>
