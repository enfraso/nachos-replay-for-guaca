<template>
    <div class="guacamole-player" ref="containerRef">
        <!-- Operation Progress Overlay -->
        <div v-if="operationText" class="operation-overlay">
            <div class="operation-content">
                <div class="operation-spinner"></div>
                <p class="operation-text">{{ operationText }}</p>
                <div class="operation-progress-bar">
                    <div class="operation-progress-fill" :style="{ width: (operationProgress * 100) + '%' }"></div>
                </div>
                <button v-if="cancelOperation" class="btn btn-secondary btn-sm" @click="cancelOperation">
                    Cancelar
                </button>
            </div>
        </div>

        <!-- Display Container -->
        <div class="player-display" ref="displayRef">
            <!-- Guacamole Canvas será inserido aqui -->
            <div v-if="!isLoaded && !error" class="player-loading">
                <div class="spinner spinner-lg"></div>
                <p>{{ loadingMessage }}</p>
            </div>
            <div v-if="error" class="player-error">
                <div class="error-icon">⚠️</div>
                <p>{{ error }}</p>
                <button class="btn btn-primary" @click="retryLoad">Tentar Novamente</button>
            </div>
        </div>

        <!-- Controls -->
        <div class="player-controls" v-if="isLoaded">
            <div class="controls-left">
                <button class="btn btn-primary btn-icon" @click="togglePlay" :title="isPlaying ? 'Pausar' : 'Reproduzir'">
                    {{ isPlaying ? '⏸️' : '▶️' }}
                </button>
                <button class="btn btn-secondary btn-icon" @click="stop" title="Parar">
                    ⏹️
                </button>
                <button class="btn btn-secondary btn-icon" @click="skipBackward" title="Voltar 10s">
                    ⏪
                </button>
                <button class="btn btn-secondary btn-icon" @click="skipForward" title="Avançar 10s">
                    ⏩
                </button>
            </div>
            
            <div class="controls-center">
                <div 
                    class="progress-bar" 
                    ref="progressRef"
                    @mousedown="beginSeekRequest"
                    @touchstart="beginSeekRequest"
                >
                    <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
                    <div class="progress-handle" :style="{ left: progressPercent + '%' }"></div>
                </div>
                <span class="time-display">
                    {{ formatTime(pendingSeekRequest ? seekPosition : currentPosition) }} / {{ formatTime(duration) }}
                </span>
            </div>
            
            <div class="controls-right">
                <select v-model="playbackSpeed" class="form-select speed-select" @change="updateSpeed">
                    <option value="0.25">0.25x</option>
                    <option value="0.5">0.5x</option>
                    <option value="1">1x</option>
                    <option value="1.5">1.5x</option>
                    <option value="2">2x</option>
                    <option value="4">4x</option>
                    <option value="8">8x</option>
                </select>
                <button class="btn btn-ghost btn-icon" @click="toggleFullscreen" title="Tela Cheia">
                    {{ isFullscreen ? '⛶' : '🔲' }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
    streamUrl: {
        type: String,
        required: true
    },
    autoPlay: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits(['loaded', 'error', 'progress', 'ended'])

// Refs
const containerRef = ref(null)
const displayRef = ref(null)
const progressRef = ref(null)

// State
const isLoaded = ref(false)
const isPlaying = ref(false)
const isFullscreen = ref(false)
const error = ref(null)
const loadingMessage = ref('Carregando replay...')
const currentPosition = ref(0)
const duration = ref(0)
const playbackSpeed = ref('1')

// Operation progress (baseado no projeto de referência)
const operationText = ref(null)
const operationProgress = ref(0)
const cancelOperation = ref(null)

// Seek state (baseado no projeto de referência)
const pendingSeekRequest = ref(false)
const resumeAfterSeekRequest = ref(false)
const seekPosition = ref(0)

// Guacamole instances
let recording = null
let display = null
let tunnel = null
let positionTimer = null

// Computed
const progressPercent = computed(() => {
    if (duration.value <= 0) return 0
    const pos = pendingSeekRequest.value ? seekPosition.value : currentPosition.value
    return (pos / duration.value) * 100
})

// Helper functions
function zeroPad(value) {
    return value > 9 ? value : '0' + value
}

function formatTime(ms) {
    const value = Math.floor((ms || 0) / 1000)
    const hours = Math.floor(value / 3600)
    const minutes = Math.floor((value % 3600) / 60)
    const seconds = value % 60
    
    if (hours > 0) {
        return `${hours}:${zeroPad(minutes)}:${zeroPad(seconds)}`
    }
    return `${zeroPad(minutes)}:${zeroPad(seconds)}`
}

// Timer functions
function startPositionTimer() {
    stopPositionTimer()
    positionTimer = setInterval(() => {
        if (recording && !pendingSeekRequest.value) {
            currentPosition.value = recording.getPosition()
            duration.value = recording.getDuration()
        }
    }, 100)
}

function stopPositionTimer() {
    if (positionTimer) {
        clearInterval(positionTimer)
        positionTimer = null
    }
}

// Seek functions (baseado no projeto de referência)
function beginSeekRequest(event) {
    if (!recording || !progressRef.value) return
    
    // Salvar estado de reprodução
    if (!pendingSeekRequest.value) {
        resumeAfterSeekRequest.value = isPlaying.value
        if (recording.isPlaying && recording.isPlaying()) {
            recording.pause()
        }
    }
    
    pendingSeekRequest.value = true
    
    // Calcular posição inicial
    updateSeekPosition(event)
    
    // Adicionar listeners para movimento
    document.addEventListener('mousemove', updateSeekPosition)
    document.addEventListener('mouseup', commitSeekRequest)
    document.addEventListener('touchmove', updateSeekPosition)
    document.addEventListener('touchend', commitSeekRequest)
}

function updateSeekPosition(event) {
    if (!progressRef.value) return
    
    const rect = progressRef.value.getBoundingClientRect()
    const clientX = event.type.includes('touch') ? event.touches[0].clientX : event.clientX
    const percent = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
    seekPosition.value = Math.floor(percent * duration.value)
}

function commitSeekRequest() {
    // Remover listeners
    document.removeEventListener('mousemove', updateSeekPosition)
    document.removeEventListener('mouseup', commitSeekRequest)
    document.removeEventListener('touchmove', updateSeekPosition)
    document.removeEventListener('touchend', commitSeekRequest)
    
    if (!recording || !pendingSeekRequest.value) return
    
    // Mostrar progresso durante seek
    operationText.value = 'Buscando posição solicitada...'
    operationProgress.value = 0
    
    cancelOperation.value = () => {
        if (recording.cancel) recording.cancel()
        operationText.value = null
        currentPosition.value = seekPosition.value
    }
    
    // Executar seek
    recording.seek(seekPosition.value, () => {
        operationText.value = null
        cancelOperation.value = null
        currentPosition.value = seekPosition.value
        
        // Retomar reprodução se estava tocando
        if (resumeAfterSeekRequest.value && recording.play) {
            recording.play()
        }
    })
    
    pendingSeekRequest.value = false
}

// Main loading function
async function loadRecording() {
    try {
        loadingMessage.value = 'Verificando biblioteca Guacamole...'
        
        if (typeof window.Guacamole === 'undefined') {
            throw new Error('Biblioteca Guacamole não carregada. Verifique a conexão com a internet.')
        }
        
        const Guacamole = window.Guacamole
        
        // Mostrar progresso de carregamento
        operationText.value = 'Seu replay está sendo carregado. Por favor aguarde...'
        operationProgress.value = 0
        
        cancelOperation.value = () => {
            if (recording && recording.abort) recording.abort()
            operationText.value = null
            error.value = 'Carregamento cancelado'
        }
        
        loadingMessage.value = 'Conectando ao servidor...'
        
        // Criar túnel estático
        tunnel = new Guacamole.StaticHTTPTunnel(props.streamUrl)
        
        loadingMessage.value = 'Inicializando player...'
        
        // Criar gravação
        recording = new Guacamole.SessionRecording(tunnel)
        
        // Obter display
        display = recording.getDisplay()
        
        // Adicionar display ao container
        await nextTick()
        if (displayRef.value) {
            const displayElement = display.getElement()
            displayElement.style.width = '100%'
            displayElement.style.height = '100%'
            displayElement.style.objectFit = 'contain'
            displayRef.value.appendChild(displayElement)
        }
        
        // Event handlers (baseados no projeto de referência)
        recording.onplay = () => {
            isPlaying.value = true
            startPositionTimer()
        }
        
        recording.onpause = () => {
            isPlaying.value = false
            stopPositionTimer()
        }
        
        // onprogress é chamado durante o download/parsing
        recording.onprogress = (recordingDuration, parsedSize) => {
            duration.value = recordingDuration
            
            // Calcular progresso se temos tamanho total
            if (tunnel.size) {
                operationProgress.value = parsedSize / tunnel.size
            }
            
            emit('progress', { duration: recordingDuration, loaded: parsedSize })
        }
        
        // onseek é chamado durante operações de seek
        recording.onseek = (position, current, total) => {
            if (!pendingSeekRequest.value) {
                currentPosition.value = position
            }
            
            // Atualizar progresso durante seek
            if (total > 0) {
                operationProgress.value = current / total
            }
            
            emit('progress', { position, current, total })
        }
        
        // onload é chamado quando termina de carregar
        recording.onload = () => {
            operationText.value = null
            cancelOperation.value = null
            duration.value = recording.getDuration()
            emit('loaded', { duration: duration.value })
        }
        
        recording.onerror = (msg) => {
            operationText.value = null
            cancelOperation.value = null
            
            let errorMessage = msg
            if (msg && msg.includes && msg.includes('403')) {
                errorMessage = 'Acesso negado. Verifique suas permissões.'
            } else if (msg && msg.includes && msg.includes('404')) {
                errorMessage = 'Arquivo de replay não encontrado.'
            } else if (msg && msg.includes && msg.includes('network')) {
                errorMessage = 'Erro de rede. Verifique sua conexão.'
            }
            
            error.value = `Erro ao reproduzir: ${errorMessage}`
            emit('error', errorMessage)
            stopPositionTimer()
        }
        
        // Conectar e carregar
        loadingMessage.value = 'Carregando dados da sessão...'
        recording.connect()
        
        // Aguardar carregamento inicial
        await new Promise((resolve, reject) => {
            const checkLoaded = setInterval(() => {
                if (recording.getDuration() > 0) {
                    clearInterval(checkLoaded)
                    resolve()
                }
            }, 100)
            
            // Timeout de 30 segundos
            setTimeout(() => {
                clearInterval(checkLoaded)
                if (recording.getDuration() === 0) {
                    reject(new Error('Timeout ao carregar replay. O arquivo pode estar vazio ou corrompido.'))
                } else {
                    resolve()
                }
            }, 30000)
        })
        
        duration.value = recording.getDuration()
        isLoaded.value = true
        error.value = null
        operationText.value = null
        cancelOperation.value = null
        
        emit('loaded', { duration: duration.value })
        
        if (props.autoPlay) {
            play()
        }
        
    } catch (err) {
        console.error('Erro ao carregar replay:', err)
        operationText.value = null
        cancelOperation.value = null
        error.value = `Falha ao carregar: ${err.message}`
        emit('error', err.message)
    }
}

function play() {
    if (recording && recording.play) {
        recording.play()
    }
}

function pause() {
    if (recording && recording.pause) {
        recording.pause()
    }
}

function togglePlay() {
    if (isPlaying.value) {
        pause()
    } else {
        play()
    }
}

function stop() {
    stopPositionTimer()
    if (recording) {
        if (recording.pause) recording.pause()
        if (recording.seek) recording.seek(0)
        currentPosition.value = 0
    }
}

function seek(event) {
    if (!recording || !progressRef.value) return
    
    const rect = progressRef.value.getBoundingClientRect()
    const percent = (event.clientX - rect.left) / rect.width
    const position = Math.floor(percent * duration.value)
    
    if (recording.seek) recording.seek(position)
}

function skipForward() {
    if (!recording) return
    const newPosition = Math.min(currentPosition.value + 10000, duration.value)
    if (recording.seek) recording.seek(newPosition)
}

function skipBackward() {
    if (!recording) return
    const newPosition = Math.max(currentPosition.value - 10000, 0)
    if (recording.seek) recording.seek(newPosition)
}

function updateSpeed() {
    console.log(`Velocidade alterada para ${playbackSpeed.value}x`)
}

function toggleFullscreen() {
    if (!containerRef.value) return
    
    if (!document.fullscreenElement) {
        containerRef.value.requestFullscreen().then(() => {
            isFullscreen.value = true
        }).catch(err => {
            console.error('Erro ao entrar em tela cheia:', err)
        })
    } else {
        document.exitFullscreen().then(() => {
            isFullscreen.value = false
        })
    }
}

function retryLoad() {
    error.value = null
    isLoaded.value = false
    operationText.value = null
    loadRecording()
}

function cleanup() {
    stopPositionTimer()
    if (recording) {
        try {
            if (recording.pause) recording.pause()
            if (recording.disconnect) recording.disconnect()
        } catch (e) {
            // Ignora erros na limpeza
        }
    }
    recording = null
    display = null
    tunnel = null
}

// Lifecycle
onMounted(() => {
    loadRecording()
    
    document.addEventListener('fullscreenchange', () => {
        isFullscreen.value = !!document.fullscreenElement
    })
})

onUnmounted(() => {
    cleanup()
})

// Watch for URL changes
watch(() => props.streamUrl, () => {
    cleanup()
    isLoaded.value = false
    error.value = null
    loadRecording()
})

// Expose methods
defineExpose({
    play,
    pause,
    togglePlay,
    stop,
    seek: (position) => recording?.seek?.(position),
    isPlaying: () => isPlaying.value,
    getDuration: () => duration.value,
    getPosition: () => currentPosition.value
})
</script>

<style scoped>
.guacamole-player {
    display: flex;
    flex-direction: column;
    background: var(--color-gray-900);
    border-radius: var(--radius-lg);
    overflow: hidden;
    height: 100%;
    position: relative;
}

.guacamole-player:fullscreen {
    border-radius: 0;
}

/* Operation Overlay (baseado no projeto de referência) */
.operation-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
}

