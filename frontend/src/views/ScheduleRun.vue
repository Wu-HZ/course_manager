<template>
  <div class="page-container">
    <h2>执行排课</h2>

    <SchedulePrecheckPanel
      :precheck="precheck"
      :loading="precheckLoading"
      @refresh="loadPrecheck"
    />

    <el-card class="run-card">
      <template #header>排课参数</template>
      <el-form label-width="140px">
        <el-form-item label="单次求解时限（秒）">
          <el-input-number v-model="timeLimit" :min="10" :max="1500" />
          <span class="form-hint">每次求解尝试的时间上限。</span>
        </el-form-item>
        <el-form-item label="最大尝试次数">
          <el-input-number v-model="maxAttempts" :min="1" :max="250" />
          <span class="form-hint">无解时自动重试的最大次数。</span>
        </el-form-item>
        <el-form-item label="总超时时间（秒）">
          <el-input-number v-model="totalTimeout" :min="30" :max="3000" />
          <span class="form-hint">所有尝试累计允许使用的总时间。</span>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="running"
            :disabled="Boolean(precheck && !precheck.summary.can_run)"
            @click="runSchedule"
          >
            <el-icon v-if="!running"><VideoPlay /></el-icon>
            {{ running ? '排课中...' : '开始排课' }}
          </el-button>
          <span v-if="precheck && !precheck.summary.can_run" class="form-blocking-text">
            请先处理上方必须项后再开始排课。
          </span>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card ref="resultCardRef" v-if="result" class="result-card" :class="resultClass">
      <template #header>排课结果</template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="结果名称">
          {{ getScheduleResultDisplayName(result) }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType">{{ statusText }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="总耗时">{{ result.solve_time_ms }} ms</el-descriptions-item>
        <el-descriptions-item label="课表条目数">
          {{ result.entry_count || result.entries?.length || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ result.created_at }}</el-descriptions-item>
        <el-descriptions-item label="自动分配" v-if="autoAssignedCount !== null">
          <el-tag type="success" size="small">{{ autoAssignedCount }} 条</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="retryStats" class="retry-stats">
        <el-divider content-position="left">重试统计</el-divider>
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="尝试次数">
            <el-tag :type="retryStats.attempts === 1 ? 'success' : 'warning'" size="small">
              {{ retryStats.attempts }} 次
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="失败次数">
            <el-tag :type="retryStats.failures === 0 ? 'success' : 'info'" size="small">
              {{ retryStats.failures }} 次
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="成功率">
            <el-tag :type="retryStats.success_rate >= 50 ? 'success' : 'warning'" size="small">
              {{ retryStats.success_rate?.toFixed(1) }}%
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="retryStats.failure_reasons?.length" class="failure-reasons">
          <h5>失败原因</h5>
          <ul>
            <li v-for="(fail, i) in retryStats.failure_reasons" :key="i">
              第 {{ fail.attempt }} 次：{{ fail.reason }}
            </li>
          </ul>
        </div>
      </div>

      <div v-if="errors.length" class="errors">
        <h4>错误信息</h4>
        <ul>
          <li v-for="(err, i) in errors" :key="i">{{ err }}</li>
        </ul>
      </div>

      <div v-if="diagnostics.length" class="diagnostics">
        <el-divider />
        <h4>诊断分析</h4>
        <pre class="diagnostics-content">{{ diagnostics.join('\n') }}</pre>
      </div>

      <div class="actions" v-if="result.id">
        <el-button type="primary" @click="$router.push('/schedule-view')">查看课表</el-button>
        <el-button @click="$router.push('/assignments')">查看授课分配</el-button>
      </div>
    </el-card>

    <el-card class="history-card">
      <template #header>历史记录</template>
      <ScheduleResultPicker
        ref="pickerRef"
        inline
        :model-value="result?.id ?? null"
        :current-result="result"
        @update:model-value="onHistorySelect"
      />
    </el-card>

    <el-dialog
      v-model="completionDialogVisible"
      :title="completionDialogTitle"
      width="520px"
      :close-on-click-modal="false"
    >
      <div class="completion-dialog">
        <div class="completion-dialog__status">
          <span class="completion-dialog__label">结果状态</span>
          <el-tag :type="statusType" effect="dark">{{ statusText }}</el-tag>
        </div>
        <p class="completion-dialog__description">{{ completionDialogDescription }}</p>
        <div class="completion-dialog__meta">
          <div class="completion-dialog__meta-item">
            <span class="completion-dialog__meta-label">结果名称</span>
            <strong>{{ completionResultName }}</strong>
          </div>
          <div class="completion-dialog__meta-item">
            <span class="completion-dialog__meta-label">总耗时</span>
            <strong>{{ completionSolveTimeText }}</strong>
          </div>
          <div class="completion-dialog__meta-item" v-if="autoAssignedCount !== null">
            <span class="completion-dialog__meta-label">自动分配</span>
            <strong>{{ autoAssignedCount }} 节</strong>
          </div>
          <div class="completion-dialog__meta-item" v-if="retryStats?.attempts">
            <span class="completion-dialog__meta-label">尝试次数</span>
            <strong>{{ retryStats.attempts }} 次</strong>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="completionDialogVisible = false">
          {{ completionDialogMode === 'success' ? '稍后查看' : '关闭' }}
        </el-button>
        <el-button type="primary" @click="handleCompletionPrimaryAction">
          {{ completionDialogPrimaryText }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import SchedulePrecheckPanel from '../components/SchedulePrecheckPanel.vue'
import { getSchedulePrecheck, getScheduleResult, runSchedule as runScheduleApi } from '../api/scheduler'
import {
  getScheduleResultDisplayName,
  getScheduleResultStatusText,
  getScheduleResultStatusType,
} from '../utils/scheduleResults'
import ScheduleResultPicker from '../components/ScheduleResultPicker.vue'

const timeLimit = ref(300)
const maxAttempts = ref(50)
const totalTimeout = ref(600)
const running = ref(false)
const result = ref(null)
const errors = ref([])
const diagnostics = ref([])
const autoAssignedCount = ref(null)
const retryStats = ref(null)
const pickerRef = ref(null)
const resultCardRef = ref(null)
const precheck = ref(null)
const precheckLoading = ref(false)
const completionDialogVisible = ref(false)
const completionDialogMode = ref('success')
const lastSolveTimeMs = ref(0)
const router = useRouter()

const statusText = computed(() => getScheduleResultStatusText(result.value?.solve_status))
const statusType = computed(() => getScheduleResultStatusType(result.value?.solve_status))
const resultClass = computed(() => {
  const status = result.value?.solve_status
  if (status === 'INFEASIBLE' || status === 'FAILED_ALL_ATTEMPTS') {
    return 'error'
  }
  return 'success'
})
const completionDialogTitle = computed(() => (
  completionDialogMode.value === 'success' ? '排课完成' : '排课已结束'
))
const completionDialogPrimaryText = computed(() => (
  completionDialogMode.value === 'success' ? '查看课表' : '查看结果详情'
))
const completionResultName = computed(() => {
  if (!result.value) {
    return '本次求解'
  }
  if (result.value.display_name || result.value.id) {
    return getScheduleResultDisplayName(result.value)
  }
  return '本次求解'
})
const completionSolveTimeText = computed(() => {
  const solveTimeMs = result.value?.solve_time_ms ?? lastSolveTimeMs.value
  return solveTimeMs ? `${solveTimeMs} ms` : '未返回'
})
const completionDialogDescription = computed(() => {
  const status = result.value?.solve_status
  if (completionDialogMode.value === 'success') {
    if (status === 'OPTIMAL') {
      return '已生成最优课表，可以立即进入课表查看页核对结果。'
    }
    if (status === 'FEASIBLE') {
      return '已生成可用课表，可以立即进入课表查看页继续检查。'
    }
    return '已生成排课结果，可以立即进入课表查看页查看。'
  }

  if (status === 'INFEASIBLE') {
    return '本次求解已结束，但当前约束下未找到可行课表。请查看下方错误信息和诊断分析。'
  }
  if (status === 'FAILED_ALL_ATTEMPTS') {
    return '本次求解已结束，但所有尝试都未生成可用课表。请查看失败原因和诊断分析。'
  }
  if (status === 'MODEL_INVALID') {
    return '本次求解已结束，但模型配置存在问题，未生成可用课表。请查看下方诊断信息。'
  }
  return '本次求解已结束，但未生成可用课表。请查看当前页面的结果信息。'
})

const openCompletionDialog = (mode) => {
  completionDialogMode.value = mode
  completionDialogVisible.value = true
}

const scrollToResultCard = async () => {
  completionDialogVisible.value = false
  await nextTick()
  resultCardRef.value?.$el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const handleCompletionPrimaryAction = async () => {
  if (completionDialogMode.value === 'success') {
    completionDialogVisible.value = false
    await router.push('/schedule-view')
    return
  }
  await scrollToResultCard()
}

const loadPrecheck = async () => {
  precheckLoading.value = true
  try {
    precheck.value = await getSchedulePrecheck()
  } catch (error) {
    console.error('Failed to load precheck:', error)
  } finally {
    precheckLoading.value = false
  }
}

const onHistorySelect = async (id) => {
  if (!id) {
    result.value = null
    return
  }
  try {
    result.value = await getScheduleResult(id)
    errors.value = []
    diagnostics.value = []
    autoAssignedCount.value = null
    retryStats.value = null
  } catch {
    ElMessage.error('加载排课结果失败')
  }
}

const runSchedule = async () => {
  if (precheck.value && !precheck.value.summary.can_run) {
    ElMessage.error('请先处理排课前检查中的必须项')
    return
  }

  running.value = true
  completionDialogVisible.value = false
  result.value = null
  errors.value = []
  diagnostics.value = []
  autoAssignedCount.value = null
  retryStats.value = null
  lastSolveTimeMs.value = 0

  try {
    const res = await runScheduleApi({
      timeLimit: timeLimit.value,
      maxAttempts: maxAttempts.value,
      totalTimeout: totalTimeout.value,
    })
    result.value = res.result
    autoAssignedCount.value = res.auto_assigned_count || 0
    retryStats.value = res.retry_stats || null
    lastSolveTimeMs.value = res.solve_time_ms || res.result?.solve_time_ms || 0
    if (!res.success) {
      errors.value = res.errors || []
      diagnostics.value = res.diagnostics || []
    }
    ElMessage.success('排课完成')
    openCompletionDialog(res.success === false ? 'failure' : 'success')
    pickerRef.value?.refresh()
  } catch (error) {
    if (error.response?.data) {
      result.value = error.response.data.result || { solve_status: error.response.data.status }
      errors.value = error.response.data.errors || []
      diagnostics.value = error.response.data.diagnostics || []
      autoAssignedCount.value = error.response.data.auto_assigned_count || null
      retryStats.value = error.response.data.retry_stats || null
      lastSolveTimeMs.value = error.response.data.solve_time_ms || 0
      ElMessage.error('排课失败')
      openCompletionDialog('failure')
    } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      errors.value = ['请求超时，请稍后刷新页面查看历史记录。']
      ElMessage.error('请求超时，后台可能仍在计算')
    } else {
      errors.value = [error.message || '未知错误']
      ElMessage.error(`排课失败: ${error.message || '未知错误'}`)
    }
  } finally {
    running.value = false
    pickerRef.value?.refresh()
    await loadPrecheck()
  }
}

onMounted(loadPrecheck)
</script>

<style scoped>
.page-container {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

.page-container h2 {
  margin-bottom: 20px;
}

.run-card,
.result-card,
.history-card {
  margin-bottom: 20px;
}

.result-card.error {
  border-color: #f56c6c;
}

.result-card.success {
  border-color: #67c23a;
}

.form-hint {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}

.form-blocking-text {
  margin-left: 12px;
  font-size: 12px;
  color: #f56c6c;
}

.errors {
  margin-top: 20px;
  color: #f56c6c;
}

.errors h4,
.diagnostics h4 {
  margin-bottom: 10px;
}

.diagnostics {
  margin-top: 10px;
}

.diagnostics h4 {
  color: #409eff;
}

.diagnostics-content {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 400px;
  overflow-y: auto;
}

.actions {
  margin-top: 20px;
}

.retry-stats {
  margin-top: 15px;
}

.failure-reasons {
  margin-top: 10px;
  padding: 10px;
  background: #fef0f0;
  border-radius: 4px;
  font-size: 13px;
}

.failure-reasons h5 {
  margin: 0 0 8px 0;
  color: #f56c6c;
}

.failure-reasons ul {
  margin: 0;
  padding-left: 20px;
}

.failure-reasons li {
  margin-bottom: 4px;
  color: #606266;
}

.completion-dialog__status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.completion-dialog__label,
.completion-dialog__meta-label {
  color: #909399;
  font-size: 13px;
}

.completion-dialog__description {
  margin: 16px 0;
  color: #303133;
  line-height: 1.7;
}

.completion-dialog__meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.completion-dialog__meta-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.completion-dialog__meta-item strong {
  display: block;
  margin-top: 6px;
  color: #303133;
  line-height: 1.5;
}
</style>
