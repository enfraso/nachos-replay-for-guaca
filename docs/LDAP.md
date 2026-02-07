# Integração LDAP/Active Directory - Nachos Replay

Este documento descreve como configurar a integração com LDAP/Active Directory para autenticação.

---

## Visão Geral

O Nachos Replay suporta autenticação híbrida:
1. **LDAP/AD** - Usuários autenticam com credenciais corporativas
2. **Local** - Usuários criados manualmente no sistema

Quando LDAP está habilitado, o sistema primeiro tenta autenticar via LDAP. Se falhar, tenta autenticação local.

---

## Configuração

### Variáveis de Ambiente

```env
# Habilitar LDAP
LDAP_ENABLED=true

# Servidor LDAP
LDAP_SERVER=ldap://ldap.empresa.com:389
# ou LDAPS: ldaps://ldap.empresa.com:636

# Base DN para buscas
LDAP_BASE_DN=dc=empresa,dc=com

# Credenciais de bind (conta de serviço)
LDAP_BIND_DN=cn=service-account,ou=services,dc=empresa,dc=com
LDAP_BIND_PASSWORD=senha-do-servico

# DN base para buscar usuários
LDAP_USER_SEARCH_BASE=ou=users,dc=empresa,dc=com

# DN base para buscar grupos
LDAP_GROUP_SEARCH_BASE=ou=groups,dc=empresa,dc=com

# Atributos do usuário
LDAP_USER_ATTR_USERNAME=sAMAccountName   # ou uid para OpenLDAP
LDAP_USER_ATTR_EMAIL=mail
LDAP_USER_ATTR_DISPLAY_NAME=displayName
```

### Exemplo para Active Directory

```env
LDAP_ENABLED=true
LDAP_SERVER=ldap://dc01.empresa.local:389
LDAP_BASE_DN=dc=empresa,dc=local
LDAP_BIND_DN=cn=svc-nachos,ou=Services,dc=empresa,dc=local
LDAP_BIND_PASSWORD=SeNhA_SeGuRa_123
LDAP_USER_SEARCH_BASE=ou=Users,dc=empresa,dc=local
LDAP_GROUP_SEARCH_BASE=ou=Groups,dc=empresa,dc=local
LDAP_USER_ATTR_USERNAME=sAMAccountName
LDAP_USER_ATTR_EMAIL=mail
LDAP_USER_ATTR_DISPLAY_NAME=displayName
```

### Exemplo para OpenLDAP

```env
LDAP_ENABLED=true
LDAP_SERVER=ldap://ldap.empresa.com:389
LDAP_BASE_DN=dc=empresa,dc=com
LDAP_BIND_DN=cn=readonly,dc=empresa,dc=com
LDAP_BIND_PASSWORD=senha_readonly
LDAP_USER_SEARCH_BASE=ou=people,dc=empresa,dc=com
LDAP_GROUP_SEARCH_BASE=ou=groups,dc=empresa,dc=com
LDAP_USER_ATTR_USERNAME=uid
LDAP_USER_ATTR_EMAIL=mail
LDAP_USER_ATTR_DISPLAY_NAME=cn
```

---

## Fluxo de Autenticação

```
┌─────────────┐          ┌─────────────┐          ┌─────────────┐
│   Cliente   │──login──▶│   Backend   │──bind───▶│    LDAP     │
│             │          │             │◀─result──│   Server    │
└─────────────┘          └──────┬──────┘          └─────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
             ┌─────────────┐         ┌─────────────┐
             │ LDAP Success│         │ LDAP Failed │
             │             │         │             │
             │ Create/     │         │ Try local   │
             │ Update user │         │ auth        │
             └─────────────┘         └─────────────┘
                    │                       │
                    └───────────┬───────────┘
                                │
                                ▼
                         ┌─────────────┐
                         │ Return JWT  │
                         │ Tokens      │
                         └─────────────┘
```

---

## Funcionalidades

### 1. Autenticação
- Usuário informa username e password
- Sistema tenta bind no LDAP com as credenciais
- Se bem-sucedido, busca atributos do usuário
- Se falhar, tenta autenticação local

### 2. Provisão Automática
Quando um usuário LDAP faz login pela primeira vez:
- É criado automaticamente no banco local
- Recebe role padrão "viewer"
- Dados são sincronizados do LDAP (email, display_name)

### 3. Sincronização
Em logins subsequentes:
- Email e display_name são atualizados do LDAP
- Role e grupos são mantidos localmente

### 4. Mapeamento de Grupos (futuro)
Será possível mapear grupos LDAP para roles:
```env
LDAP_GROUP_ADMIN_DN=cn=nachos-admins,ou=groups,...
LDAP_GROUP_AUDITOR_DN=cn=nachos-auditors,ou=groups,...
```

---

## Configuração via Interface

Administradores podem configurar LDAP pela interface web:

1. Acesse **Configurações → LDAP**
2. Habilite a integração
3. Configure os parâmetros
4. Use o botão **Testar Conexão**
5. Salve as configurações

---

## Troubleshooting

### Erro de Conexão
```
Erro: Can't contact LDAP server
```

Verificações:
1. O servidor LDAP está acessível? Teste com `telnet`:
   ```bash
   telnet ldap.empresa.com 389
   ```
2. O firewall permite a conexão?
3. O DNS resolve o hostname?

### Erro de Bind
```
Erro: Invalid credentials (49)
```

Verificações:
1. O BIND_DN está correto e no formato esperado?
2. A senha está correta?
3. A conta tem permissão de bind?

### Usuário não encontrado
```
Erro: User not found in LDAP
```

Verificações:
1. O USER_SEARCH_BASE está correto?
2. O atributo de username está correto (sAMAccountName vs uid)?
3. O usuário existe no path configurado?

### Teste de Conexão Manual

```bash
# Linux
ldapsearch -x -H ldap://servidor:389 \
  -D "cn=admin,dc=empresa,dc=com" \
  -w senha \
  -b "ou=users,dc=empresa,dc=com" \
  "(sAMAccountName=usuario)"

# Windows PowerShell
$cred = Get-Credential
Get-ADUser -Identity usuario -Server servidor
```

---

## Segurança

### Recomendações

1. **Use LDAPS** em produção (porta 636)
2. **Conta de serviço** com permissões mínimas (apenas leitura)
3. **Não armazene** a senha do bind em código
4. **Rotacione** a senha da conta de serviço periodicamente
5. **Monitore** logs de autenticação

### Configuração LDAPS

```env
LDAP_SERVER=ldaps://ldap.empresa.com:636
```

Se usar certificado auto-assinado:
```env
LDAP_TLS_VERIFY=false  # NÃO recomendado em produção
```

---

## Logs

Ações de autenticação são registradas no log de auditoria:

```json
{
    "action": "login",
    "username": "john.doe",
    "details": {
        "success": true,
        "ldap": true
    }
}
```

Para debug, aumente o log level:
```env
LOG_LEVEL=DEBUG
```
