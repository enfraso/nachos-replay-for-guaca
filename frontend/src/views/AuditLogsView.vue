<template>
  <div class="audit-page">
    <!-- Header -->
    <div class="page-header">
      <h2>{{ $t('audit.title') }}</h2>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="exportLogs('csv')">
          📥 {{ $t('audit.exportCsv') }}
        </button>
        <button class="btn btn-secondary" @click="exportLogs('json')">
          📥 {{ $t('audit.exportJson') }}
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-card card">
      <div class="card-body">
        <div class="filters-grid">
          <div class="form-group">
            <input
              v-model="filters.username"
              type="text"
              class="form-input"
              :placeholder="$t('audit.user')"
            />
          </div>
          <div class="form-group">
            <select v-model="filters.action" class="form-select">
              <option value="">{{ $t('common.all') }} {{ $t('audit.action') }}</option>
              <option v-for="action in actions" :key="action" :value="action">
                {{ $t(`audit.actions.${action}`) }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <input
              v-model="filters.ip"
              type="text"
              class="form-input"
              :placeholder="$t('audit.ip')"
            />
          </div>
          <div class="form-group">
            <input
              v-model="filters.dateFrom"
              type="date"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <input
              v-model="filters.dateTo"
              type="date"
              class="form-input"
            />
          </div>
          <button class="btn btn-primary" @click="fetchLogs">
            {{ $t('common.filter') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="card">
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>{{ $t('audit.timestamp') }}</th>
              <th>{{ $t('audit.user') }}</th>
              <th>{{ $t('audit.action') }}</th>
              <th>{{ $t('audit.ip') }}</th>
              <th>{{ $t('audit.details') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="5" class="text-center p-lg">
                <div class="spinner"></div>
              </td>
            </tr>
            <tr v-else-if="logs.length === 0">
              <td colspan="5" class="text-center p-lg text-muted">
                {{ $t('common.noData') }}
              </td>
            </tr>
            <tr v-for="log in logs" :key="log.id">
              <td>{{ formatDate(log.created_at) }}</td>
              <td>{{ log.username || '-' }}</td>
              <td>
                <span :class="['badge', getActionBadge(log.action)]">
                  {{ $t(`audit.actions.${log.action}`) }}
                </span>
              </td>
              <td>{{ log.ip_address || '-' }}</td>
              <td class="details-cell">
                <code v-if="log.details && Object.keys(log.details).length">
                  {{ JSON.stringify(log.details).slice(0, 50) }}...
                </code>
                <span v-else class="text-muted">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="card-footer">
        <div class="pagination-info">
          {{ $t('common.page') }} {{ page }} {{ $t('common.of') }} {{ totalPages }}
        </div>
        <div class="pagination">
          <button 
            class="pagination-item"
            :disabled="page === 1"
            @click="goToPage(page - 1)"
          >
            ←
          </button>
          <button 
            class="pagination-item"
            :disabled="page === totalPages"
            @click="goToPage(page + 1)"
          >
            →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/composables/useApi'

const { locale } = useI18n()

const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const isLoading = ref(false)

const filters = reactive({
  username: '',
  action: '',
  ip: '',
  dateFrom: '',
  dateTo: ''
})

const actions = ['view', 'download', 'search', 'login', 'logout', 'export', 'create', 'update', 'delete']

const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1)

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString(locale.value)
}

function getActionBadge(action) {
  const badges = {
    view: 'badge-primary',
    download: 'badge-accent',
    search: 'badge-primary',
    login: 'badge-success',
    logout: 'badge-warning',
    export: 'badge-accent',
    create: 'badge-success',
    update: 'badge-warning',
    delete: 'badge-error'
  }
  return badges[action] || 'badge-primary'
}

async function fetchLogs() {
  isLoading.value = true

  try {
    const params = new URLSearchParams()
    params.append('page', page.value)
    params.append('page_size', pageSize.value)
    
    if (filters.username) params.append('username', filters.username)
    if (filters.action) params.append('action', filters.action)
    if (filters.ip) params.append('ip_address', filters.ip)
    if (filters.dateFrom) params.append('date_from', filters.dateFrom)
    if (filters.dateTo) params.append('date_to', filters.dateTo)

    const response = await api.get(`/api/audit/logs?${params.toString()}`)
    
    logs.value = response.data.items
    total.value = response.data.total
  } catch (err) {
    console.error('Failed to fetch audit logs:', err)
  } finally {
    isLoading.value = false
  }
}

function goToPage(newPage) {
  page.value = newPage
  fetchLogs()
}

async function exportLogs(format) {
  try {
    const params = new URLSearchParams()
    params.append('format', format)
    
    if (filters.username) params.append('username', filters.username)
    if (filters.action) params.append('action', filters.action)
    if (filters.dateFrom) params.append('date_from', filters.dateFrom)
    if (filters.dateTo) params.append('date_to', filters.dateTo)

    const response = await api.get(`/api/audit/export?${params.toString()}`, {
      responseType: 'blob'
    })

    // Download file
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `audit_logs.${format}`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (err) {
    console.error('Failed to export logs:', err)
  }
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.filters-card {
  margin-bottom: var(--spacing-lg);
}

.filters-grid {
  display: flex;
  gap: var(--spacing-md);
  align-items: flex-end;
  flex-wrap: wrap;
}

.filters-grid .form-group {
  margin-bottom: 0;
  flex: 1;
  min-width: 120px;
}

.details-cell {
  max-width: 200px;
}

.details-cell code {
  font-size: var(--font-size-xs);
  background: var(--color-gray-100);
  padding: 2px 4px;
  border-radius: var(--border-radius-sm);
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pagination-info {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}
</style>
