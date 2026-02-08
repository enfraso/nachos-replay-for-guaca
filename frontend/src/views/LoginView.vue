<template>
    <div class="login-page">
        <div class="login-card">
            <!-- Logo -->
            <div class="login-header">
                <div class="logo">
                    <img 
                        v-if="branding.logoUrl" 
                        :src="branding.logoUrl" 
                        :alt="branding.appName"
                        class="logo-image"
                    />
                    <span v-else class="logo-icon">{{ branding.logoEmoji }}</span>
                    <h1>{{ branding.appName }}</h1>
                </div>
                <p class="subtitle">{{ $t('auth.loginSubtitle') }}</p>
            </div>

            <!-- Error Message -->
            <div v-if="authStore.error" class="alert alert-error">
                {{ authStore.error }}
            </div>

            <!-- Login Form -->
            <form @submit.prevent="handleLogin" class="login-form">
                <div class="form-group">
                    <label class="form-label" for="username">
                        {{ $t('auth.username') }}
                    </label>
                    <input
                        id="username"
                        v-model="username"
                        type="text"
                        class="form-input"
                        :placeholder="$t('auth.username')"
                        required
                        autofocus
                    />
                </div>

                <div class="form-group">
                    <label class="form-label" for="password">
                        {{ $t('auth.password') }}
                    </label>
                    <input
                        id="password"
                        v-model="password"
                        type="password"
                        class="form-input"
                        :placeholder="$t('auth.password')"
                        required
                    />
                </div>

                <button
                    type="submit"
                    class="btn btn-primary btn-lg btn-block"
                    :disabled="authStore.isLoading || !username || !password"
                >
                    <span v-if="authStore.isLoading" class="spinner spinner-white"></span>
                    <span v-else>{{ $t('auth.login') }}</span>
                </button>
            </form>

            <!-- Footer -->
            <div class="login-footer">
                <p>{{ branding.footerText }}</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')

// Configuração de branding - facilmente customizável via variáveis de ambiente
const branding = computed(() => ({
    appName: import.meta.env.VITE_APP_NAME || 'Nachos Replay',
    logoUrl: import.meta.env.VITE_LOGO_URL || '',  // URL da logo customizada
    logoEmoji: import.meta.env.VITE_LOGO_EMOJI || '🌮',
    footerText: import.meta.env.VITE_FOOTER_TEXT || ''
}))

async function handleLogin() {
    authStore.clearError()

    const success = await authStore.login(username.value, password.value)

    if (success) {
        const redirect = route.query.redirect || '/'
        router.push(redirect)
    }
}
</script>

<style scoped>
.login-page {
    min-height: 100vh;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-lg);
    background: linear-gradient(135deg, var(--color-gray-900) 0%, var(--color-gray-800) 100%);
}

.login-card {
    width: 100%;
    max-width: 420px;
    background: var(--bg-card);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-xl);
    padding: var(--spacing-2xl);
    animation: slideUp 0.4s ease;
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.login-header {
    text-align: center;
    margin-bottom: var(--spacing-xl);
}

.logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
}

.logo-icon {
    font-size: 2.5rem;
}

.logo-image {
    height: 48px;
    width: auto;
    object-fit: contain;
}

.logo h1 {
    font-size: var(--font-size-2xl);
    background: linear-gradient(135deg, var(--color-primary-500), var(--color-accent-500));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}

.subtitle {
    color: var(--text-secondary);
    margin: 0;
}

.login-form {
    margin-bottom: var(--spacing-lg);
}

.btn-block {
    width: 100%;
    justify-content: center;
}

.login-footer {
    text-align: center;
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-color);
}

.login-footer p {
    font-size: var(--font-size-xs);
    color: var(--text-muted);
    margin: 0;
}

@media (max-width: 768px) {
    .login-card {
        padding: var(--spacing-lg);
    }
}
</style>
