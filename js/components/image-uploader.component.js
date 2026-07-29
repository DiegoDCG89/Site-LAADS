/* =============================================================
   IMAGE UPLOADER COMPONENT
   ---------------------------------------------------------------
   Conecta um <input type="file"> a validação + compressão
   (Laads.ImageService) e a uma pré-visualização <img>, reaproveitado
   tanto para a imagem do evento quanto para a logo do patrocinador.
   ============================================================= */
(function (global) {
  'use strict';

  const ImageService = global.Laads.ImageService;
  const Toast = global.Laads.Toast;

  // options: { inputId, previewId, onChange(dataUrl) }
  function bindImageInput(options) {
    const input = document.getElementById(options.inputId);
    const preview = document.getElementById(options.previewId);
    if (!input) return;

    input.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      try {
        const dataUrl = await ImageService.process(file);
        if (preview) preview.src = dataUrl;
        if (typeof options.onChange === 'function') options.onChange(dataUrl);
      } catch (err) {
        Toast.error(err.message || 'Não foi possível processar a imagem.');
        input.value = '';
      }
    });
  }

  global.Laads = global.Laads || {};
  global.Laads.ImageUploader = { bindImageInput };
})(window);