.operation-content {
    text-align: center;
    max-width: 400px;
    padding: var(--spacing-xl);
}

.operation-spinner {
    width: 48px;
    height: 48px;
    border: 4px solid var(--color-gray-600);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto var(--spacing-md);
}

.operation-text {
    color: var(--color-gray-200);
    margin-bottom: var(--spacing-md);
    font-size: var(--font-size-sm);
}

.operation-progress-bar {
    height: 6px;
    background: var(--color-gray-700);
    border-radius: var(--radius-full);
    overflow: hidden;
    margin-bottom: var(--spacing-md);
}

.operation-progress-fill {
    height: 100%;
    background: var(--color-primary-500);
    transition: width 0.2s linear;
}

.player-display {
    flex: 1;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #000;
    min-height: 300px;
    overflow: hidden;
}

.player-display :deep(canvas) {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
}

.player-loading,
.player-error {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.8);
    color: var(--color-gray-300);
    z-index: 10;
}

.player-loading p,
.player-error p {
    margin-top: var(--spacing-md);
    text-align: center;
}

.error-icon {
    font-size: 3rem;
}

.player-controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: var(--color-gray-800);
    flex-wrap: wrap;
}

.controls-left,
.controls-right {
    display: flex;
    gap: var(--spacing-sm);
    align-items: center;
}

