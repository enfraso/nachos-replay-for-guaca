<template>
  <div class="groups-page">
    <!-- Header -->
    <div class="page-header">
      <h2>{{ $t('groups.title') }}</h2>
      <button class="btn btn-primary" @click="showAddModal = true">
        + {{ $t('groups.add') }}
      </button>
    </div>

    <!-- Groups Grid -->
    <div class="groups-grid">
      <div v-if="isLoading" class="text-center p-lg">
        <div class="spinner"></div>
      </div>
      <div v-else-if="groups.length === 0" class="card p-lg text-center text-muted">
        {{ $t('common.noData') }}
      </div>
      <div 
        v-for="group in groups" 
        :key="group.id"
        class="card group-card"
      >
        <div class="group-header">
          <div class="group-icon">🏢</div>
          <div class="group-info">
            <h3>{{ group.name }}</h3>
            <p class="text-muted text-sm">{{ group.description || '-' }}</p>
          </div>
          <div class="group-actions">
            <button class="btn btn-sm btn-ghost" @click="editGroup(group)">
              ✏️
            </button>
            <button class="btn btn-sm btn-ghost" @click="confirmDelete(group)">
              🗑
            </button>
          </div>
        </div>
        <div class="group-stats">
          <div class="stat">
            <span class="stat-value">{{ group.member_count || 0 }}</span>
            <span class="stat-label">{{ $t('groups.members') }}</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ group.child_count || 0 }}</span>
            <span class="stat-label">{{ $t('groups.childGroups') }}</span>
          </div>
        </div>
        <div v-if="group.parent_groups?.length" class="group-parents">
          <span class="text-sm text-muted">{{ $t('groups.parentGroups') }}:</span>
          <span 
            v-for="parent in group.parent_groups" 
            :key="parent.id"
            class="badge badge-primary"
          >
            {{ parent.name }}
          </span>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showAddModal || editModal" class="modal-backdrop" @click.self="closeModal">
      <div class="modal">
        <h3>{{ editModal ? $t('users.edit') : $t('groups.add') }}</h3>
        <form @submit.prevent="saveGroup">
          <div class="form-group">
            <label class="form-label">{{ $t('groups.name') }}</label>
            <input 
              v-model="formData.name" 
              type="text" 
              class="form-input"
              required
            />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('groups.description') }}</label>
            <textarea 
              v-model="formData.description" 
              class="form-input"
              rows="3"
            ></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" @click="closeModal">
              {{ $t('common.cancel') }}
            </button>
            <button type="submit" class="btn btn-primary">
              {{ $t('common.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <div v-if="deleteModal" class="modal-backdrop" @click.self="deleteModal = null">
      <div class="modal">
        <h3>{{ $t('users.delete') }}</h3>
        <p>Are you sure you want to delete this group?</p>
        <p class="font-medium">{{ deleteModal.name }}</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="deleteModal = null">
            {{ $t('common.cancel') }}
          </button>
          <button class="btn btn-danger" @click="deleteGroup">
            {{ $t('users.delete') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/composables/useApi'

const groups = ref([])
const isLoading = ref(false)
const showAddModal = ref(false)
const editModal = ref(null)
const deleteModal = ref(null)

const formData = reactive({
  name: '',
  description: ''
})

async function fetchGroups() {
  isLoading.value = true
  try {
    const response = await api.get('/api/groups')
    groups.value = response.data.items || response.data
  } catch (err) {
    console.error('Failed to fetch groups:', err)
  } finally {
    isLoading.value = false
  }
}

function editGroup(group) {
  editModal.value = group
  formData.name = group.name
  formData.description = group.description || ''
}

function confirmDelete(group) {
  deleteModal.value = group
}

function closeModal() {
  showAddModal.value = false
  editModal.value = null
  formData.name = ''
  formData.description = ''
}

async function saveGroup() {
  try {
    if (editModal.value) {
      await api.put(`/api/groups/${editModal.value.id}`, formData)
    } else {
      await api.post('/api/groups', formData)
    }
    closeModal()
    fetchGroups()
  } catch (err) {
    console.error('Failed to save group:', err)
  }
}

async function deleteGroup() {
  try {
    await api.delete(`/api/groups/${deleteModal.value.id}`)
    deleteModal.value = null
    fetchGroups()
  } catch (err) {
    console.error('Failed to delete group:', err)
  }
}

onMounted(() => {
  fetchGroups()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-lg);
}

.group-card {
  padding: var(--spacing-lg);
}

.group-header {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-md);
}

.group-icon {
  font-size: 2rem;
}

.group-info {
  flex: 1;
}

.group-info h3 {
  margin-bottom: var(--spacing-xs);
}

.group-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.group-stats {
  display: flex;
  gap: var(--spacing-xl);
  padding: var(--spacing-md) 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  margin-bottom: var(--spacing-md);
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary-500);
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
}

.group-parents {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  flex-wrap: wrap;
}

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
  max-width: 450px;
  width: 100%;
  z-index: var(--z-modal);
}

.modal h3 {
  margin-bottom: var(--spacing-lg);
}

.modal-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
  margin-top: var(--spacing-lg);
}
</style>
