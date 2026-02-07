# Arquitetura do Sistema - Nachos Replay

## Visão Geral

O Nachos Replay é uma aplicação web moderna implementada seguindo uma arquitetura de microsserviços containerizada com Docker.

---

## Diagrama de Componentes

```
┌──────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                 │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                      Vue.js 3 + Vite                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │  │
│  │  │   Pinia     │  │ Vue Router  │  │   Vue I18n  │             │  │
│  │  │  (Estado)   │  │  (Rotas)    │  │   (i18n)    │             │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │  │
│  │                                                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────┐│  │
│  │  │                         VIEWS                                ││  │
│  │  │  Login │ Dashboard │ Replays │ Player │ Audit │ Admin       ││  │
│  │  └─────────────────────────────────────────────────────────────┘│  │
│  └────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │ HTTP/REST (JSON)
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          NGINX (Reverse Proxy)                        │
│   - Serve arquivos estáticos do frontend                             │
│   - Proxy /api/* para backend:8000                                   │
│   - Compressão gzip                                                  │
│   - Headers de segurança                                             │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                  │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                      FastAPI (Python)                           │  │
│  │                                                                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │  │
│  │  │    API      │  │  Services   │  │   Models    │             │  │
│  │  │  Endpoints  │──│  (Negócio)  │──│ (SQLAlchemy)│             │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │  │
│  │         │                                   │                    │  │
│  │  ┌──────┴──────┐                    ┌──────┴──────┐             │  │
│  │  │   Pydantic  │                    │   Alembic   │             │  │
│  │  │  (Schemas)  │                    │ (Migrations)│             │  │
│  │  └─────────────┘                    └─────────────┘             │  │
│  └────────────────────────────────────────────────────────────────┘  │
└────────────────────┬─────────────────────────────┬───────────────────┘
                     │                             │
                     ▼                             ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│        PostgreSQL 16        │   │          Redis 7            │
│  - Dados de usuários        │   │  - Cache de sessões         │
│  - Metadados de replays     │   │  - Queue de tarefas         │
│  - Logs de auditoria        │   │  - Rate limiting            │
│  - Configurações            │   │                             │
└─────────────────────────────┘   └─────────────────────────────┘
```

---

## Fluxos Principais

### 1. Fluxo de Autenticação

```
┌────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐
│ Cliente │───▶│ /login  │───▶│ Backend │───▶│ Database │
└────────┘    └─────────┘    └────┬────┘    └──────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
              ▼                                       ▼
       ┌─────────────┐                    ┌─────────────────┐
       │ LDAP Server │  (se habilitado)   │ Tabela "users"  │
       │ (opcional)  │                    │ (hash bcrypt)   │
       └─────────────┘                    └─────────────────┘
              │                                       │
              └───────────────────┬───────────────────┘
                                  │
                                  ▼
                          ┌─────────────┐
                          │ JWT Tokens  │
                          │ Access/     │
                          │ Refresh     │
                          └─────────────┘
```

### 2. Fluxo de Reprodução de Replay

```
┌────────┐    ┌───────────────┐    ┌─────────┐    ┌──────────────┐
│ Cliente │───▶│ /replays/:id  │───▶│ Backend │───▶│ Arquivo .m4v │
└────────┘    └───────────────┘    └────┬────┘    │ ou .guac     │
                                        │         └──────────────┘
                                        │
                                        ▼
                                 ┌─────────────┐
                                 │ Streaming   │
                                 │ Response    │
                                 │ (chunks)    │
                                 └─────────────┘
```

---

## Modelos de Dados

### User
```python
class User:
    id: UUID (PK)
    username: str (unique)
    email: str (nullable)
    display_name: str (nullable)
    password_hash: str (nullable, bcrypt)
    ldap_dn: str (nullable)
    role: UserRole (admin|viewer|auditor)
    is_active: bool
    is_ldap_user: bool
    last_login: datetime
    created_at: datetime
    updated_at: datetime
```

### Replay
```python
class Replay:
    id: UUID (PK)
    filename: str (unique)
    original_path: str
    stored_path: str
    session_name: str
    owner_id: UUID (FK -> users)
    owner_username: str
    client_ip: str
    file_size: int (bytes)
    duration_seconds: int
    session_start: datetime
    session_end: datetime
    imported_at: datetime
    status: ReplayStatus (active|archived|deleted)
    metadata_json: JSONB
```

### AuditLog
```python
class AuditLog:
    id: UUID (PK)
    user_id: UUID (FK -> users)
    username: str
    replay_id: UUID (FK -> replays)
    action: AuditAction (view|download|search|login|etc)
    ip_address: str
    user_agent: str
    details: JSONB
    created_at: datetime
```

### Group
```python
class Group:
    id: UUID (PK)
    name: str (unique)
    description: str
    ldap_dn: str (nullable)
    created_at: datetime
    updated_at: datetime
```

---

## Segurança

### Autenticação
- **JWT (JSON Web Tokens)** com access e refresh tokens
- Access token expira em 30 minutos
- Refresh token expira em 7 dias
- Blacklist de tokens para logout

### Autorização
- **RBAC (Role-Based Access Control)**
- Três perfis: `admin`, `auditor`, `viewer`
- Guards de rota no frontend
- Decorators de permissão no backend

### Senhas
- Hash com **bcrypt** (12 rounds)
- Não armazenamento de senhas em texto plano

### Headers de Segurança (Nginx)
```
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

---

## Escalabilidade

### Horizontal
- Backend stateless (JWT)
- Múltiplas réplicas via Docker Swarm ou Kubernetes
- Load balancer na frente do Nginx

### Vertical
- Pool de conexões PostgreSQL (5-15)
- Cache Redis para sessões
- Compressão gzip para respostas

### Storage
- Volumes Docker para persistência
- Suporte a S3/MinIO para arquivos grandes (futuro)

---

## Monitoramento

### Health Checks
- `/health` - Status geral da aplicação
- Checks de PostgreSQL e Redis

### Logs
- Formato JSON estruturado
- Níveis: DEBUG, INFO, WARNING, ERROR
- Integração futura com ELK Stack

### Métricas (futuro)
- Prometheus + Grafana
- Latência de requests
- Uso de memória/CPU
