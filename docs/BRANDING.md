# Customização de Branding

Para personalizar o nome e logo do sistema, edite as variáveis no arquivo `.env`:

## Variáveis Disponíveis

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `VITE_APP_NAME` | Nome do sistema | `Replay Viewer Corp` |
| `VITE_LOGO_URL` | URL da logo | `/assets/minha-logo.png` |
| `VITE_LOGO_EMOJI` | Emoji (se sem logo) | `🔒` |
| `VITE_FOOTER_TEXT` | Texto no rodapé | `© 2026 Minha Empresa` |

## Exemplo de Customização

```bash
# .env
VITE_APP_NAME=Sistema de Replays Corporativo
VITE_LOGO_URL=/assets/logo-empresa.png
VITE_FOOTER_TEXT=© 2026 Empresa XYZ
```

## Adicionar Logo Customizada

1. Coloque o arquivo da logo em `frontend/public/assets/`
2. Configure `VITE_LOGO_URL=/assets/nome-do-arquivo.png`
3. Reconstrua o frontend: `docker compose up -d --build frontend`

## Usuários de Teste (Documentação)

Para desenvolvimento e testes, estes usuários estão disponíveis:

| Usuário | Senha | Role |
|---------|-------|------|
| admin | admin123 | Administrador |
| viewer | viewer123 | Visualizador |
| auditor | auditor123 | Auditor |

> ⚠️ **Atenção**: Altere as senhas em produção!
