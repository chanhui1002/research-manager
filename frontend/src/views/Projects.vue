<template>
  <div>
    <div class="page-header">
      <h2>项目管理</h2>
      <el-button type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon> 新增项目
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
            <el-option v-for="l in projectLevels" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="tableData" stripe border style="width: 100%; margin-top: 16px">
      <el-table-column prop="title" label="项目名称" min-width="200" show-overflow-tooltip />
      <el-table-column prop="source" label="来源" width="140" show-overflow-tooltip />
      <el-table-column prop="level" label="级别" width="80" />
      <el-table-column prop="start_date" label="立项" width="100" />
      <el-table-column prop="status" label="状态" width="80" />
      <el-table-column prop="total_funding" label="经费(万)" width="90" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" @click="showAttachments(row)">附件</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑项目' : '新增项目'" width="650px" destroy-on-close>
      <el-form :model="form" label-width="120px">
        <el-form-item label="项目名称" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="项目编号">
          <el-input v-model="form.project_number" />
        </el-form-item>
        <el-form-item label="项目来源">
          <el-select v-model="form.source" clearable>
            <el-option v-for="s in projectSources" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目级别">
          <el-select v-model="form.level" clearable>
            <el-option v-for="l in projectLevels" :key="l" :label="l" :value="l" />
          </el-select>
        </el-form-item>
        <el-form-item label="参与排名">
          <el-input-number v-model="form.participant_rank" :min="1" controls-position="right" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="立项时间">
              <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结项时间">
              <el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="项目状态">
          <el-select v-model="form.status" clearable>
            <el-option v-for="s in projectStatuses" :key="s" :label="s" :value="s" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="总经费(万元)">
              <el-input-number v-model="form.total_funding" :min="0" :precision="2" controls-position="right" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="到账(万元)">
              <el-input-number v-model="form.received_funding" :min="0" :precision="2" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>

      <el-divider v-if="savedId" />
      <div v-if="savedId">
        <h4 style="margin-bottom: 10px">上传证明材料</h4>
        <AttachmentManager entity-type="project" :entity-id="savedId" />
      </div>

      <template #footer>
        <el-button @click="closeDialog">{{ isEdit ? '完成' : '取消' }}</el-button>
        <el-button type="primary" @click="handleSubmit" >保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="attachDialogVisible" title="附件管理" width="600px" destroy-on-close>
      <AttachmentManager v-if="currentRow" entity-type="project" :entity-id="currentRow.id" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'
import AttachmentManager from '../components/AttachmentManager.vue'

const projectSources = ['国家自然科学基金', '国家社科基金', '省部级项目', '厅局级项目', '横向项目', '校级项目', '其他']
const projectLevels = ['国家级', '省部级', '厅局级', '校级']
const projectStatuses = ['在研', '已结题', '已验收']

const tableData = ref([])
const dialogVisible = ref(false)
const attachDialogVisible = ref(false)
const isEdit = ref(false)
const currentRow = ref(null)
const savedId = ref(null)
const filters = ref({ keyword: '', year: null, level: '' })

const defaultForm = () => ({
  title: '', project_number: '', source: '', level: '',
  participant_rank: null, start_date: null, end_date: null, status: '',
  total_funding: null, received_funding: null, notes: '',
})
const form = ref(defaultForm())

async function loadData() {
  const params = {}
  if (filters.value.keyword) params.keyword = filters.value.keyword
  if (filters.value.year) params.year = filters.value.year
  if (filters.value.level) params.level = filters.value.level
  const { data } = await api.get('/projects', { params })
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
  if (!form.value.title) { ElMessage.warning('请填写项目名称'); return }
  if (isEdit.value) { await api.put(`/projects/${currentRow.value.id}`, form.value); ElMessage.success('更新成功'); dialogVisible.value = false; savedId.value = null }
  else { const { data } = await api.post('/projects', form.value); savedId.value = data.id; isEdit.value = true; currentRow.value = data; ElMessage.success('创建成功，请上传证明材料') }
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await api.delete(`/projects/${row.id}`); ElMessage.success('删除成功'); loadData()
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
