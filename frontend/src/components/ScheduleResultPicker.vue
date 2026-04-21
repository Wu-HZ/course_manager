<template>
  <div class="result-picker" :class="{ inline }">
    <!-- 非内嵌模式：摘要 + 打开抽屉按钮 -->
    <template v-if="!inline">
      <div class="picker-summary">
        <template v-if="currentResult">
          <el-icon v-if="currentResult.is_favorite" class="star-icon active"><StarFilled /></el-icon>
          <span class="summary-name">{{ getScheduleResultDisplayName(currentResult) }}</span>
          <el-tag
            :type="getScheduleResultStatusType(currentResult.solve_status)"
            size="small"
          >
            {{ getScheduleResultStatusText(currentResult.solve_status) }}
          </el-tag>
          <span class="summary-time">{{ currentResult.created_at }}</span>
          <el-tag v-if="currentResult.is_active" type="success" size="small" effect="dark">使用中</el-tag>
        </template>
        <span v-else class="summary-empty">未选择排课结果</span>
        <el-button type="primary" plain @click="openDrawer">
          <el-icon><Menu /></el-icon>
          <span>切换 / 管理</span>
        </el-button>
      </div>

      <el-drawer
        v-model="drawerOpen"
        title="排课结果管理"
        direction="rtl"
        size="860px"
        :destroy-on-close="false"
      >
        <ResultTable
          ref="tableRef"
          :selected-id="modelValue"
          :show-activate-action="showActivateAction"
          @select-row="onRowSelectAndClose"
          @activated="onActivated"
          @changed="onTableChanged"
        />
      </el-drawer>
    </template>

    <!-- 内嵌模式 -->
    <ResultTable
      v-else
      ref="tableRef"
      :selected-id="modelValue"
      :show-activate-action="showActivateAction"
      @select-row="onRowSelect"
      @activated="onActivated"
      @changed="onTableChanged"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Menu, StarFilled } from '@element-plus/icons-vue'
import {
  getScheduleResultDisplayName,
  getScheduleResultStatusText,
  getScheduleResultStatusType
} from '../utils/scheduleResults'
import ResultTable from './ScheduleResultTable.vue'

const props = defineProps({
  modelValue: { type: [Number, String], default: null },
  currentResult: { type: Object, default: null },
  inline: { type: Boolean, default: false },
  showActivateAction: { type: Boolean, default: true }
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const drawerOpen = ref(false)
const tableRef = ref(null)

const openDrawer = () => {
  drawerOpen.value = true
  // 抽屉已打开过的话，主动刷一下列表，避免数据陈旧
  if (tableRef.value) {
    tableRef.value.refresh()
  }
}

const onRowSelect = (row) => {
  emit('update:modelValue', row.id)
}

const onRowSelectAndClose = (row) => {
  emit('update:modelValue', row.id)
  drawerOpen.value = false
}

const onActivated = (row) => {
  // 激活后切换到该结果并通知父刷新
  emit('update:modelValue', row.id)
  emit('refresh')
}

const onTableChanged = (payload = {}) => {
  // 当前所选被删除 → 通知父清空
  const deleted = payload.deletedIds || []
  if (deleted.includes(props.modelValue)) {
    emit('update:modelValue', null)
  }
  emit('refresh')
}

defineExpose({
  refresh: () => tableRef.value?.refresh()
})
</script>

<style scoped>
.picker-summary {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.summary-name {
  font-weight: 600;
  color: #303133;
}
.summary-time {
  color: #909399;
  font-size: 13px;
}
.summary-empty {
  color: #909399;
}
.star-icon {
  color: #f0a020;
}
.result-picker.inline {
  width: 100%;
}
</style>
