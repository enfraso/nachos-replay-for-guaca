# Guia de Instalação - Nachos Replay

## Pré-requisitos

### 1. Docker e Docker Compose
Certifique-se de ter Docker 24+ e Docker Compose v2 instalados:

```bash
# Verificar versões
docker --version
docker compose version

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install docker.io docker-compose-plugin

# Windows
# Instale o Docker Desktop: https://docs.docker.com/desktop/windows/install/
```

### 2. Requisitos de Hardware
- **CPU:** 2+ cores
- **RAM:** 4GB mínimo (8GB recomendado)
- **Disco:** 20GB + espaço para replays

---

## Instalação com Docker (Recomendado)

### Passo 1: Clone o Repositório
```bash
git clone <repository-url>
cd nachos-replay-for-guaca
```

### Passo 2: Configure as Variáveis de Ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com suas configurações
nano .env
```

Variáveis importantes:
```env
# SEGURANÇA - MUDE EM PRODUÇÃO!
SECRET_KEY=gere-uma-chave-segura-com-32-caracteres
JWT_SECRET_KEY=gere-outra-chave-segura-com-32-caracteres

# Banco de Dados
DATABASE_URL=postgresql://nachos:nachos_secret@db:5432/nachos_replay

# LDAP (opcional)
LDAP_ENABLED=false
# LDAP_SERVER=ldap://seu-servidor:389
# LDAP_BASE_DN=dc=empresa,dc=com
```

### Passo 3: Inicie os Containers
```bash
# Build e start
docker compose up -d

# Acompanhe os logs
docker compose logs -f

# Aguarde até ver:
# nachos-backend  | INFO:     Application startup complete.
# nachos-frontend | ... nginx: ... running
```

### Passo 4: Acesse a Aplicação
- **Frontend:** http://localhost
- **API Docs:** http://localhost:8000/docs (Swagger)
- **API ReDoc:** http://localhost:8000/redoc

### Passo 5: Faça Login
Use as credenciais de teste:

| Usuário | Senha | Perfil |
|---------|-------|--------|
| admin | admin123 | Administrador |
| viewer | viewer123 | Visualizador |
| auditor | auditor123 | Auditor |

---

## Instalação para Desenvolvimento

### Backend (Python)

```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export DATABASE_URL="postgresql://nachos:nachos_secret@localhost:5432/nachos_replay"
export SECRET_KEY="dev-secret-key"
export JWT_SECRET_KEY="dev-jwt-secret"

# Rodar migrations (se houver)
# alembic upgrade head

# Iniciar servidor de desenvolvimento
uvicorn app.main:app --reload --port 8000
```

### Frontend (Vue.js)

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev

# Acesse http://localhost:5173
```

---

## Configuração de Produção

### 1. Gere Chaves Seguras
```bash
# Linux/Mac
openssl rand -hex 32  # SECRET_KEY
openssl rand -hex 32  # JWT_SECRET_KEY

# PowerShell
[Convert]::ToBase64String((1..32|%{[byte](Get-Random -Max 256)}))
```

### 2. Configure HTTPS
Edite `frontend/nginx.conf` para adicionar SSL:
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ...
}
```

### 3. Configure Volume de Replays
Monte o diretório de gravações do Guacamole:
```yaml
# docker-compose.yml
volumes:
  guacamole_recordings:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/guacamole/recordings
```

### 4. Configure Backup
```bash
# Backup do PostgreSQL
docker compose exec db pg_dump -U nachos nachos_replay > backup.sql

# Restore
docker compose exec -T db psql -U nachos nachos_replay < backup.sql
```

---

## Integração com Guacamole

### Configurar Diretório de Gravações

1. Configure o Guacamole para gravar sessões:
```xml
<!-- guacamole.properties ou connection settings -->
recording-path: /guacamole-recordings
recording-name: ${GUAC_DATE}-${GUAC_TIME}
```

2. Monte o diretório no docker-compose:
```yaml
services:
  backend:
    volumes:
      - /path/to/guacamole-recordings:/guacamole/recordings:ro
```

3. Configure a importação automática no `.env`:
```env
GUACAMOLE_RECORDINGS_PATH=/guacamole/recordings
REPLAY_IMPORT_DELAY_HOURS=24
```

---

## Troubleshooting

### Container não inicia
```bash
# Ver logs detalhados
docker compose logs backend

# Verificar status dos containers
docker compose ps

# Reiniciar do zero
docker compose down -v
docker compose up -d --build
```

### Erro de conexão com banco
```bash
# Verificar se o PostgreSQL está healthy
docker compose ps db

# Acessar o banco manualmente
docker compose exec db psql -U nachos -d nachos_replay

# Recriar o banco
docker compose down -v
docker compose up -d
```

### Frontend não carrega
```bash
# Reconstruir frontend
docker compose build frontend
docker compose up -d frontend

# Verificar logs do nginx
docker compose logs frontend
```

### Erro de login
```bash
# Verificar logs do backend
docker compose logs backend | grep -i error

# Verificar se usuários existem
docker compose exec db psql -U nachos -d nachos_replay -c "SELECT username, role FROM users;"
```

---

## Comandos Úteis

```bash
# Status de todos os serviços
docker compose ps

# Logs em tempo real
docker compose logs -f

# Reiniciar um serviço
docker compose restart backend

# Reconstruir e reiniciar
docker compose up -d --build

# Limpar tudo e recomeçar
docker compose down -v
docker compose up -d

# Shell no container
docker compose exec backend bash
docker compose exec db psql -U nachos -d nachos_replay

# Ver uso de recursos
docker stats
```
