/* =============================================================
   BACKUP SERVICE
   ---------------------------------------------------------------
   Exporta e importa um backup completo do sistema (eventos,
   inscrições, patrocinadores, squads, credenciais de usuário,
   mensagens e configurações) como um único arquivo JSON.

   A importação sempre valida a estrutura do arquivo antes de
   aplicar, e quem chama `apply()` é responsável por pedir
   confirmação ao usuário antes (ver admin.html), já que a
   operação substitui os dados atuais.
   ============================================================= */
(function (global) {
  'use strict';

  const Api = global.Laads.Api;
  const BACKUP_VERSION = 1;
  const REQUIRED_KEYS = ['events', 'sponsors', 'squads', 'signups', 'messages', 'credentials', 'settings'];
  const REQUIRED_ARRAY_KEYS = ['events', 'sponsors', 'squads', 'signups', 'messages'];

  const Backup = {
    async build() {
      const [events, sponsors, squads, signups, messages, credentials, settings] = await Promise.all([
        Api.getEvents(),
        Api.getSponsors(),
        Api.getSquads(),
        Api.getSignups(),
        Api.getMessages(),
        Api.getCredentials(),
        Api.getSettings(),
      ]);

      return {
        app: 'LaADS',
        version: BACKUP_VERSION,
        exportedAt: new Date().toISOString(),
        data: { events, sponsors, squads, signups, messages, credentials, settings },
      };
    },

    // Validação estrutural básica — não confia cegamente no arquivo importado.
    validate(parsed) {
      if (!parsed || typeof parsed !== 'object') {
        return { ok: false, error: 'Arquivo inválido: JSON malformado.' };
      }
      if (!parsed.data || typeof parsed.data !== 'object') {
        return { ok: false, error: 'Arquivo inválido: estrutura de dados ausente.' };
      }
      const missing = REQUIRED_KEYS.filter(key => !(key in parsed.data));
      if (missing.length) {
        return { ok: false, error: 'Arquivo inválido: faltam os campos "' + missing.join('", "') + '".' };
      }
      const notArrays = REQUIRED_ARRAY_KEYS.filter(key => !Array.isArray(parsed.data[key]));
      if (notArrays.length) {
        return { ok: false, error: 'Arquivo inválido: os campos "' + notArrays.join('", "') + '" deveriam ser listas.' };
      }
      return { ok: true };
    },

    async parseFile(file) {
      let text;
      try {
        text = await file.text();
      } catch (e) {
        return { ok: false, error: 'Não foi possível ler o arquivo selecionado.' };
      }

      let parsed;
      try {
        parsed = JSON.parse(text);
      } catch (e) {
        return { ok: false, error: 'O arquivo selecionado não é um JSON válido.' };
      }

      const check = Backup.validate(parsed);
      if (!check.ok) return check;
      return { ok: true, backup: parsed };
    },

    // Substitui todos os dados do sistema pelos do backup. Quem chama deve
    // ter confirmado com o usuário antes (a substituição é irreversível
    // sem um backup anterior).
    async apply(backup) {
      const { data } = backup;
      const results = await Promise.all([
        Api.setEvents(data.events),
        Api.setSponsors(data.sponsors),
        Api.setSquads(data.squads),
        Api.setSignups(data.signups),
        Api.setMessages(data.messages),
        data.credentials ? Api.setCredentials(data.credentials) : Promise.resolve({ ok: true }),
        data.settings ? Api.setSettings(data.settings) : Promise.resolve({ ok: true }),
      ]);
      const failed = results.find(r => r && r.ok === false);
      return failed || { ok: true };
    },

    download(backup) {
      const json = JSON.stringify(backup, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'backup-laads-' + new Date().toISOString().slice(0, 10) + '.json';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },
  };

  global.Laads = global.Laads || {};
  global.Laads.Backup = Backup;
})(window);
