<template>
    <div class="audit-page">
        <div class="page-header">
            <div>
                <h2>{{ $t('audit.title') }}</h2>
                <p class="text-muted">{{ $t('audit.subtitle') }}</p>
            </div>
        </div>

        <!-- Filters -->
        <div class="filters-section">
            <div class="filters-row">
                <input
                    v-model="searchQuery"
                    type="text"
                    class="form-input flex-1"
                    placeholder="Buscar por usuário ou ação..."
                    @keyup.enter="fetchLogs"
                />
                <input
                    v-model="filterDate"
                    type="date"
                    class="form-input"
                />
                <button class="btn btn-primary" @click="fetchLogs">
                    🔍 {{ $t('common.search') }}
                </button>
            </div>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="loading-container">
            <div class="spinner spinner-lg"></div>
        </div>

        <!-- Empty State -->
        <div v-else-if="logs.length === 0" class="empty-state">
            <div class="empty-state-icon">📋</div>
            <div class="empty-state-title">{{ $t('audit.noLogs') }}</div>
        </div>

        <!-- Logs Table -->
        <div v-else class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>{{ $t('audit.timestamp') }}</th>
                        <th>{{ $t('common.user') }}</th>
                        <th>{{ $t('audit.action') }}</th>
                        <th>{{ $t('audit.resource') }}</th>
                        <th>{{ $t('audit.ip') }}</th>
                        <th>{{ $t('audit.details') }}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="log in logs" :key="log.id">
                        <td>{{ formatDate(log.timestamp) }}</td>
                        <td><strong>{{ log.username }}</strong></td>
                        <td>
                            <span :class="['badge', getActionBadge(log.action)]">
                                {{ log.action }}
                            </span>
                        </td>
                        <td>{{ log.resource_type }}/{{ log.resource_id }}</td>
                        <td><code>{{ log.ip_address }}</code></td>
                        <td class="truncate" style="max-width: 200px">
                            {{ log.details || '-' }}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Pagination -->
        <div v-if="logs.length > 0" class="pagination-container">
            <div class="pagination-info">
                {{ $t('pagination.showing') }} {{ logs.length }} {{ $t('pagination.results') }}
            </div>
            <div class="pagination">
                <button
                    class="pagination-item"
                    :class="{ disabled: page <= 1 }"
                    @click="prevPage"
                >
                    ←
                </button>
                <span class="pagination-item active">{{ page }}</span>
                <button
                    class="pagination-item"
                    :class="{ disabled: !hasMore }"
                    @click="nextPage"
                >
                    →
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/composables/useApi'

const { locale } = useI18n()

const logs = ref([])
const isLoading = ref(true)
const searchQuery = ref('')
const filterDate = ref('')
const page = ref(1)
const hasMore = ref(true)

function formatDate(dateStr) {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString(locale.value)
}

function getActionBadge(action) {
    const actions = {
        login: 'badge-success',
        logout: 'badge-gray',
        create: 'badge-primary',
        update: 'badge-warning',
        delete: 'badge-error',
        view: 'badge-accent'
    }
    return actions[action?.toLowerCase()] || 'badge-gray'
}

async function fetchLogs() {
    isLoading.value = true
    try {
        const params = new URLSearchParams({ page: page.value, per_page: 20 })
        if (searchQuery.value) params.append('search', searchQuery.value)
        if (filterDate.value) params.append('date', filterDate.value)
        
        const { data } = await api.get(`/api/audit?${params}`)
        logs.value = data.items || data || []
        hasMore.value = logs.value.length >= 20
    } catch (err) {
        console.error('Failed to fetch audit logs:', err)
        logs.value = []
    } finally {
        isLoading.value = false
    }
}

function nextPage() {
    if (hasMore.value) {
        page.value++
        fetchLogs()
    }
}

function prevPage() {
    if (page.value > 1) {
        page.value--
        fetchLogs()
    }
}

onMounted(() => fetchLogs())
</script>

<style scoped>
.audit-page {
    max-width: var(--content-max-width);
}

.page-header {
    margin-bottom: var(--spacing-lg);
}

.filters-section {
    margin-bottom: var(--spacing-lg);
}

.filters-row {
    display: flex;
    gap: var(--spacing-sm);
}

.loading-container {
    text-align: center;
    padding: var(--spacing-3xl);
}

.pagination-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: var(--spacing-lg);
}

@media (max-width: 768px) {
    .filters-row {
        flex-direction: column;
    }
}
</style>
