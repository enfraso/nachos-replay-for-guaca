# API Reference - Nachos Replay

## Visão Geral

A API REST do Nachos Replay segue os padrões RESTful e utiliza JSON para comunicação. Todas as rotas que requerem autenticação esperam o header `Authorization: Bearer <token>`.

**Base URL:** `http://localhost/api` (ou `/api` relativo ao frontend)

---

## Autenticação

### POST /auth/login
Autentica um usuário e retorna tokens JWT.

**Request:**
```json
{
    "username": "admin",
    "password": "admin123"
}
```

**Response 200:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

**Response 401:**
```json
{
    "detail": "Invalid username or password"
}
```

---

### GET /auth/me
Retorna informações do usuário autenticado.

**Headers:** `Authorization: Bearer <access_token>`

**Response 200:**
```json
{
    "id": "bb849887-...",
    "username": "admin",
    "email": "admin@example.com",
    "display_name": "Administrator",
    "role": "admin",
    "groups": ["admins", "managers"]
}
```

---

### POST /auth/refresh
Renova o access token usando o refresh token.

**Request:**
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 200:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

---

### POST /auth/logout
Invalida o token atual.

**Headers:** `Authorization: Bearer <access_token>`

**Response 200:**
```json
{
    "message": "Logged out successfully"
}
```

---

## Replays

### GET /replays
Lista replays com paginação e filtros.

**Query Parameters:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| page | int | Página (default: 1) |
| page_size | int | Itens por página (default: 20, max: 100) |
| query | string | Busca em username, session_name, client_ip |
| username | string | Filtrar por usuário |
| date_from | datetime | Data inicial |
| date_to | datetime | Data final |
| status | string | active, archived, deleted |
| sort_by | string | Campo para ordenação |
| sort_order | string | asc ou desc |

**Response 200:**
```json
{
    "items": [
        {
            "id": "uuid",
            "filename": "session_20240101_120000.guac",
            "session_name": "SSH Session",
            "owner_username": "john.doe",
            "client_ip": "192.168.1.100",
            "file_size": 1048576,
            "duration_seconds": 3600,
            "session_start": "2024-01-01T12:00:00Z",
            "session_end": "2024-01-01T13:00:00Z",
            "imported_at": "2024-01-02T08:00:00Z",
            "status": "active"
        }
    ],
    "total": 150,
    "page": 1,
    "page_size": 20,
    "total_pages": 8
}
```

---

### GET /replays/{id}
Retorna detalhes de um replay específico.

**Response 200:**
```json
{
    "id": "uuid",
    "filename": "session_20240101_120000.guac",
    "original_path": "/guacamole/recordings/...",
    "stored_path": "/app/replays/...",
    "session_name": "SSH Session",
    "owner_username": "john.doe",
    "client_ip": "192.168.1.100",
    "file_size": 1048576,
    "duration_seconds": 3600,
    "session_start": "2024-01-01T12:00:00Z",
    "session_end": "2024-01-01T13:00:00Z",
    "imported_at": "2024-01-02T08:00:00Z",
    "status": "active",
    "metadata_json": {
        "protocol": "ssh",
        "hostname": "server01",
        "port": 22
    },
    "created_at": "2024-01-02T08:00:00Z",
    "updated_at": "2024-01-02T08:00:00Z"
}
```

---

### GET /replays/{id}/stream
Retorna o stream do replay para reprodução.

**Response:** Binary stream com headers apropriados para o player.

---

### DELETE /replays/{id}
Exclui um replay (soft delete, marca como "deleted").

**Permissões:** admin

**Response 200:**
```json
{
    "message": "Replay deleted successfully"
}
```

---

## Estatísticas

### GET /stats/overview
Retorna estatísticas gerais do dashboard.

**Response 200:**
```json
{
    "total_replays": 1500,
    "total_users": 45,
    "total_storage_bytes": 10737418240,
    "replays_today": 23,
    "replays_this_week": 156,
    "active_sessions": 5
}
```

---

### GET /stats/top-users
Retorna top usuários por quantidade de replays.

**Query Parameters:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| limit | int | Quantidade de usuários (default: 5) |

**Response 200:**
```json
[
    {
        "username": "john.doe",
        "display_name": "John Doe",
        "replay_count": 234,
        "total_duration_seconds": 86400
    },
    {
        "username": "jane.smith",
        "display_name": "Jane Smith",
        "replay_count": 189,
        "total_duration_seconds": 72000
    }
]
```

---

### GET /stats/replays-over-time
Retorna quantidade de replays por dia.

**Query Parameters:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| days | int | Quantidade de dias (default: 14) |

