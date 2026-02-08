/**
 * Nachos Replay - Stats Store
 * Pinia store for dashboard statistics
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/composables/useApi'

export const useStatsStore = defineStore('stats', () => {
    // State
    const overview = ref({
        totalReplays: 0,
        totalUsers: 0,
        totalStorageBytes: 0,
        replaysToday: 0,
        replaysThisWeek: 0,
        activeSessions: 0
    })

    const topUsers = ref([])
    const replaysOverTime = ref([])
    const isLoading = ref(false)
    const error = ref(null)

    // Actions
    async function fetchOverview() {
        isLoading.value = true
        error.value = null

        try {
            const response = await api.get('/api/stats/overview')
            overview.value = response.data
            return overview.value
        } catch (err) {
            error.value = 'Falha ao carregar estatísticas'
            console.error('Failed to fetch stats:', err)
            return null
        } finally {
            isLoading.value = false
        }
    }

    async function fetchTopUsers(limit = 5) {
        try {
            const response = await api.get(`/api/stats/top-users?limit=${limit}`)
            topUsers.value = response.data
            return topUsers.value
        } catch (err) {
            console.error('Failed to fetch top users:', err)
            return []
        }
    }

    async function fetchReplaysOverTime(days = 14) {
        try {
            const response = await api.get(`/api/stats/replays-over-time?days=${days}`)
            replaysOverTime.value = response.data
            return replaysOverTime.value
        } catch (err) {
            console.error('Failed to fetch replays over time:', err)
            return []
        }
    }

    async function fetchAll() {
        await Promise.all([
            fetchOverview(),
            fetchTopUsers(),
            fetchReplaysOverTime()
        ])
    }

    return {
        // State
        overview,
        topUsers,
        replaysOverTime,
        isLoading,
        error,
        // Actions
        fetchOverview,
        fetchTopUsers,
        fetchReplaysOverTime,
        fetchAll
    }
})
