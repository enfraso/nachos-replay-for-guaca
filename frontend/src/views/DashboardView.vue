<template>
    <div class="dashboard">
        <!-- Welcome Section -->
        <div class="welcome-section">
            <h2>{{ $t('dashboard.welcome') }}, {{ authStore.displayName }}!</h2>
            <p class="text-muted">{{ currentDate }}</p>
        </div>

        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stats-card">
                <div class="stats-card-icon">🎬</div>
                <div class="stats-card-content">
                    <div class="stats-card-value">{{ formatNumber(stats.totalReplays) }}</div>
                    <div class="stats-card-label">{{ $t('dashboard.totalReplays') }}</div>
                </div>
            </div>

            <div class="stats-card accent">
                <div class="stats-card-icon">👥</div>
                <div class="stats-card-content">
                    <div class="stats-card-value">{{ formatNumber(stats.totalUsers) }}</div>
                    <div class="stats-card-label">{{ $t('dashboard.totalUsers') }}</div>
                </div>
            </div>

            <div class="stats-card success">
                <div class="stats-card-icon">📅</div>
                <div class="stats-card-content">
                    <div class="stats-card-value">{{ formatNumber(stats.replaysToday) }}</div>
                    <div class="stats-card-label">{{ $t('dashboard.replaysToday') }}</div>
                </div>
            </div>

            <div class="stats-card warning">
                <div class="stats-card-icon">💾</div>
                <div class="stats-card-content">
                    <div class="stats-card-value">{{ formatBytes(stats.totalStorageBytes) }}</div>
                    <div class="stats-card-label">{{ $t('dashboard.storageUsed') }}</div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="charts-row">
            <!-- Replays Over Time -->
            <div class="card chart-card">
                <div class="card-header">
                    <h3>{{ $t('dashboard.replaysOverTime') }}</h3>
                </div>
                <div class="card-body">
                    <div class="chart-container">
                        <canvas ref="timeChartRef"></canvas>
                    </div>
                </div>
            </div>

            <!-- Top Users -->
            <div class="card">
                <div class="card-header">
                    <h3>{{ $t('dashboard.topUsers') }}</h3>
                </div>
                <div class="card-body">
                    <div v-if="statsStore.topUsers.length === 0" class="empty-state">
                        <p>{{ $t('common.noData') }}</p>
                    </div>
                    <div v-else class="top-users-list">
                        <div
                            v-for="(user, index) in statsStore.topUsers"
                            :key="user.username"
                            class="top-user-item"
                        >
                            <span class="rank">{{ index + 1 }}</span>
                            <span class="username">{{ user.display_name || user.username }}</span>
                            <span class="count">{{ user.replay_count }} replays</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { useStatsStore } from '@/stores/stats'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const { locale } = useI18n()
const authStore = useAuthStore()
const statsStore = useStatsStore()

const timeChartRef = ref(null)
let timeChart = null

const stats = computed(() => statsStore.overview)

const currentDate = computed(() => {
    return new Date().toLocaleDateString(locale.value, {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    })
})

function formatNumber(num) {
    return new Intl.NumberFormat(locale.value).format(num || 0)
}

function formatBytes(bytes) {
    if (!bytes) return '0 B'
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}

function updateChart() {
    if (!timeChartRef.value || !statsStore.replaysOverTime.length) return

    const ctx = timeChartRef.value.getContext('2d')

    if (timeChart) {
        timeChart.destroy()
    }

    const labels = statsStore.replaysOverTime.map(d => {
        const date = new Date(d.date)
        return date.toLocaleDateString(locale.value, { month: 'short', day: 'numeric' })
    })

    const data = statsStore.replaysOverTime.map(d => d.count)

    timeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Replays',
                data,
                borderColor: '#005BAB',
                backgroundColor: 'rgba(0, 91, 171, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#005BAB',
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        precision: 0
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    })
}

onMounted(async () => {
    await statsStore.fetchAll()
    updateChart()
})

onUnmounted(() => {
    if (timeChart) {
        timeChart.destroy()
    }
})
</script>

<style scoped>
.dashboard {
    max-width: var(--content-max-width);
}

.welcome-section {
    margin-bottom: var(--spacing-xl);
}

.welcome-section h2 {
    margin-bottom: var(--spacing-xs);
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--spacing-lg);
    margin-bottom: var(--spacing-xl);
}

.stats-card-content {
    flex: 1;
}

.charts-row {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: var(--spacing-lg);
}

.chart-card .card-body {
    height: 300px;
    padding: var(--spacing-md);
}

.chart-container {
    height: 100%;
    width: 100%;
}

.empty-state {
    text-align: center;
    color: var(--text-muted);
    padding: var(--spacing-xl);
}

.top-users-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
}

.top-user-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--color-gray-50);
    border-radius: var(--radius-md);
}

.top-user-item .rank {
    width: 24px;
    height: 24px;
    background: var(--color-primary-500);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-bold);
}

.top-user-item .username {
    flex: 1;
    font-weight: var(--font-weight-medium);
}

.top-user-item .count {
    font-size: var(--font-size-sm);
    color: var(--text-muted);
}

@media (max-width: 1280px) {
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 1024px) {
    .charts-row {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .stats-grid {
        grid-template-columns: 1fr;
    }
    
    .chart-card .card-body {
        height: 250px;
    }
}
</style>
