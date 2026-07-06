<template>
  <div class="attachment-manager">
    <div class="upload-area">
      <el-upload
        :action="`/api/attachments/${entityType}/${entityId}`"
        :on-success="onUploadSuccess"
        :on-error="onUploadError"
        :before-upload="beforeUpload"
        :show-file-list="false"
        :data="{ label: uploadLabel }"
        multiple
        name="file"
      >
        <el-button type="primary" size="small">
          <el-icon><Upload /></el-icon> 上传附件
        </el-button>
      </el-upload>
      <el-input
        v-model="uploadLabel"
        placeholder="附件标签（可选，如：录用通知、检索证明）"
        size="small"
        style="width: 250px; margin-left: 10px"
      />
    </div>

    <el-table :data="attachments" stripe size="small" style="margin-top: 12px" v-loading="loading">
      <el-table-column prop="original_filename" label="文件名" min-width="180" show-overflow-tooltip />
      <el-table-column prop="label" label="标签" width="110" />
      <el-table-column prop="file_size" label="大小" width="90">
        <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="previewFile(row)" v-if="canPreview(row)">预览</el-button>
          <el-button size="small" @click="downloadFile(row)">下载</el-button>
          <el-button size="small" type="danger" @click="deleteFile(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="previewVisible" title="文件预览" width="80%" top="5vh" destroy-on-close>
      <div class="preview-container">
        <iframe v-if="previewUrl" :src="previewUrl" class="preview-iframe"></iframe>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api/index.js'

const props = defineProps({
  entityType: { type: String, required: true },
  entityId: { type: String, required: true },
})

const attachments = ref([])
const uploadLabel = ref('')
const loading = ref(false)
const previewVisible = ref(false)
const previewUrl = ref('')

async function loadAttachments() {
  loading.value = true
  try {
    const { data } = await api.get(`/attachments/${props.entityType}/${props.entityId}`)
    attachments.value = data
  } finally {
    loading.value = false
  }
}

function onUploadSuccess() {
  ElMessage.success('上传成功')
  loadAttachments()
}

function onUploadError() {
  ElMessage.error('上传失败，请重试')
}

function beforeUpload(file) {
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件不能超过50MB')
    return false
  }
  return true
}

function canPreview(row) {
  if (!row.mime_type) return false
  return row.mime_type === 'application/pdf' ||
         row.mime_type.startsWith('image/')
}

function previewFile(row) {
  previewUrl.value = `/api/attachments/preview/${row.id}`
  previewVisible.value = true
}

function downloadFile(row) {
  window.open(`/api/attachments/download/${row.id}`, '_blank')
}

async function deleteFile(row) {
  await ElMessageBox.confirm('确定删除该附件？', '提示', { type: 'warning' })
  await api.delete(`/attachments/remove/${row.id}`)
  ElMessage.success('删除成功')
  loadAttachments()
}

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

onMounted(loadAttachments)
</script>

<style scoped>
.upload-area {
  display: flex;
  align-items: center;
}
.preview-container {
  width: 100%;
  height: 70vh;
}
.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
