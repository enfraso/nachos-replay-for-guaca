<template>
    <div class="upload-replay">
        <!-- Drag & Drop Area -->
        <div 
            class="upload-area"
            :class="{ 'drag-over': isDragging, 'uploading': isUploading }"
            @drop.prevent="handleDrop"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @click="triggerFileInput"
        >
            <input 
                ref="fileInput"
                type="file"
                accept=".guac"
                @change="handleFileSelect"
                style="display: none"
            />
            
            <div v-if="!selectedFile && !isUploading" class="upload-prompt">
                <div class="upload-icon">📁</div>
                <h3>{{ $t('upload.title') || 'Upload Replay' }}</h3>
                <p class="text-muted">
                    {{ $t('upload.dragDrop') || 'Arraste um arquivo .guac aqui ou clique para selecionar' }}
                </p>
                <button class="btn btn-primary">
                    {{ $t('upload.selectFile') || 'Selecionar Arquivo' }}
                </button>
            </div>
            
            <div v-else-if="selectedFile && !isUploading" class="file-preview">
                <div class="file-icon">📄</div>
                <div class="file-info">
                    <h4>{{ selectedFile.name }}</h4>
                    <p class="text-muted">{{ formatBytes(selectedFile.size) }}</p>
                </div>
                <button class="btn btn-ghost btn-sm" @click.stop="clearFile">
                    ✕
                </button>
            </div>
            
            <div v-else-if="isUploading" class="upload-progress">
                <div class="spinner spinner-lg"></div>
                <p>{{ uploadMessage }}</p>
                <div class="progress-bar">
                    <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
                </div>
                <p class="text-sm text-muted">{{ uploadProgress }}%</p>
            </div>
        </div>
        
        <!-- Error Message -->
        <div v-if="error" class="alert alert-error">
            <span class="alert-icon">⚠️</span>
            <span>{{ error }}</span>
            <button class="btn btn-ghost btn-sm" @click="error = null">✕</button>
        </div>
        
        <!-- Success Message -->
        <div v-if="success" class="alert alert-success">
            <span class="alert-icon">✅</span>
            <span>{{ success }}</span>
        </div>
        
        <!-- Upload Button -->
        <div v-if="selectedFile && !isUploading" class="upload-actions">
            <button class="btn btn-secondary" @click="clearFile">
                {{ $t('common.cancel') || 'Cancelar' }}
            </button>
            <button class="btn btn-primary" @click="uploadFile">
                {{ $t('upload.upload') || 'Fazer Upload' }}
            </button>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useReplaysStore } from '@/stores/replays'

const emit = defineEmits(['uploaded', 'close'])

const router = useRouter()
const replaysStore = useReplaysStore()

const fileInput = ref(null)
const selectedFile = ref(null)
const isDragging = ref(false)
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadMessage = ref('')
const error = ref(null)
const success = ref(null)

function triggerFileInput() {
    if (!isUploading.value) {
        fileInput.value?.click()
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0]
    if (file) {
        validateAndSetFile(file)
    }
}

function handleDrop(event) {
    isDragging.value = false
    const file = event.dataTransfer.files[0]
    if (file) {
        validateAndSetFile(file)
    }
}

function validateAndSetFile(file) {
    error.value = null
    
    // Validate extension
    if (!file.name.endsWith('.guac')) {
        error.value = 'Apenas arquivos .guac são permitidos'
        return
    }
    
    // Validate size (max 500MB)
    const maxSize = 500 * 1024 * 1024
    if (file.size > maxSize) {
        error.value = 'Arquivo muito grande. Tamanho máximo: 500MB'
        return
    }
    
    if (file.size === 0) {
        error.value = 'Arquivo está vazio'
        return
    }
    
    selectedFile.value = file
}

function clearFile() {
    selectedFile.value = null
    error.value = null
    success.value = null
    if (fileInput.value) {
        fileInput.value.value = ''
    }
}

async function uploadFile() {
    if (!selectedFile.value) return
    
    isUploading.value = true
    uploadProgress.value = 0
    uploadMessage.value = 'Preparando upload...'
    error.value = null
    success.value = null
    
    try {
        // Create FormData
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        
        uploadMessage.value = 'Enviando arquivo...'
        
        // Upload via store
        const replay = await replaysStore.uploadReplay(formData, (progress) => {
            uploadProgress.value = progress
            uploadMessage.value = `Enviando... ${progress}%`
        })
        
        uploadProgress.value = 100
        uploadMessage.value = 'Upload concluído!'
        success.value = `Arquivo "${selectedFile.value.name}" enviado com sucesso!`
        
        // Emit event
        emit('uploaded', replay)
        
        // Wait a bit to show success message
        setTimeout(() => {
            // Redirect to player
            router.push(`/replays/${replay.id}`)
        }, 1500)
        
    } catch (err) {
        console.error('Upload error:', err)
        error.value = err.response?.data?.detail || err.message || 'Erro ao fazer upload'
        isUploading.value = false
        uploadProgress.value = 0
    }
}

function formatBytes(bytes) {
    if (!bytes) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}
</script>

<style scoped>
.upload-replay {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
}

.upload-area {
    border: 2px dashed var(--color-gray-300);
    border-radius: var(--radius-lg);
    padding: var(--spacing-2xl);
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    background: var(--bg-primary);
    min-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.upload-area:hover:not(.uploading) {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
}

.upload-area.drag-over {
    border-color: var(--color-primary-500);
    background: var(--color-primary-100);
    transform: scale(1.02);
}

.upload-area.uploading {
    cursor: not-allowed;
    border-style: solid;
}

.upload-prompt {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md);
}

.upload-icon {
    font-size: 4rem;
    margin-bottom: var(--spacing-sm);
}

.upload-prompt h3 {
    margin: 0;
    color: var(--text-primary);
}

.file-preview {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    background: var(--bg-secondary);
    border-radius: var(--radius-md);
    width: 100%;
    max-width: 500px;
}

.file-icon {
    font-size: 3rem;
}

.file-info {
    flex: 1;
    text-align: left;
}

.file-info h4 {
    margin: 0 0 var(--spacing-xs) 0;
    font-size: var(--font-size-md);
    word-break: break-all;
}

.upload-progress {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md);
    width: 100%;
    max-width: 400px;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background: var(--color-gray-200);
    border-radius: var(--radius-full);
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: var(--color-primary-500);
    transition: width 0.3s ease;
    border-radius: var(--radius-full);
}

.upload-actions {
    display: flex;
    gap: var(--spacing-md);
    justify-content: flex-end;
}

.alert {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    border-radius: var(--radius-md);
}

.alert-error {
    background: rgba(239, 68, 68, 0.1);
    color: var(--color-error-700);
    border: 1px solid var(--color-error-200);
}

.alert-success {
    background: rgba(34, 197, 94, 0.1);
    color: var(--color-success-700);
    border: 1px solid var(--color-success-200);
}

.alert-icon {
    font-size: 1.25rem;
}

.spinner {
    border: 3px solid var(--color-gray-300);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.spinner-lg {
    width: 48px;
    height: 48px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
    .upload-area {
        padding: var(--spacing-lg);
        min-height: 250px;
    }
    
    .upload-icon {
        font-size: 3rem;
    }
    
    .upload-actions {
        flex-direction: column-reverse;
    }
    
    .upload-actions button {
        width: 100%;
    }
}
</style>
