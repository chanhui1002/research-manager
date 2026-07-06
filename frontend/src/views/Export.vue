<template>
  <div>
    <h2 style="margin-bottom: 20px">数据导出</h2>

    <el-card>
      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="成果类型">
          <el-select v-model="exportForm.entity_type" @change="onTypeChange">
            <el-option label="论文" value="paper" />
            <el-option label="专著" value="book" />
            <el-option label="项目" value="project" />
            <el-option label="奖励" value="award" />
            <el-option label="采纳证明" value="adoption" />
            <el-option label="荣誉称号" value="honor" />
            <el-option label="培训证明" value="training" />
          </el-select>
        </el-form-item>

        <el-form-item label="关键词">
          <el-input v-model="exportForm.keyword" placeholder="按标题筛选（可选）" clearable style="width: 300px" />
        </el-form-item>

        <el-form-item label="年份范围">
          <el-input-number v-model="exportForm.year_start" :min="1990" :max="2030" placeholder="起始" controls-position="right" style="width: 130px" />
          <span style="margin: 0 8px">至</span>
          <el-input-number v-model="exportForm.year_end" :min="1990" :max="2030" placeholder="结束" controls-position="right" style="width: 130px" />
        </el-form-item>

        <el-form-item label="导出字段">
          <el-checkbox-group v-model="exportForm.selectedFields">
            <el-checkbox v-for="(label, key) in availableFields" :key="key" :label="key">
              {{ label }}
            </el-checkbox>
          </el-checkbox-group>
          <div style="margin-top: 8px">
            <el-button size="small" @click="selectAllFields">全选</el-button>
            <el-button size="small" @click="exportForm.selectedFields = []">清空</el-button>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleExport" :loading="exporting">
            <el-icon><Download /></el-icon> 导出Excel
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api/index.js'

const availableFields = ref({})
const exporting = ref(false)

const exportForm = reactive({
  entity_type: 'paper',
  keyword: '',
  year_start: null,
  year_end: null,
  selectedFields: [],
})

async function loadFields() {
  const { data } = await api.get(`/export/${exportForm.entity_type}/fields`)
  availableFields.value = data
  exportForm.selectedFields = Object.keys(data)
}

function onTypeChange() {
  loadFields()
}

function selectAllFields() {
  exportForm.selectedFields = Object.keys(availableFields.value)
}

async function handleExport() {
  if (exportForm.selectedFields.length === 0) {
    ElMessage.warning('请至少选择一个导出字段')
    return
  }
  exporting.value = true
  try {
    const params = new URLSearchParams()
    if (exportForm.keyword) params.append('keyword', exportForm.keyword)
    if (exportForm.year_start) params.append('year_start', exportForm.year_start)
    if (exportForm.year_end) params.append('year_end', exportForm.year_end)
    params.append('fields', exportForm.selectedFields.join(','))

    const response = await api.get(`/export/${exportForm.entity_type}?${params.toString()}`, {
      responseType: 'blob',
    })

    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${exportForm.entity_type}_export.xlsx`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(loadFields)
</script>
