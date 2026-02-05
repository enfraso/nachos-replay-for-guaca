<template>
  <div class="settings-page">
    <h2>{{ $t('nav.settings') }}</h2>

    <!-- System Settings -->
    <div class="card">
      <div class="card-header">
        <h3>⚙️ System Settings</h3>
      </div>
      <div class="card-body">
        <div class="settings-grid">
          <div class="form-group">
            <label class="form-label">Replay Directory</label>
            <input 
              v-model="settings.replay_directory" 
              type="text" 
              class="form-input"
              disabled
            />
            <p class="form-hint">Configured via environment variable</p>
          </div>
          <div class="form-group">
            <label class="form-label">File Scan Interval (minutes)</label>
            <input 
              v-model.number="settings.scan_interval" 
              type="number" 
              class="form-input"
              min="1"
              max="60"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Archive After (days)</label>
            <input 
              v-model.number="settings.archive_after_days" 
              type="number" 
              class="form-input"
              min="1"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Delete After (days)</label>
            <input 
              v-model.number="settings.delete_after_days" 
              type="number" 
              class="form-input"
              min="1"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- LDAP Settings -->
    <div class="card mt-lg">
      <div class="card-header">
        <h3>🔐 AD/LDAP Settings</h3>
      </div>
      <div class="card-body">
        <div class="settings-grid">
          <div class="form-group full-width">
            <label class="form-label">
              <input type="checkbox" v-model="settings.ldap_enabled" />
              Enable AD/LDAP Authentication
            </label>
          </div>
          <div class="form-group">
            <label class="form-label">LDAP Server URL</label>
            <input 
              v-model="settings.ldap_url" 
              type="text" 
              class="form-input"
              placeholder="ldap://domain.local:389"
              :disabled="!settings.ldap_enabled"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Base DN</label>
            <input 
              v-model="settings.ldap_base_dn" 
              type="text" 
              class="form-input"
              placeholder="DC=domain,DC=local"
              :disabled="!settings.ldap_enabled"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Bind User</label>
            <input 
              v-model="settings.ldap_bind_user" 
              type="text" 
              class="form-input"
              :disabled="!settings.ldap_enabled"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Bind Password</label>
            <input 
              v-model="settings.ldap_bind_password" 
              type="password" 
              class="form-input"
              :disabled="!settings.ldap_enabled"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Storage Stats -->
    <div class="card mt-lg">
      <div class="card-header">
        <h3>💾 Storage Statistics</h3>
      </div>
      <div class="card-body">
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-value">{{ formatBytes(storageStats.total_size) }}</span>
            <span class="stat-label">Total Size</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ storageStats.total_files }}</span>
            <span class="stat-label">Total Files</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ storageStats.active_files }}</span>
            <span class="stat-label">Active</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ storageStats.archived_files }}</span>
            <span class="stat-label">Archived</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Actions -->
    <div class="page-actions mt-lg">
      <button class="btn btn-primary" @click="saveSettings">
        {{ $t('common.save') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/composables/useApi'

const settings = reactive({
  replay_directory: '/var/lib/guacamole/recordings',
  scan_interval: 5,
  archive_after_days: 90,
  delete_after_days: 365,
  ldap_enabled: false,
  ldap_url: '',
  ldap_base_dn: '',
  ldap_bind_user: '',
  ldap_bind_password: ''
})

const storageStats = ref({
  total_size: 0,
  total_files: 0,
  active_files: 0,
  archived_files: 0
})

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

async function fetchSettings() {
  try {
    const response = await api.get('/api/stats/storage')
    storageStats.value = response.data
  } catch (err) {
    console.error('Failed to fetch storage stats:', err)
  }
}

async function saveSettings() {
  try {
    // In a real implementation, this would save to the backend
    console.log('Saving settings:', settings)
    alert('Settings saved successfully!')
  } catch (err) {
    console.error('Failed to save settings:', err)
  }
}

onMounted(() => {
  fetchSettings()
})
</script>

<style scoped>
.settings-page h2 {
  margin-bottom: var(--spacing-lg);
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.settings-grid .full-width {
  grid-column: 1 / -1;
}

.form-hint {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  margin-top: var(--spacing-xs);
}

.stats-row {
  display: flex;
  gap: var(--spacing-xl);
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-item .stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary-500);
}

.stat-item .stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-muted);
}

.page-actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-row {
    flex-wrap: wrap;
  }
}
</style>
