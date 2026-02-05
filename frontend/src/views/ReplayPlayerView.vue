<template>
  <div class="replay-player-page">
    <!-- Header -->
    <div class="player-header">
      <button class="btn btn-ghost" @click="goBack">
        ← {{ $t('common.cancel') }}
      </button>
      <div class="replay-info" v-if="replay">
        <h2>{{ replay.session_name || replay.filename }}</h2>
        <p class="text-muted">
          {{ replay.owner_username }} • {{ formatDate(replay.session_start) }}
          • {{ formatDuration(replay.duration_seconds) }}
        </p>
      </div>
      <div class="player-controls">
        <select v-model="playbackSpeed" class="form-select speed-select">
          <option :value="0.5">0.5x</option>
          <option :value="1">1x</option>
          <option :value="2">2x</option>
          <option :value="4">4x</option>
        </select>
        <button class="btn btn-secondary" @click="toggleFullscreen">
          ⛶ {{ $t('replays.player.controls.fullscreen') }}
        </button>
      </div>
    </div>

    <!-- Player Container -->
    <div 
      ref="playerContainer"
      class="player-container"
      :class="{ fullscreen: isFullscreen }"
    >
      <div v-if="isLoading" class="player-loading">
        <div class="spinner spinner-lg"></div>
        <p>{{ $t('replays.player.loading') }}</p>
      </div>

      <div v-else-if="error" class="player-error">
        <p class="text-error">{{ $t('replays.player.error') }}</p>
        <p class="text-muted text-sm">{{ error }}</p>
        <button class="btn btn-primary mt-md" @click="loadReplay">
          {{ $t('common.retry') || 'Retry' }}
        </button>
      </div>

      <div v-else class="player-display" ref="displayRef">
        <!-- Guacamole display will be rendered here -->
        <canvas ref="canvasRef" class="replay-canvas"></canvas>
      </div>

      <!-- Playback Controls -->
      <div class="playback-bar" v-if="!isLoading && !error">
        <button class="control-btn" @click="togglePlay">
          {{ isPlaying ? '⏸' : '▶' }}
        </button>
        <div class="progress-container">
          <input
            type="range"
            class="progress-bar"
            v-model="currentPosition"
            :max="duration"
            @input="seek"
          />
          <div class="time-display">
            {{ formatTime(currentPosition) }} / {{ formatTime(duration) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useReplaysStore } from '@/stores/replays'
import api from '@/composables/useApi'

const route = useRoute()
const router = useRouter()
const { locale } = useI18n()
const replaysStore = useReplaysStore()

const playerContainer = ref(null)
const displayRef = ref(null)
const canvasRef = ref(null)

const replay = ref(null)
const isLoading = ref(true)
const error = ref(null)
const isPlaying = ref(false)
const isFullscreen = ref(false)
const playbackSpeed = ref(1)
const currentPosition = ref(0)
const duration = ref(0)

// Simulated playback state
let playbackInterval = null
let replayData = null

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString(locale.value)
}

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

function formatTime(ms) {
  const seconds = Math.floor(ms / 1000)
  return formatDuration(seconds)
}

async function loadReplay() {
  isLoading.value = true
  error.value = null

  try {
    // Fetch replay details
    const replayId = route.params.id
    const replayDetails = await replaysStore.fetchReplay(replayId)
    
    if (!replayDetails) {
      throw new Error('Replay not found')
    }

    replay.value = replayDetails
    duration.value = (replayDetails.duration_seconds || 0) * 1000

    // In a real implementation, you would:
    // 1. Load the Guacamole JS library
    // 2. Create a Guac.SessionRecording from the stream URL
    // 3. Connect the display to the canvas

    // For now, we show a placeholder message
    if (canvasRef.value) {
      const ctx = canvasRef.value.getContext('2d')
      canvasRef.value.width = 800
      canvasRef.value.height = 600
      
      ctx.fillStyle = '#1a1a2e'
      ctx.fillRect(0, 0, 800, 600)
      
      ctx.fillStyle = '#ffffff'
      ctx.font = '20px Inter, sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('Guacamole Replay Player', 400, 280)
      ctx.font = '14px Inter, sans-serif'
      ctx.fillStyle = '#666'
      ctx.fillText('Configure guacamole-common-js library to enable playback', 400, 320)
      ctx.fillText(`File: ${replayDetails.filename}`, 400, 350)
    }

    isLoading.value = false
  } catch (err) {
    console.error('Failed to load replay:', err)
    error.value = err.message || 'Failed to load replay'
    isLoading.value = false
  }
}

function togglePlay() {
  isPlaying.value = !isPlaying.value

  if (isPlaying.value) {
    startPlayback()
  } else {
    stopPlayback()
  }
}

function startPlayback() {
  if (playbackInterval) clearInterval(playbackInterval)
  
  playbackInterval = setInterval(() => {
    currentPosition.value += 100 * playbackSpeed.value
    
    if (currentPosition.value >= duration.value) {
      currentPosition.value = duration.value
      stopPlayback()
    }
  }, 100)
}

function stopPlayback() {
  isPlaying.value = false
  if (playbackInterval) {
    clearInterval(playbackInterval)
    playbackInterval = null
  }
}

function seek() {
  // In a real implementation, this would seek the Guacamole recording
  console.log('Seeking to:', currentPosition.value)
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    playerContainer.value?.requestFullscreen()
    isFullscreen.value = true
  } else {
    document.exitFullscreen()
    isFullscreen.value = false
  }
}

function goBack() {
  router.push('/replays')
}

watch(playbackSpeed, (newSpeed) => {
  if (isPlaying.value) {
    stopPlayback()
    startPlayback()
  }
})

onMounted(() => {
  loadReplay()
  
  document.addEventListener('fullscreenchange', () => {
    isFullscreen.value = !!document.fullscreenElement
  })
})

onUnmounted(() => {
  stopPlayback()
})
</script>

<style scoped>
.replay-player-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - var(--spacing-2xl) * 2);
}

.player-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.replay-info {
  flex: 1;
}

.replay-info h2 {
  margin-bottom: var(--spacing-xs);
}

.player-controls {
  display: flex;
  gap: var(--spacing-sm);
}

.speed-select {
  width: auto;
}

.player-container {
  flex: 1;
  background: var(--bg-dark);
  border-radius: var(--border-radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.player-container.fullscreen {
  border-radius: 0;
}

.player-loading,
.player-error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-inverse);
}

.player-display {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.replay-canvas {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.playback-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-lg);
  background: rgba(0, 0, 0, 0.8);
}

.control-btn {
  width: 40px;
  height: 40px;
  background: var(--color-primary-500);
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 16px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.control-btn:hover {
  background: var(--color-primary-400);
  transform: scale(1.1);
}

.progress-container {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.progress-bar {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  cursor: pointer;
}

.progress-bar::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  background: var(--color-accent-500);
  border-radius: 50%;
  cursor: pointer;
}

.time-display {
  font-size: var(--font-size-sm);
  color: rgba(255, 255, 255, 0.7);
  font-family: monospace;
  min-width: 120px;
  text-align: right;
}
</style>
