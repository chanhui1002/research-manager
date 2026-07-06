<template>
  <div>
    <div class="page-header">
      <h2>专著管理</h2>
      <el-button type="primary" @click="showDialog()">
        <el-icon><Plus /></el-icon> 新增专著
      </el-button>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="搜索书名" clearable @clear="loadData" />
        </el-form-item>
        <el-form-item label="年份">
          <el-input-number v-model="filters.year" :min="1990" :max="2030" clearable controls-position="right" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.book_type" clearable placeholder="类型">
            <el-option v-for="t in bookTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="tableData" stripe border style="width: 100%; margin-top: 16px">
      <el-table-column prop="title" label="书名" min-width="200" show-overflow-tooltip />
      <el-table-column prop="publisher" label="出版社" width="150" show-overflow-tooltip />
      <el-table-column prop="publish_date" label="出版时间" width="110" />
      <el-table-column prop="book_type" label="类型" width="80" />
      <el-table-column prop="total_words" label="总字数(万)" width="100" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="showDialog(row)">编辑</el-button>
          <el-button size="small" @click="showAttachments(row)">附件</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑专著' : '新增专著'" width="600px" destroy-on-close>
      <el-form :model="form" label-width="130px">
        <el-form-item label="书名" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="出版社">
          <el-input v-model="form.publisher" />
        </el-form-item>
        <el-form-item label="出版时间">
          <el-date-picker v-model="form.publish_date" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.book_type" clearable>
            <el-option v-for="t in bookTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="ISBN">
          <el-input v-model="form.isbn" />
        </el-form-item>
        <el-form-item label="总字数(万字)">
          <el-input-number v-model="form.total_words" :min="0" :precision="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="本人撰写(万字)">
          <el-input-number v-model="form.my_words" :min="0" :precision="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="全部作者">
          <el-input v-model="form.authors" placeholder="逗号分隔" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>

      <el-divider v-if="savedId" />
      <div v-if="savedId">
        <h4 style="margin-bottom: 10px">上传证明材料</h4>
        <AttachmentManager entity-type="book" :entity-id="savedId" />
      </div>

      <template #footer>
        <el-button @click="closeDialog">{{ isEdit ? '完成' : '取消' }}</el-button>
        <el-button type="primary" @click="handleSubmit" >保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="attachDialogVisible" title="附件管理" width="600px" destroy-on-close>
      <AttachmentManager v-if="currentRow" entity-type="book" :entity-id="currentRow.id" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'
import AttachmentManager from '../components/AttachmentManager.vue'

const bookTypes = ['专著', '编著', '译著', '教材']

const tableData = ref([])
const dialogVisible = ref(false)
const attachDialogVisible = ref(false)
const isEdit = ref(false)
const currentRow = ref(null)
const savedId = ref(null)
const filters = ref({ keyword: '', year: null, book_type: '' })

const defaultForm = () => ({
  title: '', publisher: '', publish_date: null, book_type: '',
  isbn: '', total_words: null, my_words: null, authors: '', notes: '',
})
const form = ref(defaultForm())

async function loadData() {
  const params = {}
  if (filters.value.keyword) params.keyword = filters.value.keyword
  if (filters.value.year) params.year = filters.value.year
  if (filters.value.book_type) params.book_type = filters.value.book_type
  const { data } = await api.get('/books', { params })
  tableData.value = data
}

function resetFilters() { filters.value = { keyword: '', year: null, book_type: '' }; loadData() }

function showDialog(row) {
  if (row) { isEdit.value = true; currentRow.value = row; savedId.value = row.id; form.value = { ...row } }
  else { isEdit.value = false; currentRow.value = null; savedId.value = null; form.value = defaultForm() }
  dialogVisible.value = true
}

function closeDialog() { dialogVisible.value = false; savedId.value = null; loadData() }

function showAttachments(row) { currentRow.value = row; attachDialogVisible.value = true }

async function handleSubmit() {
  if (!form.value.title) { ElMessage.warning('请填写书名'); return }
  if (isEdit.value) { await api.put(`/books/${currentRow.value.id}`, form.value); ElMessage.success('更新成功'); dialogVisible.value = false; savedId.value = null }
  else { const { data } = await api.post('/books', form.value); savedId.value = data.id; isEdit.value = true; currentRow.value = data; ElMessage.success('创建成功，请上传证明材料') }
  loadData()
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await api.delete(`/books/${row.id}`); ElMessage.success('删除成功'); loadData()
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
