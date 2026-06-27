# DJ VRC Booking — Documentação da API para o Frontend

> Base URL: `http://localhost:5000/api/v1`  
> Todos os endpoints retornam JSON. Autenticação via **Bearer Token** no header `Authorization`.

---

## Índice

1. [Autenticação e formato de resposta](#1-autenticação-e-formato-de-resposta)
2. [Auth — Registro, Login e Conta](#2-auth)
3. [OAuth — Discord e Google](#3-oauth--discord-e-google)
4. [Vinculação de Contas (Link/Unlink)](#4-vinculação-de-contas)
5. [DJs — Perfis e Busca](#5-djs)
6. [Agenda do DJ](#6-agenda-do-dj)
7. [Bookings — Propostas e Status](#7-bookings)
8. [Eventos](#8-eventos)
9. [Notificações](#9-notificações)
10. [Admin](#10-admin)
11. [Modelos de dados](#11-modelos-de-dados)
12. [Fluxos completos](#12-fluxos-completos)

---

## 1. Autenticação e formato de resposta

### Header de autenticação

Toda rota protegida exige o token JWT no header:

```
Authorization: Bearer <access_token>
```

### Formato padrão de resposta

**Sucesso:**
```json
{
  "success": true,
  "message": "OK",
  "data": { ... }
}
```

**Erro:**
```json
{
  "success": false,
  "message": "Descrição do erro"
}
```

### Códigos HTTP utilizados

| Código | Significado |
|--------|-------------|
| `200` | Sucesso |
| `201` | Criado |
| `400` | Erro de validação / regra de negócio |
| `401` | Não autenticado (token ausente, inválido ou expirado) |
| `403` | Acesso negado (sem permissão) |
| `404` | Recurso não encontrado |
| `409` | Conflito (e.g. e-mail já cadastrado) |
| `410` | Token expirado (verificação de e-mail, reset de senha) |
| `500` | Erro interno do servidor |

### Tokens JWT

| Token | Duração padrão | Uso |
|-------|---------------|-----|
| `access_token` | 1 hora (3600s) | Enviar em todas as requisições autenticadas |
| `refresh_token` | 30 dias (2592000s) | Renovar o `access_token` sem novo login |

---

## 2. Auth

### Verificar métodos de cadastro ativos

```
GET /auth/register-config
```

Retorna quais métodos de login estão habilitados no momento.

**Resposta:**
```json
{
  "data": {
    "email_enabled": true,
    "discord_enabled": true,
    "google_enabled": false
  }
}
```

---

### Registro

```
POST /auth/register
```

**Body:**
```json
{
  "email": "usuario@email.com",
  "username": "NomeDeUsuario",
  "password": "minimo8chars",
  "is_dj": false
}
```

> Para cadastro via OAuth (Discord/Google), inclua também `discord_id`, `discord_username`, `discord_display_name`, `discord_avatar` (ou equivalentes Google). Contas OAuth são ativadas automaticamente e recebem tokens direto na resposta.

**Resposta (e-mail):** `201` — pede verificação de e-mail.  
**Resposta (OAuth):** `201` — inclui `access_token`, `refresh_token` e `user`.

---

### Verificar e-mail

```
GET /auth/verify-email/<token>
```

Token enviado por e-mail. Sem body.

---

### Login

```
POST /auth/login
```

**Body:**
```json
{
  "email": "usuario@email.com",
  "password": "minhasenha"
}
```

**Resposta:**
```json
{
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "user": { ... }
  }
}
```

---

### Refresh Token

```
POST /auth/refresh
```

Enviar o `refresh_token` no header `Authorization: Bearer <refresh_token>`.

**Resposta:**
```json
{
  "data": {
    "access_token": "novo_token"
  }
}
```

---

### Logout

```
POST /auth/logout
```

Revoga o token atual. Requer `access_token` no header.

---

### Dados do usuário logado

```
GET /auth/me
```

**Resposta:** objeto `user` completo (campo `data`).

---

### Atualizar conta

```
PUT /auth/me
```

**Body (campos opcionais):**
```json
{
  "username": "NovoNome",
  "email": "novo@email.com",
  "password": "novaSenha123"
}
```

---

### Excluir conta

```
DELETE /auth/me
```

**Body:**
```json
{
  "confirm": "EXCLUIR"
}
```

> Bloqueado se houver bookings ativos (pendente, aceito ou em andamento).  
> Não funciona para contas `admin`.

---

### Esqueci minha senha

```
POST /auth/forgot-password
```

**Body:**
```json
{ "email": "usuario@email.com" }
```

Sempre retorna sucesso (não revela se o e-mail existe).

---

### Redefinir senha

```
POST /auth/reset-password/<token>
```

**Body:**
```json
{ "password": "novaSenha123" }
```

---

### Ativar modo DJ

```
POST /auth/activate-dj
```

Qualquer usuário pode ativar o modo DJ sem mudar seu `role` base.

---

### Preferências de notificação

```
PUT /auth/notifications
```

**Body (campos opcionais):**
```json
{
  "notify_discord_dm": true,
  "notify_discord_webhook": false,
  "webhook_url": "https://discord.com/api/webhooks/..."
}
```

---

### Formulário de contato

```
POST /auth/contact
```

**Body:**
```json
{
  "name": "Nome",
  "email": "email@exemplo.com",
  "subject": "Assunto",
  "message": "Mensagem com pelo menos 10 caracteres."
}
```

---

## 3. OAuth — Discord e Google

### Login com Discord

```
GET /auth/discord
```

Retorna `{ "data": { "redirect_url": "https://discord.com/api/oauth2/authorize?..." } }`.

O frontend deve redirecionar o usuário para essa URL.

---

### Callback Discord

```
GET /auth/discord/callback?code=<code>
```

> **Atenção:** O `DISCORD_REDIRECT_URI` configurado no `.env` aponta para o **frontend** (ex: `http://localhost:3000/auth/discord/callback`). O Discord redireciona o usuário para o frontend com `?code=` na URL. O frontend então lê esse `code` e faz a chamada GET para a API com ele. Todos os callbacks OAuth retornam JSON — não fazem redirect HTTP.

Dois cenários possíveis na resposta:

**Usuário existente:**
```json
{
  "data": {
    "action": "login",
    "access_token": "...",
    "refresh_token": "...",
    "user": { ... }
  }
}
```

**Usuário novo:**
```json
{
  "data": {
    "action": "register",
    "discord_id": "123456789",
    "discord_username": "usuario",
    "discord_display_name": "Usuário VRC",
    "discord_avatar": "hash",
    "email": "email@discord.com",
    "suggested_username": "usuario"
  }
}
```

> Quando `action === "register"`, redirecione para a tela de cadastro pré-preenchida com esses dados. Envie esses dados no body do `POST /auth/register`.

---

### Login com Google

```
GET /auth/google
```

Retorna `{ "data": { "redirect_url": "https://accounts.google.com/..." } }`.

> Retorna 403 se Google OAuth estiver desativado no painel admin.

---

### Callback Google

```
GET /auth/google/callback?code=<code>
```

Mesma lógica do Discord: o Google redireciona para o frontend com `?code=`, o frontend repassa para a API, que retorna `action: "login"` ou `action: "register"`.

---

## 4. Vinculação de Contas

Rotas para vincular/desvincular Discord e Google de uma conta existente (usuário já logado).

### Iniciar vinculação Discord

```
POST /auth/link/discord
```

Retorna `redirect_url` para o OAuth Discord (usando `DISCORD_LINK_REDIRECT_URI`).

---

### Callback de vinculação Discord

```
GET /auth/link/discord/callback?code=<code>
```

Vincula o Discord à conta logada.

---

### Vincular Discord manualmente (por ID)

```
POST /auth/link/discord/manual
```

**Body:**
```json
{
  "discord_id": "123456789012345678",
  "discord_username": "usuario#0000"
}
```

---

### Desvincular Discord

```
POST /auth/unlink/discord
```

> Bloqueado se Discord for o único método de login (sem senha e sem Google).

---

### Iniciar vinculação Google

```
GET /auth/link/google
```

Retorna `redirect_url`.

---

### Callback de vinculação Google

```
GET /auth/link/google/callback?code=<code>
```

---

### Desvincular Google

```
POST /auth/unlink/google
```

---

## 5. DJs

### Listar e buscar DJs

```
GET /djs/
```

**Query params:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `page` | int | Página (default: 1) |
| `per_page` | int | Por página (max: 50) |
| `genre` | string | Filtrar por slug de gênero |
| `language` | string | Filtrar por idioma (ex: `pt-BR`) |
| `country` | string | Filtrar por país |
| `min_price` | float | Preço mínimo por hora |
| `max_price` | float | Preço máximo por hora |
| `search` | string | Busca por nome artístico ou bio |
| `sort` | string | `recent` (default), `price_asc`, `price_desc` |

**Resposta:**
```json
{
  "data": {
    "djs": [ { ...djProfile } ],
    "total": 42,
    "pages": 3,
    "page": 1,
    "per_page": 20
  }
}
```

---

### Ver perfil de um DJ

```
GET /djs/<dj_id>
```

---

### DJs em destaque

```
GET /djs/featured
```

Retorna DJs com `featured_until` no futuro. Ideal para a home/landing page.

---

### Estatísticas públicas

```
GET /djs/stats
```

```json
{
  "data": {
    "total_djs": 12,
    "total_genres": 17,
    "total_events": 48
  }
}
```

---

### Listar gêneros musicais

```
GET /djs/genres
```

---

### Listar formatos de apresentação

```
GET /djs/presentation-formats
```

---

### Criar perfil DJ

```
POST /djs/
```

Requer `is_dj: true` na conta (ative com `POST /auth/activate-dj` primeiro).

**Body:**
```json
{
  "artist_name": "DJ Vortex",
  "bio": "DJ de VRChat com 3 anos de experiência.",
  "languages": ["pt-BR", "en-US"],
  "country": "BR",
  "timezone": "America/Sao_Paulo",
  "discord_tag": "vortex#0000",
  "twitch_url": "https://twitch.tv/vortex",
  "youtube_url": "https://youtube.com/@vortex",
  "vrchat_username": "VortexDJ",
  "website_url": "https://vortex.com",
  "experience_years": 3,
  "equipment": "Pioneer DDJ-400, Serato DJ",
  "event_experience": "100+ eventos VRChat",
  "hourly_rate": 50.00,
  "event_rate": 150.00,
  "minimum_rate": 30.00,
  "currency": "USD",
  "negotiable": true,
  "request_quote": false,
  "genre_ids": [1, 3, 5],
  "presentation_format_ids": [1, 2]
}
```

---

### Editar perfil DJ (usuário logado)

```
PUT /djs/me
```

Mesmos campos do POST acima. Todos opcionais.

Campos adicionais editáveis:
```json
{
  "avatar_url": "https://...",
  "banner_url": "https://...",
  "logo_url": "https://...",
  "notify_dm": true,
  "notify_webhook": false,
  "webhook_url": "https://discord.com/api/webhooks/..."
}
```

---

### Ver meu perfil DJ

```
GET /djs/me
```

Retorna perfil completo com campos privados (`full=true`).

---

### Excluir perfil DJ

```
DELETE /djs/me
```

> Bloqueado se houver bookings ativos. Desativa `is_dj` na conta mas não exclui o usuário.

---

### Definir disponibilidade

```
POST /djs/me/availability
```

**Body:**
```json
{
  "availability": [
    {
      "weekday": 5,
      "start_time": "20:00",
      "end_time": "23:00"
    },
    {
      "weekday": 6,
      "start_time": "18:00",
      "end_time": "00:00"
    },
    {
      "blocked_date": "2025-12-25"
    }
  ]
}
```

> `weekday`: 0=Segunda, 1=Terça, ..., 6=Domingo.  
> Substitui toda a disponibilidade existente.

---

## 6. Agenda do DJ

### Ver agenda pública de um DJ

```
GET /djs/<dj_id>/agenda
```

Retorna eventos futuros não privados. Não requer autenticação.

---

### Ver minha agenda completa (DJ logado)

```
GET /djs/me/agenda
```

Inclui eventos privados. Requer modo DJ ativo.

---

### Adicionar evento manual à agenda

```
POST /djs/me/agenda
```

**Body:**
```json
{
  "event_name": "VRChat Party Night",
  "event_date": "2025-08-15",
  "event_time": "21:00",
  "duration_minutes": 120,
  "platform": "VRChat",
  "description": "Festa especial de aniversário.",
  "is_private": false
}
```

---

### Editar entrada da agenda

```
PUT /djs/me/agenda/<entry_id>
```

> Eventos originados de um booking (`source: "booking"`) só permitem alterar `is_private`.  
> Eventos manuais (`source: "manual"`) permitem edição completa.

---

### Remover evento da agenda

```
DELETE /djs/me/agenda/<entry_id>
```

> Apenas eventos manuais. Para remover eventos de booking, cancele o booking.

---

## 7. Bookings

### Criar proposta (contratante)

```
POST /bookings/
```

**Body:**
```json
{
  "dj_profile_id": 5,
  "event_name": "Festa VRChat",
  "event_date": "2025-09-20",
  "event_time": "20:00",
  "duration_minutes": 120,
  "platform": "VRChat",
  "description": "Evento de aniversário da nossa comunidade.",
  "offered_value": 80.00,
  "currency": "USD"
}
```

> DJ deve estar aprovado e ativo. Ao criar, o sistema envia notificações automáticas via DM do Discord.

---

### Listar meus bookings

```
GET /bookings/
```

**Query params:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `page` | int | Página (default: 1) |
| `per_page` | int | Por página (max: 50) |
| `status` | string | Filtrar por status |

> O sistema retorna automaticamente os bookings relevantes para o papel do usuário:  
> - **Admin**: todos os bookings  
> - **DJ**: bookings recebidos no seu perfil + bookings enviados como contratante  
> - **Contratante**: apenas bookings que enviou

---

### Ver um booking

```
GET /bookings/<booking_id>
```

---

### Aceitar proposta (DJ)

```
POST /bookings/<booking_id>/accept
```

> Apenas para bookings com `status: "pending"`.  
> Cria automaticamente: entrada na agenda pública do DJ + Evento associado.  
> Dispara notificações via Discord DM.

---

### Recusar proposta (DJ)

```
POST /bookings/<booking_id>/decline
```

**Body (opcional):**
```json
{
  "notes": "Indisponível nessa data."
}
```

---

### Cancelar booking

```
POST /bookings/<booking_id>/cancel
```

Pode ser feito pelo contratante, pelo DJ ou pelo admin.  
Remove a entrada da agenda do DJ automaticamente.

---

### Apagar booking

```
DELETE /bookings/<booking_id>
```

Só é possível apagar bookings com status `declined` ou `cancelled`.  
Usuários comuns devem aguardar 24h após o cancelamento/recusa.  
Admins podem apagar imediatamente.

---

### Status possíveis de um booking

| Status | Descrição |
|--------|-----------|
| `pending` | Aguardando resposta do DJ |
| `accepted` | DJ aceitou |
| `declined` | DJ recusou |
| `cancelled` | Cancelado por contratante, DJ ou admin |
| `completed` | Evento realizado |

---

## 8. Eventos

Eventos são criados **automaticamente** quando um booking é aceito. O frontend raramente precisará criá-los manualmente.

### Listar eventos

```
GET /events/
```

**Query params:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `page` | int | Página |
| `per_page` | int | Por página (max: 50) |
| `status` | string | Filtrar por status |

---

### Ver evento

```
GET /events/<event_id>
```

---

### Atualizar evento

```
PUT /events/<event_id>
```

Apenas o organizador ou admin pode editar.

**Body (campos opcionais):**
```json
{
  "name": "Novo nome",
  "description": "Descrição atualizada",
  "platform": "VRChat",
  "stream_url": "https://twitch.tv/...",
  "status": "ongoing"
}
```

### Status possíveis de um evento

| Status | Descrição |
|--------|-----------|
| `pending` | Aguardando confirmação |
| `confirmed` | Confirmado (criado quando booking é aceito) |
| `ongoing` | Em andamento |
| `finished` | Encerrado |
| `cancelled` | Cancelado |

---

## 9. Notificações

### Listar notificações

```
GET /notifications/
```

**Query params:**

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `page` | int | Página |
| `per_page` | int | Por página (max: 50) |
| `unread` | bool | `true` para apenas não lidas |

**Resposta:**
```json
{
  "data": {
    "notifications": [ { ...notification } ],
    "total": 10,
    "unread_count": 3,
    "page": 1,
    "pages": 1
  }
}
```

---

### Marcar como lida

```
POST /notifications/<notif_id>/read
```

---

### Marcar como não lida

```
POST /notifications/<notif_id>/unread
```

---

### Marcar todas como lidas

```
POST /notifications/read-all
```

---

### Apagar notificação

```
DELETE /notifications/<notif_id>
```

---

### Apagar todas as notificações

```
DELETE /notifications/delete-all
```

---

### Tipos de notificação (`type`)

| Tipo | Quando é gerado |
|------|----------------|
| `new_proposal` | Contratante enviou uma proposta para o DJ |
| `accepted` | DJ aceitou a proposta |
| `declined` | DJ recusou a proposta |
| `cancelled` | Booking foi cancelado |
| `reminder` | Lembrete de evento (futuro) |
| `system` | Notificação do sistema |

---

## 10. Admin

Todas as rotas abaixo exigem `role: "admin"`.

### Dashboard

```
GET /admin/dashboard
```

Retorna contagens gerais de usuários, perfis DJ, bookings e eventos.

---

### Usuários

```
GET /admin/users
```

**Query params:** `page`, `per_page`, `role`, `search` (busca por username ou e-mail).

```
GET /admin/users/<user_id>
POST /admin/users/<user_id>/suspend
POST /admin/users/<user_id>/activate
```

---

### Perfis DJ

```
GET /admin/djs?approved=true|false
POST /admin/djs/<dj_id>/approve
POST /admin/djs/<dj_id>/reject
```

---

### DJs em destaque

```
GET /admin/featured
```

Lista todos os DJs aprovados com seu status de destaque.

```
POST /admin/featured/<dj_id>
```

**Body:**
```json
{
  "days": 30
}
```

> `days: 0` remove o destaque. Máximo: 365 dias.

---

### Gêneros e Formatos

```
POST /admin/genres
DELETE /admin/genres/<genre_id>

POST /admin/presentation-formats
DELETE /admin/presentation-formats/<fmt_id>
```

**Body para criação:**
```json
{
  "name": "Funk",
  "slug": "funk"
}
```

---

### Logs de auditoria

```
GET /admin/audit-logs?page=1&per_page=50
```

---

### Configurações do site

```
GET /admin/site-config
PUT /admin/site-config
```

**Body para atualizar:**
```json
{
  "register_email_enabled": "1",
  "register_discord_enabled": "1",
  "register_google_enabled": "0"
}
```

> Os valores são strings `"0"` ou `"1"`.

---

## 11. Modelos de dados

### User (privado — retornado em `/auth/me`)

```json
{
  "id": 1,
  "username": "VortexDJ",
  "email": "vortex@email.com",
  "role": "contractor",
  "is_dj": true,
  "is_active": true,
  "is_verified": true,
  "is_suspended": false,
  "discord_id": "123456789",
  "discord_username": "vortex",
  "discord_display_name": "Vortex UwU",
  "discord_avatar": "hashDoAvatar",
  "google_id": null,
  "google_name": null,
  "google_avatar": null,
  "notify_discord_dm": true,
  "notify_discord_webhook": false,
  "webhook_url": null,
  "created_at": "2025-01-01T00:00:00"
}
```

> `role` só pode ser `"contractor"` ou `"admin"`. O modo DJ é controlado pela flag `is_dj`.

---

### DJProfile

```json
{
  "id": 3,
  "user_id": 1,
  "artist_name": "DJ Vortex",
  "avatar_url": "https://...",
  "banner_url": "https://...",
  "bio": "DJ de VRChat.",
  "languages": ["pt-BR", "en-US"],
  "country": "BR",
  "timezone": "America/Sao_Paulo",
  "experience_years": 3,
  "hourly_rate": "50.00",
  "event_rate": "150.00",
  "minimum_rate": "30.00",
  "currency": "USD",
  "negotiable": true,
  "request_quote": false,
  "is_featured": false,
  "genres": [
    { "id": 1, "name": "EDM", "slug": "edm" }
  ],
  "presentation_formats": [
    { "id": 1, "name": "Live via Twitch", "slug": "live-twitch" }
  ],
  "availability": [ ... ],
  "social": {
    "discord": "vortex#0000",
    "discord_username": "vortex",
    "twitch": "https://twitch.tv/vortex",
    "youtube": null,
    "vrchat": "VortexDJ",
    "website": null
  }
}
```

---

### Booking

```json
{
  "id": 7,
  "contractor_id": 2,
  "contractor_name": "NomeContratante",
  "dj_profile_id": 3,
  "dj_name": "DJ Vortex",
  "event_id": 5,
  "event_name": "Festa VRChat",
  "event_date": "2025-09-20",
  "event_time": "20:00",
  "duration_minutes": 120,
  "platform": "VRChat",
  "description": "Aniversário da comunidade.",
  "offered_value": "80.00",
  "currency": "USD",
  "status": "pending",
  "dj_notes": null,
  "created_at": "2025-08-01T14:00:00"
}
```

---

### Notification

```json
{
  "id": 1,
  "type": "new_proposal",
  "title": "Nova proposta recebida!",
  "body": "Você recebeu uma proposta para 'Festa VRChat'.",
  "is_read": false,
  "resource_type": "booking",
  "resource_id": 7,
  "created_at": "2025-08-01T14:00:00"
}
```

---

### DJScheduleEntry (Agenda)

```json
{
  "id": 1,
  "dj_profile_id": 3,
  "booking_id": 7,
  "event_name": "Festa VRChat",
  "event_date": "2025-09-20",
  "event_time": "20:00",
  "duration_minutes": 120,
  "platform": "VRChat",
  "description": null,
  "source": "booking",
  "is_private": false
}
```

> `source: "booking"` = criado automaticamente quando booking é aceito.  
> `source: "manual"` = adicionado manualmente pelo DJ.

---

## 12. Fluxos completos

### Fluxo 1 — Cadastro por e-mail

```
1. GET  /auth/register-config          → verificar se email_enabled: true
2. POST /auth/register                 → cadastrar (sem discord_id/google_id)
3. Usuário clica no link do e-mail
4. GET  /auth/verify-email/<token>     → ativa a conta
5. POST /auth/login                    → obter tokens
```

---

### Fluxo 2 — Login por Discord (conta nova)

```
1. GET  /auth/discord                      → obter redirect_url
2. Redirecionar usuário para o Discord
3. Discord redireciona para o FRONTEND:    http://localhost:3000/auth/discord/callback?code=...
4. Frontend lê o ?code= da URL e chama:   GET /api/v1/auth/discord/callback?code=<code>
5. API retorna JSON: { action: "register", discord_id, email, ... }
6. Frontend exibe formulário pré-preenchido
7. POST /auth/register (com discord_id e dados do Discord)
8. API retorna access_token + refresh_token imediatamente
```

---

### Fluxo 3 — Booking completo

```
1. GET  /djs/?search=vortex            → buscar DJ
2. GET  /djs/<dj_id>                   → ver perfil
3. GET  /djs/<dj_id>/agenda            → verificar disponibilidade
4. POST /bookings/                     → enviar proposta (como contratante)
   → DJ recebe DM no Discord automaticamente

5. [DJ] GET  /bookings/?status=pending → ver propostas recebidas
6. [DJ] POST /bookings/<id>/accept     → aceitar
   → Agenda do DJ atualizada, Evento criado, contratante notificado por DM

7. GET  /events/<event_id>             → acompanhar evento
```

---

### Fluxo 4 — Ativar modo DJ e criar perfil

```
1. POST /auth/activate-dj              → ativar flag is_dj na conta
2. GET  /djs/genres                    → listar gêneros disponíveis
3. GET  /djs/presentation-formats      → listar formatos
4. POST /djs/                          → criar perfil com genre_ids e format_ids
5. PUT  /djs/me                        → editar avatar, bio, preços, etc.
6. POST /djs/me/availability           → definir disponibilidade semanal
```

---

### Fluxo 5 — Renovação de token

```
1. Fazer requisição → API retorna 401 { error: "token_expired" }
2. POST /auth/refresh (com refresh_token no header)
3. Salvar novo access_token
4. Repetir requisição original
5. Se refresh também expirou → redirecionar para login
```

---

## Observações importantes

- **Rate limits ativos:** `/auth/register` (10/hora), `/auth/login` (20/hora), `/auth/forgot-password` (5/hora).
- **Paginação:** Todas as listagens são paginadas. Use `page` e `per_page`. O máximo de `per_page` varia por endpoint (20–200).
- **Datas e horários:** Sempre no formato ISO 8601 (`YYYY-MM-DD` para datas, `HH:MM` para horários).
- **Valores monetários:** Retornados como strings (`"50.00"`) para evitar problemas de float. Envie como number ou string.
- **Avatar do Discord:** O campo `discord_avatar` contém apenas o hash. A URL completa é: `https://cdn.discordapp.com/avatars/<discord_id>/<avatar_hash>.png`
- **Health check:** `GET /health` → `{ "status": "ok", "version": "1.0.0" }` — sem autenticação.
