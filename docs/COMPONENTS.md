# Componentes do Frontend - Nachos Replay

Este documento descreve a estrutura e funcionalidade de cada componente do frontend Vue.js.

---

## Estrutura de Diretórios

```
frontend/src/
├── assets/styles/        # CSS Design System
├── components/           # Componentes Vue reutilizáveis
│   ├── layouts/          # Layouts de página
│   └── common/           # Componentes comuns
├── composables/          # Composables Vue (lógica reutilizável)
├── stores/               # Pinia stores (estado global)
├── router/               # Configuração de rotas
├── i18n/                 # Internacionalização
├── views/                # Páginas/Views
├── App.vue               # Componente raiz
└── main.js               # Entry point
```

---

## Design System (CSS)

### variables.css
Define todos os tokens de design:

| Categoria | Exemplos |
|-----------|----------|
| Cores primárias | `--color-primary-500: #005BAB` |
| Cores de accent | `--color-accent-500: #FF6600` |
| Cores semânticas | `--color-success-500`, `--color-error-500` |
| Tipografia | `--font-size-sm`, `--font-weight-bold` |
| Espaçamento | `--spacing-xs` a `--spacing-3xl` |
| Bordas | `--radius-sm`, `--radius-full` |
| Sombras | `--shadow-sm`, `--shadow-lg` |
| Transições | `--transition-fast`, `--transition-normal` |

### main.css
Estilos globais incluindo:
- Reset CSS
- Classes utilitárias
- Componentes base (botões, inputs, cards, tabelas)
- Media queries para responsividade

---

## Layouts

### DefaultLayout.vue
Layout principal para páginas autenticadas.

**Características:**
- Sidebar colapsável com navegação
- Topbar com título da página e ações
- Menu mobile responsivo
- Exibição do usuário logado
- Botão de logout

**Props:** Nenhuma (usa slots)

**Slots:**
- `default` - Conteúdo da página

**Uso:**
```vue
<!-- Automático via meta.layout no router -->
```

---

### BlankLayout.vue
Layout simples para páginas sem navegação (login, 404).

**Características:**
- Container centralizado
- Sem sidebar/topbar
- Usado para Login e NotFound

---

## Views (Páginas)

### LoginView.vue
Página de autenticação.

**Funcionalidades:**
- Formulário de login
- Validação de campos
- Exibição de erros
- Botões de demo credentials
- Redirect após login

**Dependências:** `useAuthStore`

---

### DashboardView.vue
Página inicial com estatísticas.

**Funcionalidades:**
- 4 cards de estatísticas (total replays, usuários, storage, replays hoje)
- Gráfico de replays por período (últimos 14 dias)
- Tabela de replays recentes

**Dependências:** `useStatsStore`

---

### ReplaysView.vue
Listagem de replays.

**Funcionalidades:**
- Tabela com paginação
- Busca por texto
- Filtros (data, usuário, status)
- Ações (visualizar, excluir)
- Layout responsivo (cards em mobile)

**Dependências:** `useReplaysStore`

---

### ReplayPlayerView.vue
Player de reprodução de sessão.

**Funcionalidades:**
- Container do player
- Controles (play, pause, velocidade)
- Barra de progresso
- Informações do replay
- Modo fullscreen

**Dependências:** `useReplaysStore`, route params

---

### AuditLogsView.vue
Logs de auditoria.

**Funcionalidades:**
- Tabela de logs
- Filtros (usuário, ação, data)
- Paginação
- Badges coloridos por tipo de ação

**Permissões:** admin, auditor

---

### UsersView.vue
Gerenciamento de usuários.

**Funcionalidades:**
- Tabela de usuários
- Modal de criação/edição
- Validação de formulário
- Exclusão com confirmação

**Permissões:** admin

---

### GroupsView.vue
Gerenciamento de grupos.

**Funcionalidades:**
- Grid de cards de grupos
- Modal de criação/edição
- Contagem de membros

**Permissões:** admin

---

### SettingsView.vue
Configurações do sistema.

