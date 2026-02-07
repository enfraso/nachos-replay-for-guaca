<template>
    <div class="not-found-page">
        <div class="not-found-card">
            <div class="error-icon">🔍</div>
            <h1>404</h1>
            <h2>{{ $t('errors.notFound') }}</h2>
            <p>{{ $t('errors.notFoundMessage') }}</p>
            <router-link to="/" class="btn btn-primary btn-lg">
                {{ $t('errors.goHome') }}
            </router-link>
        </div>
    </div>
</template>

<script setup>
</script>

<style scoped>
.not-found-page {
    width: 100%;
    padding: var(--spacing-lg);
}

.not-found-card {
    text-align: center;
    background: var(--bg-card);
    border-radius: var(--radius-xl);
    padding: var(--spacing-3xl);
    box-shadow: var(--shadow-xl);
    max-width: 500px;
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

.error-icon {
    font-size: 4rem;
    margin-bottom: var(--spacing-md);
}

.not-found-card h1 {
    font-size: 5rem;
    background: linear-gradient(135deg, var(--color-primary-500), var(--color-accent-500));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1;
}

.not-found-card h2 {
    font-size: var(--font-size-xl);
    margin: var(--spacing-md) 0;
}

.not-found-card p {
    color: var(--text-muted);
    margin-bottom: var(--spacing-xl);
}
</style>
