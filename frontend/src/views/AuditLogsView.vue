<template>
    <div class="audit-page">
        <div class="page-header">
            <div>
                <h2>{{ $t('audit.title') }}</h2>
                <p class="text-muted">{{ $t('audit.subtitle') }}</p>
            </div>
            <div class="header-actions">
                <button 
                    class="btn btn-secondary" 
                    @click="exportLogs('csv')"
                    :disabled="isExporting"
                >
                    <span v-if="isExporting && exportFormat === 'csv'" class="spinner spinner-sm"></span>
                    <span v-else>📥 Exportar CSV</span>
                </button>
                <button 
                    class="btn btn-secondary" 
                    @click="exportLogs('json')"
                    :disabled="isExporting"
                >
                    <span v-if="isExporting && exportFormat === 'json'" class="spinner spinner-sm"></span>
                    <span v-else>📥 Exportar JSON</span>
                </button>
            </div>
        </div>

        <!-- Filters -->
        <div class="filters-section card">
            <div class="card-body">
                <div class="filters-row">
                    <div class="filter-group">
                        <label class="form-label">Usuário</label>
                        <input
                            v-model="filters.username"
                            type="text"
                            class="form-input"
                            placeholder="Nome de usuário..."
                        />
                    </div>
                    <div class="filter-group">
                        <label class="form-label">Ação</label>
                        <select v-model="filters.action" class="form-select">
                            <option value="">Todas</option>
                            <option value="login">Login</option>
                            <option value="logout">Logout</option>
                            <option value="view">Visualização</option>
                            <option value="download">Download</option>
                            <option value="search">Busca</option>
                            <option value="create">Criação</option>
                            <option value="update">Atualização</option>
                            <option value="delete">Exclusão</option>
                            <option value="export">Exportação</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label class="form-label">IP</label>
                        <input
                            v-model="filters.ip_address"
                            type="text"
                            class="form-input"
                            placeholder="Endereço IP..."
                        />
                    </div>
                    <div class="filter-group">
                        <label class="form-label">Data Início</label>
                        <input
                            v-model="filters.date_from"
                            type="datetime-local"
                            class="form-input"
                        />
                    </div>
                    <div class="filter-group">
                        <label class="form-label">Data Fim</label>
                        <input
                            v-model="filters.date_to"
                            type="datetime-local"
                            class="form-input"
                        />
                    </div>
                </div>
                <div class="filters-actions">
                    <button class="btn btn-primary" @click="fetchLogs">
                        🔍 Buscar
                    </button>
                    <button class="btn btn-ghost" @click="clearFilters">
                        ✖️ Limpar
                    </button>
                </div>
            </div>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="loading-container">
            <div class="spinner spinner-lg"></div>
        </div>

        <!-- Error -->
        <div v-else-if="error" class="alert alert-error">
            {{ error }}
        </div>

        <!-- Empty State -->
        <div v-else-if="logs.length === 0" class="empty-state">
            <div class="empty-state-icon">📋</div>
            <div class="empty-state-title">{{ $t('audit.noLogs') }}</div>
            <p class="text-muted">Nenhum log de auditoria encontrado</p>
        </div>

        <!-- Logs Table -->
        <div v-else class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>Data/Hora</th>
                        <th>Usuário</th>
                        <th>Ação</th>
                        <th>Replay</th>
                        <th>IP</th>
                        <th>Detalhes</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="log in logs" :key="log.id">
                        <td class="nowrap">{{ formatDate(log.created_at) }}</td>
                        <td><strong>{{ log.username || '-' }}</strong></td>
                        <td>
                            <span :class="['badge', getActionBadge(log.action)]">
                                {{ getActionLabel(log.action) }}
                            </span>
                        </td>
                        <td>
                            <router-link 
                                v-if="log.replay_id" 
                                :to="`/replays/${log.replay_id}`"
                                class="link"
                            >
                                Ver replay
                            </router-link>
                            <span v-else class="text-muted">-</span>
                        </td>
                        <td><code>{{ log.ip_address || '-' }}</code></td>
                        <td>
                            <button 
                                v-if="log.details && Object.keys(log.details).length > 0"
                                class="btn btn-ghost btn-sm"
                                @click="showDetails(log)"
                            >
                                📄 Ver
                            </button>
                            <span v-else class="text-muted">-</span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        <div v-if="logs.length > 0" class="pagination-container">
            <div class="pagination-info">
                Mostrando {{ logs.length }} de {{ total }} registros
            </div>
            <div class="pagination">
                <button
                    class="pagination-item"
                    :disabled="page <= 1"
                    @click="goToPage(page - 1)"
                >
                    ←
                </button>
                <span class="pagination-item active">{{ page }} / {{ totalPages }}</span>
                <button
                    class="pagination-item"
                    :disabled="page >= totalPages"
                    @click="goToPage(page + 1)"
                >
                    →
                </button>
            </div>
        </div>

        <!-- Details Modal -->
        <div v-if="selectedLog" class="modal-overlay" @click.self="selectedLog = null">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Detalhes do Log</h3>
                    <button class="btn btn-ghost" @click="selectedLog = null">✖️</button>
                </div>
                <div class="modal-body">
                    <div class="detail-row">
                        <span class="detail-label">ID:</span>
                        <code>{{ selectedLog.id }}</code>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Usuário:</span>
                        <span>{{ selectedLog.username }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Ação:</span>
                        <span :class="['badge', getActionBadge(selectedLog.action)]">
                            {{ getActionLabel(selectedLog.action) }}
                        </span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Data:</span>
                        <span>{{ formatDate(selectedLog.created_at) }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">IP:</span>
                        <code>{{ selectedLog.ip_address }}</code>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">User Agent:</span>
                        <small>{{ selectedLog.user_agent || '-' }}</small>
                    </div>
                    <div v-if="selectedLog.details" class="detail-row">
                        <span class="detail-label">Detalhes:</span>
                        <pre class="details-json">{{ JSON.stringify(selectedLog.details, null, 2) }}</pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/composables/useApi'

const { locale } = useI18n()

const logs = ref([])
const isLoading = ref(true)
const error = ref(null)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedLog = ref(null)
const isExporting = ref(false)
const exportFormat = ref('')

const filters = reactive({
    username: '',
    action: '',
    ip_address: '',
    date_from: '',
    date_to: ''
})

const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1)

const actionLabels = {
    login: 'Login',
    logout: 'Logout',
    view: 'Visualização',
    download: 'Download',
    search: 'Busca',
    create: 'Criação',
    update: 'Atualização',
    delete: 'Exclusão',
    export: 'Exportação'
}

function formatDate(dateStr) {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString(locale.value, {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    })
}

function getActionLabel(action) {
    return actionLabels[action?.toLowerCase()] || action
}

function getActionBadge(action) {
    const badges = {
        login: 'badge-success',
        logout: 'badge-secondary',
        view: 'badge-accent',
        download: 'badge-primary',
        search: 'badge-info',
        create: 'badge-success',
        update: 'badge-warning',
        delete: 'badge-error',
        export: 'badge-primary'
    }
    return badges[action?.toLowerCase()] || 'badge-secondary'
}

async function fetchLogs() {
    isLoading.value = true
    error.value = null
    
    try {
        const params = new URLSearchParams({
            page: page.value.toString(),
            page_size: pageSize.value.toString()
        })
        
        if (filters.username) params.append('username', filters.username)
        if (filters.action) params.append('action', filters.action)
        if (filters.ip_address) params.append('ip_address', filters.ip_address)
        if (filters.date_from) {
            params.append('date_from', new Date(filters.date_from).toISOString())
        }
        if (filters.date_to) {
            params.append('date_to', new Date(filters.date_to).toISOString())
        }
        
        const { data } = await api.get(`/api/audit/logs?${params}`)
        logs.value = data.items || []
        total.value = data.total || 0
    } catch (err) {
        console.error('Failed to fetch audit logs:', err)
        error.value = err.response?.data?.detail || 'Erro ao carregar logs de auditoria'
        logs.value = []
    } finally {
        isLoading.value = false
    }
}

function clearFilters() {
    filters.username = ''
    filters.action = ''
    filters.ip_address = ''
    filters.date_from = ''
    filters.date_to = ''
    page.value = 1
    fetchLogs()
}

function goToPage(newPage) {
    if (newPage >= 1 && newPage <= totalPages.value) {
        page.value = newPage
        fetchLogs()
    }
}

function showDetails(log) {
    selectedLog.value = log
}

async function exportLogs(format) {
    isExporting.value = true
    exportFormat.value = format
    error.value = ''
    
    try {
        const params = new URLSearchParams({ format })
        
        if (filters.username) params.append('username', filters.username)
        if (filters.action) params.append('action', filters.action)
        if (filters.date_from) {
            params.append('date_from', new Date(filters.date_from).toISOString())
        }
        if (filters.date_to) {
            params.append('date_to', new Date(filters.date_to).toISOString())
        }
        
        // Usar fetch nativo para download de arquivo
        const token = localStorage.getItem('accessToken')
        const response = await fetch(`/api/audit/export?${params}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.detail || `Erro HTTP ${response.status}`)
        }
        
        const blob = await response.blob()
        
        if (blob.size === 0) {
            throw new Error('Arquivo vazio - nenhum log encontrado')
        }
        
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `audit_logs_${new Date().toISOString().split('T')[0]}.${format}`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
    } catch (err) {
        console.error('Export failed:', err)
        error.value = `Erro ao exportar: ${err.message}`
    } finally {
        isExporting.value = false
        exportFormat.value = ''
    }
}

onMounted(() => fetchLogs())
</script>

<style scoped>
.audit-page {
    max-width: var(--content-max-width);
}

.page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-lg);
    flex-wrap: wrap;
    gap: var(--spacing-md);
}

.header-actions {
    display: flex;
    gap: var(--spacing-sm);
}

.filters-section {
    margin-bottom: var(--spacing-lg);
}

.filters-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: var(--spacing-md);
}

.filter-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
}

.filters-actions {
    display: flex;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--color-gray-200);
}

.loading-container {
    text-align: center;
    padding: var(--spacing-3xl);
}

.table-container {
    overflow-x: auto;
}

.nowrap {
    white-space: nowrap;
}

.link {
    color: var(--color-primary-500);
    text-decoration: none;
}

.link:hover {
    text-decoration: underline;
}

.pagination-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: var(--spacing-lg);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--color-gray-200);
}

.pagination {
    display: flex;
    gap: var(--spacing-xs);
}

.pagination-item {
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--color-gray-300);
    border-radius: var(--radius-sm);
    background: var(--bg-primary);
    cursor: pointer;
}

.pagination-item.active {
    background: var(--color-primary-500);
    color: white;
    border-color: var(--color-primary-500);
}

.pagination-item:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Modal */
.modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: var(--spacing-md);
}

.modal-content {
    background: var(--bg-primary);
    border-radius: var(--radius-lg);
    max-width: 600px;
    width: 100%;
    max-height: 80vh;
    overflow-y: auto;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--color-gray-200);
}

.modal-body {
    padding: var(--spacing-md);
}

.detail-row {
    display: flex;
    gap: var(--spacing-md);
    padding: var(--spacing-sm) 0;
    border-bottom: 1px solid var(--color-gray-100);
}

.detail-row:last-child {
    border-bottom: none;
}

.detail-label {
    font-weight: 600;
    min-width: 100px;
    color: var(--color-gray-600);
}

.details-json {
    background: var(--color-gray-100);
    padding: var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    overflow-x: auto;
    margin: 0;
    max-width: 400px;
}

@media (max-width: 768px) {
    .page-header {
        flex-direction: column;
    }
    
    .header-actions {
        width: 100%;
    }
    
    .header-actions button {
        flex: 1;
    }
    
    .filters-row {
        grid-template-columns: 1fr;
    }
}
</style>
