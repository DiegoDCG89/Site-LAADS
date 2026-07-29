/* =============================================================
   AUTH SERVICE
   ---------------------------------------------------------------
   Login local do painel administrativo. A senha em si NUNCA é
   armazenada — apenas o hash SHA-256 (Web Crypto API), calculado
   aqui. Também controla sessão (sessionStorage) e um limitador
   simples de tentativas de login.
   ============================================================= */
(function (global) {
  'use strict';

  const Api = global.Laads.Api;
  const Storage = global.Laads.Storage;

  const SESSION_KEY = 'laads_admin_session_v1';
  const LOGIN_ATTEMPTS_KEY = 'laads_admin_login_attempts_v1';

  /* Credencial padrão de fábrica do painel: usuário "root" / senha "Superoot".
     Só é usada enquanto NENHUM usuário próprio tiver sido cadastrado ainda
     (ou seja, enquanto Api.getCredentials() não retornar nada salvo). Assim
     que alguém troca as credenciais pela seção "Segurança" dentro do painel,
     essa credencial padrão deixa de funcionar — o valor salvo em
     Api.getCredentials() sempre tem prioridade.

     Guardamos aqui apenas o HASH SHA-256 da senha padrão (nunca o texto
     puro), pelo mesmo motivo de nunca guardarmos a senha do usuário em
     texto puro: hash("Superoot") = a419a20704323faefd5f2bcdb495cc76a4b3be9
     4294a0b56cc9eaa0241e5f7fd. */
  const DEFAULT_CREDENTIALS = {
    username: 'root',
    passHash: 'a419a20704323faefd5f2bcdb495cc76a4b3be94294a0b56cc9eaa0241e5f7fd',
  };

  async function sha256Hex(text) {
    const bytes = new TextEncoder().encode(text);
    const digest = await crypto.subtle.digest('SHA-256', bytes);
    return Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2, '0')).join('');
  }

  /* Credenciais "efetivas": as salvas pelo usuário (via Segurança), ou,
     na ausência delas, a credencial padrão de fábrica. */
  async function getEffectiveCredentials() {
    const stored = await Api.getCredentials();
    return stored || DEFAULT_CREDENTIALS;
  }

  const Auth = {
    async hasCredentials() {
      const creds = await Api.getCredentials();
      return !!creds;
    },

    /* Cadastro/troca de usuário e senha só pode acontecer de DENTRO do
       painel (seção "Segurança", já autenticado) — não existe mais uma
       tela pública de "primeiro acesso". */
    async updateCredentials(username, password) {
      const passHash = await sha256Hex(password);
      await Api.setCredentials({ username, passHash });
    },

    async verifyLogin(username, password) {
      const creds = await getEffectiveCredentials();
      const hash = await sha256Hex(password);
      return username === creds.username && hash === creds.passHash;
    },

    startSession() { Storage.session.setItem(SESSION_KEY, '1'); },
    hasSession() { return Storage.session.getItem(SESSION_KEY, null) === '1'; },
    endSession() { Storage.session.removeItem(SESSION_KEY); },

    /* ---- Limite de tentativas de login (mitigação simples de força bruta) ----
       Como este é um site estático sem backend, este controle roda inteiramente
       no navegador de quem tenta logar — não impede um ataque automatizado feito
       fora do navegador, mas evita tentativas repetidas via formulário e dá um
       atrito básico. Para proteção real, um backend com limite por IP é necessário. */
    getLoginAttempts() {
      return Storage.session.getItem(LOGIN_ATTEMPTS_KEY, { count: 0, lockUntil: 0 });
    },
    setLoginAttempts(data) { Storage.session.setItem(LOGIN_ATTEMPTS_KEY, data); },
    resetLoginAttempts() { Auth.setLoginAttempts({ count: 0, lockUntil: 0 }); },

    // Registra uma falha e devolve o timestamp (ms) até quando o login
    // fica bloqueado (0 se ainda não atingiu o limite).
    registerFailedAttempt() {
      const { count } = Auth.getLoginAttempts();
      const nextCount = count + 1;
      let lockMs = 0;
      if (nextCount >= 12) lockMs = 5 * 60 * 1000;
      else if (nextCount >= 8) lockMs = 60 * 1000;
      else if (nextCount >= 5) lockMs = 15 * 1000;
      const lockUntil = lockMs ? Date.now() + lockMs : 0;
      Auth.setLoginAttempts({ count: nextCount, lockUntil });
      return lockUntil;
    },
  };

  global.Laads = global.Laads || {};
  global.Laads.Auth = Auth;
})(window);
