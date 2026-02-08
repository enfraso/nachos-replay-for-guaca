<template>
    <div class="player-page">
        <!-- Loading -->
        <div v-if="isLoading" class="loading-container">
            <div class="spinner spinner-lg"></div>
            <p>{{ $t('player.loading') }}</p>
        </div>

        <!-- Player Content -->
        <div v-else-if="replay" class="player-container">
            <!-- Player Header -->
            <div class="player-header">
                <router-link to="/replays" class="btn btn-secondary btn-sm">
                    ← {{ $t('common.back') }}
                </router-link>
                <h2>{{ $t('player.title') }}</h2>
                <div class="player-meta">
                    <span class="badge badge-primary">{{ replay.protocol?.toUpperCase() || 'RDP' }}</span>
                    <span v-if="replay.status" class="badge" :class="statusClass">{{ replay.status }}</span>
                </div>
            </div>

            <!-- Guacamole Player Component -->
            <div class="player-area">
                <GuacamolePlayer
                    v-if="streamUrl"
                    :streamUrl="streamUrl"
                    :autoPlay="false"
                    @loaded="onPlayerLoaded"
                    @error="onPlayerError"
                    @progress="onPlayerProgress"
                    @ended="onPlayerEnded"
                    ref="playerRef"
                />
            </div>

            <!-- Replay Info -->
            <div class="replay-info card">
                <div class="card-header">
                    <h3>{{ $t('player.info') }}</h3>
                </div>
                <div class="card-body">
                    <div class="info-grid">
                        <div class="info-item">
                            <span class="info-label">{{ $t('common.user') }}</span>
                            <span class="info-value">{{ replay.owner_username || replay.username || '-' }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">{{ $t('replays.hostname') }}</span>
                            <span class="info-value">{{ replay.hostname || replay.session_name || '-' }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">{{ $t('replays.protocol') }}</span>
                            <span class="info-value">{{ replay.protocol?.toUpperCase() || 'RDP' }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">IP do Cliente</span>
                            <span class="info-value">{{ replay.client_ip || '-' }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">{{ $t('replays.startDate') }}</span>
                            <span class="info-value">{{ formatDate(replay.session_start || replay.start_time) }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">{{ $t('replays.duration') }}</span>
                            <span class="info-value">{{ formatDuration(replay.duration_seconds || replay.duration) }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">{{ $t('replays.size') }}</span>
                            <span class="info-value">{{ formatBytes(replay.file_size || replay.size_bytes) }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">Importado em</span>
                            <span class="info-value">{{ formatDate(replay.imported_at) }}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Player Status -->
            <div v-if="playerStatus" class="player-status card">
                <div class="card-body">
                    <div class="status-row">
                        <span class="status-label">Status:</span>
                        <span class="status-value" :class="playerStatusClass">{{ playerStatus }}</span>
                    </div>
                    <div v-if="playerDuration > 0" class="status-row">
                        <span class="status-label">Duração detectada:</span>
                        <span class="status-value">{{ formatDuration(playerDuration / 1000) }}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Error State -->
        <div v-else class="empty-state">
            <div class="empty-state-icon">❌</div>
            <div class="empty-state-title">{{ $t('common.error') }}</div>
            <p class="text-muted">Não foi possível carregar o replay</p>
            <router-link to="/replays" class="btn btn-primary">
                {{ $t('common.back') }}
            </router-link>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useReplaysStore } from '@/stores/replays'
import GuacamolePlayer from '@/components/GuacamolePlayer.vue'

const route = useRoute()
const { locale } = useI18n()
const replaysStore = useReplaysStore()

const playerRef = ref(null)
const isLoading = ref(true)
const playerStatus = ref('')
const playerDuration = ref(0)

const replay = computed(() => replaysStore.currentReplay)

// Construir URL de streaming baseada no ID do replay com token de autenticação
const streamUrl = computed(() => {
    if (!replay.value?.id) return ''
    const baseUrl = import.meta.env.VITE_API_URL || ''
    const token = localStorage.getItem('accessToken')
    const url = `${baseUrl}/api/replays/${replay.value.id}/stream`
    // Adicionar token como query parameter para autenticação
    // (StaticHTTPTunnel não envia headers Authorization)
    return token ? `${url}?token=${encodeURIComponent(token)}` : url
})

const statusClass = computed(() => {
    const status = replay.value?.status
    if (status === 'active') return 'badge-success'
    if (status === 'archived') return 'badge-warning'
    if (status === 'deleted') return 'badge-danger'
    return 'badge-secondary'
})

const playerStatusClass = computed(() => {
    if (playerStatus.value.includes('Erro')) return 'text-error'
    if (playerStatus.value.includes('Carregado')) return 'text-success'
    return ''
})

function formatDate(dateStr) {
    if (!dateStr) return '-'
    try {
        return new Date(dateStr).toLocaleString(locale.value, {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        })
    } catch {
        return dateStr
    }
}

function formatDuration(seconds) {
    if (!seconds || isNaN(seconds)) return '-'
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = Math.floor(seconds % 60)
    
    if (h > 0) {
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    }
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function formatBytes(bytes) {
    if (!bytes || isNaN(bytes)) return '-'
    const units = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

// Player event handlers
function onPlayerLoaded(data) {
    playerStatus.value = '✅ Carregado e pronto'
    playerDuration.value = data.duration
    console.log('Player carregado:', data)
}

function onPlayerError(errorMsg) {
    playerStatus.value = `❌ Erro: ${errorMsg}`
    console.error('Erro no player:', errorMsg)
}

function onPlayerProgress(data) {
    // Atualiza progresso se necessário para alguma funcionalidade externa
}

function onPlayerEnded() {
    playerStatus.value = '🏁 Reprodução finalizada'
}

onMounted(async () => {
    const id = route.params.id
    if (id) {
        await replaysStore.fetchReplay(id)
    }
    isLoading.value = false
})

onUnmounted(() => {
    replaysStore.currentReplay = null
})
</script>

<style scoped>
.player-page {
    max-width: 1400px;
    margin: 0 auto;
}

.loading-container {
    text-align: center;
    padding: var(--spacing-3xl);
}

.spinner {
    border: 3px solid var(--color-gray-300);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.spinner-lg {
    width: 48px;
    height: 48px;
    margin: 0 auto;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.player-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
    flex-wrap: wrap;
}

.player-header h2 {
    flex: 1;
    margin: 0;
    min-width: 200px;
}

.player-meta {
    display: flex;
    gap: var(--spacing-sm);
}

.player-area {
    margin-bottom: var(--spacing-lg);
    border-radius: var(--radius-lg);
    overflow: hidden;
    min-height: 400px;
    background: var(--color-gray-900);
}

.replay-info {
    margin-bottom: var(--spacing-lg);
}

.info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-md);
}

.info-item {
    display: flex;
    flex-direction: column;
}

.info-label {
    font-size: var(--font-size-xs);
    color: var(--text-muted);
    margin-bottom: var(--spacing-xs);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.info-value {
    font-weight: var(--font-weight-medium);
    word-break: break-word;
}

.player-status {
    background: var(--bg-secondary);
}

.status-row {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-xs) 0;
}

.status-label {
    font-weight: var(--font-weight-medium);
    color: var(--text-secondary);
}

.status-value {
    color: var(--text-primary);
}

.text-success {
    color: var(--color-success-500);
}

.text-error {
    color: var(--color-error-500);
}

.badge {
    display: inline-flex;
    align-items: center;
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    border-radius: var(--radius-sm);
    text-transform: uppercase;
}

.badge-primary {
    background: var(--color-primary-100);
    color: var(--color-primary-700);
}

.badge-success {
    background: rgba(34, 197, 94, 0.1);
    color: var(--color-success-500);
}

.badge-warning {
    background: rgba(245, 158, 11, 0.1);
    color: var(--color-warning-500);
}

.badge-danger {
    background: rgba(239, 68, 68, 0.1);
    color: var(--color-error-500);
}

.badge-secondary {
    background: var(--color-gray-100);
    color: var(--color-gray-600);
}

.empty-state {
    text-align: center;
    padding: var(--spacing-3xl);
}

.empty-state-icon {
    font-size: 4rem;
    margin-bottom: var(--spacing-md);
}

.empty-state-title {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--spacing-sm);
}

@media (max-width: 768px) {
    .player-header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .info-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
</style>
