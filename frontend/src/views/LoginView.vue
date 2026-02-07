<template>
    <div class="login-page">
        <div class="login-card">
            <!-- Logo -->
            <div class="login-header">
                <div class="logo">
                    <span class="logo-icon">🌮</span>
                    <h1>Nachos Replay</h1>
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

            <!-- Demo Credentials -->
            <div class="demo-info">
                <p>Usuários de teste:</p>
                <div class="demo-users">
                    <button @click="fillDemo('admin', 'admin123')" class="demo-btn">
                        admin / admin123
                    </button>
                    <button @click="fillDemo('viewer', 'viewer123')" class="demo-btn">
                        viewer / viewer123
                    </button>
                    <button @click="fillDemo('auditor', 'auditor123')" class="demo-btn">
                        auditor / auditor123
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')

async function handleLogin() {
    authStore.clearError()

    const success = await authStore.login(username.value, password.value)

    if (success) {
        const redirect = route.query.redirect || '/'
        router.push(redirect)
    }
}

function fillDemo(user, pass) {
    username.value = user
    password.value = pass
}
</script>

<style scoped>
.login-page {
    width: 100%;
    padding: var(--spacing-lg);
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

.demo-info {
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-color);
    text-align: center;
}

.demo-info p {
    font-size: var(--font-size-xs);
    color: var(--text-muted);
    margin-bottom: var(--spacing-sm);
}

.demo-users {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
}

.demo-btn {
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--color-gray-100);
    border: none;
    border-radius: var(--radius-sm);
    font-size: var(--font-size-xs);
    font-family: monospace;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
}

.demo-btn:hover {
    background: var(--color-primary-100);
    color: var(--color-primary-600);
}

@media (max-width: 768px) {
    .login-card {
        padding: var(--spacing-lg);
    }
}
</style>
