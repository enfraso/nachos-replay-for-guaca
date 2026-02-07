<template>
    <div class="replays-page">
        <!-- Header -->
        <div class="page-header">
            <div>
                <h2>{{ $t('replays.title') }}</h2>
                <p class="text-muted">{{ $t('replays.subtitle') }}</p>
            </div>
        </div>

        <!-- Filters -->
        <div class="filters-section">
            <div class="search-box">
                <input
                    v-model="searchQuery"
                    type="text"
                    class="form-input"
                    :placeholder="$t('replays.searchPlaceholder')"
                    @keyup.enter="applyFilters"
                />
                <button class="btn btn-primary" @click="applyFilters">
                    🔍 {{ $t('common.search') }}
                </button>
            </div>
            
            <div class="filters-row">
                <input
                    v-model="filterStartDate"
                    type="date"
                    class="form-input filter-input"
                />
                <input
                    v-model="filterEndDate"
                    type="date"
                    class="form-input filter-input"
                />
                <button class="btn btn-secondary" @click="resetFilters">
                    {{ $t('common.clear') }}
                </button>
            </div>
        </div>

        <!-- Loading -->
        <div v-if="replaysStore.isLoading" class="loading-container">
            <div class="spinner spinner-lg"></div>
            <p>{{ $t('common.loading') }}</p>
        </div>

        <!-- Empty State -->
        <div v-else-if="replaysStore.replays.length === 0" class="empty-state">
            <div class="empty-state-icon">🎬</div>
            <div class="empty-state-title">{{ $t('replays.noReplays') }}</div>
            <div class="empty-state-description">{{ $t('common.noResults') }}</div>
        </div>

        <!-- Replays Table (Desktop) -->
        <div v-else class="table-container hide-mobile">
            <table class="table">
                <thead>
                    <tr>
                        <th>{{ $t('common.user') }}</th>
                        <th>{{ $t('replays.hostname') }}</th>
                        <th>{{ $t('replays.protocol') }}</th>
                        <th>{{ $t('replays.startDate') }}</th>
                        <th>{{ $t('replays.duration') }}</th>
                        <th>{{ $t('replays.size') }}</th>
                        <th>{{ $t('common.actions') }}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="replay in replaysStore.replays" :key="replay.id">
                        <td>
                            <strong>{{ replay.username }}</strong>
                        </td>
                        <td>{{ replay.hostname || '-' }}</td>
                        <td>
                            <span class="badge badge-primary">{{ replay.protocol?.toUpperCase() || 'RDP' }}</span>
                        </td>
                        <td>{{ formatDate(replay.start_time) }}</td>
                        <td>{{ formatDuration(replay.duration) }}</td>
                        <td>{{ formatBytes(replay.size_bytes) }}</td>
                        <td class="table-actions">
                            <router-link
                                :to="`/replays/${replay.id}`"
                                class="btn btn-sm btn-primary"
                            >
                                ▶ {{ $t('replays.play') }}
                            </router-link>
                            <button
                                v-if="authStore.isAdmin"
                                class="btn btn-sm btn-danger"
                                @click="confirmDelete(replay)"
                            >
                                🗑️
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Replays Cards (Mobile) -->
        <div class="replays-cards hide-desktop">
            <div v-for="replay in replaysStore.replays" :key="replay.id" class="replay-card">
                <div class="replay-card-header">
                    <strong>{{ replay.username }}</strong>
                    <span class="badge badge-primary">{{ replay.protocol?.toUpperCase() || 'RDP' }}</span>
                </div>
                <div class="replay-card-body">
                    <div class="replay-info">
                        <span class="label">Host:</span>
                        <span>{{ replay.hostname || '-' }}</span>
                    </div>
                    <div class="replay-info">
                        <span class="label">Data:</span>
                        <span>{{ formatDate(replay.start_time) }}</span>
                    </div>
                    <div class="replay-info">
                        <span class="label">Duração:</span>
                        <span>{{ formatDuration(replay.duration) }}</span>
                    </div>
                </div>
                <div class="replay-card-footer">
                    <router-link
                        :to="`/replays/${replay.id}`"
                        class="btn btn-sm btn-primary btn-block"
                    >
                        ▶ {{ $t('replays.play') }}
                    </router-link>
                </div>
            </div>
        </div>

        <!-- Pagination -->
        <div v-if="replaysStore.replays.length > 0" class="pagination-container">
            <div class="pagination-info">
                {{ $t('pagination.showing') }} {{ (replaysStore.page - 1) * replaysStore.perPage + 1 }}-{{ Math.min(replaysStore.page * replaysStore.perPage, replaysStore.total) }} {{ $t('pagination.of') }} {{ replaysStore.total }}
            </div>
            <div class="pagination">
                <button
                    class="pagination-item"
                    :class="{ disabled: !replaysStore.hasPrevPage }"
                    @click="replaysStore.prevPage()"
                >
                    ←
                </button>
                <span class="pagination-item active">{{ replaysStore.page }}</span>
                <button
                    class="pagination-item"
                    :class="{ disabled: !replaysStore.hasNextPage }"
                    @click="replaysStore.nextPage()"
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
import { useAuthStore } from '@/stores/auth'
import { useReplaysStore } from '@/stores/replays'

