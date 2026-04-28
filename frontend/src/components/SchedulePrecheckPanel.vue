<template>
  <el-card class="precheck-card" shadow="hover" v-loading="loading">
    <template #header>
      <div class="card-header">
        <div>
          <div class="card-title">排课前检查</div>
          <div class="card-subtitle">
            开始排课前，系统会检查基础数据、授课分配和关键约束。请先处理红色问题。
          </div>
        </div>
        <el-tag
          v-if="precheck"
          :type="precheck.summary.can_run ? 'success' : 'danger'"
          effect="dark"
        >
          {{ precheck.summary.can_run ? '基础检查已通过' : '存在必须处理项' }}
        </el-tag>
      </div>
    </template>

    <template v-if="precheck">
      <div v-if="precheck.blocking_issues.length" class="section">
        <div class="section-title danger">必须处理</div>
        <div
          v-for="issue in precheck.blocking_issues"
          :key="issue.key"
          class="issue-item issue-danger"
        >
          <div class="issue-title">{{ issue.title }}</div>
          <div class="issue-detail">{{ issue.detail }}</div>
          <div v-if="issue.actions?.length" class="issue-actions">
            <el-button
              v-for="action in issue.actions"
              :key="`${issue.key}-${action.route}`"
              size="small"
              type="danger"
              plain
              @click="router.push(action.route)"
            >
              {{ action.label }}
            </el-button>
          </div>
        </div>
      </div>

      <div v-if="precheck.warning_issues.length" class="section">
        <div class="section-title warning">建议处理</div>
        <div
          v-for="issue in precheck.warning_issues"
          :key="issue.key"
          class="issue-item issue-warning"
        >
          <div class="issue-title">{{ issue.title }}</div>
          <div class="issue-detail">{{ issue.detail }}</div>
          <div v-if="issue.actions?.length" class="issue-actions">
            <el-button
              v-for="action in issue.actions"
              :key="`${issue.key}-${action.route}`"
              size="small"
              plain
              @click="router.push(action.route)"
            >
              {{ action.label }}
            </el-button>
          </div>
        </div>
      </div>

      <div v-if="precheck.passed_checks.length" class="section">
        <div class="section-title success">已通过</div>
        <div class="passed-grid">
          <div
            v-for="item in precheck.passed_checks"
            :key="item.key"
            class="passed-item"
          >
            <div class="passed-title">{{ item.title }}</div>
            <div class="passed-detail">{{ item.detail }}</div>
          </div>
        </div>
      </div>

      <div class="footer-bar">
        <div class="footer-summary" :class="{ danger: !precheck.summary.can_run }">
          {{ footerText }}
        </div>
        <el-button @click="$emit('refresh')">刷新检查结果</el-button>
      </div>
    </template>

    <el-empty v-else description="暂无检查结果">
      <el-button @click="$emit('refresh')">重新加载</el-button>
    </el-empty>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  precheck: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['refresh'])

const router = useRouter()

const footerText = computed(() => {
  if (!props.precheck) {
    return '暂无检查结果。'
  }
  if (!props.precheck.summary.can_run) {
    return `当前不可开始排课，请先处理 ${props.precheck.summary.blocking_issue_count} 个必须项。`
  }
  if (props.precheck.summary.warning_issue_count > 0) {
    return `基础检查已通过，可以开始试排；建议先留意 ${props.precheck.summary.warning_issue_count} 项优化提示。`
  }
  return '基础检查已通过，可以开始排课。'
})
</script>

<style scoped>
.precheck-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.card-subtitle {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.6;
  color: #606266;
}

.section + .section {
  margin-top: 18px;
}

.section-title {
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 600;
}

.section-title.danger {
  color: #f56c6c;
}

.section-title.warning {
  color: #e6a23c;
}

.section-title.success {
  color: #67c23a;
}

.issue-item {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #ebeef5;
}

.issue-item + .issue-item {
  margin-top: 10px;
}

.issue-danger {
  border-color: #f8d7da;
  background: #fff8f8;
}

.issue-warning {
  border-color: #f5dab1;
  background: #fffdf7;
}

.issue-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.issue-detail {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.7;
  color: #606266;
}

.issue-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.passed-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.passed-item {
  padding: 12px 14px;
  border-radius: 10px;
  background: #f7fbf5;
  border: 1px solid #d9ecce;
}

.passed-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.passed-detail {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.6;
  color: #606266;
}

.footer-bar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.footer-summary {
  font-size: 13px;
  color: #67c23a;
}

.footer-summary.danger {
  color: #f56c6c;
}

@media (max-width: 768px) {
  .card-header,
  .footer-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .passed-grid {
    grid-template-columns: 1fr;
  }
}
</style>
