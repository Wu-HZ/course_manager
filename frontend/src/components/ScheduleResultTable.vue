<template>
  <div class="result-table">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="search"
          placeholder="按名称搜索"
          clearable
          size="small"
          style="width: 180px;"
          @input="onFilterChange"
        />
        <el-select
          v-model="statusFilter"
          placeholder="所有状态"
          clearable
          size="small"
          style="width: 130px;"
          @change="onFilterChange"
        >
          <el-option
            v-for="opt in STATUS_OPTIONS"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <el-switch
          v-model="favoriteOnly"
          active-text="只看收藏"
          size="default"
          @change="onFilterChange"
        />
      </div>
      <div class="toolbar-right">
        <el-button
          size="small"
          :disabled="!selectedRows.length"
          :loading="actionLoading"
          @click="onBulkFavorite(true)"
        >
          <el-icon><StarFilled /></el-icon>
          批量收藏
        </el-button>
        <el-button
          size="small"
          :disabled="!selectedRows.length"
          :loading="actionLoading"
          @click="onBulkFavorite(false)"
        >
          <el-icon><Star /></el-icon>
          取消收藏
        </el-button>
        <el-button
          size="small"
          type="danger"
          plain
          :disabled="!selectedRows.length"
          :loading="actionLoading"
          @click="onBulkDelete"
        >
          <el-icon><Delete /></el-icon>
          批量删除 ({{ selectedRows.length }})
        </el-button>
      </div>
    </div>

    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="items"
      stripe
      border
      highlight-current-row
      :row-class-name="rowClassName"
      @selection-change="onSelectionChange"
      @row-click="onRowClick"
    >
      <el-table-column type="selection" width="44" />
      <el-table-column label="★" width="48" align="center">
        <template #default="{ row }">
          <el-button
            link
            class="star-btn"
            :class="{ active: row.is_favorite }"
            @click.stop="onToggleFavorite(row)"
          >
            <el-icon><StarFilled v-if="row.is_favorite" /><Star v-else /></el-icon>
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="名称" min-width="180">
        <template #default="{ row }">
          <span :class="{ 'row-selected-name': row.id === selectedId }">
            {{ getScheduleResultDisplayName(row) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag
            :type="getScheduleResultStatusType(row.solve_status)"
            size="small"
          >
            {{ getScheduleResultStatusText(row.solve_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="created_at" width="170" />
      <el-table-column label="条目数" prop="entry_count" width="80" align="center" />
      <el-table-column label="当前" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.is_active" type="success" size="small" effect="dark">使用中</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" :width="showActivateAction ? 220 : 160" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="showActivateAction && !row.is_active && canActivate(row)"
            size="small"
            :loading="actionLoading"
            @click.stop="onActivate(row)"
          >
            激活
          </el-button>
          <el-button
            size="small"
            :loading="actionLoading"
            @click.stop="onRename(row)"
          >
            改名
          </el-button>
          <el-button
            size="small"
            type="danger"
            plain
            :loading="actionLoading"
            @click.stop="onDeleteRow(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-bar">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="onPageSizeChange"
        @current-change="fetchData"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Star, StarFilled, Delete } from '@element-plus/icons-vue'
import {
  getScheduleResults, updateScheduleResult, deleteScheduleResult,
  bulkDeleteScheduleResults, activateResult, toggleFavoriteScheduleResult
} from '../api/scheduler'
import {
  getScheduleResultDisplayName,
  getScheduleResultStatusText,
  getScheduleResultStatusType
} from '../utils/scheduleResults'

const STATUS_OPTIONS = [
  { value: 'OPTIMAL', label: '最优解' },
  { value: 'FEASIBLE', label: '可行解' },
  { value: 'INFEASIBLE', label: '无可行解' },
  { value: 'MODEL_INVALID', label: '模型无效' },
  { value: 'UNKNOWN', label: '未知' }
]

const props = defineProps({
  selectedId: { type: [Number, String], default: null },
  showActivateAction: { type: Boolean, default: true }
})

const emit = defineEmits(['select-row', 'activated', 'changed'])

const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const loading = ref(false)
const actionLoading = ref(false)
const search = ref('')
const favoriteOnly = ref(false)
const statusFilter = ref('')
const selectedRows = ref([])

let searchDebounce = null

const isDialogCancelled = (error) => (
  error === 'cancel' || error === 'close' ||
  error?.action === 'cancel' || error?.action === 'close'
)

const buildParams = () => {
  const params = { page: page.value, page_size: pageSize.value }
  if (favoriteOnly.value) params.is_favorite = true
  if (statusFilter.value) params.solve_status = statusFilter.value
  if (search.value.trim()) params.search = search.value.trim()
  return params
}

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getScheduleResults(buildParams())
    items.value = res.results || []
    total.value = res.count || 0
  } catch {
    ElMessage.error('加载排课结果失败')
  } finally {
    loading.value = false
  }
}

const onFilterChange = () => {
  clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => {
    page.value = 1
    fetchData()
  }, 250)
}

const onPageSizeChange = () => {
  page.value = 1
  fetchData()
}

const canActivate = (row) => (
  row.solve_status === 'OPTIMAL' || row.solve_status === 'FEASIBLE'
)

const rowClassName = ({ row }) => (
  row.id === props.selectedId ? 'current-selected-row' : ''
)

const onSelectionChange = (rows) => {
  selectedRows.value = rows
}

const onRowClick = (row, column) => {
  if (column?.type === 'selection') return
  if (column?.label === '操作' || column?.label === '★') return
  emit('select-row', row)
}

const onToggleFavorite = async (row) => {
  actionLoading.value = true
  try {
    await toggleFavoriteScheduleResult(row.id, !row.is_favorite)
    await fetchData()
    emit('changed')
  } catch {
    ElMessage.error('收藏状态更新失败')
  } finally {
    actionLoading.value = false
  }
}

const onRename = async (row) => {
  try {
    const { value } = await ElMessageBox.prompt(
      '输入新的课表名称，留空将恢复默认名称。',
      '重命名课表',
      {
        confirmButtonText: '保存',
        cancelButtonText: '取消',
        inputValue: row.name || '',
        inputPlaceholder: '例如：三月试排 V2'
      }
    )
    actionLoading.value = true
    await updateScheduleResult(row.id, { name: value.trim() })
    ElMessage.success(value.trim() ? '课表名称已更新' : '已恢复默认课表名称')
    await fetchData()
    emit('changed')
  } catch (e) {
    if (isDialogCancelled(e)) return
    ElMessage.error('重命名失败')
  } finally {
    actionLoading.value = false
  }
}

const onDeleteRow = async (row) => {
  const name = getScheduleResultDisplayName(row)
  try {
    await ElMessageBox.confirm(
      `确定删除"${name}"吗？删除后该次排课结果及课表条目都会一起移除。`,
      '删除课表',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    actionLoading.value = true
    await deleteScheduleResult(row.id)
    ElMessage.success(`已删除 ${name}`)
    await fetchData()
    emit('changed', { deletedIds: [row.id] })
  } catch (e) {
    if (isDialogCancelled(e)) return
    ElMessage.error('删除失败')
  } finally {
    actionLoading.value = false
  }
}

const onBulkDelete = async () => {
  if (!selectedRows.value.length) return
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedRows.value.length} 条排课结果吗？此操作不可撤销。`,
      '批量删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    actionLoading.value = true
    const ids = selectedRows.value.map(r => r.id)
    const res = await bulkDeleteScheduleResults(ids)
    ElMessage.success(`已删除 ${res.deleted ?? ids.length} 条`)
    await fetchData()
    emit('changed', { deletedIds: ids })
  } catch (e) {
    if (isDialogCancelled(e)) return
    ElMessage.error('批量删除失败')
  } finally {
    actionLoading.value = false
  }
}

const onBulkFavorite = async (isFavorite) => {
  if (!selectedRows.value.length) return
  actionLoading.value = true
  try {
    await Promise.all(
      selectedRows.value
        .filter(r => r.is_favorite !== isFavorite)
        .map(r => updateScheduleResult(r.id, { is_favorite: isFavorite }))
    )
    ElMessage.success(isFavorite ? '已标为收藏' : '已取消收藏')
    await fetchData()
    emit('changed')
  } catch {
    ElMessage.error('批量操作失败')
  } finally {
    actionLoading.value = false
  }
}

const onActivate = async (row) => {
  actionLoading.value = true
  try {
    await activateResult(row.id)
    ElMessage.success(`已激活 ${getScheduleResultDisplayName(row)}`)
    await fetchData()
    emit('activated', row)
    emit('changed')
  } catch {
    ElMessage.error('激活失败')
  } finally {
    actionLoading.value = false
  }
}

defineExpose({ refresh: fetchData })

onMounted(fetchData)
</script>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.star-btn {
  color: #c0c4cc;
  font-size: 18px;
  padding: 4px;
}
.star-btn.active {
  color: #f0a020;
}
.row-selected-name {
  font-weight: 600;
  color: #409eff;
}
:deep(.current-selected-row) {
  background-color: #ecf5ff !important;
}
.pagination-bar {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
