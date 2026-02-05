<template>
  <div class="users-page">
    <!-- Header -->
    <div class="page-header">
      <h2>{{ $t('users.title') }}</h2>
      <button class="btn btn-primary" @click="showAddModal = true">
        + {{ $t('users.add') }}
      </button>
    </div>

    <!-- Table -->
    <div class="card">
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>{{ $t('users.username') }}</th>
              <th>{{ $t('users.displayName') }}</th>
              <th>{{ $t('users.email') }}</th>
              <th>{{ $t('users.role') }}</th>
              <th>{{ $t('users.status') }}</th>
              <th>{{ $t('users.lastLogin') }}</th>
              <th>{{ $t('replays.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isLoading">
              <td colspan="7" class="text-center p-lg">
                <div class="spinner"></div>
              </td>
            </tr>
            <tr v-else-if="users.length === 0">
              <td colspan="7" class="text-center p-lg text-muted">
                {{ $t('common.noData') }}
              </td>
            </tr>
            <tr v-for="user in users" :key="user.id">
              <td class="font-medium">{{ user.username }}</td>
              <td>{{ user.display_name || '-' }}</td>
              <td>{{ user.email || '-' }}</td>
              <td>
                <span :class="['badge', getRoleBadge(user.role)]">
                  {{ $t(`users.roles.${user.role}`) }}
                </span>
              </td>
              <td>
                <span :class="['badge', user.is_active ? 'badge-success' : 'badge-error']">
                  {{ user.is_active ? $t('users.statusActive') : $t('users.statusInactive') }}
                </span>
              </td>
              <td>{{ formatDate(user.last_login) }}</td>
              <td>
                <div class="actions">
                  <button 
                    class="btn btn-sm btn-secondary"
                    @click="editUser(user)"
                    :title="$t('users.edit')"
                  >
                    ✏️
                  </button>
                  <button 
                    class="btn btn-sm btn-danger"
                    @click="confirmDelete(user)"
                    :title="$t('users.delete')"
                    :disabled="user.username === 'admin'"
                  >
                    🗑
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showAddModal || editModal" class="modal-backdrop" @click.self="closeModal">
      <div class="modal">
        <h3>{{ editModal ? $t('users.edit') : $t('users.add') }}</h3>
        <form @submit.prevent="saveUser">
          <div class="form-group">
            <label class="form-label">{{ $t('users.username') }}</label>
            <input 
              v-model="formData.username" 
              type="text" 
              class="form-input"
              :disabled="!!editModal"
              required
            />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('users.displayName') }}</label>
            <input 
              v-model="formData.display_name" 
              type="text" 
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('users.email') }}</label>
            <input 
              v-model="formData.email" 
              type="email" 
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">{{ $t('users.role') }}</label>
            <select v-model="formData.role" class="form-select">
              <option value="viewer">{{ $t('users.roles.viewer') }}</option>
              <option value="auditor">{{ $t('users.roles.auditor') }}</option>
              <option value="admin">{{ $t('users.roles.admin') }}</option>
            </select>
          </div>
          <div v-if="!editModal" class="form-group">
            <label class="form-label">{{ $t('auth.password') }}</label>
            <input 
              v-model="formData.password" 
              type="password" 
              class="form-input"
              required
            />
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
        <p>{{ $t('users.confirmDelete') }}</p>
        <p class="font-medium">{{ deleteModal.username }}</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="deleteModal = null">
            {{ $t('common.cancel') }}
          </button>
          <button class="btn btn-danger" @click="deleteUser">
            {{ $t('users.delete') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/composables/useApi'

const { locale } = useI18n()

const users = ref([])
const isLoading = ref(false)
const showAddModal = ref(false)
const editModal = ref(null)
const deleteModal = ref(null)

const formData = reactive({
  username: '',
  display_name: '',
  email: '',
  role: 'viewer',
  password: ''
})

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString(locale.value)
}

function getRoleBadge(role) {
  const badges = {
    admin: 'badge-error',
    auditor: 'badge-warning',
    viewer: 'badge-primary'
  }
  return badges[role] || 'badge-primary'
}

async function fetchUsers() {
  isLoading.value = true
  try {
    const response = await api.get('/api/users')
    users.value = response.data.items || response.data
  } catch (err) {
    console.error('Failed to fetch users:', err)
  } finally {
    isLoading.value = false
  }
}

function editUser(user) {
  editModal.value = user
  formData.username = user.username
  formData.display_name = user.display_name || ''
  formData.email = user.email || ''
  formData.role = user.role
  formData.password = ''
}

function confirmDelete(user) {
  deleteModal.value = user
}

function closeModal() {
  showAddModal.value = false
  editModal.value = null
  Object.assign(formData, {
    username: '',
    display_name: '',
    email: '',
    role: 'viewer',
    password: ''
  })
}

async function saveUser() {
  try {
    if (editModal.value) {
      await api.put(`/api/users/${editModal.value.id}`, {
        display_name: formData.display_name,
        email: formData.email,
        role: formData.role
      })
    } else {
      await api.post('/api/users', formData)
    }
    closeModal()
    fetchUsers()
  } catch (err) {
    console.error('Failed to save user:', err)
  }
}

async function deleteUser() {
  try {
    await api.delete(`/api/users/${deleteModal.value.id}`)
    deleteModal.value = null
    fetchUsers()
  } catch (err) {
    console.error('Failed to delete user:', err)
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.actions {
  display: flex;
  gap: var(--spacing-xs);
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
