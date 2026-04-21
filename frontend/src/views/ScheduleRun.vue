<template>
  <div class="page-container">
    <h2>执行排课</h2>

    <el-card class="run-card">
      <template #header>排课参数</template>
      <el-form label-width="140px">
        <el-form-item label="单次求解时限(秒)">
          <el-input-number v-model="timeLimit" :min="10" :max="1500" />
          <span class="form-hint">每次求解尝试的时间限制</span>
        </el-form-item>
        <el-form-item label="最大尝试次数">
          <el-input-number v-model="maxAttempts" :min="1" :max="250" />
          <span class="form-hint">自动重试的最大次数</span>
        </el-form-item>
        <el-form-item label="总超时时间(秒)">
          <el-input-number v-model="totalTimeout" :min="30" :max="3000" />
          <span class="form-hint">所有尝试的总时间上限</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="running" @click="runSchedule">
            <el-icon v-if="!running"><VideoPlay /></el-icon>
            {{ running ? '排课中...' : '开始排课' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="result" class="result-card" :class="resultClass">
      <template #header>排课结果</template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="结果名称">{{ getScheduleResultDisplayName(result) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType">{{ statusText }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="总耗时">{{ result.solve_time_ms }} ms</el-descriptions-item>
        <el-descriptions-item label="课表条目数">{{ result.entry_count || result.entries?.length || 0 }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ result.created_at }}</el-descriptions-item>
        <el-descriptions-item label="自动分配" v-if="autoAssignedCount !== null">
          <el-tag type="success" size="small">{{ autoAssignedCount }} 条</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 重试统计 -->
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
          <h5>失败原因:</h5>
          <ul>
            <li v-for="(fail, i) in retryStats.failure_reasons" :key="i">
              第{{ fail.attempt }}次: {{ fail.reason }}
            </li>
          </ul>
        </div>
      </div>

      <div v-if="errors.length" class="errors">
        <h4>错误信息:</h4>
        <ul>
          <li v-for="(err, i) in errors" :key="i">{{ err }}</li>
        </ul>
      </div>
      <div v-if="diagnostics.length" class="diagnostics">
        <el-divider />
        <h4>诊断分析:</h4>
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { runSchedule as runScheduleApi, getScheduleResult } from '../api/scheduler'
import {
  getScheduleResultDisplayName,
  getScheduleResultStatusText,
  getScheduleResultStatusType
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

const statusText = computed(() => {
  return getScheduleResultStatusText(result.value?.solve_status)
})

const statusType = computed(() => getScheduleResultStatusType(result.value?.solve_status))
const resultClass = computed(() => {
  const status = result.value?.solve_status
  if (status === 'INFEASIBLE' || status === 'FAILED_ALL_ATTEMPTS') return 'error'
  return 'success'
})

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
  running.value = true
  result.value = null
  errors.value = []
  diagnostics.value = []
  autoAssignedCount.value = null
  retryStats.value = null

  try {
    const res = await runScheduleApi({
      timeLimit: timeLimit.value,
      maxAttempts: maxAttempts.value,
      totalTimeout: totalTimeout.value
    })
    result.value = res.result
    autoAssignedCount.value = res.auto_assigned_count || 0
    retryStats.value = res.retry_stats || null
    if (!res.success) {
      errors.value = res.errors || []
      diagnostics.value = res.diagnostics || []
    }
    ElMessage.success('排课完成')
    pickerRef.value?.refresh()
  } catch (e) {
    if (e.response?.data) {
      result.value = e.response.data.result || { solve_status: e.response.data.status }
      errors.value = e.response.data.errors || []
      diagnostics.value = e.response.data.diagnostics || []
      autoAssignedCount.value = e.response.data.auto_assigned_count || null
      retryStats.value = e.response.data.retry_stats || null
      ElMessage.error('排课失败')
    } else if (e.code === 'ECONNABORTED' || e.message?.includes('timeout')) {
      errors.value = ['请求超时，请稍后刷新页面查看历史记录']
      ElMessage.error('请求超时，后台可能仍在计算')
    } else {
      errors.value = [e.message || '未知错误']
      ElMessage.error('排课失败: ' + (e.message || '未知错误'))
    }
  } finally {
    running.value = false
    pickerRef.value?.refresh()  // 无论成功失败都刷新历史
  }
}
</script>

<style scoped>
.page-container { background: #fff; padding: 20px; border-radius: 4px; }
.page-container h2 { margin-bottom: 20px; }
.run-card, .result-card, .history-card { margin-bottom: 20px; }
.result-card.error { border-color: #f56c6c; }
.result-card.success { border-color: #67c23a; }
.form-hint { margin-left: 10px; color: #909399; font-size: 12px; }
.errors { margin-top: 20px; color: #f56c6c; }
.errors h4 { margin-bottom: 10px; }
.diagnostics { margin-top: 10px; }
.diagnostics h4 { margin-bottom: 10px; color: #409eff; }
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
.actions { margin-top: 20px; }
.retry-stats { margin-top: 15px; }
.failure-reasons {
  margin-top: 10px;
  padding: 10px;
  background: #fef0f0;
  border-radius: 4px;
  font-size: 13px;
}
.failure-reasons h5 { margin: 0 0 8px 0; color: #f56c6c; }
.failure-reasons ul { margin: 0; padding-left: 20px; }
.failure-reasons li { margin-bottom: 4px; color: #909399; }
</style>