**Response 200:**
```json
[
    {"date": "2024-01-01", "count": 45, "total_duration_seconds": 16200},
    {"date": "2024-01-02", "count": 52, "total_duration_seconds": 18720}
]
```

---

## Auditoria

### GET /audit
Lista logs de auditoria.

**Permissões:** admin, auditor

**Query Parameters:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| page | int | Página |
| page_size | int | Itens por página |
| user_id | uuid | Filtrar por usuário |
| action | string | Filtrar por ação |
| date_from | datetime | Data inicial |
| date_to | datetime | Data final |

**Response 200:**
```json
{
    "items": [
        {
            "id": "uuid",
            "user_id": "uuid",
            "username": "admin",
            "action": "login",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "details": {"success": true},
            "created_at": "2024-01-01T12:00:00Z"
        }
    ],
    "total": 500,
    "page": 1,
    "page_size": 20,
    "total_pages": 25
}
```

---

### POST /audit/export
Exporta logs de auditoria.

**Permissões:** admin

**Request:**
```json
{
    "format": "csv",
    "filters": {
        "date_from": "2024-01-01T00:00:00Z",
        "date_to": "2024-01-31T23:59:59Z"
    }
}
```

**Response:** Arquivo CSV ou JSON para download.

---

## Usuários

### GET /users
Lista todos os usuários.

**Permissões:** admin

**Response 200:**
```json
{
    "items": [
        {
            "id": "uuid",
            "username": "john.doe",
            "email": "john@example.com",
            "display_name": "John Doe",
            "role": "viewer",
            "is_active": true,
            "is_ldap_user": false,
            "last_login": "2024-01-01T12:00:00Z",
            "created_at": "2023-01-01T00:00:00Z",
            "groups": []
        }
    ],
    "total": 45,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
}
```

---

### POST /users
Cria um novo usuário.

**Permissões:** admin

**Request:**
```json
{
    "username": "new.user",
    "email": "new@example.com",
    "display_name": "New User",
    "password": "securepassword123",
    "role": "viewer",
    "is_active": true
}
```

**Response 201:**
```json
{
    "id": "uuid",
    "username": "new.user",
    "email": "new@example.com",
    "display_name": "New User",
    "role": "viewer",
    "is_active": true,
    "is_ldap_user": false,
    "created_at": "2024-01-01T12:00:00Z"
}
```

---

### PUT /users/{id}
Atualiza um usuário existente.

**Permissões:** admin

**Request:**
```json
{
    "email": "updated@example.com",
    "display_name": "Updated Name",
    "role": "auditor",
    "is_active": true
}
```

**Response 200:** Usuário atualizado.

---

### DELETE /users/{id}
Exclui um usuário.

**Permissões:** admin

**Response 200:**
```json
{
    "message": "User deleted successfully"
}
```

---

## Grupos

### GET /groups
Lista todos os grupos.

**Permissões:** admin

**Response 200:**
```json
{
    "items": [
        {
            "id": "uuid",
            "name": "Administrators",
            "description": "System administrators",
            "ldap_dn": null,
            "user_count": 5,
            "created_at": "2023-01-01T00:00:00Z"
        }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
}
```

---

### POST /groups
Cria um novo grupo.

**Permissões:** admin

**Request:**
```json
{
    "name": "New Group",
    "description": "Description of the group"
}
```

**Response 201:** Grupo criado.

---

### PUT /groups/{id}
Atualiza um grupo.

**Permissões:** admin

---

### DELETE /groups/{id}
Exclui um grupo.

**Permissões:** admin

---

## Configurações

### GET /settings
Retorna configurações do sistema.

**Permissões:** admin

**Response 200:**
```json
{
    "items": [
        {
            "key": "retention_days",
            "value": "365",
            "description": "Days to retain replays"
        },
        {
            "key": "ldap_enabled",
            "value": "false",
            "description": "Enable LDAP authentication"
        }
    ]
}
```

---

### PUT /settings/{key}
Atualiza uma configuração.

**Permissões:** admin

**Request:**
```json
{
    "value": "180"
}
```

---

## Health Check

### GET /health
Verifica status da aplicação.

**Response 200:**
```json
{
    "status": "healthy",
    "version": "2.0.0",
    "database": "connected",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 400 | Bad Request - Dados inválidos |
| 401 | Unauthorized - Token ausente ou inválido |
| 403 | Forbidden - Sem permissão |
| 404 | Not Found - Recurso não encontrado |
| 422 | Unprocessable Entity - Validação falhou |
| 500 | Internal Server Error - Erro no servidor |

**Formato de Erro:**
```json
{
    "detail": "Mensagem de erro",
    "type": "ErrorType"
}
```
