/* =============================================================
   IMAGE SERVICE
   ---------------------------------------------------------------
   Valida e comprime imagens enviadas pelo painel administrativo
   (banners de evento, logos de patrocinador) antes de salvar.

   Regras:
   - Apenas PNG, JPG, JPEG, WEBP e SVG são aceitos.
   - Limite final de 2 MB por imagem.
   - Imagens raster (não-SVG) acima do limite são comprimidas
     automaticamente (redimensiona + reduz qualidade) até caber.
   - SVG não passa por canvas (é XML, não bitmap): só é validado
     quanto ao tamanho.
   ============================================================= */
(function (global) {
  'use strict';

  const MAX_BYTES = 2 * 1024 * 1024; // 2 MB
  const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/svg+xml'];
  const ALLOWED_EXT = ['png', 'jpg', 'jpeg', 'webp', 'svg'];

  function getExtension(filename) {
    const parts = String(filename || '').split('.');
    return parts.length > 1 ? parts.pop().toLowerCase() : '';
  }

  function isAllowed(file) {
    const ext = getExtension(file.name);
    const typeOk = !file.type || ALLOWED_TYPES.includes(file.type.toLowerCase());
    const extOk = ALLOWED_EXT.includes(ext);
    return typeOk && extOk;
  }

  function readAsDataUrl(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(reader.error || new Error('Falha ao ler o arquivo.'));
      reader.readAsDataURL(file);
    });
  }

  function dataUrlSizeBytes(dataUrl) {
    const base64 = String(dataUrl).split(',')[1] || '';
    return Math.ceil(base64.length * 3 / 4);
  }

  function loadImageElement(dataUrl) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error('Não foi possível carregar a imagem.'));
      img.src = dataUrl;
    });
  }

  // Reduz progressivamente qualidade/tamanho até caber em MAX_BYTES,
  // ou até esgotar as tentativas.
  async function compressRasterImage(originalDataUrl) {
    const img = await loadImageElement(originalDataUrl);
    let quality = 0.85;
    let scale = 1;
    let result = originalDataUrl;

    for (let attempt = 0; attempt < 6 && dataUrlSizeBytes(result) > MAX_BYTES; attempt++) {
      const width = Math.max(1, Math.round(img.width * scale));
      const height = Math.max(1, Math.round(img.height * scale));

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, width, height);

      result = canvas.toDataURL('image/jpeg', quality);
      quality = Math.max(0.4, quality - 0.15);
      scale = Math.max(0.4, scale - 0.15);
    }

    return result;
  }

  const ImageService = {
    MAX_BYTES,
    ALLOWED_EXT,

    validate(file) {
      if (!file) return { ok: false, error: 'Nenhum arquivo selecionado.' };
      if (!isAllowed(file)) {
        return { ok: false, error: 'Formato não suportado. Envie PNG, JPG, JPEG, WEBP ou SVG.' };
      }
      return { ok: true };
    },

    // Lê, valida e (para raster) comprime o arquivo até 2 MB, devolvendo
    // uma data URL pronta para pré-visualização e armazenamento.
    async process(file) {
      const validation = ImageService.validate(file);
      if (!validation.ok) throw new Error(validation.error);

      const isSvg = getExtension(file.name) === 'svg' || file.type === 'image/svg+xml';
      let dataUrl = await readAsDataUrl(file);

      if (isSvg) {
        if (dataUrlSizeBytes(dataUrl) > MAX_BYTES) {
          throw new Error('O arquivo SVG excede o limite de 2 MB.');
        }
        return dataUrl;
      }

      if (dataUrlSizeBytes(dataUrl) > MAX_BYTES) {
        dataUrl = await compressRasterImage(dataUrl);
        if (dataUrlSizeBytes(dataUrl) > MAX_BYTES) {
          throw new Error('Não foi possível reduzir a imagem abaixo de 2 MB. Tente uma imagem menor.');
        }
      }

      return dataUrl;
    },
  };

  global.Laads = global.Laads || {};
  global.Laads.ImageService = ImageService;
})(window);
