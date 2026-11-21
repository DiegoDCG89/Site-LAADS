# LaADS: site Flask + painel de controle

Site da Liga Acadêmica de ADS (design do projeto original, agora em **Flask + Jinja**), com:

- **Painel em `/admin`** para editar todos os textos, listas (eventos, parceiros, benefícios…), imagens e ver inscrições/mensagens.
- **Google Sheets como banco de dados** (uma aba por tipo de conteúdo; dá para editar direto na planilha também).
- **Google Drive para as imagens** (ficam privadas; o site as serve por `/media/<id>` com cache de CDN).
- Pronto para o **Vercel** (sem build de Node no deploy).

Sem nenhuma credencial configurada o site já funciona com o conteúdo original, e o painel roda em "modo local". Dá para testar tudo antes de mexer no Google.

---

## 1. Rodar localmente

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env        # preencha pelo menos SECRET_KEY e ADMIN_PASSWORD
python app.py               # http://localhost:5000   |   painel: http://localhost:5000/admin
```

Gere o `SECRET_KEY` com `python -c "import secrets;print(secrets.token_urlsafe(48))"`.
Para guardar a senha como hash (recomendado): `python scripts/hash_password.py` e use `ADMIN_PASSWORD_HASH` no lugar de `ADMIN_PASSWORD`.

Testes: `pytest` (39 testes, incluindo um Google Sheets/Drive simulado).

---

## 2. Configurar o Google (uma vez, ~15 min)

### 2.1 Planilha e pasta
1. Crie uma **planilha** vazia no Google Sheets. Copie o ID da URL: `docs.google.com/spreadsheets/d/`**`ESTE_TRECHO`**`/edit` → `SPREADSHEET_ID`.
2. Crie uma **pasta** no Google Drive para as imagens. Copie o final da URL: `drive.google.com/drive/folders/`**`ESTE_TRECHO`** → `DRIVE_FOLDER_ID`.
3. Ambas devem pertencer à **mesma conta Google** que você vai autorizar no passo 2.3.

### 2.2 Projeto no Google Cloud
1. Em <https://console.cloud.google.com> crie um projeto (ex.: `laads-site`).
2. **APIs e serviços → Biblioteca**: ative **Google Sheets API** e **Google Drive API**.
3. **Tela de permissão OAuth** (Google Auth Platform): tipo *Externo*, preencha nome e e-mail.
   **Importante:** depois publique o app (**"Publicar app" / status "Em produção"**). Em modo *Teste* o token expira em **7 dias** e o painel para de salvar.
   O aviso "app não verificado" na hora de autorizar é normal: é só você usando o próprio app (Avançado → continuar).
4. **Credenciais → Criar credenciais → ID do cliente OAuth → Tipo: App para computador.** Baixe o JSON e salve como `client_secret.json` na raiz (já está no `.gitignore`).

### 2.3 Gerar o token
```bash
python scripts/get_refresh_token.py --client-secret client_secret.json
```
Entre com a conta dona da planilha/pasta. O script imprime `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` e `GOOGLE_REFRESH_TOKEN`. Coloque no `.env`.

### 2.4 Criar as abas
```bash
python scripts/setup_sheets.py
```
(ou, depois, o botão **Inicializar planilha** no painel). Cria as abas e grava o conteúdo atual do site. Nunca apaga nada.

> **Por que OAuth e não conta de serviço?** Contas de serviço não têm cota no "Meu Drive" e falham ao enviar imagens. Elas funcionam para o Sheets e, no Drive, só em *Drives compartilhados* (Workspace). Se for o seu caso, use `GOOGLE_SERVICE_ACCOUNT_JSON` e compartilhe planilha/pasta com o e-mail da conta de serviço.

---

## 3. Publicar no Vercel

1. Suba o projeto para um repositório no GitHub (o `.env` e `client_secret.json` **não** vão: estão no `.gitignore`).
2. No Vercel: **Add New → Project →** importe o repositório. O Flask é detectado sozinho (`app.py`), sem build command.
3. **Settings → Environment Variables**: cadastre as mesmas variáveis do `.env`
   `SECRET_KEY`, `ADMIN_PASSWORD_HASH` (ou `ADMIN_PASSWORD`), `SPREADSHEET_ID`, `DRIVE_FOLDER_ID`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`.
4. **Deploy**. Acesse `https://seu-site.vercel.app/admin`.

No painel, a **Visão geral** mostra se Planilha e Drive estão conectados e explica qualquer erro.

---

## 4. Como usar o painel

