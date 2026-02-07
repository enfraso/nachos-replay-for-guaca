<template>
    <div class="default-layout" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
        <!-- Sidebar -->
        <aside class="sidebar" :class="{ 'mobile-open': isMobileMenuOpen }">
            <div class="sidebar-header">
                <div class="logo">
                    <span class="logo-icon">🌮</span>
                    <span class="logo-text" v-show="!isSidebarCollapsed">Nachos Replay</span>
                </div>
                <button class="btn-toggle hide-mobile" @click="toggleSidebar" :title="isSidebarCollapsed ? 'Expandir' : 'Recolher'">
                    <span v-if="isSidebarCollapsed">→</span>
                    <span v-else>←</span>
                </button>
            </div>
            
            <nav class="sidebar-nav">
                <router-link to="/" class="nav-item" @click="closeMobileMenu">
                    <span class="nav-icon">📊</span>
                    <span class="nav-text">{{ $t('nav.dashboard') }}</span>
                </router-link>
                
                <router-link to="/replays" class="nav-item" @click="closeMobileMenu">
                    <span class="nav-icon">🎬</span>
                    <span class="nav-text">{{ $t('nav.replays') }}</span>
                </router-link>
                
                <router-link v-if="authStore.isAuditor" to="/audit" class="nav-item" @click="closeMobileMenu">
                    <span class="nav-icon">📋</span>
                    <span class="nav-text">{{ $t('nav.audit') }}</span>
                </router-link>
                
                <div v-if="authStore.isAdmin" class="nav-divider"></div>
                
                <router-link v-if="authStore.isAdmin" to="/users" class="nav-item" @click="closeMobileMenu">
                    <span class="nav-icon">👥</span>
                    <span class="nav-text">{{ $t('nav.users') }}</span>
                </router-link>
                
                <router-link v-if="authStore.isAdmin" to="/groups" class="nav-item" @click="closeMobileMenu">
                    <span class="nav-icon">🏷️</span>
                    <span class="nav-text">{{ $t('nav.groups') }}</span>
                </router-link>
                
                <router-link v-if="authStore.isAdmin" to="/settings" class="nav-item" @click="closeMobileMenu">
                    <span class="nav-icon">⚙️</span>
                    <span class="nav-text">{{ $t('nav.settings') }}</span>
                </router-link>
            </nav>
            
            <div class="sidebar-footer">
                <div class="user-info">
                    <div class="user-avatar">{{ userInitials }}</div>
                    <div class="user-details" v-show="!isSidebarCollapsed">
                        <div class="user-name">{{ authStore.displayName }}</div>
                        <div class="user-role">{{ $t(`users.roles.${authStore.userRole}`) }}</div>
                    </div>
                </div>
                <button class="btn-logout" @click="handleLogout" :title="$t('auth.logout')">
                    <span>🚪</span>
                </button>
            </div>
        </aside>
        
        <!-- Mobile overlay -->
        <div class="mobile-overlay" v-if="isMobileMenuOpen" @click="closeMobileMenu"></div>
        
        <!-- Main content -->
        <div class="main-wrapper">
            <!-- Topbar -->
            <header class="topbar">
                <button class="btn-menu hide-desktop" @click="toggleMobileMenu">
                    <span>☰</span>
                </button>
                
                <div class="topbar-title hide-mobile">
                    <h1>{{ pageTitle }}</h1>
                </div>
                
                <div class="topbar-actions">
                    <button class="btn btn-ghost btn-icon" @click="refreshPage" title="Atualizar">
                        🔄
                    </button>
                </div>
            </header>
            
            <!-- Page content -->
            <main class="main-content">
                <slot></slot>
            </main>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()

const isSidebarCollapsed = ref(false)
const isMobileMenuOpen = ref(false)

const pageTitle = computed(() => {
    const titles = {
        'Dashboard': t('nav.dashboard'),
        'Replays': t('nav.replays'),
        'ReplayPlayer': t('player.title'),
        'Audit': t('nav.audit'),
        'Users': t('nav.users'),
        'Groups': t('nav.groups'),
        'Settings': t('nav.settings')
    }
    return titles[route.name] || 'Nachos Replay'
})

const userInitials = computed(() => {
    const name = authStore.displayName || 'U'
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
})

function toggleSidebar() {
    isSidebarCollapsed.value = !isSidebarCollapsed.value
}

