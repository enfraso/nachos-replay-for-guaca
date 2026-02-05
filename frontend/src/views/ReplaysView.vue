<template>
  <div class="replays-page">
    <!-- Header -->
    <div class="page-header">
      <h2>{{ $t('replays.title') }}</h2>
      <div class="header-actions">
        <button 
          v-if="replaysStore.hasFilters" 
          class="btn btn-secondary"
          @click="replaysStore.clearFilters(); fetchReplays()"
        >
          {{ $t('common.clear') }}
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-card card">
      <div class="card-body">
        <div class="filters-grid">
          <div class="form-group">
            <input
              v-model="filters.query"
              type="text"
              class="form-input"
              :placeholder="$t('replays.search')"
              @keyup.enter="applyFilters"
            />
          </div>
          <div class="form-group">
            <input
              v-model="filters.username"
              type="text"
              class="form-input"
              :placeholder="$t('replays.user')"
            />
          </div>
          <div class="form-group">
            <input
              v-model="filters.clientIp"
              type="text"
              class="form-input"
              :placeholder="$t('replays.ip')"
            />
          </div>
          <div class="form-group">
            <select v-model="filters.status" class="form-select">
              <option value="">{{ $t('common.all') }} {{ $t('replays.status') }}</option>
              <option value="active">{{ $t('replays.active') }}</option>
              <option value="archived">{{ $t('replays.archived') }}</option>
            </select>
          </div>
          <button class="btn btn-primary" @click="applyFilters">
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
              <th>{{ $t('replays.session') }}</th>
              <th>{{ $t('replays.user') }}</th>
              <th>{{ $t('replays.ip') }}</th>
              <th>{{ $t('replays.duration') }}</th>
              <th>{{ $t('replays.date') }}</th>
              <th>{{ $t('replays.size') }}</th>
              <th>{{ $t('replays.status') }}</th>
              <th>{{ $t('replays.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="replaysStore.isLoading">
              <td colspan="8" class="text-center p-lg">
                <div class="spinner"></div>
              </td>
            </tr>
            <tr v-else-if="replaysStore.replays.length === 0">
              <td colspan="8" class="text-center p-lg text-muted">
                {{ $t('replays.noResults') }}
              </td>
            </tr>
            <tr v-for="replay in replaysStore.replays" :key="replay.id">
              <td>
                <div class="replay-name">
                  <span class="filename">{{ replay.session_name || replay.filename }}</span>
                </div>
              </td>
              <td>{{ replay.owner_username || '-' }}</td>
              <td>{{ replay.client_ip || '-' }}</td>
              <td>{{ formatDuration(replay.duration_seconds) }}</td>
              <td>{{ formatDate(replay.session_start || replay.imported_at) }}</td>
              <td>{{ formatBytes(replay.file_size) }}</td>
              <td>
                <span :class="['badge', `badge-${getStatusColor(replay.status)}`]">
                  {{ $t(`replays.${replay.status}`) }}
                </span>
              </td>
              <td>
                <div class="actions">
                  <button 
                    class="btn btn-sm btn-primary"
                    @click="openPlayer(replay.id)"
                    :title="$t('replays.play')"
                  >
                    ▶
                  </button>
                  <button 
                    v-if="authStore.isAdmin"
                    class="btn btn-sm btn-danger"
                    @click="confirmDelete(replay)"
                    :title="$t('replays.delete')"
                  >
                    🗑
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="card-footer">
        <div class="pagination-info">
          {{ $t('common.showing') }} 
          {{ (replaysStore.page - 1) * replaysStore.pageSize + 1 }}
          - {{ Math.min(replaysStore.page * replaysStore.pageSize, replaysStore.total) }}
          {{ $t('common.of') }} {{ replaysStore.total }} {{ $t('common.items') }}
        </div>
        <div class="pagination">
          <button 
            class="pagination-item"
            :disabled="replaysStore.page === 1"
            @click="goToPage(replaysStore.page - 1)"
          >
            ←
          </button>
          <template v-for="p in visiblePages" :key="p">
            <button 
              class="pagination-item"
              :class="{ active: p === replaysStore.page }"
              @click="goToPage(p)"
            >
              {{ p }}
            </button>
          </template>
          <button 
            class="pagination-item"
            :disabled="replaysStore.page === replaysStore.totalPages"
            @click="goToPage(replaysStore.page + 1)"
          >
            →
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="deleteModal" class="modal-backdrop" @click.self="deleteModal = null">
      <div class="modal">
        <h3>{{ $t('replays.delete') }}</h3>
        <p>{{ $t('replays.confirmDelete') }}</p>
        <p class="text-muted text-sm">{{ deleteModal.filename }}</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="deleteModal = null">
            {{ $t('common.cancel') }}
          </button>
          <button class="btn btn-danger" @click="deleteReplay">
            {{ $t('replays.delete') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useReplaysStore } from '@/stores/replays'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const { locale } = useI18n()
const replaysStore = useReplaysStore()
const authStore = useAuthStore()

const filters = reactive({
  query: '',
  username: '',
  clientIp: '',
  status: ''
})

const deleteModal = ref(null)

const visiblePages = computed(() => {
  const total = replaysStore.totalPages
  const current = replaysStore.page
  const pages = []
  
  let start = Math.max(1, current - 2)
  let end = Math.min(total, current + 2)
  
  if (end - start < 4) {
    if (start === 1) end = Math.min(total, 5)
    else start = Math.max(1, end - 4)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

function formatDuration(seconds) {
  if (!seconds) return '00:00'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString(locale.value)
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

function getStatusColor(status) {
  const colors = {
    active: 'success',
    archived: 'warning',
    deleted: 'error'
  }
  return colors[status] || 'primary'
}

function applyFilters() {
  replaysStore.setFilters(filters)
  fetchReplays()
}

async function fetchReplays() {
  await replaysStore.fetchReplays()
}

function goToPage(page) {
  replaysStore.setPage(page)
  fetchReplays()
}

function openPlayer(id) {
  router.push(`/replays/${id}`)
}

function confirmDelete(replay) {
  deleteModal.value = replay
}

async function deleteReplay() {
  if (deleteModal.value) {
    await replaysStore.deleteReplay(deleteModal.value.id)
    deleteModal.value = null
  }
}

onMounted(() => {
  fetchReplays()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
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
  min-width: 150px;
}

.replay-name .filename {
  font-weight: var(--font-weight-medium);
}

.actions {
  display: flex;
  gap: var(--spacing-xs);
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

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal-backdrop);
}

.modal {
  background: var(--bg-card);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-xl);
  max-width: 400px;
  width: 100%;
  z-index: var(--z-modal);
}

.modal h3 {
  margin-bottom: var(--spacing-md);
}

.modal-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
  margin-top: var(--spacing-lg);
}

@media (max-width: 768px) {
  .filters-grid {
    flex-direction: column;
  }
  
  .filters-grid .form-group {
    width: 100%;
  }
}
</style>
