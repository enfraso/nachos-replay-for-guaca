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
                </div>
            </div>

            <!-- Player Area -->
            <div class="player-area">
                <div class="player-wrapper" ref="playerRef">
                    <!-- Guacamole player would be embedded here -->
                    <div class="player-placeholder">
                        <div class="player-icon">🎬</div>
                        <p>Player de Replay</p>
                        <p class="text-muted text-sm">Integração com Guacamole Client</p>
                    </div>
                </div>

                <!-- Player Controls -->
                <div class="player-controls">
                    <div class="controls-left">
                        <button class="btn btn-primary btn-icon" @click="togglePlay">
                            {{ isPlaying ? '⏸️' : '▶️' }}
                        </button>
                        <button class="btn btn-secondary btn-icon" @click="stop">
                            ⏹️
                        </button>
                    </div>
                    
                    <div class="controls-center">
                        <div class="progress-bar">
                            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
                        </div>
                        <span class="time-display">{{ formatTime(currentTime) }} / {{ formatTime(totalTime) }}</span>
                    </div>
                    
                    <div class="controls-right">
                        <select v-model="playbackSpeed" class="form-select speed-select">
                            <option value="0.5">0.5x</option>
                            <option value="1">1x</option>
                            <option value="1.5">1.5x</option>
                            <option value="2">2x</option>
                            <option value="4">4x</option>
                        </select>
                        <button class="btn btn-ghost btn-icon" @click="toggleFullscreen">
                            🔲
                        </button>
                    </div>
                </div>
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
                            <span class="info-value">{{ replay.username }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">{{ $t('replays.hostname') }}</span>
                            <span class="info-value">{{ replay.hostname || '-' }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">{{ $t('replays.protocol') }}</span>
                            <span class="info-value">{{ replay.protocol?.toUpperCase() || 'RDP' }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">{{ $t('replays.startDate') }}</span>
                            <span class="info-value">{{ formatDate(replay.start_time) }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">{{ $t('replays.duration') }}</span>
                            <span class="info-value">{{ formatDuration(replay.duration) }}</span>
                        </div>
                        <div class="info-item">
                            <span class="info-label">{{ $t('replays.size') }}</span>
                            <span class="info-value">{{ formatBytes(replay.size_bytes) }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Error State -->
        <div v-else class="empty-state">
            <div class="empty-state-icon">❌</div>
            <div class="empty-state-title">{{ $t('common.error') }}</div>
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

const route = useRoute()
const { locale } = useI18n()
const replaysStore = useReplaysStore()

const playerRef = ref(null)
const isLoading = ref(true)
const isPlaying = ref(false)
const currentTime = ref(0)
const playbackSpeed = ref('1')

const replay = computed(() => replaysStore.currentReplay)
const totalTime = computed(() => replay.value?.duration || 0)
const progress = computed(() => totalTime.value > 0 ? (currentTime.value / totalTime.value) * 100 : 0)

function formatDate(dateStr) {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString(locale.value)
}

function formatDuration(seconds) {
    if (!seconds) return '-'
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function formatBytes(bytes) {
    if (!bytes) return '-'
    const units = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60)
    const s = Math.floor(seconds % 60)
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function togglePlay() {
    isPlaying.value = !isPlaying.value
}

function stop() {
    isPlaying.value = false
    currentTime.value = 0
}

function toggleFullscreen() {
    if (playerRef.value) {
        if (document.fullscreenElement) {
            document.exitFullscreen()
        } else {
            playerRef.value.requestFullscreen()
        }
    }
}

onMounted(async () => {
    const id = route.params.id
    await replaysStore.fetchReplay(id)
    isLoading.value = false
})

onUnmounted(() => {
    replaysStore.currentReplay = null
})
</script>

<style scoped>
.player-page {
    max-width: var(--content-max-width);
}

.loading-container {
    text-align: center;
    padding: var(--spacing-3xl);
}

.player-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
}

.player-header h2 {
    flex: 1;
    margin: 0;
}

.player-area {
    background: var(--color-gray-900);
    border-radius: var(--radius-lg);
    overflow: hidden;
    margin-bottom: var(--spacing-lg);
}

.player-wrapper {
    aspect-ratio: 16 / 9;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.player-placeholder {
    text-align: center;
    color: var(--color-gray-400);
}

.player-icon {
    font-size: 4rem;
    margin-bottom: var(--spacing-md);
}

.player-controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: var(--color-gray-800);
}

.controls-left,
.controls-right {
    display: flex;
    gap: var(--spacing-sm);
}

.controls-center {
    flex: 1;
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
}

.progress-bar {
    flex: 1;
    height: 6px;
    background: var(--color-gray-600);
    border-radius: var(--radius-full);
    cursor: pointer;
}

.progress-fill {
    height: 100%;
    background: var(--color-primary-500);
    border-radius: var(--radius-full);
    transition: width 0.1s linear;
}

.time-display {
    font-size: var(--font-size-sm);
    color: var(--color-gray-300);
    white-space: nowrap;
}

.speed-select {
    width: 70px;
    padding: var(--spacing-xs);
    font-size: var(--font-size-sm);
    background: var(--color-gray-700);
    border-color: var(--color-gray-600);
    color: white;
}

.info-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
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
}

.info-value {
    font-weight: var(--font-weight-medium);
}

@media (max-width: 768px) {
    .player-header {
        flex-wrap: wrap;
    }
    
    .player-controls {
        flex-wrap: wrap;
    }
    
    .controls-center {
        order: 3;
        width: 100%;
        margin-top: var(--spacing-sm);
    }
    
    .info-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
</style>
