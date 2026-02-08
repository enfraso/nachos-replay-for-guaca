# Nachos Replay - Documentação Técnica Completa

Este documento contém a documentação técnica detalhada de todo o sistema Nachos Replay, incluindo explicações linha a linha de todos os arquivos de código.

---

## Sumário

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Arquitetura](#2-arquitetura)
3. [Configuração Docker](#3-configuração-docker)
4. [Backend (FastAPI)](#4-backend-fastapi)
5. [Frontend (Vue.js 3)](#5-frontend-vuejs-3)
6. [Banco de Dados](#6-banco-de-dados)
7. [API Reference](#7-api-reference)

---

# 1. Visão Geral do Sistema

O **Nachos Replay** é um sistema web completo para centralização, armazenamento e reprodução de gravações de sessões Apache Guacamole.

## Funcionalidades Principais

- 🎬 Armazenamento centralizado de replays do Guacamole
- 🔍 Busca e filtros avançados (por usuário, data, IP)
- ▶️ Reprodução de sessões no navegador
- 📋 Logs de auditoria completos
- 👥 Gerenciamento de usuários e grupos
- 🔐 Autenticação JWT + LDAP/AD

## Stack Tecnológico

| Componente | Tecnologia | Versão |
|------------|------------|--------|
| Frontend | Vue.js + Vite | 3.4 / 5.0 |
| Estado | Pinia | 2.1 |
| Backend | FastAPI | 0.109 |
| ORM | SQLAlchemy | 2.0 |
| Banco | PostgreSQL | 16 |
| Cache | Redis | 7 |

---

# 2. Arquitetura

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
                    └─────────────┘
```

---

# 3. Configuração Docker

## docker-compose.yml

Este arquivo orquestra todos os serviços do sistema.

```yaml
version: '3.8'

services:
  # ===========================================
  # Backend API (FastAPI)
  # ===========================================
  backend:
    build:
      context: ./backend        # Diretório com Dockerfile do backend
      dockerfile: Dockerfile
    container_name: nachos-backend
    restart: unless-stopped
    ports:
      - "8000:8000"             # Expõe API na porta 8000
    environment:
      # URL de conexão com PostgreSQL
      - DATABASE_URL=postgresql://nachos:nachos_secret@db:5432/nachos_replay
      # Chaves secretas (usar variáveis em produção)
      - SECRET_KEY=${SECRET_KEY:-dev-secret-key-change-me}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-dev-jwt-secret-change-me}
      - LDAP_ENABLED=${LDAP_ENABLED:-false}
      # Caminhos de armazenamento
      - GUACAMOLE_RECORDINGS_PATH=/guacamole/recordings
      - REPLAY_STORAGE_PATH=/app/replays
    volumes:
      - replay_storage:/app/replays              # Volume para replays
      - guacamole_recordings:/guacamole/recordings:ro  # Gravações Guacamole (read-only)
    depends_on:
      db:
        condition: service_healthy   # Aguarda banco estar healthy
      redis:
        condition: service_started
    networks:
      - nachos-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ===========================================
  # Frontend (Vue.js + Nginx)
  # ===========================================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: nachos-frontend
    restart: unless-stopped
    ports:
      - "80:80"      # HTTP
      - "443:443"    # HTTPS
    depends_on:
      - backend
    networks:
      - nachos-network

  # ===========================================
  # Database (PostgreSQL)
  # ===========================================
  db:
    image: postgres:16-alpine     # Imagem leve do PostgreSQL 16
    container_name: nachos-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: nachos       # Usuário do banco
      POSTGRES_PASSWORD: nachos_secret
      POSTGRES_DB: nachos_replay  # Nome do banco
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Persistência dos dados
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql:ro  # Schema inicial
    networks:
      - nachos-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nachos -d nachos_replay"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ===========================================
  # Redis (Session/Cache)
  # ===========================================
  redis:
    image: redis:7-alpine
    container_name: nachos-redis
    restart: unless-stopped
    command: redis-server --appendonly yes  # Persistência AOF
    volumes:
      - redis_data:/data
    networks:
      - nachos-network

networks:
  nachos-network:
    driver: bridge

volumes:
  postgres_data:           # Dados do PostgreSQL
  redis_data:              # Dados do Redis
  replay_storage:          # Replays armazenados
  guacamole_recordings:    # Gravações do Guacamole (volume externo)
    external: true
    name: guacamole_recordings
```

---

# 4. Backend (FastAPI)

## 4.1 Estrutura de Diretórios

```
backend/
├── app/
│   ├── __init__.py      # Versão da aplicação
│   ├── main.py          # Entry point FastAPI
│   ├── config.py        # Configurações (Pydantic Settings)
│   ├── database.py      # Conexão SQLAlchemy
│   ├── models.py        # Modelos ORM
│   ├── schemas.py       # Schemas Pydantic
│   ├── api/             # Endpoints
│   │   ├── __init__.py  # Router principal
│   │   ├── auth.py      # Autenticação
│   │   ├── users.py     # CRUD usuários
│   │   ├── replays.py   # CRUD replays
│   │   ├── audit.py     # Logs de auditoria
│   │   ├── stats.py     # Estatísticas
│   │   └── deps.py      # Dependencies
│   ├── services/        # Lógica de negócio
│   │   ├── audit_service.py
│   │   ├── ldap_service.py
│   │   └── replay_service.py
│   └── utils/           # Utilitários
│       ├── security.py  # JWT, hashing
│       └── helpers.py
├── init.sql             # Schema SQL inicial
├── Dockerfile
└── requirements.txt
```

---

## 4.2 main.py - Entry Point

Arquivo principal que inicializa a aplicação FastAPI.

```python
"""
Nachos Replay for Guaca - FastAPI Main Application
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import settings
from app.database import init_db
from app.api import api_router
from app.tasks.scheduler import start_scheduler, stop_scheduler

# Configura logging com nível definido nas settings
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerenciador de ciclo de vida da aplicação.
    Executado no startup e shutdown.
    """
    logger.info(f"Starting {settings.app_name} v{__version__}")
    
    # Inicializa conexão com banco de dados
    await init_db()
    logger.info("Database initialized")
    
    # Inicia scheduler para tarefas em background
    start_scheduler()
    logger.info("Scheduler started")
    
    yield  # A aplicação roda aqui
    
    # Shutdown
    stop_scheduler()
    logger.info("Scheduler stopped")
    logger.info("Application shutdown complete")


# Cria instância FastAPI
app = FastAPI(
    title=settings.app_name,
    description="Sistema de Replay e Auditoria de Sessões Apache Guacamole",
    version=__version__,
    docs_url="/docs" if settings.debug else None,   # Swagger só em debug
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Middleware CORS para permitir requests do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Origins permitidas
    allow_credentials=True,                     # Permite cookies
    allow_methods=["*"],                        # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],                        # Todos os headers
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware que loga todas as requisições.
    """
    start_time = datetime.now(timezone.utc)
    
    response = await call_next(request)
    
    process_time = (datetime.now(timezone.utc) - start_time).total_seconds()
    
    logger.debug(
        f"{request.method} {request.url.path} "
        f"- {response.status_code} - {process_time:.3f}s"
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handler global para exceções não tratadas.
    Retorna erro 500 com tipo da exceção.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )


# Inclui todas as rotas da API
app.include_router(api_router)


@app.get("/health")
async def health_check():
    """
    Endpoint de health check para orquestradores de container.
    """
    from app.schemas import HealthCheck
    
    return HealthCheck(
        status="healthy",
        version=__version__,
        database="connected",
        timestamp=datetime.now(timezone.utc)
    )


@app.get("/")
async def root():
    """Endpoint raiz."""
    return {
        "name": settings.app_name,
        "version": __version__,
        "docs": "/docs" if settings.debug else None
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug  # Auto-reload em debug
    )
```

---

## 4.3 config.py - Configurações

Configurações da aplicação usando Pydantic Settings.

```python
"""
Nachos Replay for Guaca - Configuration
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Configurações carregadas de variáveis de ambiente.
    Valores default são usados se não definidos.
    """
    
    # Aplicação
    app_name: str = "Nachos Replay for Guaca"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "dev-secret-key-change-in-production"
    
    # Banco de Dados
    database_url: str = "postgresql://nachos:nachos_secret@localhost:5432/nachos_replay"
    db_pool_size: int = 5         # Conexões no pool
    db_max_overflow: int = 10     # Conexões extras permitidas
    
    # JWT
    jwt_secret_key: str = "dev-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30    # 30 minutos
    jwt_refresh_token_expire_days: int = 7       # 7 dias
    
    # LDAP / Active Directory
    ldap_enabled: bool = False
    ldap_server: str = ""
    ldap_base_dn: str = ""
    ldap_bind_dn: str = ""
    ldap_bind_password: str = ""
    ldap_user_search_base: str = ""
    ldap_group_search_base: str = ""
    ldap_user_attr_username: str = "sAMAccountName"  # AD
    ldap_user_attr_email: str = "mail"
    ldap_user_attr_display_name: str = "displayName"
    
    # Guacamole
    guacamole_recordings_path: str = "/guacamole/recordings"
    replay_storage_path: str = "/app/replays"
    replay_import_delay_hours: int = 24  # Delay para importar sessões
    
    # Storage
    retention_days: int = 365      # Dias para manter replays
    max_storage_gb: int = 500      # Limite de armazenamento
    archive_enabled: bool = True   # Habilita arquivamento
    archive_compression: str = "gzip"
    
    # Segurança
    cors_origins: str = "http://localhost,http://localhost:5173"
    allowed_hosts: str = "localhost,127.0.0.1"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Converte string de origins para lista."""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Converte string de hosts para lista."""
        return [host.strip() for host in self.allowed_hosts.split(",")]
    
    class Config:
        env_file = ".env"           # Arquivo com variáveis
        case_sensitive = False      # Ignora case nas variáveis


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância cacheada de Settings."""
    return Settings()


# Instância global
settings = get_settings()
```

---

## 4.4 models.py - Modelos SQLAlchemy

Modelos ORM que representam as tabelas do banco.

```python
"""
Nachos Replay for Guaca - SQLAlchemy Models
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
import enum

from sqlalchemy import (
    String, Text, Boolean, Integer, BigInteger, DateTime,
    ForeignKey, Index, Enum, TIMESTAMP
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Classe base para todos os modelos."""
    pass


# ============================================
# Enums
# ============================================

class UserRole(str, enum.Enum):
    """Roles disponíveis para usuários."""
    ADMIN = "admin"       # Administrador total
    VIEWER = "viewer"     # Apenas visualização
    AUDITOR = "auditor"   # Visualização + auditoria


class ReplayStatus(str, enum.Enum):
    """Status de um replay."""
    ACTIVE = "active"     # Disponível para visualização
    ARCHIVED = "archived" # Arquivado
    DELETED = "deleted"   # Marcado para exclusão


class AuditAction(str, enum.Enum):
    """Ações registradas na auditoria."""
    VIEW = "view"
    DOWNLOAD = "download"
    SEARCH = "search"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


# ============================================
# User Model
# ============================================

class User(Base):
    """Modelo de usuário do sistema."""
    __tablename__ = "users"
    
    # Campos principais
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    ldap_dn: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Role com enum do PostgreSQL (fix: values_callable para lowercase)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole, 
            name="user_role", 
            create_type=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=UserRole.VIEWER
    )
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_ldap_user: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    groups: Mapped[List["Group"]] = relationship(
        "Group",
        secondary="user_groups",
        back_populates="users"
    )
    replays: Mapped[List["Replay"]] = relationship(
        "Replay",
        back_populates="owner"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user"
    )


# ============================================
# Replay Model
# ============================================

class Replay(Base):
    """Modelo de replay de sessão Guacamole."""
    __tablename__ = "replays"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    filename: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    original_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    session_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    owner_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    owner_username: Mapped[Optional[str]] = mapped_column(String(100))
    client_ip: Mapped[Optional[str]] = mapped_column(String(45))
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    session_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    session_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Status com enum
    status: Mapped[ReplayStatus] = mapped_column(
        Enum(
            ReplayStatus, 
            name="replay_status", 
            create_type=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        default=ReplayStatus.ACTIVE
    )
    
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    owner: Mapped[Optional["User"]] = relationship("User", back_populates="replays")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="replay")
    
    # Índices para otimização de queries
    __table_args__ = (
        Index("idx_replays_owner_username", "owner_username"),
        Index("idx_replays_status", "status"),
        Index("idx_replays_session_start", "session_start"),
    )


# ============================================
# AuditLog Model
# ============================================

class AuditLog(Base):
    """Log de auditoria (imutável)."""
    __tablename__ = "audit_logs"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL")
    )
    username: Mapped[Optional[str]] = mapped_column(String(100))
    replay_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("replays.id", ondelete="SET NULL")
    )
    
    # Ação registrada
    action: Mapped[AuditAction] = mapped_column(
        Enum(
            AuditAction, 
            name="audit_action", 
            create_type=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")
    replay: Mapped[Optional["Replay"]] = relationship("Replay", back_populates="audit_logs")
```

---

# 5. Frontend (Vue.js 3)

## 5.1 Estrutura de Diretórios

```
frontend/
├── src/
│   ├── assets/styles/       # CSS Design System
│   │   ├── variables.css    # Tokens (cores, fontes, espaçamentos)
│   │   └── main.css         # Estilos globais
│   ├── components/
│   │   ├── layouts/         # DefaultLayout, BlankLayout
│   │   └── common/          # Componentes reutilizáveis
│   ├── composables/
│   │   └── useApi.js        # Cliente Axios com interceptors
│   ├── stores/              # Pinia (estado global)
│   │   ├── index.js         # Cria instância Pinia
│   │   ├── auth.js          # Autenticação
│   │   ├── replays.js       # Gerenciamento de replays
│   │   └── stats.js         # Estatísticas
│   ├── router/
│   │   └── index.js         # Rotas Vue Router
│   ├── i18n/                # Internacionalização
│   │   ├── index.js         # Configuração vue-i18n
│   │   └── locales/         # pt-BR.json, en.json
│   ├── views/               # Páginas
│   │   ├── LoginView.vue
│   │   ├── DashboardView.vue
│   │   ├── ReplaysView.vue
│   │   ├── ReplayPlayerView.vue
│   │   ├── AuditLogsView.vue
│   │   ├── UsersView.vue
│   │   ├── GroupsView.vue
│   │   ├── SettingsView.vue
│   │   └── NotFoundView.vue
│   ├── App.vue              # Componente raiz
│   └── main.js              # Entry point
├── package.json
├── vite.config.js
└── Dockerfile
```

---

## 5.2 package.json

Dependências e scripts do projeto.

```json
{
    "name": "nachos-replay-frontend",
    "private": true,
    "version": "2.0.0",
    "type": "module",
    "scripts": {
        "dev": "vite",                    // Servidor de desenvolvimento
        "build": "vite build",            // Build para produção
        "preview": "vite preview",        // Preview do build
        "lint": "eslint . --ext .vue,.js --fix"
    },
    "dependencies": {
        "vue": "^3.4.15",                 // Framework Vue.js 3
        "vue-router": "^4.2.5",           // Roteamento SPA
        "pinia": "^2.1.7",                // Estado global reativo
        "axios": "^1.6.7",                // Cliente HTTP
        "vue-i18n": "^9.9.0",             // Internacionalização
        "chart.js": "^4.4.1",             // Gráficos
        "vue-chartjs": "^5.3.0",          // Wrapper Vue para Chart.js
        "@vueuse/core": "^10.7.2",        // Composables utilitários
        "date-fns": "^3.3.1"              // Manipulação de datas
    },
    "devDependencies": {
        "@vitejs/plugin-vue": "^5.0.3",   // Plugin Vue para Vite
        "vite": "^5.0.12"                 // Bundler
    }
}
```

---

## 5.3 vite.config.js

Configuração do Vite para build e desenvolvimento.

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
    plugins: [vue()],
    
    resolve: {
        alias: {
            // @ aponta para src/ (ex: import x from '@/components/X.vue')
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    
    server: {
        port: 5173,  // Porta do dev server
        proxy: {
            // Proxy /api/* para o backend
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true
            }
        }
    },
    
    build: {
        outDir: 'dist',       // Diretório de output
        sourcemap: false,     // Sem sourcemaps em produção
        minify: 'terser',     // Minificação
        rollupOptions: {
            output: {
                // Code splitting por vendor
                manualChunks: {
                    vendor: ['vue', 'vue-router', 'pinia'],
                    charts: ['chart.js', 'vue-chartjs']
                }
            }
        }
    }
})
```

---

## 5.4 main.js - Entry Point

```javascript
/**
 * Nachos Replay - Main Entry Point
 */
import { createApp } from 'vue'
import { pinia } from './stores'       // Instância Pinia
import router from './router'          // Vue Router
import i18n from './i18n'              // Internacionalização
import App from './App.vue'            // Componente raiz

import './assets/styles/main.css'      // Estilos globais

// Cria instância Vue
const app = createApp(App)

// Registra plugins
app.use(pinia)    // Estado global
app.use(router)   // Rotas
app.use(i18n)     // Traduções

// Monta no elemento #app
app.mount('#app')
```

---

## 5.5 App.vue - Componente Raiz

```vue
<template>
    <!-- Layout dinâmico baseado na rota atual -->
    <component :is="layout">
        <!-- Transição suave entre páginas -->
        <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
                <component :is="Component" />
            </transition>
        </router-view>
    </component>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import DefaultLayout from '@/components/layouts/DefaultLayout.vue'
import BlankLayout from '@/components/layouts/BlankLayout.vue'

const route = useRoute()
const authStore = useAuthStore()

// Seleciona layout baseado no meta da rota
const layout = computed(() => {
    const layoutName = route.meta.layout || 'default'
    return layoutName === 'blank' ? BlankLayout : DefaultLayout
})

// Inicializa autenticação ao montar
onMounted(async () => {
    await authStore.init()
})
</script>

<style>
#app {
    min-height: 100vh;
}
</style>
```

---

## 5.6 router/index.js - Rotas

```javascript
/**
 * Nachos Replay - Vue Router
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/LoginView.vue'),  // Lazy loading
        meta: { requiresAuth: false, layout: 'blank' }
    },
    {
        path: '/',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/replays',
        name: 'Replays',
        component: () => import('@/views/ReplaysView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/replays/:id',
        name: 'ReplayPlayer',
        component: () => import('@/views/ReplayPlayerView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/audit',
        name: 'Audit',
        component: () => import('@/views/AuditLogsView.vue'),
        meta: { requiresAuth: true, requiresRole: ['admin', 'auditor'] }
    },
    {
        path: '/users',
        name: 'Users',
        component: () => import('@/views/UsersView.vue'),
        meta: { requiresAuth: true, requiresRole: ['admin'] }
    },
    {
        path: '/groups',
        name: 'Groups',
        component: () => import('@/views/GroupsView.vue'),
        meta: { requiresAuth: true, requiresRole: ['admin'] }
    },
    {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/SettingsView.vue'),
        meta: { requiresAuth: true, requiresRole: ['admin'] }
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/NotFoundView.vue'),
        meta: { requiresAuth: false, layout: 'blank' }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// Navigation Guard - proteção de rotas
router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()

    // Se tem token mas não carregou usuário, inicializa
    if (!authStore.user && authStore.accessToken) {
        await authStore.init()
    }

    // Verifica autenticação
    if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
        return next({ name: 'Login', query: { redirect: to.fullPath } })
    }

    // Verifica permissão de role
    if (to.meta.requiresRole) {
        const userRole = authStore.userRole
        if (!to.meta.requiresRole.includes(userRole)) {
            return next({ name: 'Dashboard' })
        }
    }

    // Redireciona se já logado tentando acessar login
    if (to.name === 'Login' && authStore.isAuthenticated) {
        return next({ name: 'Dashboard' })
    }

    next()
})

export default router
```

---

## 5.7 stores/auth.js - Store de Autenticação

```javascript
/**
 * Nachos Replay - Auth Store
 * Pinia store for authentication state
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/composables/useApi'

export const useAuthStore = defineStore('auth', () => {
    // State - dados reativos
    const user = ref(null)                                   // Dados do usuário
    const accessToken = ref(localStorage.getItem('accessToken') || null)
    const refreshToken = ref(localStorage.getItem('refreshToken') || null)
    const isLoading = ref(false)
    const error = ref(null)

    // Getters - propriedades computadas
    const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
    const isAdmin = computed(() => user.value?.role === 'admin')
    const isAuditor = computed(() => ['admin', 'auditor'].includes(user.value?.role))
    const userRole = computed(() => user.value?.role || 'viewer')
    const displayName = computed(() => user.value?.display_name || user.value?.username || '')

    // Actions - métodos
    async function login(username, password) {
        isLoading.value = true
        error.value = null

        try {
            // Chama API de login
            const response = await api.post('/api/auth/login', { username, password })

            // Armazena tokens
            accessToken.value = response.data.access_token
            refreshToken.value = response.data.refresh_token

            // Persiste no localStorage
            localStorage.setItem('accessToken', response.data.access_token)
            localStorage.setItem('refreshToken', response.data.refresh_token)

            // Busca dados do usuário
            await fetchUser()
            return true
        } catch (err) {
            error.value = err.response?.data?.detail || 'Falha no login. Verifique suas credenciais.'
            return false
        } finally {
            isLoading.value = false
        }
    }

    async function fetchUser() {
        if (!accessToken.value) return null

        try {
            const response = await api.get('/api/auth/me')
            user.value = response.data
            return user.value
        } catch (err) {
            if (err.response?.status === 401) {
                await logout()
            }
            return null
        }
    }

    async function refreshAccessToken() {
        if (!refreshToken.value) return false

        try {
            const response = await api.post('/api/auth/refresh', {
                refresh_token: refreshToken.value
            })

            accessToken.value = response.data.access_token
            refreshToken.value = response.data.refresh_token

            localStorage.setItem('accessToken', response.data.access_token)
            localStorage.setItem('refreshToken', response.data.refresh_token)

            return true
        } catch (err) {
            await logout()
            return false
        }
    }

    async function logout() {
        try {
            if (accessToken.value) {
                await api.post('/api/auth/logout')
            }
        } catch (err) {
            // Ignora erros no logout
        } finally {
            // Limpa estado
            user.value = null
            accessToken.value = null
            refreshToken.value = null
            localStorage.removeItem('accessToken')
            localStorage.removeItem('refreshToken')
        }
    }

    function clearError() {
        error.value = null
    }

    async function init() {
        if (accessToken.value) {
            await fetchUser()
        }
    }

    return {
        // State
        user, accessToken, refreshToken, isLoading, error,
        // Getters
        isAuthenticated, isAdmin, isAuditor, userRole, displayName,
        // Actions
        login, logout, fetchUser, refreshAccessToken, clearError, init
    }
})
```

---

## 5.8 composables/useApi.js - Cliente HTTP

```javascript
/**
 * Nachos Replay - API Client
 * Axios instance with interceptors for JWT auth
 */
import axios from 'axios'

// Cria instância Axios configurada
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Interceptor de REQUEST - adiciona token JWT
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('accessToken')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => Promise.reject(error)
)

// Interceptor de RESPONSE - trata erros e refresh token
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config

        // Se 401 e não é retry, tenta refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true

            try {
                const refreshToken = localStorage.getItem('refreshToken')
                if (!refreshToken) {
                    throw new Error('No refresh token')
                }

                // Chama endpoint de refresh
                const response = await axios.post('/api/auth/refresh', {
                    refresh_token: refreshToken
                })

                const { access_token, refresh_token } = response.data

                // Atualiza tokens
                localStorage.setItem('accessToken', access_token)
                localStorage.setItem('refreshToken', refresh_token)

                // Retenta request original com novo token
                originalRequest.headers.Authorization = `Bearer ${access_token}`
                return api(originalRequest)
            } catch (refreshError) {
                // Falhou - limpa e redireciona para login
                localStorage.removeItem('accessToken')
                localStorage.removeItem('refreshToken')
                window.location.href = '/login'
                return Promise.reject(refreshError)
            }
        }

        return Promise.reject(error)
    }
)

export default api
```

---

## 5.9 CSS Design System (variables.css)

```css
/* ===========================================
   Nachos Replay - CSS Variables (Design System)
   Cores baseadas na identidade da Caixa Econômica Federal
   =========================================== */

:root {
    /* ========== Primary Colors (Azul Caixa) ========== */
    --color-primary-50: #e6f0f7;
    --color-primary-100: #cce1ef;
    --color-primary-200: #99c3df;
    --color-primary-300: #66a5cf;
    --color-primary-400: #3387bf;
    --color-primary-500: #005BAB; /* Main - Azul Caixa */
    --color-primary-600: #004d91;
    --color-primary-700: #003f77;
    --color-primary-800: #00315d;
    --color-primary-900: #002343;

    /* ========== Accent Colors (Laranja Caixa) ========== */
    --color-accent-50: #fff5eb;
    --color-accent-100: #ffe6cc;
    --color-accent-200: #ffcc99;
    --color-accent-300: #ffb366;
    --color-accent-400: #ff9933;
    --color-accent-500: #FF6600; /* Main - Laranja Caixa */
    --color-accent-600: #cc5200;
    --color-accent-700: #994d00;
    --color-accent-800: #663d00;
    --color-accent-900: #332800;

    /* ========== Gray Scale ========== */
    --color-gray-50: #f8fafc;
    --color-gray-100: #f1f5f9;
    --color-gray-200: #e2e8f0;
    --color-gray-300: #cbd5e1;
    --color-gray-400: #94a3b8;
    --color-gray-500: #64748b;
    --color-gray-600: #475569;
    --color-gray-700: #334155;
    --color-gray-800: #1e293b;
    --color-gray-900: #0f172a;

    /* ========== Semantic Colors ========== */
    --color-success-500: #22c55e;  /* Verde */
    --color-warning-500: #f59e0b;  /* Amarelo */
    --color-error-500: #ef4444;    /* Vermelho */
    --color-info-500: #0ea5e9;     /* Azul claro */

    /* ========== Background & Surface ========== */
    --bg-primary: #f8fafc;    /* Fundo principal */
    --bg-secondary: #ffffff;  /* Fundo secundário */
    --bg-card: #ffffff;       /* Fundo de cards */
    --bg-sidebar: #0f172a;    /* Sidebar escura */
    --bg-topbar: #ffffff;     /* Topbar clara */

    /* ========== Text Colors ========== */
    --text-primary: #1e293b;    /* Texto principal */
    --text-secondary: #475569;  /* Texto secundário */
    --text-muted: #94a3b8;      /* Texto desabilitado */
    --text-inverse: #ffffff;    /* Texto invertido (em fundos escuros) */

    /* ========== Typography ========== */
    --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    
    --font-size-xs: 0.75rem;     /* 12px */
    --font-size-sm: 0.875rem;    /* 14px */
    --font-size-base: 1rem;      /* 16px */
    --font-size-lg: 1.125rem;    /* 18px */
    --font-size-xl: 1.25rem;     /* 20px */
    --font-size-2xl: 1.5rem;     /* 24px */

    /* ========== Spacing (base 4px) ========== */
    --spacing-xs: 0.25rem;   /* 4px */
    --spacing-sm: 0.5rem;    /* 8px */
    --spacing-md: 1rem;      /* 16px */
    --spacing-lg: 1.5rem;    /* 24px */
    --spacing-xl: 2rem;      /* 32px */

    /* ========== Border Radius ========== */
    --radius-sm: 0.25rem;    /* 4px */
    --radius-md: 0.5rem;     /* 8px */
    --radius-lg: 0.75rem;    /* 12px */
    --radius-full: 9999px;   /* Circular */

    /* ========== Shadows ========== */
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);

    /* ========== Layout ========== */
    --sidebar-width: 260px;
    --sidebar-collapsed-width: 70px;
    --topbar-height: 64px;
}
```

---

# 6. Banco de Dados

## init.sql - Schema Inicial

```sql
-- Nachos Replay - Database Schema
-- PostgreSQL 16

-- Extensões
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enums
CREATE TYPE user_role AS ENUM ('admin', 'viewer', 'auditor');
CREATE TYPE replay_status AS ENUM ('active', 'archived', 'deleted');
CREATE TYPE audit_action AS ENUM (
    'view', 'download', 'search', 'login', 
    'logout', 'export', 'create', 'update', 'delete'
);

-- Tabela de usuários
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    display_name VARCHAR(255),
    password_hash VARCHAR(255),
    ldap_dn VARCHAR(500),
    role user_role DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    is_ldap_user BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de grupos
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    ldap_dn VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de relacionamento usuário-grupo
CREATE TABLE user_groups (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, group_id)
);

-- Tabela de replays
CREATE TABLE replays (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(500) UNIQUE NOT NULL,
    original_path VARCHAR(1000) NOT NULL,
    stored_path VARCHAR(1000) NOT NULL,
    session_name VARCHAR(255),
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    owner_username VARCHAR(100),
    client_ip VARCHAR(45),
    file_size BIGINT DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0,
    session_start TIMESTAMP WITH TIME ZONE,
    session_end TIMESTAMP WITH TIME ZONE,
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status replay_status DEFAULT 'active',
    metadata_json JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de logs de auditoria
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(100),
    replay_id UUID REFERENCES replays(id) ON DELETE SET NULL,
    action audit_action NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_replays_owner_username ON replays(owner_username);
CREATE INDEX idx_replays_status ON replays(status);
CREATE INDEX idx_replays_session_start ON replays(session_start);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Usuários iniciais (senhas hasheadas com bcrypt)
INSERT INTO users (username, email, display_name, password_hash, role, is_active) VALUES
    ('admin', 'admin@nachos.local', 'Administrator', 
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.mqKz.OT3H', 'admin', TRUE),
    ('viewer', 'viewer@nachos.local', 'Viewer User',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.mqKz.OT3H', 'viewer', TRUE),
    ('auditor', 'auditor@nachos.local', 'Auditor User',
     '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.mqKz.OT3H', 'auditor', TRUE);
```

---

# 7. API Reference

## Endpoints Disponíveis

| Grupo | Endpoint | Método | Descrição |
|-------|----------|--------|-----------|
| Auth | `/api/auth/login` | POST | Login |
| Auth | `/api/auth/me` | GET | Usuário atual |
| Auth | `/api/auth/refresh` | POST | Renovar token |
| Auth | `/api/auth/logout` | POST | Logout |
| Replays | `/api/replays` | GET | Listar replays |
| Replays | `/api/replays/{id}` | GET | Detalhes |
| Replays | `/api/replays/{id}/stream` | GET | Stream |
| Replays | `/api/replays/{id}` | DELETE | Excluir |
| Stats | `/api/stats/overview` | GET | Estatísticas |
| Stats | `/api/stats/top-users` | GET | Top usuários |
| Stats | `/api/stats/replays-over-time` | GET | Replays/tempo |
| Audit | `/api/audit` | GET | Logs |
| Audit | `/api/audit/export` | POST | Exportar |
| Users | `/api/users` | GET/POST | CRUD |
| Users | `/api/users/{id}` | PUT/DELETE | CRUD |
| Groups | `/api/groups` | GET/POST | CRUD |
| Groups | `/api/groups/{id}` | PUT/DELETE | CRUD |

---

## Autenticação

Todas as rotas (exceto login) requerem header:
```
Authorization: Bearer <access_token>
```

---

# Acesso ao Sistema

- **Frontend:** http://localhost
- **API Docs:** http://localhost:8000/docs

## Credenciais de Teste

| Usuário | Senha | Role |
|---------|-------|------|
| admin | admin123 | Administrador |
| viewer | viewer123 | Visualizador |
| auditor | auditor123 | Auditor |

---

*Documento gerado automaticamente - Nachos Replay v2.0.0*
