<template>
  <div>
    <div class="page-header">
      <h2>论文管理</h2>
      <el-button type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon> 新增论文
      </el-button>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索标题" clearable @clear="loadData" />
        </el-form-item>
        <el-form-item label="年份">
          <el-input-number v-model="filters.year" :min="1990" :max="2030" placeholder="年份" clearable controls-position="right" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.paper_type" clearable placeholder="论文类型">
            <el-option v-for="t in paperTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="tableData" stripe border style="width: 100%; margin-top: 16px">
      <el-table-column prop="title" label="论文题目" min-width="200" show-overflow-tooltip />
      <el-table-column prop="authors" label="作者" width="150" show-overflow-tooltip />
      <el-table-column prop="journal" label="期刊/会议" width="150" show-overflow-tooltip />
      <el-table-column prop="publish_date" label="发表时间" width="110" />
      <el-table-column prop="paper_type" label="类型" width="90" />
      <el-table-column prop="cas_quartile" label="分区" width="80" />
      <el-table-column prop="impact_factor" label="IF" width="70" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" @click="showAttachments(row)">附件</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑论文' : '新增论文'" width="700px" destroy-on-close>
      <el-form :model="form" label-width="130px">
        <el-form-item label="论文题目" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="期刊/会议">
          <el-input v-model="form.journal" />
        </el-form-item>
        <el-form-item label="发表时间">
          <el-date-picker v-model="form.publish_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="论文类型">
          <el-select v-model="form.paper_type" clearable>
            <el-option v-for="t in paperTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="中科院分区">
              <el-select v-model="form.cas_quartile" clearable>
                <el-option v-for="q in casQuartiles" :key="q" :label="q" :value="q" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="JCR分区">
              <el-select v-model="form.jcr_quartile" clearable>
                <el-option v-for="q in jcrQuartiles" :key="q" :label="q" :value="q" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="影响因子">
              <el-input-number v-model="form.impact_factor" :precision="3" :step="0.1" :min="0" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="全部作者">
          <el-input v-model="form.authors" placeholder="逗号分隔" />
        </el-form-item>
        <el-form-item label="学生一作导师通讯">
          <el-switch v-model="form.is_student_first_supervisor_corresponding" />
        </el-form-item>
        <el-form-item label="DOI">
          <el-input v-model="form.doi" />
        </el-form-item>
        <el-form-item label="归属单位">
          <el-input v-model="form.affiliation" />
        </el-form-item>
        <el-form-item label="学科分类">
          <el-input v-model="form.discipline" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>

      <el-divider v-if="savedId" />
      <div v-if="savedId">
        <h4 style="margin-bottom: 10px">上传证明材料</h4>
        <AttachmentManager entity-type="paper" :entity-id="savedId" />
      </div>

      <template #footer>
        <el-button @click="closeDialog">{{ isEdit ? '完成' : '取消' }}</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="attachDialogVisible" title="附件管理" width="600px" destroy-on-close>
      <AttachmentManager v-if="currentRow" entity-type="paper" :entity-id="currentRow.id" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'
import AttachmentManager from '../components/AttachmentManager.vue'

const paperTypes = ['SCI', 'SSCI', 'EI', 'CSSCI', '北大核心', '普刊', '会议论文']
const casQuartiles = ['1区', '2区', '3区', '4区']
const jcrQuartiles = ['Q1', 'Q2', 'Q3', 'Q4']

const tableData = ref([])
const dialogVisible = ref(false)
const attachDialogVisible = ref(false)
const isEdit = ref(false)
const currentRow = ref(null)
const savedId = ref(null)
const filters = ref({ keyword: '', year: null, paper_type: '' })

const defaultForm = () => ({
  title: '', journal: '', publish_date: null, paper_type: '',
  cas_quartile: '', jcr_quartile: '', impact_factor: null,
  authors: '', is_student_first_supervisor_corresponding: false,
  doi: '', affiliation: '', discipline: '', notes: '',
})
const form = ref(defaultForm())

async function loadData() {
  const params = {}
  if (filters.value.keyword) params.keyword = filters.value.keyword
  if (filters.value.year) params.year = filters.value.year
  if (filters.value.paper_type) params.paper_type = filters.value.paper_type
  const { data } = await api.get('/papers', { params })
  tableData.value = data
}

function resetFilters() {
  filters.value = { keyword: '', year: null, paper_type: '' }
  loadData()
}

function showDialog(row) {
  if (row) {
    isEdit.value = true
    currentRow.value = row
    savedId.value = row.id
    form.value = { ...row }
  } else {
    isEdit.value = false
    currentRow.value = null
    savedId.value = null
    form.value = defaultForm()
  }
  dialogVisible.value = true
}

function closeDialog() {
  dialogVisible.value = false
  savedId.value = null
  loadData()
}

function showAttachments(row) {
  currentRow.value = row
  attachDialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.title) {
    ElMessage.warning('请填写论文题目')
    return
  }
  try {
    if (isEdit.value) {
      await api.put(`/papers/${currentRow.value.id}`, form.value)
      ElMessage.success('更新成功')
      dialogVisible.value = false
      savedId.value = null
    } else {
      const { data } = await api.post('/papers/', form.value)
      savedId.value = data.id
      isEdit.value = true
      currentRow.value = data
      ElMessage.success('创建成功，请上传证明材料')
    }
    loadData()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除该论文？', '提示', { type: 'warning' })
  try {
    await api.delete(`/papers/${row.id}`)
    ElMessage.success('删除成功')
    loadData()
  } catch (e) {
    ElMessage.error('删除失败：' + (e.response?.data?.detail || e.message))
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.filter-card { margin-bottom: 0; }
</style>
