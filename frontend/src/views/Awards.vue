<template>
  <div>
    <div class="page-header">
      <h2>奖励管理</h2>
      <el-button type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon> 新增奖励
      </el-button>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索名称" clearable @clear="loadData" />
        </el-form-item>
        <el-form-item label="年份">
          <el-input-number v-model="filters.year" :min="1990" :max="2030" clearable controls-position="right" />
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="filters.level" clearable>
            <el-option v-for="l in awardLevels" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="tableData" stripe border style="width: 100%; margin-top: 16px">
      <el-table-column prop="title" label="奖励名称" min-width="200" show-overflow-tooltip />
      <el-table-column prop="category" label="类别" width="100" />
      <el-table-column prop="granting_body" label="颁奖单位" width="150" show-overflow-tooltip />
      <el-table-column prop="level" label="级别" width="80" />
      <el-table-column prop="grade" label="等级" width="70" />
      <el-table-column prop="award_date" label="获奖时间" width="110" />
      <el-table-column prop="my_rank" label="排名" width="60" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" @click="showAttachments(row)">附件</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑奖励' : '新增奖励'" width="600px" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="奖励名称" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="奖励类别">
          <el-select v-model="form.category" clearable>
            <el-option v-for="c in awardCategories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="颁奖单位">
          <el-input v-model="form.granting_body" />
        </el-form-item>
        <el-form-item label="获奖级别">
          <el-select v-model="form.level" clearable>
            <el-option v-for="l in awardLevels" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="获奖等级">
          <el-select v-model="form.grade" clearable>
            <el-option v-for="g in awardGrades" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>
        <el-form-item label="获奖时间">
          <el-date-picker v-model="form.award_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="本人排名">
          <el-input-number v-model="form.my_rank" :min="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="全部获奖人">
          <el-input v-model="form.recipients" placeholder="逗号分隔" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>

      <el-divider v-if="savedId" />
      <div v-if="savedId">
        <h4 style="margin-bottom: 10px">上传证明材料</h4>
        <AttachmentManager entity-type="award" :entity-id="savedId" />
      </div>

      <template #footer>
        <el-button @click="closeDialog">{{ isEdit ? '完成' : '取消' }}</el-button>
        <el-button type="primary" @click="handleSubmit" >保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="attachDialogVisible" title="附件管理" width="600px" destroy-on-close>
      <AttachmentManager v-if="currentRow" entity-type="award" :entity-id="currentRow.id" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'
import AttachmentManager from '../components/AttachmentManager.vue'

const awardCategories = ['科研奖励', '教学奖励', '荣誉称号']
const awardLevels = ['国家级', '省部级', '厅局级', '校级']
const awardGrades = ['特等', '一等', '二等', '三等']

const tableData = ref([])
const dialogVisible = ref(false)
const attachDialogVisible = ref(false)
const isEdit = ref(false)
const currentRow = ref(null)
const savedId = ref(null)
const filters = ref({ keyword: '', year: null, level: '' })

const defaultForm = () => ({
  title: '', category: '', granting_body: '', level: '', grade: '',
  award_date: null, my_rank: null, recipients: '', notes: '',
})
const form = ref(defaultForm())

async function loadData() {
  const params = {}
  if (filters.value.keyword) params.keyword = filters.value.keyword
  if (filters.value.year) params.year = filters.value.year
  if (filters.value.level) params.level = filters.value.level
  const { data } = await api.get('/awards', { params })
  tableData.value = data
}

function resetFilters() { filters.value = { keyword: '', year: null, level: '' }; loadData() }

function showDialog(row) {
  if (row) { isEdit.value = true; currentRow.value = row; savedId.value = row.id; form.value = { ...row } }
  else { isEdit.value = false; currentRow.value = null; savedId.value = null; form.value = defaultForm() }
  dialogVisible.value = true
}

function closeDialog() { dialogVisible.value = false; savedId.value = null; loadData() }

function showAttachments(row) { currentRow.value = row; attachDialogVisible.value = true }

async function handleSubmit() {
  if (!form.value.title) { ElMessage.warning('请填写奖励名称'); return }
  if (isEdit.value) { await api.put(`/awards/${currentRow.value.id}`, form.value); ElMessage.success('更新成功'); dialogVisible.value = false; savedId.value = null }
  else { const { data } = await api.post('/awards', form.value); savedId.value = data.id; isEdit.value = true; currentRow.value = data; ElMessage.success('创建成功，请上传证明材料') }
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await api.delete(`/awards/${row.id}`); ElMessage.success('删除成功'); loadData()
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
