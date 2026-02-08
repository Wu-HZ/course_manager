<template>
  <div class="page-container">
    <div class="page-header">
      <h2>排课参数设置</h2>
      <el-button type="warning" @click="handleReset">恢复默认值</el-button>
    </div>

    <el-form :model="form" label-width="180px" v-loading="loading">
      <!-- 基础配置 -->
      <el-divider content-position="left">基础配置</el-divider>

      <el-form-item label="班会课程名">
        <el-input v-model="form.class_meeting_name" style="width: 200px" />
        <div class="help-text">班会课的课程名称，如"班会"、"班队会"、"主题班会"等</div>
      </el-form-item>

      <el-form-item label="合班课时段">
        <el-input v-model="form.combined_class_slots" style="width: 300px" />
        <div class="help-text">格式"星期,节次"用分号分隔，如"1,4;1,5;3,4;3,5"表示周二和周四下午（星期从0=周一开始，节次从0开始）</div>
      </el-form-item>

      <el-form-item label="求解器线程数">
        <el-input-number v-model="form.solver_num_workers" :min="1" :max="16" />
        <div class="help-text">并行计算的线程数，建议设为CPU核心数</div>
      </el-form-item>

      <!-- 硬约束参数 -->
      <el-divider content-position="left">硬约束参数</el-divider>

      <el-form-item label="连堂禁跨节次对">
        <el-input v-model="form.h9_consecutive_forbidden" style="width: 200px" />
        <div class="help-text">格式如"1,2;3,4"表示第2-3节和第4-5节之间禁止连堂（0起始，用分号分隔多组）</div>
      </el-form-item>

      <el-form-item label="教师同班单日上限">
        <el-input-number v-model="form.h11_teacher_class_daily_max" :min="1" :max="6" />
        <span class="unit">节</span>
        <div class="help-text">同一教师同一天在同一班级最多上几节课</div>
      </el-form-item>

      <!-- 软约束权重 -->
      <el-divider content-position="left">软约束权重（数值越大越重要）</el-divider>

      <el-form-item label="S1 上午优先权重">
        <el-input-number v-model="form.s1_am_preference_weight" :min="0" :max="100" />
        <div class="help-text">标记"上午优先"的课程排在上午的奖励分</div>
      </el-form-item>

      <el-form-item label="S2 连堂偏好权重">
        <el-input-number v-model="form.s2_consecutive_weight" :min="0" :max="100" />
        <div class="help-text">允许连堂的课程连续排列的奖励分</div>
      </el-form-item>

      <el-form-item label="S3 分布均匀权重">
        <el-input-number v-model="form.s3_distribution_weight" :min="0" :max="100" />
        <div class="help-text">同课同班同天超过1节的惩罚分</div>
      </el-form-item>

      <el-form-item label="S4 教师日负载阈值">
        <el-input-number v-model="form.s4_teacher_daily_threshold" :min="1" :max="6" />
        <span class="unit">节</span>
        <div class="help-text">教师单日课时超过此值开始惩罚</div>
      </el-form-item>

      <el-form-item label="S4 教师日负载权重">
        <el-input-number v-model="form.s4_teacher_daily_weight" :min="0" :max="100" />
        <div class="help-text">教师单日课时超出阈值的惩罚分</div>
      </el-form-item>

      <el-form-item label="S5 避免第一节权重">
        <el-input-number v-model="form.s5_avoid_first_weight" :min="0" :max="100" />
        <div class="help-text">标记"避免第一节"的课程排在第一节的惩罚分</div>
      </el-form-item>

      <el-form-item label="S6 换班惩罚权重">
        <el-input-number v-model="form.s6_subject_switch_weight" :min="0" :max="100" />
        <div class="help-text">教师连续两节在不同班级上课的惩罚分</div>
      </el-form-item>

      <el-form-item label="S7 同班换科惩罚权重">
        <el-input-number v-model="form.s7_same_class_subject_switch_weight" :min="0" :max="100" />
        <div class="help-text">教师连续两节在同一班级但上不同科目的惩罚分</div>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleSave" :loading="saving">保存设置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const loading = ref(false)
const saving = ref(false)
const form = ref({
  class_meeting_name: '班会',
  combined_class_slots: '1,4;1,5;3,4;3,5',
  solver_num_workers: 4,
  h9_consecutive_forbidden: '1,2;3,4',
  h11_teacher_class_daily_max: 2,
  s1_am_preference_weight: 10,
  s2_consecutive_weight: 5,
  s3_distribution_weight: 2,
  s4_teacher_daily_threshold: 3,
  s4_teacher_daily_weight: 8,
  s5_avoid_first_weight: 6,
  s6_subject_switch_weight: 5,
  s7_same_class_subject_switch_weight: 3
})

const loadSettings = async () => {
  loading.value = true
  try {
    const data = await api.get('/scheduler-settings/')
    form.value = data
  } catch (e) {
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    await api.put('/scheduler-settings/update/', form.value)
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleReset = async () => {
  await ElMessageBox.confirm('确定恢复所有参数为默认值?', '提示', { type: 'warning' })
  try {
    const data = await api.post('/scheduler-settings/reset/')
    form.value = data
    ElMessage.success('已恢复默认值')
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.page-container { background: #fff; padding: 20px; border-radius: 4px; max-width: 800px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; }
.help-text { color: #909399; font-size: 12px; margin-top: 5px; }
.unit { margin-left: 10px; color: #606266; }
</style>
