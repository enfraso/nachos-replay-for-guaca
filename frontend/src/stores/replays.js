/**
 * Nachos Replay for Guaca - Replays Store
 * Pinia store for replays state management
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/composables/useApi'

export const useReplaysStore = defineStore('replays', () => {
    // State
    const replays = ref([])
    const currentReplay = ref(null)
    const total = ref(0)
    const page = ref(1)
    const pageSize = ref(20)
    const isLoading = ref(false)
    const error = ref(null)

    // Filters
    const filters = ref({
        query: '',
        username: '',
        sessionName: '',
        clientIp: '',
        dateFrom: null,
        dateTo: null,
        status: ''
    })

    // Getters
    const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1)
    const hasFilters = computed(() => {
        return Object.values(filters.value).some(v => v !== '' && v !== null)
    })

    // Actions
    async function fetchReplays() {
        isLoading.value = true
        error.value = null

        try {
            const params = new URLSearchParams()
            params.append('page', page.value)
            params.append('page_size', pageSize.value)

            if (filters.value.query) params.append('query', filters.value.query)
            if (filters.value.username) params.append('username', filters.value.username)
            if (filters.value.sessionName) params.append('session_name', filters.value.sessionName)
            if (filters.value.clientIp) params.append('client_ip', filters.value.clientIp)
            if (filters.value.dateFrom) params.append('date_from', filters.value.dateFrom)
            if (filters.value.dateTo) params.append('date_to', filters.value.dateTo)
            if (filters.value.status) params.append('status', filters.value.status)

            const response = await api.get(`/api/replays?${params.toString()}`)

            replays.value = response.data.items
            total.value = response.data.total

            return response.data
        } catch (err) {
            error.value = err.response?.data?.detail || 'Failed to fetch replays'
            return null
        } finally {
            isLoading.value = false
        }
    }

    async function fetchReplay(id) {
        isLoading.value = true
        error.value = null

        try {
            const response = await api.get(`/api/replays/${id}`)
            currentReplay.value = response.data
            return response.data
        } catch (err) {
            error.value = err.response?.data?.detail || 'Failed to fetch replay'
            return null
        } finally {
            isLoading.value = false
        }
    }

    async function deleteReplay(id, hardDelete = false) {
        try {
            await api.delete(`/api/replays/${id}?hard_delete=${hardDelete}`)

            // Remove from list
            replays.value = replays.value.filter(r => r.id !== id)
            total.value--

            return true
        } catch (err) {
            error.value = err.response?.data?.detail || 'Failed to delete replay'
            return false
        }
    }

    function getStreamUrl(id) {
        return `/api/replays/${id}/stream`
    }

    function setPage(newPage) {
        page.value = newPage
    }

    function setFilters(newFilters) {
        filters.value = { ...filters.value, ...newFilters }
        page.value = 1 // Reset to first page
    }

    function clearFilters() {
        filters.value = {
            query: '',
            username: '',
            sessionName: '',
            clientIp: '',
            dateFrom: null,
            dateTo: null,
            status: ''
        }
        page.value = 1
    }

    return {
        // State
        replays,
        currentReplay,
        total,
        page,
        pageSize,
        isLoading,
        error,
        filters,
        // Getters
        totalPages,
        hasFilters,
        // Actions
        fetchReplays,
        fetchReplay,
        deleteReplay,
        getStreamUrl,
        setPage,
        setFilters,
        clearFilters
    }
})
