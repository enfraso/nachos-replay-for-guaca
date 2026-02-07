/**
 * Nachos Replay - Replays Store
 * Pinia store for replays management
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/composables/useApi'

export const useReplaysStore = defineStore('replays', () => {
    // State
    const replays = ref([])
    const currentReplay = ref(null)
    const isLoading = ref(false)
    const error = ref(null)

    // Pagination
    const page = ref(1)
    const perPage = ref(20)
    const total = ref(0)

    // Filters
    const filters = ref({
        search: '',
        username: '',
        startDate: '',
        endDate: '',
        status: ''
    })

    // Getters
    const totalPages = computed(() => Math.ceil(total.value / perPage.value))
    const hasNextPage = computed(() => page.value < totalPages.value)
    const hasPrevPage = computed(() => page.value > 1)

    // Actions
    async function fetchReplays(resetPage = false) {
        if (resetPage) page.value = 1

        isLoading.value = true
        error.value = null

        try {
            const params = new URLSearchParams({
                page: page.value,
                per_page: perPage.value
            })

            if (filters.value.search) params.append('search', filters.value.search)
            if (filters.value.username) params.append('username', filters.value.username)
            if (filters.value.startDate) params.append('start_date', filters.value.startDate)
            if (filters.value.endDate) params.append('end_date', filters.value.endDate)
            if (filters.value.status) params.append('status', filters.value.status)

            const response = await api.get(`/api/replays?${params}`)

            replays.value = response.data.items || response.data
            total.value = response.data.total || replays.value.length

            return replays.value
        } catch (err) {
            error.value = 'Falha ao carregar replays'
            console.error('Failed to fetch replays:', err)
            return []
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
            return currentReplay.value
        } catch (err) {
            error.value = 'Falha ao carregar replay'
            console.error('Failed to fetch replay:', err)
            return null
        } finally {
            isLoading.value = false
        }
    }

    async function deleteReplay(id) {
        try {
            await api.delete(`/api/replays/${id}`)
            replays.value = replays.value.filter(r => r.id !== id)
            return true
        } catch (err) {
            error.value = 'Falha ao excluir replay'
            return false
        }
    }

    function setFilters(newFilters) {
        filters.value = { ...filters.value, ...newFilters }
    }

    function resetFilters() {
        filters.value = {
            search: '',
            username: '',
            startDate: '',
            endDate: '',
            status: ''
        }
        page.value = 1
    }

    function nextPage() {
        if (hasNextPage.value) {
            page.value++
            fetchReplays()
        }
    }

    function prevPage() {
        if (hasPrevPage.value) {
            page.value--
            fetchReplays()
        }
    }

    function goToPage(pageNum) {
        if (pageNum >= 1 && pageNum <= totalPages.value) {
            page.value = pageNum
            fetchReplays()
        }
    }

    return {
        // State
        replays,
        currentReplay,
        isLoading,
        error,
        page,
        perPage,
        total,
        filters,
        // Getters
        totalPages,
        hasNextPage,
        hasPrevPage,
        // Actions
        fetchReplays,
        fetchReplay,
        deleteReplay,
        setFilters,
        resetFilters,
        nextPage,
        prevPage,
        goToPage
    }
})
