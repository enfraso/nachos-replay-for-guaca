<template>
    <div class="settings-page">
        <div class="page-header">
            <h2>{{ $t('settings.title') }}</h2>
            <p class="text-muted">{{ $t('settings.subtitle') }}</p>
        </div>

        <!-- Tabs -->
        <div class="settings-tabs">
            <button
                v-for="tab in tabs"
                :key="tab.id"
                :class="['tab-btn', { active: activeTab === tab.id }]"
                @click="activeTab = tab.id"
            >
                {{ tab.icon }} {{ $t(`settings.${tab.id}`) }}
            </button>
        </div>

        <!-- General Settings -->
        <div v-if="activeTab === 'general'" class="settings-section card">
            <div class="card-body">
                <form @submit.prevent="saveSettings">
                    <div class="form-group">
                        <label class="form-label">{{ $t('settings.appName') }}</label>
                        <input v-model="settings.app_name" type="text" class="form-input" />
                    </div>
                    <div class="form-group">
                        <label class="form-label">{{ $t('settings.language') }}</label>
                        <select v-model="settings.language" class="form-select">
                            <option value="pt-BR">Português (Brasil)</option>
                            <option value="en">English</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">{{ $t('settings.theme') }}</label>
                        <select v-model="settings.theme" class="form-select">
                            <option value="light">{{ $t('settings.themes.light') }}</option>
                            <option value="dark">{{ $t('settings.themes.dark') }}</option>
                            <option value="auto">{{ $t('settings.themes.auto') }}</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary" :disabled="isSaving">
                        <span v-if="isSaving" class="spinner spinner-white"></span>
                        <span v-else>{{ $t('common.save') }}</span>
                    </button>
                </form>
            </div>
        </div>

        <!-- Storage Settings -->
        <div v-if="activeTab === 'storage'" class="settings-section card">
            <div class="card-body">
                <form @submit.prevent="saveSettings">
                    <div class="form-group">
                        <label class="form-label">{{ $t('settings.retentionDays') }}</label>
                        <input v-model.number="settings.retention_days" type="number" min="1" class="form-input" />
                        <span class="form-hint">Replays mais antigos serão excluídos automaticamente</span>
                    </div>
                    <div class="form-group">
                        <label class="form-label">{{ $t('settings.maxStorageGB') }}</label>
                        <input v-model.number="settings.max_storage_gb" type="number" min="1" class="form-input" />
                    </div>
                    <button type="submit" class="btn btn-primary" :disabled="isSaving">
                        {{ $t('common.save') }}
                    </button>
                </form>
            </div>
        </div>

        <!-- LDAP Settings -->
        <div v-if="activeTab === 'ldap'" class="settings-section card">
            <div class="card-body">
                <form @submit.prevent="saveSettings">
                    <div class="form-group">
                        <label class="flex items-center gap-sm">
                            <input v-model="settings.ldap_enabled" type="checkbox" />
                            <span>{{ $t('settings.ldapEnabled') }}</span>
                        </label>
                    </div>
                    <template v-if="settings.ldap_enabled">
                        <div class="form-group">
                            <label class="form-label">{{ $t('settings.ldapServer') }}</label>
                            <input v-model="settings.ldap_server" type="text" class="form-input" placeholder="ldap://servidor:389" />
                        </div>
                        <div class="form-group">
                            <label class="form-label">{{ $t('settings.ldapBaseDN') }}</label>
                            <input v-model="settings.ldap_base_dn" type="text" class="form-input" placeholder="dc=empresa,dc=com" />
                        </div>
                    </template>
                    <button type="submit" class="btn btn-primary" :disabled="isSaving">
                        {{ $t('common.save') }}
                    </button>
                </form>
            </div>
        </div>

        <!-- Success Message -->
        <div v-if="showSuccess" class="alert alert-success mt-md">
            ✅ {{ $t('settings.saveSuccess') }}
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/composables/useApi'

const tabs = [
    { id: 'general', icon: '⚙️' },
    { id: 'storage', icon: '💾' },
    { id: 'ldap', icon: '🔐' }
]

const activeTab = ref('general')
const isSaving = ref(false)
const showSuccess = ref(false)

const settings = ref({
    app_name: 'Nachos Replay',
    language: 'pt-BR',
    theme: 'light',
    retention_days: 90,
    max_storage_gb: 100,
    ldap_enabled: false,
    ldap_server: '',
    ldap_base_dn: ''
})

async function fetchSettings() {
    try {
        const { data } = await api.get('/api/settings')
        settings.value = { ...settings.value, ...data }
    } catch (err) {
        console.error('Failed to fetch settings:', err)
    }
}

async function saveSettings() {
    isSaving.value = true
    showSuccess.value = false
    try {
        await api.put('/api/settings', settings.value)
        showSuccess.value = true
        setTimeout(() => showSuccess.value = false, 3000)
    } catch (err) {
        console.error('Failed to save settings:', err)
    } finally {
        isSaving.value = false
    }
}

onMounted(() => fetchSettings())
</script>

<style scoped>
.settings-page {
    max-width: 800px;
}

.page-header {
    margin-bottom: var(--spacing-lg);
}

.settings-tabs {
    display: flex;
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-lg);
    border-bottom: 2px solid var(--border-color);
    padding-bottom: var(--spacing-xs);
}

.tab-btn {
    padding: var(--spacing-sm) var(--spacing-md);
    background: none;
    border: none;
    font-size: var(--font-size-sm);
    color: var(--text-muted);
    cursor: pointer;
    border-radius: var(--radius-md) var(--radius-md) 0 0;
    transition: all var(--transition-fast);
}

.tab-btn:hover {
    color: var(--text-primary);
    background: var(--color-gray-100);
}

.tab-btn.active {
    color: var(--color-primary-500);
    background: var(--color-primary-50);
    font-weight: var(--font-weight-medium);
}

.settings-section {
    margin-bottom: var(--spacing-lg);
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

@media (max-width: 768px) {
    .settings-tabs {
        flex-wrap: wrap;
    }
    
    .tab-btn {
        flex: 1;
        text-align: center;
    }
}
</style>
