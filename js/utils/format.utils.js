/* =============================================================
   FORMAT UTILS
   ---------------------------------------------------------------
   Máscara de telefone e padrões de validação usados nos
   formulários públicos (index.html).
   ============================================================= */
(function (global) {
  'use strict';

  // Aplica a máscara (XX) X XXXX-XXXX enquanto o usuário digita.
  function maskPhone(input) {
    let digits = input.value.replace(/\D/g, '').slice(0, 11);
    let out = '';
    if (digits.length > 0) out = '(' + digits.slice(0, 2);
    if (digits.length >= 2) out += ') ';
    if (digits.length >= 3) out += digits.slice(2, 3) + ' ';
    if (digits.length >= 3) out += digits.slice(3, 7);
    if (digits.length >= 8) out += '-' + digits.slice(7, 11);
    input.value = out;
  }

  const PHONE_PATTERN = /^\(\d{2}\) \d \d{4}-\d{4}$/;
  const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  global.Laads = global.Laads || {};
  global.Laads.FormatUtils = { maskPhone, PHONE_PATTERN, EMAIL_PATTERN };
})(window);
