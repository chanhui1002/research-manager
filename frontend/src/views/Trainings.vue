<template>
  <div>
    <div class="page-header">
      <h2>培训证明管理</h2>
      <el-button type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon> 新增培训证明
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
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="tableData" stripe border style="width: 100%; margin-top: 16px">
      <el-table-column prop="title" label="培训名称" min-width="200" show-overflow-tooltip />
      <el-table-column prop="organizer" label="主办单位" width="180" show-overflow-tooltip />
      <el-table-column prop="training_date" label="培训时间" width="120" />
      <el-table-column prop="duration" label="培训时长" width="100" />
      <el-table-column prop="certificate_number" label="证书编号" width="150" show-overflow-tooltip />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" @click="showAttachments(row)">附件</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑培训证明' : '新增培训证明'" width="600px" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="培训名称" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="主办单位">
          <el-input v-model="form.organizer" />
        </el-form-item>
        <el-form-item label="培训时间">
          <el-date-picker v-model="form.training_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="培训时长">
          <el-input v-model="form.duration" placeholder="如: 3天 / 40学时" />
        </el-form-item>
        <el-form-item label="证书编号">
          <el-input v-model="form.certificate_number" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>

      <el-divider v-if="savedId" />
      <div v-if="savedId">
        <h4 style="margin-bottom: 10px">上传证明材料</h4>
        <AttachmentManager entity-type="training" :entity-id="savedId" />
      </div>

      <template #footer>
        <el-button @click="closeDialog">{{ savedId ? '完成' : '取消' }}</el-button>
        <el-button type="primary" @click="handleSubmit" v-if="!savedId">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="attachDialogVisible" title="附件管理" width="600px" destroy-on-close>
      <AttachmentManager v-if="currentRow" entity-type="training" :entity-id="currentRow.id" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'
import AttachmentManager from '../components/AttachmentManager.vue'

const tableData = ref([])
const dialogVisible = ref(false)
const attachDialogVisible = ref(false)
const isEdit = ref(false)
const currentRow = ref(null)
const savedId = ref(null)
const filters = ref({ keyword: '', year: null })

const defaultForm = () => ({
  title: '', organizer: '', training_date: null, duration: '', certificate_number: '', notes: '',
})
const form = ref(defaultForm())

async function loadData() {
  const params = {}
  if (filters.value.keyword) params.keyword = filters.value.keyword
  if (filters.value.year) params.year = filters.value.year
  const { data } = await api.get('/trainings', { params })
  tableData.value = data
}

function resetFilters() { filters.value = { keyword: '', year: null }; loadData() }

function showDialog(row) {
  if (row) { isEdit.value = true; currentRow.value = row; savedId.value = row.id; form.value = { ...row } }
  else { isEdit.value = false; currentRow.value = null; savedId.value = null; form.value = defaultForm() }
  dialogVisible.value = true
}

function closeDialog() { dialogVisible.value = false; savedId.value = null; loadData() }

function showAttachments(row) { currentRow.value = row; attachDialogVisible.value = true }

async function handleSubmit() {
  if (!form.value.title) { ElMessage.warning('请填写培训名称'); return }
  if (isEdit.value) { await api.put(`/trainings/${currentRow.value.id}`, form.value); ElMessage.success('更新成功') }
  else { const { data } = await api.post('/trainings', form.value); savedId.value = data.id; ElMessage.success('创建成功，请上传证明材料') }
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await api.delete(`/trainings/${row.id}`); ElMessage.success('删除成功'); loadData()
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
