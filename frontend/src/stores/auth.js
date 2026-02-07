/**
 * Nachos Replay - Auth Store
 * Pinia store for authentication state
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/composables/useApi'

export const useAuthStore = defineStore('auth', () => {
    // State
    const user = ref(null)
    const accessToken = ref(localStorage.getItem('accessToken') || null)
    const refreshToken = ref(localStorage.getItem('refreshToken') || null)
    const isLoading = ref(false)
    const error = ref(null)

    // Getters
    const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
    const isAdmin = computed(() => user.value?.role === 'admin')
    const isAuditor = computed(() => ['admin', 'auditor'].includes(user.value?.role))
    const userRole = computed(() => user.value?.role || 'viewer')
    const displayName = computed(() => user.value?.display_name || user.value?.username || '')

    // Actions
    async function login(username, password) {
        isLoading.value = true
        error.value = null

        try {
            const response = await api.post('/api/auth/login', { username, password })

            accessToken.value = response.data.access_token
            refreshToken.value = response.data.refresh_token

            localStorage.setItem('accessToken', response.data.access_token)
            localStorage.setItem('refreshToken', response.data.refresh_token)

            await fetchUser()
            return true
        } catch (err) {
            error.value = err.response?.data?.detail || 'Falha no login. Verifique suas credenciais.'
            return false
        } finally {
            isLoading.value = false
        }
    }

    async function fetchUser() {
        if (!accessToken.value) return null

        try {
            const response = await api.get('/api/auth/me')
            user.value = response.data
            return user.value
        } catch (err) {
            if (err.response?.status === 401) {
                await logout()
            }
            return null
        }
    }

    async function refreshAccessToken() {
        if (!refreshToken.value) return false

        try {
            const response = await api.post('/api/auth/refresh', {
                refresh_token: refreshToken.value
            })

            accessToken.value = response.data.access_token
            refreshToken.value = response.data.refresh_token

            localStorage.setItem('accessToken', response.data.access_token)
            localStorage.setItem('refreshToken', response.data.refresh_token)

            return true
        } catch (err) {
            await logout()
            return false
        }
    }

    async function logout() {
        try {
            if (accessToken.value) {
                await api.post('/api/auth/logout')
            }
        } catch (err) {
            // Ignore errors on logout
        } finally {
            user.value = null
            accessToken.value = null
            refreshToken.value = null
            localStorage.removeItem('accessToken')
            localStorage.removeItem('refreshToken')
        }
    }

    function clearError() {
        error.value = null
    }

    async function init() {
        if (accessToken.value) {
            await fetchUser()
        }
    }

    return {
        // State
        user,
        accessToken,
        refreshToken,
        isLoading,
        error,
        // Getters
        isAuthenticated,
        isAdmin,
        isAuditor,
        userRole,
        displayName,
        // Actions
        login,
        logout,
        fetchUser,
        refreshAccessToken,
        clearError,
        init
    }
})
