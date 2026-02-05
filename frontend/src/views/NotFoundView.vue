<template>
  <div class="not-found-page">
    <div class="not-found-card">
      <div class="error-code">404</div>
      <h1>Página não encontrada</h1>
      <p class="text-muted">
        A página que você está procurando não existe ou foi removida.
      </p>
      <router-link to="/" class="btn btn-primary">
        ← Voltar ao Dashboard
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.not-found-page {
  width: 100%;
  padding: var(--spacing-lg);
}

.not-found-card {
  max-width: 400px;
  background: var(--bg-card);
  border-radius: var(--border-radius-xl);
  box-shadow: var(--shadow-xl);
  padding: var(--spacing-2xl);
  text-align: center;
}

.error-code {
  font-size: 6rem;
  font-weight: var(--font-weight-bold);
  background: linear-gradient(135deg, var(--color-primary-500), var(--color-accent-500));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: var(--spacing-md);
}

h1 {
  margin-bottom: var(--spacing-sm);
}

p {
  margin-bottom: var(--spacing-xl);
}
</style>