**Funcionalidades:**
- Abas (Geral, Armazenamento, LDAP)
- Formulários de configuração
- Feedback de sucesso/erro

**Permissões:** admin

---

### NotFoundView.vue
Página 404.

**Funcionalidades:**
- Mensagem de erro estilizada
- Link para voltar ao início
- Animação de entrada

---

## Stores (Pinia)

### auth.js
Gerencia autenticação e dados do usuário.

**Estado:**
- `user` - Dados do usuário logado
- `accessToken` - Token JWT
- `refreshToken` - Token de refresh
- `isLoading` - Estado de carregamento
- `error` - Mensagem de erro

**Getters:**
- `isAuthenticated` - Se usuário está logado
- `isAdmin` - Se é administrador
- `isAuditor` - Se é auditor ou admin
- `userRole` - Role do usuário
- `displayName` - Nome de exibição

**Actions:**
- `login(username, password)` - Fazer login
- `logout()` - Fazer logout
- `fetchUser()` - Buscar dados do usuário
- `refreshAccessToken()` - Renovar token
- `init()` - Inicializar estado

---

### replays.js
Gerencia lista e detalhes de replays.

**Estado:**
- `replays` - Lista de replays
- `currentReplay` - Replay selecionado
- `pagination` - Dados de paginação
- `filters` - Filtros ativos
- `isLoading` - Estado de carregamento

**Actions:**
- `fetchReplays()` - Buscar lista
- `fetchReplay(id)` - Buscar um replay
- `deleteReplay(id)` - Excluir replay
- `setFilters(filters)` - Aplicar filtros

---

### stats.js
Gerencia estatísticas do dashboard.

**Estado:**
- `overview` - Estatísticas gerais
- `topUsers` - Top usuários
- `replaysOverTime` - Replays por período

**Actions:**
- `fetchOverview()` - Buscar estatísticas
- `fetchTopUsers(limit)` - Buscar top usuários
- `fetchReplaysOverTime(days)` - Buscar replays por período
- `fetchAll()` - Buscar tudo

---

## Composables

### useApi.js
Cliente Axios configurado.

**Funcionalidades:**
- Base URL configurável via env
- Interceptor de request (adiciona token)
- Interceptor de response (tratamento de erros)
- Auto-refresh de token em 401

**Uso:**
```javascript
import api from '@/composables/useApi'

const { data } = await api.get('/api/endpoint')
await api.post('/api/endpoint', { data })
```

---

## Router

### Configuração de Rotas

| Rota | View | Auth | Roles |
|------|------|------|-------|
| `/login` | LoginView | ❌ | - |
| `/` | DashboardView | ✅ | todos |
| `/replays` | ReplaysView | ✅ | todos |
| `/replays/:id` | ReplayPlayerView | ✅ | todos |
| `/audit` | AuditLogsView | ✅ | admin, auditor |
| `/users` | UsersView | ✅ | admin |
| `/groups` | GroupsView | ✅ | admin |
| `/settings` | SettingsView | ✅ | admin |
| `*` | NotFoundView | ❌ | - |

### Navigation Guards
- Verifica autenticação
- Verifica permissões de role
- Redireciona para login se não autenticado
- Redireciona para dashboard se não autorizado

---

## Internacionalização (i18n)

### Idiomas Suportados
- 🇧🇷 Português (Brasil) - `pt-BR` (padrão)
- 🇺🇸 English - `en`

### Uso nos Componentes
```vue
<template>
    <h1>{{ $t('nav.dashboard') }}</h1>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t, locale } = useI18n()

// Mudar idioma
locale.value = 'en'
</script>
```

### Estrutura das Traduções
```json
{
    "common": { "save": "Salvar", "cancel": "Cancelar" },
    "auth": { "login": "Entrar", "logout": "Sair" },
    "nav": { "dashboard": "Dashboard", "replays": "Replays" },
    "dashboard": { "totalReplays": "Total de Replays" },
    "replays": { "title": "Replays de Sessão" },
    "users": { "title": "Gerenciamento de Usuários" },
    "errors": { "notFound": "Página não encontrada" }
}
```
