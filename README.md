# Nachos Replay for Guaca

Sistema de Replay e Auditoria de Sessões Apache Guacamole para centralização, armazenamento e reprodução de gravações de sessões remotas.

![Vue.js](https://img.shields.io/badge/Vue.js-3.4-4FC08D?logo=vue.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [API Reference](#-api-reference)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Desenvolvimento](#-desenvolvimento)
- [Licença](#-licença)

---

## 🎯 Visão Geral

O **Nachos Replay** é um sistema web completo para:
- 🎬 Centralizar gravações de sessões do Apache Guacamole
- 🔍 Pesquisar e filtrar replays por usuário, data, IP
- ▶️ Reproduzir sessões diretamente no navegador
- 📋 Auditar todas as ações realizadas no sistema
- 👥 Gerenciar usuários, grupos e permissões
- 🔐 Integração com Active Directory (LDAP)

### Design
Interface baseada nas cores da **Caixa Econômica Federal**:
- Azul primário: `#005BAB`
- Laranja accent: `#FF6600`

---

## ✨ Funcionalidades

### Dashboard
- Cards de estatísticas (total replays, usuários, armazenamento)
- Gráfico de replays por período
- Lista de replays recentes

### Replays
- Listagem com paginação e filtros
- Busca por usuário, IP, hostname
- Filtro por data e duração
- Reprodução em player integrado

### Auditoria
- Log de todas as ações do sistema
- Filtros por usuário, ação, data
- Exportação para CSV/JSON

### Administração
- Gerenciamento de usuários (CRUD)
- Gerenciamento de grupos
- Configurações do sistema
- Integração LDAP/AD

---

## 🏗 Arquitetura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Browser   │────▶│   Nginx     │────▶│  Frontend   │
│             │     │   (proxy)   │     │   Vue.js    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Backend   │────▶│ PostgreSQL  │
                    │   FastAPI   │     │             │
                    └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Redis     │
                    │  (cache)    │
                    └─────────────┘
```

### Stack Tecnológico

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| Frontend | Vue.js 3 + Vite | 3.4 / 5.0 |
| Estado | Pinia | 2.1 |
| Roteamento | Vue Router | 4.2 |
| i18n | Vue I18n | 9.9 |
| Backend | FastAPI | 0.109 |
| ORM | SQLAlchemy | 2.0 |
| Banco | PostgreSQL | 16 |
| Cache | Redis | 7 |
| Container | Docker | 24+ |

---

## 🚀 Instalação

### Requisitos
- Docker & Docker Compose v2+
- 4GB RAM mínimo
- 20GB espaço em disco

### Quick Start

```bash
# Clone o repositório
git clone <repository-url>
cd nachos-replay-for-guaca

# Configure variáveis de ambiente
cp .env.example .env
# Edite o .env conforme necessário

# Inicie os containers
docker compose up -d

# Aguarde todos os serviços iniciarem
docker compose logs -f

# Acesse
# Frontend: http://localhost
# API Docs: http://localhost:8000/docs
```

### Usuários de Teste

| Usuário | Senha | Perfil |
|---------|-------|--------|
| admin | admin123 | Administrador |
| viewer | viewer123 | Visualizador |
| auditor | auditor123 | Auditor |

---

## ⚙️ Configuração

### Variáveis de Ambiente

```env
# Aplicação
SECRET_KEY=sua-chave-secreta-aqui
JWT_SECRET_KEY=sua-chave-jwt-aqui

# Banco de Dados
DATABASE_URL=postgresql://nachos:nachos_secret@db:5432/nachos_replay

# LDAP (opcional)
LDAP_ENABLED=false
LDAP_SERVER=ldap://servidor:389
LDAP_BASE_DN=dc=empresa,dc=com
LDAP_BIND_DN=cn=admin,dc=empresa,dc=com
LDAP_BIND_PASSWORD=senha

# Guacamole
GUACAMOLE_RECORDINGS_PATH=/guacamole/recordings
REPLAY_STORAGE_PATH=/app/replays

# Storage
RETENTION_DAYS=365
MAX_STORAGE_GB=500
```

---

## 📡 API Reference

### Autenticação

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/auth/login` | POST | Login com username/password |
| `/api/auth/me` | GET | Dados do usuário atual |
| `/api/auth/refresh` | POST | Renovar token JWT |
| `/api/auth/logout` | POST | Logout (invalida token) |

### Replays

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/replays` | GET | Listar replays (paginado) |
| `/api/replays/{id}` | GET | Detalhes de um replay |
| `/api/replays/{id}/stream` | GET | Stream do replay |
| `/api/replays/{id}` | DELETE | Excluir replay |

### Estatísticas

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/stats/overview` | GET | Estatísticas gerais |
| `/api/stats/top-users` | GET | Top usuários por replays |
| `/api/stats/replays-over-time` | GET | Replays por período |

### Auditoria

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/audit` | GET | Listar logs de auditoria |
| `/api/audit/export` | POST | Exportar logs |

### Usuários (Admin)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/users` | GET | Listar usuários |
| `/api/users` | POST | Criar usuário |
| `/api/users/{id}` | PUT | Atualizar usuário |
| `/api/users/{id}` | DELETE | Excluir usuário |

### Grupos (Admin)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/groups` | GET | Listar grupos |
| `/api/groups` | POST | Criar grupo |
| `/api/groups/{id}` | PUT | Atualizar grupo |
| `/api/groups/{id}` | DELETE | Excluir grupo |

---

## 📁 Estrutura do Projeto

```
nachos-replay-for-guaca/
├── backend/
│   ├── app/
│   │   ├── api/                 # Endpoints FastAPI
│   │   │   ├── auth.py          # Autenticação JWT
│   │   │   ├── replays.py       # CRUD replays
│   │   │   ├── users.py         # CRUD usuários
│   │   │   ├── audit.py         # Logs de auditoria
│   │   │   ├── stats.py         # Estatísticas
│   │   │   └── deps.py          # Dependencies injection
│   │   ├── services/            # Lógica de negócio
│   │   │   ├── audit_service.py
│   │   │   ├── ldap_service.py
│   │   │   └── replay_service.py
│   │   ├── models.py            # Modelos SQLAlchemy
│   │   ├── schemas.py           # Schemas Pydantic
│   │   ├── config.py            # Configurações
│   │   ├── database.py          # Conexão DB
│   │   └── main.py              # App FastAPI
│   ├── init.sql                 # Schema inicial
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── assets/styles/       # CSS (Design System)
│   │   │   ├── variables.css    # Tokens de design
│   │   │   └── main.css         # Estilos globais
│   │   ├── components/
│   │   │   ├── layouts/         # DefaultLayout, BlankLayout
│   │   │   └── common/          # Componentes reutilizáveis
│   │   ├── composables/
│   │   │   └── useApi.js        # Cliente Axios
│   │   ├── stores/              # Pinia stores
│   │   │   ├── auth.js          # Autenticação
│   │   │   ├── replays.js       # Replays
│   │   │   └── stats.js         # Estatísticas
│   │   ├── router/
│   │   │   └── index.js         # Rotas + guards
│   │   ├── i18n/                # Internacionalização
│   │   │   ├── locales/         # pt-BR, en
│   │   │   └── index.js
│   │   ├── views/               # Páginas
│   │   │   ├── LoginView.vue
│   │   │   ├── DashboardView.vue
│   │   │   ├── ReplaysView.vue
│   │   │   ├── ReplayPlayerView.vue
│   │   │   ├── AuditLogsView.vue
│   │   │   ├── UsersView.vue
│   │   │   ├── GroupsView.vue
│   │   │   ├── SettingsView.vue
│   │   │   └── NotFoundView.vue
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔧 Desenvolvimento

### Backend (FastAPI)

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Rodar servidor de desenvolvimento
uvicorn app.main:app --reload --port 8000
```

### Frontend (Vue.js)

```bash
cd frontend

# Instalar dependências
npm install

# Rodar em modo desenvolvimento
npm run dev

# Build para produção
npm run build
```

### Rotas do Frontend

| Rota | Componente | Autenticação | Perfis |
|------|------------|--------------|--------|
| `/login` | LoginView | Não | - |
| `/` | DashboardView | Sim | Todos |
| `/replays` | ReplaysView | Sim | Todos |
| `/replays/:id` | ReplayPlayerView | Sim | Todos |
| `/audit` | AuditLogsView | Sim | admin, auditor |
| `/users` | UsersView | Sim | admin |
| `/groups` | GroupsView | Sim | admin |
| `/settings` | SettingsView | Sim | admin |

---

## 📦 Scripts Úteis

```bash
# Ver logs de todos os serviços
docker compose logs -f

# Ver logs de um serviço específico
docker compose logs -f backend

# Reiniciar apenas o backend
docker compose restart backend

# Reconstruir e reiniciar
docker compose up -d --build

# Acessar shell do container backend
docker compose exec backend bash

# Acessar PostgreSQL
docker compose exec db psql -U nachos -d nachos_replay

# Limpar tudo e reiniciar do zero
docker compose down -v
docker compose up -d
```

---

## 📄 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes.

---

## 🤝 Contribuição

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas alterações (`git commit -m 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request
