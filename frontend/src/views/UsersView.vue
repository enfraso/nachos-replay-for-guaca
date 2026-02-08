<template>
    <div class="users-page">
        <div class="page-header">
            <div>
                <h2>{{ $t('users.title') }}</h2>
                <p class="text-muted">{{ $t('users.subtitle') }}</p>
            </div>
            <button class="btn btn-primary" @click="openModal('create')">
                ➕ {{ $t('users.addUser') }}
            </button>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="loading-container">
            <div class="spinner spinner-lg"></div>
        </div>

        <!-- Users Table -->
        <div v-else class="table-container">
            <table class="table">
                <thead>
                    <tr>
                        <th>{{ $t('users.name') }}</th>
                        <th>{{ $t('auth.username') }}</th>
                        <th>{{ $t('users.email') }}</th>
                        <th>{{ $t('users.role') }}</th>
                        <th>{{ $t('common.status') }}</th>
                        <th>{{ $t('common.actions') }}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="user in users" :key="user.id">
                        <td><strong>{{ user.display_name || '-' }}</strong></td>
                        <td>{{ user.username }}</td>
                        <td>{{ user.email || '-' }}</td>
                        <td>
                            <span :class="['badge', getRoleBadge(user.role)]">
                                {{ $t(`users.roles.${user.role}`) }}
                            </span>
                        </td>
                        <td>
                            <span :class="['badge', user.is_active ? 'badge-success' : 'badge-gray']">
                                {{ user.is_active ? $t('users.active') : $t('users.inactive') }}
                            </span>
                        </td>
                        <td class="table-actions">
                            <button class="btn btn-sm btn-secondary" @click="openModal('edit', user)">
                                ✏️
                            </button>
                            <button class="btn btn-sm btn-danger" @click="confirmDelete(user)">
                                🗑️
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Modal -->
        <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
            <div class="modal">
                <div class="modal-header">
                    <h3>{{ modalMode === 'create' ? $t('users.addUser') : $t('users.editUser') }}</h3>
                    <button class="btn btn-ghost btn-icon" @click="closeModal">✕</button>
                </div>
                <form @submit.prevent="saveUser">
                    <div class="modal-body">
                        <div class="form-group">
                            <label class="form-label">{{ $t('auth.username') }} *</label>
                            <input v-model="form.username" type="text" class="form-input" required />
                        </div>
                        <div class="form-group">
                            <label class="form-label">{{ $t('users.name') }}</label>
                            <input v-model="form.display_name" type="text" class="form-input" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">{{ $t('users.email') }}</label>
                            <input v-model="form.email" type="email" class="form-input" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">{{ $t('auth.password') }} {{ modalMode === 'create' ? '*' : '' }}</label>
                            <input v-model="form.password" type="password" class="form-input" :required="modalMode === 'create'" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">{{ $t('users.role') }}</label>
                            <select v-model="form.role" class="form-select">
                                <option value="viewer">{{ $t('users.roles.viewer') }}</option>
                                <option value="auditor">{{ $t('users.roles.auditor') }}</option>
                                <option value="admin">{{ $t('users.roles.admin') }}</option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" @click="closeModal">
                            {{ $t('common.cancel') }}
                        </button>
                        <button type="submit" class="btn btn-primary" :disabled="isSaving">
                            <span v-if="isSaving" class="spinner spinner-white"></span>
                            <span v-else>{{ $t('common.save') }}</span>
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/composables/useApi'

const users = ref([])
const isLoading = ref(true)
const isSaving = ref(false)
const showModal = ref(false)
const modalMode = ref('create')
const editingUserId = ref(null)

const form = ref({
    username: '',
    display_name: '',
    email: '',
    password: '',
    role: 'viewer'
})

function getRoleBadge(role) {
    const roles = { admin: 'badge-error', auditor: 'badge-warning', viewer: 'badge-primary' }
    return roles[role] || 'badge-gray'
}

async function fetchUsers() {
    isLoading.value = true
    try {
        const { data } = await api.get('/api/users')
        users.value = data.items || data || []
    } catch (err) {
        console.error('Failed to fetch users:', err)
    } finally {
        isLoading.value = false
    }
}

function openModal(mode, user = null) {
    modalMode.value = mode
    if (user) {
        editingUserId.value = user.id
        form.value = { ...user, password: '' }
    } else {
        editingUserId.value = null
        form.value = { username: '', display_name: '', email: '', password: '', role: 'viewer' }
    }
    showModal.value = true
}

function closeModal() {
    showModal.value = false
}

async function saveUser() {
    isSaving.value = true
    try {
        const payload = { ...form.value }
        if (!payload.password) delete payload.password

        if (modalMode.value === 'create') {
            await api.post('/api/users', payload)
        } else {
            await api.put(`/api/users/${editingUserId.value}`, payload)
        }
        closeModal()
        fetchUsers()
    } catch (err) {
        console.error('Failed to save user:', err)
    } finally {
        isSaving.value = false
    }
}

async function confirmDelete(user) {
    if (confirm(`Tem certeza que deseja excluir o usuário ${user.username}?`)) {
        try {
            await api.delete(`/api/users/${user.id}`)
            fetchUsers()
        } catch (err) {
            console.error('Failed to delete user:', err)
        }
    }
}

onMounted(() => fetchUsers())
</script>

<style scoped>
.users-page {
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

.loading-container {
    text-align: center;
    padding: var(--spacing-3xl);
}

.form-select {
    width: 100%;
    padding: 0.625rem 0.875rem;
    font-family: inherit;
    font-size: var(--font-size-base);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background: var(--bg-secondary);
}
</style>
