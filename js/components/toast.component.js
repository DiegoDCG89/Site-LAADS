/* =============================================================
   TOAST COMPONENT
   ---------------------------------------------------------------
   Notificações amigáveis (sucesso, erro, informação) no canto da
   tela. Cria o elemento #toast automaticamente se a página ainda
   não tiver um (mantém compatibilidade com o markup existente,
   que já define <div id="toast" class="toast">).
   ============================================================= */
(function (global) {
  'use strict';

  function ensureToastElement() {
    let toast = document.getElementById('toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'toast';
      toast.className = 'toast';
      document.body.appendChild(toast);
    }
    return toast;
  }

  const VARIANT_STYLES = {
    success: { border: '#FFD166', color: '#FFD166' },
    error: { border: '#ff8a8a', color: '#ff8a8a' },
    info: { border: '#8A93B2', color: '#E8EDF9' },
  };

  let hideTimer = null;

  const Toast = {
    show(message, variant, duration) {
      const toast = ensureToastElement();
      const style = VARIANT_STYLES[variant] || VARIANT_STYLES.success;
      toast.textContent = message;
      toast.style.borderColor = style.border;
      toast.style.color = style.color;
      toast.classList.add('show');
      clearTimeout(hideTimer);
      hideTimer = setTimeout(() => toast.classList.remove('show'), duration || 3200);
    },
    success(message) { Toast.show(message, 'success'); },
    error(message) { Toast.show(message, 'error'); },
    info(message) { Toast.show(message, 'info'); },
  };

  global.Laads = global.Laads || {};
  global.Laads.Toast = Toast;
})(window);