.controls-center {
    flex: 1;
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    min-width: 200px;
}

.progress-bar {
    flex: 1;
    height: 8px;
    background: var(--color-gray-600);
    border-radius: var(--radius-full);
    cursor: pointer;
    position: relative;
    user-select: none;
}

.progress-bar:hover {
    height: 10px;
}

.progress-fill {
    height: 100%;
    background: var(--color-primary-500);
    border-radius: var(--radius-full);
    transition: width 0.1s linear;
    pointer-events: none;
}

.progress-handle {
    position: absolute;
    top: 50%;
    width: 14px;
    height: 14px;
    background: var(--color-primary-400);
    border: 2px solid white;
    border-radius: 50%;
    transform: translate(-50%, -50%);
    opacity: 0;
    transition: opacity 0.2s;
    pointer-events: none;
}

.progress-bar:hover .progress-handle {
    opacity: 1;
}

.time-display {
    font-size: var(--font-size-sm);
    color: var(--color-gray-300);
    white-space: nowrap;
    font-family: monospace;
}

.speed-select {
    width: 70px;
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: var(--font-size-sm);
    background: var(--color-gray-700);
    border-color: var(--color-gray-600);
    color: white;
    border-radius: var(--radius-sm);
}

.btn-icon {
    min-width: 36px;
    height: 36px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
}

.btn-ghost {
    background: transparent;
    border: none;
    color: var(--color-gray-300);
}

.btn-ghost:hover {
    background: var(--color-gray-700);
    color: white;
}

/* Responsivo */
@media (max-width: 768px) {
    .player-controls {
        flex-wrap: wrap;
    }
    
    .controls-center {
        order: 3;
        width: 100%;
        margin-top: var(--spacing-sm);
    }
}

/* Spinner */
.spinner {
    border: 3px solid var(--color-gray-600);
    border-top-color: var(--color-primary-500);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.spinner-lg {
    width: 48px;
    height: 48px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
</style>