function toggleMobileMenu() {
    isMobileMenuOpen.value = !isMobileMenuOpen.value
}

function closeMobileMenu() {
    isMobileMenuOpen.value = false
}

function refreshPage() {
    window.location.reload()
}

async function handleLogout() {
    await authStore.logout()
    router.push('/login')
}
</script>

<style scoped>
.default-layout {
    display: flex;
    min-height: 100vh;
    background: var(--bg-primary);
}

/* Sidebar */
.sidebar {
    width: var(--sidebar-width);
    background: var(--bg-sidebar);
    display: flex;
    flex-direction: column;
    transition: width var(--transition-normal);
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: var(--z-fixed);
}

.sidebar-collapsed .sidebar {
    width: var(--sidebar-collapsed-width);
}

.sidebar-header {
    padding: var(--spacing-md);
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
}

.logo-icon {
    font-size: 1.75rem;
}

.logo-text {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-bold);
    color: var(--text-inverse);
    white-space: nowrap;
}

.btn-toggle {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: var(--text-inverse);
    width: 32px;
    height: 32px;
    border-radius: var(--radius-md);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background var(--transition-fast);
}

.btn-toggle:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* Navigation */
.sidebar-nav {
    flex: 1;
    padding: var(--spacing-md) var(--spacing-sm);
    overflow-y: auto;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-sm) var(--spacing-md);
    color: rgba(255, 255, 255, 0.7);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-xs);
    transition: all var(--transition-fast);
    text-decoration: none;
}

.nav-item:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-inverse);
}

.nav-item.router-link-active {
    background: var(--color-primary-500);
    color: var(--text-inverse);
}

.nav-icon {
    font-size: 1.25rem;
    width: 24px;
    text-align: center;
}

.nav-text {
    white-space: nowrap;
}

.sidebar-collapsed .nav-text {
    display: none;
}

.nav-divider {
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
    margin: var(--spacing-md) var(--spacing-sm);
}

/* Sidebar footer */
.sidebar-footer {
    padding: var(--spacing-md);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.user-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
}

.user-avatar {
    width: 36px;
    height: 36px;
    background: var(--color-accent-500);
    color: var(--text-inverse);
    border-radius: var(--radius-full);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-bold);
}

.user-details {
    overflow: hidden;
}

.user-name {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--text-inverse);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.user-role {
    font-size: var(--font-size-xs);
    color: rgba(255, 255, 255, 0.6);
}

.sidebar-collapsed .user-details {
    display: none;
}

.btn-logout {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: var(--text-inverse);
    width: 36px;
    height: 36px;
    border-radius: var(--radius-md);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background var(--transition-fast);
}

.btn-logout:hover {
    background: var(--color-error-500);
}

/* Main wrapper */
.main-wrapper {
    flex: 1;
    margin-left: var(--sidebar-width);
    display: flex;
    flex-direction: column;
    transition: margin-left var(--transition-normal);
}

.sidebar-collapsed .main-wrapper {
    margin-left: var(--sidebar-collapsed-width);
}

/* Topbar */
.topbar {
    height: var(--topbar-height);
    background: var(--bg-topbar);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 var(--spacing-lg);
    position: sticky;
    top: 0;
    z-index: var(--z-sticky);
}

.topbar-title h1 {
    font-size: var(--font-size-xl);
    margin: 0;
}

.topbar-actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
}

.btn-menu {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    padding: var(--spacing-sm);
}

/* Main content */
.main-content {
    flex: 1;
    padding: var(--spacing-lg);
    max-width: 100%;
    overflow-x: hidden;
}

/* Mobile */
.mobile-overlay {
    display: none;
}

@media (max-width: 768px) {
    .sidebar {
        transform: translateX(-100%);
        width: var(--sidebar-width);
    }
    
    .sidebar.mobile-open {
        transform: translateX(0);
    }
    
    .sidebar-collapsed .sidebar {
        width: var(--sidebar-width);
    }
    
    .main-wrapper {
        margin-left: 0;
    }
    
    .sidebar-collapsed .main-wrapper {
        margin-left: 0;
    }
    
    .mobile-overlay {
        display: block;
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: calc(var(--z-fixed) - 1);
    }
    
    .main-content {
        padding: var(--spacing-md);
    }
    
    .topbar-title h1 {
        font-size: var(--font-size-lg);
    }
}
</style>