const { locale } = useI18n()
const authStore = useAuthStore()
const replaysStore = useReplaysStore()

const searchQuery = ref('')
const filterStartDate = ref('')
const filterEndDate = ref('')

function formatDate(dateStr) {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString(locale.value, {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    })
}

function formatDuration(seconds) {
    if (!seconds) return '-'
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    if (h > 0) return `${h}h ${m}m ${s}s`
    if (m > 0) return `${m}m ${s}s`
    return `${s}s`
}

function formatBytes(bytes) {
    if (!bytes) return '-'
    const units = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

function applyFilters() {
    replaysStore.setFilters({
        search: searchQuery.value,
        startDate: filterStartDate.value,
        endDate: filterEndDate.value
    })
    replaysStore.fetchReplays(true)
}

function resetFilters() {
    searchQuery.value = ''
    filterStartDate.value = ''
    filterEndDate.value = ''
    replaysStore.resetFilters()
    replaysStore.fetchReplays(true)
}

function confirmDelete(replay) {
    if (confirm(`Tem certeza que deseja excluir este replay?`)) {
        replaysStore.deleteReplay(replay.id)
    }
}

onMounted(() => {
    replaysStore.fetchReplays()
})
</script>

<style scoped>
.replays-page {
    max-width: var(--content-max-width);
}

.page-header {
    margin-bottom: var(--spacing-lg);
}

.page-header h2 {
    margin-bottom: var(--spacing-xs);
}

.filters-section {
    background: var(--bg-card);
    padding: var(--spacing-lg);
    border-radius: var(--radius-lg);
    margin-bottom: var(--spacing-lg);
}

.search-box {
    display: flex;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
}

.search-box .form-input {
    flex: 1;
}

.filters-row {
    display: flex;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
}

.filter-input {
    width: 180px;
}

.loading-container {
    text-align: center;
    padding: var(--spacing-3xl);
}

.loading-container .spinner {
    margin: 0 auto var(--spacing-md);
}

.replays-cards {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
}

.replay-card {
    background: var(--bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-color);
    overflow: hidden;
}

.replay-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--border-color);
    background: var(--color-gray-50);
}

.replay-card-body {
    padding: var(--spacing-md);
}

.replay-info {
    display: flex;
    justify-content: space-between;
    margin-bottom: var(--spacing-xs);
    font-size: var(--font-size-sm);
}

.replay-info .label {
    color: var(--text-muted);
}

.replay-card-footer {
    padding: var(--spacing-md);
    border-top: 1px solid var(--border-color);
}

.pagination-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: var(--spacing-lg);
    flex-wrap: wrap;
    gap: var(--spacing-md);
}

.pagination-info {
    font-size: var(--font-size-sm);
    color: var(--text-muted);
}

@media (max-width: 768px) {
    .filters-section {
        padding: var(--spacing-md);
    }
    
    .search-box {
        flex-direction: column;
    }
    
    .filter-input {
        width: 100%;
    }
    
    .pagination-container {
        flex-direction: column;
        align-items: stretch;
    }
    
    .pagination {
        justify-content: center;
    }
}
</style>