| Menu | O que edita |
|---|---|
| **Site** | Logo, título/descrição para o Google, imagem de compartilhamento, nomes do menu, ligar/desligar seções |
| **Topo** | Título, textos, botões, imagem de fundo, números, painel técnico, console animado, faixa de palavras |
| **Eventos** | Textos da seção + cards de eventos (com capa opcional) |
| **Faça parte** | Textos, benefícios, opções de squad do formulário |
| **Quem somos** | Texto, números (com contagem animada), Missão/Visão/Valores |
| **Parcerias** | Chamada + logos de parceiros |
| **Contato** | Textos e canais (e-mail, Instagram, WhatsApp…) |
| **Recebidos** | Inscrições e mensagens do site (marcar como lido, excluir, baixar CSV) |
| **Arquivos** | Biblioteca de imagens do Drive |

- Em listas: **arraste** pela alça (ou use ▲▼) para reordenar; o interruptor oculta um item sem apagar.
- Imagens grandes são **reduzidas no navegador** antes do envio (o Vercel limita o corpo da requisição a ~4,5 MB).
- **Ver site** abre a página sem cache para conferir as mudanças na hora. Para o público, a CDN atualiza em até **1 minuto** (`PUBLIC_CACHE_SECONDS`).
- Você pode **editar a planilha direto**: linhas novas digitadas lá ganham `id` automaticamente ao abrir a lista no painel. Colunas: `ordem` (número), `ativo` (`SIM`/`NÃO`).

---

## 5. Estrutura do projeto

```
app.py                  entrada (o Vercel detecta a variável `app`)
laads/
  schema.py             TUDO que é editável: campos, listas, menu do painel  <- comece por aqui
  defaults.py           conteúdo original (fallback e dados iniciais)
  store.py              Google Sheets (REST) + armazenamento local p/ dev
  media.py              Google Drive + proxy /media/<id>
  content.py            monta o site a partir da planilha (cache + fallback)
  public.py / admin.py  rotas do site e do painel
  security.py           login, CSRF, limite de requisições
templates/              index.html (site) e admin/*
public/static/          css (compilado), js, imagens (o Vercel serve `public/` pela CDN)
assets/tailwind.css     fonte do CSS (tokens do design original)
scripts/                hash de senha, token OAuth, inicialização da planilha
tests/                  pytest
```

**Adicionar um campo editável:** crie um `F(...)` em `laads/schema.py`, use `{{ site.cfg.minha_chave }}` no template. O painel e a planilha passam a tê-lo automaticamente.
**Mudar o visual:** edite `templates/` e `assets/tailwind.css`, rode `npm install && npm run build:css` e faça commit do `public/static/css/site.css` (o Vercel não compila CSS).
**Novo ícone no seletor:** inclua o nome em `scripts/build_icons.mjs` e rode `npm run build:icons`.

---

## 6. Segurança e limites (bom saber)

- Senha do painel por variável de ambiente (ou hash), cookie de sessão `HttpOnly` + `Secure` + `SameSite`, **CSRF** em todas as ações, bloqueio após 8 tentativas de login/15 min.
- Tudo que visitantes enviam é gravado como **texto puro** no Sheets (nunca vira fórmula) e o CSV exportado neutraliza `=`, `+`, `-`, `@`.
- Links editáveis só aceitam `http(s)`, `mailto`, `tel`, `#âncora` e `/caminho` (bloqueia `javascript:`). Uploads são validados pelo conteúdo real (JPG/PNG/WebP/GIF; **SVG é recusado** de propósito).
- A rota `/media/<id>` só entrega arquivos que estão **dentro da pasta configurada**.
- CSP restritiva e cabeçalhos de segurança em todas as páginas.
- Limite anti-spam dos formulários (campo isca + 6 envios/10 min por IP) funciona em memória por instância: é "melhor esforço" no serverless. Para proteção forte, ative o Vercel Firewall/Bot Protection.
- Cota do Sheets: 60 leituras/min por usuário. O cache de 30 s no servidor + 60 s na CDN mantém o uso muito abaixo disso. Se o Google falhar, o site continua no ar com a última versão lida (ou o conteúdo padrão).

## 7. Problemas comuns

| Sintoma | Causa provável |
|---|---|
| Painel diz "refresh token expirado / invalid_grant" | App OAuth ainda em modo *Teste*: publique e gere novo token (passo 2.2.3) |
| "Planilha ou pasta não encontrada" | `SPREADSHEET_ID`/`DRIVE_FOLDER_ID` errados, ou a conta autorizada não é dona/editora |
| "Sem permissão (403)" | Sheets API/Drive API não ativadas no projeto do Google Cloud |
| Site mostra o conteúdo antigo | Cache de até 1 min na CDN; use **Ver site** no painel ou "Limpar cache" |
| Envio de imagem falha com conta de serviço | Contas de serviço não enviam para "Meu Drive": use OAuth (passo 2.3) |
| `/admin` diz para definir variável | Falta `SECRET_KEY` e/ou `ADMIN_PASSWORD` no Vercel (redeploy após cadastrar) |
