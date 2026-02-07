# Nachos Replay for Guaca

Sistema de Replay e Auditoria de Sessões Apache Guacamole

## 🚀 Quick Start

```bash
# Clone e configure
git clone <repository>
cd nachos-replay-for-guaca
cp .env.example .env

# Inicie com Docker
docker-compose up -d

# Acesse
# Frontend: http://localhost
# API: http://localhost:8000/docs
```

## 📋 Requisitos

- Docker & Docker Compose
- PostgreSQL 16+ (incluído no docker-compose)
- Node.js 20+ (apenas para desenvolvimento frontend)
- Python 3.11+ (apenas para desenvolvimento backend)

## 🔐 Usuários de Teste (Modo Mock)

| Usuário | Senha | Perfil |
|---------|-------|--------|
| admin | admin123 | Administrador |
| viewer | viewer123 | Visualizador |
| auditor | auditor123 | Auditor |

## 📁 Estrutura

```
nachos-replay-for-guaca/
├── backend/           # FastAPI + SQLAlchemy
├── frontend/          # Vue.js 3 + Vite
├── docs/              # Documentação técnica
├── docker-compose.yml
└── .env.example
```

## 📖 Documentação

- [Instalação e Configuração](docs/INSTALLATION.md)
- [Integração AD/LDAP](docs/LDAP.md)
- [API Reference](docs/API.md)
- [Guia de Contribuição](docs/CONTRIBUTING.md)

## 🎨 Visual

Interface baseada nas cores da Caixa Econômica Federal:
- Azul primário: `#005BAB`
- Laranja accent: `#FF6600`

## 📄 Licença

MIT License
