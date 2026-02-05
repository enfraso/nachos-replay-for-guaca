/**
 * Nachos Replay for Guaca - Vue Router
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/LoginView.vue'),
        meta: { requiresAuth: false, layout: 'blank' }
    },
    {
        path: '/',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/replays',
        name: 'Replays',
        component: () => import('@/views/ReplaysView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/replays/:id',
        name: 'ReplayPlayer',
        component: () => import('@/views/ReplayPlayerView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/audit',
        name: 'Audit',
        component: () => import('@/views/AuditLogsView.vue'),
        meta: { requiresAuth: true, requiresRole: ['admin', 'auditor'] }
    },
    {
        path: '/users',
        name: 'Users',
        component: () => import('@/views/UsersView.vue'),
        meta: { requiresAuth: true, requiresRole: ['admin'] }
    },
    {
        path: '/groups',
        name: 'Groups',
        component: () => import('@/views/GroupsView.vue'),
        meta: { requiresAuth: true, requiresRole: ['admin'] }
    },
    {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue'),
        meta: { requiresAuth: true, requiresRole: ['admin'] }
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/NotFoundView.vue'),
        meta: { requiresAuth: false, layout: 'blank' }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// Navigation guard
router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()

    // Initialize auth store if needed
    if (!authStore.user && authStore.accessToken) {
        await authStore.init()
    }

    // Check if route requires authentication
    if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
        return next({ name: 'Login', query: { redirect: to.fullPath } })
    }

    // Check if route requires specific role
    if (to.meta.requiresRole) {
        const userRole = authStore.userRole
        if (!to.meta.requiresRole.includes(userRole)) {
            return next({ name: 'Dashboard' })
        }
    }

    // Redirect to dashboard if already logged in
    if (to.name === 'Login' && authStore.isAuthenticated) {
        return next({ name: 'Dashboard' })
    }

    next()
})

export default router
