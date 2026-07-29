/* =============================================================
   STORAGE SERVICE
   ---------------------------------------------------------------
   A camada MAIS BAIXA de acesso a dados do sistema. É o ÚNICO
   arquivo que deve chamar `localStorage` / `sessionStorage`
   diretamente. Todo o resto do projeto (api.service.js,
   auth.service.js, backup.service.js, páginas HTML) deve passar
   por aqui, nunca acessar o storage do navegador diretamente.

   Por que isso importa:
   - Centraliza tratamento de erros (JSON inválido, quota cheia).
   - Se um dia o projeto migrar para Supabase/Firebase/MySQL/API
     REST, apenas este arquivo (e o api.service.js, que o usa)
     precisam mudar — nada mais no projeto depende de
     `localStorage` diretamente.
   ============================================================= */
(function (global) {
  'use strict';

  function safeParse(raw, fallback) {
    if (raw === null || raw === undefined) return fallback;
    try {
      return JSON.parse(raw);
    } catch (e) {
      console.error('[Storage] Falha ao interpretar dado salvo:', e);
      return fallback;
    }
  }

  // Detecta erro de "armazenamento cheio" nos navegadores mais comuns.
  function isQuotaExceeded(err) {
    return !!err && (
      err.name === 'QuotaExceededError' ||
      err.name === 'NS_ERROR_DOM_QUOTA_REACHED' ||
      err.code === 22 ||
      err.code === 1014
    );
  }

  function buildDriver(backend) {
    return {
      getItem(key, fallback = null) {
        try {
          const raw = backend.getItem(key);
          return safeParse(raw, fallback);
        } catch (e) {
          console.error('[Storage] Falha ao ler "' + key + '":', e);
          return fallback;
        }
      },

      // Retorna sempre { ok, error? } para quem chamou tratar de
      // forma amigável (nunca lança exceção para a UI).
      setItem(key, value) {
        try {
          backend.setItem(key, JSON.stringify(value));
          return { ok: true };
        } catch (e) {
          if (isQuotaExceeded(e)) {
            console.error('[Storage] Armazenamento cheio ao salvar "' + key + '".', e);
            return { ok: false, error: 'QUOTA_EXCEEDED' };
          }
          console.error('[Storage] Falha ao salvar "' + key + '":', e);
          return { ok: false, error: 'UNKNOWN' };
        }
      },

      removeItem(key) {
        try {
          backend.removeItem(key);
          return { ok: true };
        } catch (e) {
          console.error('[Storage] Falha ao remover "' + key + '":', e);
          return { ok: false, error: 'UNKNOWN' };
        }
      },
    };
  }

  const Storage = buildDriver(global.localStorage);
  // Sessão (login, contador de tentativas): mesmo tratamento de erros,
  // mas em sessionStorage, que já era o backend usado antes.
  Storage.session = buildDriver(global.sessionStorage);

  global.Laads = global.Laads || {};
  global.Laads.Storage = Storage;
})(window);
