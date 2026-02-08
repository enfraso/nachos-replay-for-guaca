<template>
    <div class="groups-page">
        <div class="page-header">
            <div>
                <h2>{{ $t('groups.title') }}</h2>
                <p class="text-muted">{{ $t('groups.subtitle') }}</p>
            </div>
            <button class="btn btn-primary" @click="openModal('create')">
                ➕ {{ $t('groups.addGroup') }}
            </button>
        </div>

        <!-- Loading -->
        <div v-if="isLoading" class="loading-container">
            <div class="spinner spinner-lg"></div>
        </div>

        <!-- Groups Grid -->
        <div v-else class="groups-grid">
            <div v-for="group in groups" :key="group.id" class="group-card card">
                <div class="card-header">
                    <h3>{{ group.name }}</h3>
                    <div class="group-actions">
                        <button class="btn btn-sm btn-ghost" @click="openModal('edit', group)">✏️</button>
                        <button class="btn btn-sm btn-ghost" @click="confirmDelete(group)">🗑️</button>
                    </div>
                </div>
                <div class="card-body">
                    <p class="text-muted">{{ group.description || 'Sem descrição' }}</p>
                    <div class="group-stats">
                        <span class="stat">
                            <strong>{{ group.member_count || 0 }}</strong> {{ $t('groups.members') }}
                        </span>
                    </div>
                </div>
            </div>

            <div v-if="groups.length === 0" class="empty-state">
                <div class="empty-state-icon">🏷️</div>
                <div class="empty-state-title">Nenhum grupo encontrado</div>
            </div>
        </div>

        <!-- Modal -->
        <div v-if="showModal" class="modal-backdrop" @click.self="closeModal">
            <div class="modal">
                <div class="modal-header">
                    <h3>{{ modalMode === 'create' ? $t('groups.addGroup') : $t('groups.editGroup') }}</h3>
                    <button class="btn btn-ghost btn-icon" @click="closeModal">✕</button>
                </div>
                <form @submit.prevent="saveGroup">
                    <div class="modal-body">
                        <div class="form-group">
                            <label class="form-label">{{ $t('groups.name') }} *</label>
                            <input v-model="form.name" type="text" class="form-input" required />
                        </div>
                        <div class="form-group">
                            <label class="form-label">{{ $t('groups.description') }}</label>
                            <textarea v-model="form.description" class="form-input" rows="3"></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" @click="closeModal">
                            {{ $t('common.cancel') }}
                        </button>
                        <button type="submit" class="btn btn-primary" :disabled="isSaving">
                            {{ $t('common.save') }}
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

const groups = ref([])
const isLoading = ref(true)
const isSaving = ref(false)
const showModal = ref(false)
const modalMode = ref('create')
const editingGroupId = ref(null)

const form = ref({ name: '', description: '' })

async function fetchGroups() {
    isLoading.value = true
    try {
        const { data } = await api.get('/api/groups')
        groups.value = data.items || data || []
    } catch (err) {
        console.error('Failed to fetch groups:', err)
    } finally {
        isLoading.value = false
    }
}

function openModal(mode, group = null) {
    modalMode.value = mode
    if (group) {
        editingGroupId.value = group.id
        form.value = { name: group.name, description: group.description || '' }
    } else {
        editingGroupId.value = null
        form.value = { name: '', description: '' }
    }
    showModal.value = true
}

function closeModal() {
    showModal.value = false
}

async function saveGroup() {
    isSaving.value = true
    try {
        if (modalMode.value === 'create') {
            await api.post('/api/groups', form.value)
        } else {
            await api.put(`/api/groups/${editingGroupId.value}`, form.value)
        }
        closeModal()
        fetchGroups()
    } catch (err) {
        console.error('Failed to save group:', err)
    } finally {
        isSaving.value = false
    }
}

async function confirmDelete(group) {
    if (confirm(`Tem certeza que deseja excluir o grupo ${group.name}?`)) {
        try {
            await api.delete(`/api/groups/${group.id}`)
            fetchGroups()
        } catch (err) {
            console.error('Failed to delete group:', err)
        }
    }
}

onMounted(() => fetchGroups())
</script>

<style scoped>
.groups-page {
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

.groups-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: var(--spacing-lg);
}

.group-card .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.group-card .card-header h3 {
    margin: 0;
}

.group-actions {
    display: flex;
    gap: var(--spacing-xs);
}

.group-stats {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-color);
}

.group-stats .stat {
    font-size: var(--font-size-sm);
    color: var(--text-muted);
}
</style>
