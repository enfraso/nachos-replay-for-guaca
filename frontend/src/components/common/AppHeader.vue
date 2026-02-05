<template>
  <header class="app-header">
    <div class="header-left">
      <button class="menu-btn" @click="$emit('toggle-sidebar')">
        ☰
      </button>
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>

    <div class="header-right">
      <!-- Language Selector -->
      <div class="lang-selector">
        <button 
          class="lang-btn"
          :class="{ active: $i18n.locale === 'pt-BR' }"
          @click="setLocale('pt-BR')"
        >
          PT
        </button>
        <button 
          class="lang-btn"
          :class="{ active: $i18n.locale === 'en-US' }"
          @click="setLocale('en-US')"
        >
          EN
        </button>
      </div>

      <!-- User Menu -->
      <div class="user-menu" @click="showUserMenu = !showUserMenu">
        <div class="user-avatar">
          {{ userInitials }}
        </div>
        <span class="user-name">{{ authStore.displayName }}</span>
        <span class="dropdown-arrow">▾</span>

        <div v-if="showUserMenu" class="dropdown-menu">
          <div class="dropdown-item user-info">
            <span class="label">{{ $t('users.role') }}</span>
            <span class="badge badge-primary">{{ $t(`users.roles.${authStore.userRole}`) }}</span>
          </div>
          <hr />
          <button class="dropdown-item" @click="logout">
            🚪 {{ $t('auth.logout') }}
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import { setLocale as setI18nLocale } from '@/i18n'

defineEmits(['toggle-sidebar'])

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()

const showUserMenu = ref(false)

const pageTitle = computed(() => {
  const routeName = route.name?.toLowerCase() || 'dashboard'
  return t(`nav.${routeName}`) || route.name
})

const userInitials = computed(() => {
  const name = authStore.displayName || authStore.user?.username || ''
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
})

function setLocale(locale) {
  setI18nLocale(locale)
}

async function logout() {
  await authStore.logout()
  router.push('/login')
}

// Close dropdown on outside click
function handleClickOutside(e) {
  if (!e.target.closest('.user-menu')) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  background: var(--bg-header);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-lg);
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.menu-btn {
  display: none;
  padding: var(--spacing-sm);
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: var(--text-primary);
}

.page-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
}

.lang-selector {
  display: flex;
  gap: 2px;
  background: var(--color-gray-100);
  border-radius: var(--border-radius-md);
  padding: 2px;
}

.lang-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  background: transparent;
  border: none;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--border-radius-sm);
  transition: all var(--transition-fast);
}

.lang-btn.active {
  background: var(--bg-secondary);
  color: var(--color-primary-500);
  box-shadow: var(--shadow-sm);
}

.user-menu {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-gray-50);
  border-radius: var(--border-radius-md);
  cursor: pointer;
  position: relative;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--color-primary-500), var(--color-accent-500));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-inverse);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
}

.user-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.dropdown-arrow {
  color: var(--text-muted);
  font-size: 10px;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: var(--spacing-xs);
  min-width: 200px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-md);
  box-shadow: var(--shadow-lg);
  z-index: var(--z-dropdown);
}

.dropdown-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  width: 100%;
  background: none;
  border: none;
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
}

.dropdown-item:hover {
  background: var(--color-gray-50);
}

.dropdown-item.user-info {
  cursor: default;
}

.dropdown-item.user-info:hover {
  background: transparent;
}

.dropdown-item .label {
  color: var(--text-secondary);
}

.dropdown-menu hr {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 0;
}

@media (max-width: 768px) {
  .menu-btn {
    display: block;
  }
  
  .user-name {
    display: none;
  }
}
</style>
