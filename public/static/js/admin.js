/* Painel LaADS: interações (menu, ícones, imagens, ordenação, confirmações). */
(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const csrf = ($('meta[name="csrf-token"]') || {}).content || "";

  async function api(url, opts = {}) {
    const res = await fetch(url, {
      ...opts,
      headers: { "X-CSRF-Token": csrf, ...(opts.body && !(opts.body instanceof FormData) ? { "Content-Type": "application/json" } : {}), ...(opts.headers || {}) },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Erro " + res.status);
    return data;
  }

  /* ---------- Menu lateral (mobile) ---------- */
  (() => {
    const side = $("[data-sidebar]"), back = $("[data-sidebar-backdrop]");
    if (!side) return;
    const set = (open) => {
      side.classList.toggle("-translate-x-full", !open);
      back.classList.toggle("hidden", !open);
    };
    $$("[data-sidebar-open]").forEach((b) => b.addEventListener("click", () => set(true)));
    $$("[data-sidebar-close]").forEach((b) => b.addEventListener("click", () => set(false)));
    back.addEventListener("click", () => set(false));
  })();

  /* ---------- Confirmações ---------- */
  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-confirm]");
    if (el && !window.confirm(el.getAttribute("data-confirm"))) e.preventDefault();
  });

  /* ---------- Contador de caracteres ---------- */
  $$("[data-counter]").forEach((input) => {
    const max = parseInt(input.dataset.counter, 10);
    const hint = document.createElement("p");
    hint.className = "help text-right";
    input.insertAdjacentElement("afterend", hint);
    const upd = () => {
      const n = input.value.length;
      hint.textContent = n + " / " + max;
      hint.style.color = n > max ? "var(--destructive)" : "";
      hint.hidden = n < max * 0.6;
    };
    input.addEventListener("input", upd); upd();
  });

  /* ---------- Aviso de alterações não salvas ---------- */
  $$("form[data-dirty-guard]").forEach((form) => {
    let dirty = false, submitting = false;
    const label = $("[data-dirty-label]", form);
    const mark = () => { dirty = true; if (label) label.textContent = "Alterações não salvas"; };
    form.addEventListener("input", mark);
    form.addEventListener("change", mark);
    form.addEventListener("submit", () => { submitting = true; });
    form.addEventListener("admin:changed", mark);
    window.addEventListener("beforeunload", (e) => { if (dirty && !submitting) { e.preventDefault(); e.returnValue = ""; } });
  });

  /* ---------- Diálogos ---------- */
  $$("dialog").forEach((d) => {
    d.addEventListener("click", (e) => { if (e.target === d) d.close(); });
    $$("[data-dialog-close]", d).forEach((b) => b.addEventListener("click", () => d.close()));
  });

  /* ---------- Seletor de ícones ---------- */
  (() => {
    const dlg = $("#icon-dialog");
    let current = null;
    $$("[data-icon-field]").forEach((box) => {
      $("[data-icon-open]", box).addEventListener("click", () => { current = box; dlg.showModal(); });
    });
    if (!dlg) return;
    $$("[data-icon-pick]", dlg).forEach((btn) => btn.addEventListener("click", () => {
      if (!current) return;
      const name = btn.dataset.iconPick;
      $("input", current).value = name;
      $("[data-icon-name]", current).textContent = name;
      $("[data-icon-preview]", current).innerHTML = btn.innerHTML.replace("h-5 w-5", "h-4 w-4");
      current.closest("form")?.dispatchEvent(new Event("admin:changed"));
      dlg.close();
    }));
  })();

  /* ---------- Imagens: preparar (reduzir), enviar, biblioteca ---------- */
  const MAX_SIDE = 1920, LIMIT = 3_600_000;

  async function prepare(file) {
    if (file.type === "image/gif") return file;
    let bmp;
    try { bmp = await createImageBitmap(file); } catch (_) { return file; }
    const longest = Math.max(bmp.width, bmp.height);
    if (longest <= MAX_SIDE && file.size <= 2_500_000) return file;
    const keepAlpha = file.type === "image/png" || file.type === "image/webp";
    let scale = Math.min(1, MAX_SIDE / longest);
    for (let i = 0; i < 5; i++) {
      const c = document.createElement("canvas");
      c.width = Math.max(1, Math.round(bmp.width * scale));
      c.height = Math.max(1, Math.round(bmp.height * scale));
      c.getContext("2d").drawImage(bmp, 0, 0, c.width, c.height);
      const blob = await new Promise((ok) => c.toBlob(ok, keepAlpha ? "image/png" : "image/jpeg", 0.86));
      if (blob && blob.size <= LIMIT) {
        const ext = keepAlpha ? "png" : "jpg";
        return new File([blob], file.name.replace(/\.[^.]+$/, "") + "." + ext, { type: blob.type });
      }
      scale *= 0.75;
    }
    throw new Error("Não foi possível reduzir a imagem o bastante. Tente uma menor.");
  }

  async function upload(file, statusEl) {
    statusEl.textContent = "Preparando…";
    const ready = await prepare(file);
    if (ready.size > LIMIT + 300_000) throw new Error("Imagem maior que 4 MB.");
    statusEl.textContent = "Enviando " + Math.round(ready.size / 1024) + " KB para o Drive…";
    const fd = new FormData();
    fd.append("file", ready);
    return api("/admin/api/upload", { method: "POST", body: fd });
  }

  function setImage(box, id, url) {
    const input = $('input[type="hidden"]', box), img = $("[data-img-preview]", box);
    const empty = $("[data-img-empty]", box), clear = $("[data-img-clear]", box);
    input.value = id || "";
    const show = url || box.dataset.default || "";
    img.hidden = !show; if (show) img.src = show;
    if (empty) empty.hidden = !!show;
    if (clear) clear.hidden = !id;
    box.closest("form")?.dispatchEvent(new Event("admin:changed"));
  }

  const mediaDlg = $("#media-dialog");
  let libTarget = null;

  async function openLibrary(box) {
    libTarget = box;
    const grid = $("[data-media-grid]", mediaDlg), st = $("[data-media-status]", mediaDlg);
    grid.innerHTML = ""; st.textContent = "Carregando…";
    mediaDlg.showModal();
    try {
      const { files } = await api("/admin/api/midia");
      st.textContent = files.length ? "Clique em uma imagem para usá-la." : "Nenhuma imagem enviada ainda.";
      files.forEach((f) => {
        const b = document.createElement("button");
        b.type = "button";
        b.className = "aspect-square overflow-hidden rounded-md border border-border bg-secondary/40 hover:border-electric";
        const im = document.createElement("img");
        im.src = f.url; im.alt = f.name; im.loading = "lazy"; im.className = "h-full w-full object-contain";
        b.appendChild(im);
        b.addEventListener("click", () => { setImage(libTarget, f.id, f.url); mediaDlg.close(); });
        grid.appendChild(b);
      });
    } catch (err) { st.textContent = err.message; }
  }

  $$("[data-img-field]").forEach((box) => {
    const file = $("[data-img-file]", box), st = $("[data-img-status]", box);
    const standalone = box.hasAttribute("data-standalone");
    $("[data-img-upload]", box).addEventListener("click", () => file.click());
    const lib = $("[data-img-library]", box);
    if (lib) lib.addEventListener("click", () => openLibrary(box));
    const clear = $("[data-img-clear]", box);
    if (clear) clear.addEventListener("click", () => { setImage(box, "", ""); st.textContent = ""; });
    file.addEventListener("change", async () => {
      const f = file.files[0];
      if (!f) return;
      try {
        const r = await upload(f, st);
        if (standalone) { location.reload(); return; }
        setImage(box, r.id, r.url);
        st.textContent = "Imagem enviada. Clique em salvar para publicar.";
      } catch (err) { st.textContent = err.message; }
      file.value = "";
    });
  });

  /* ---------- Biblioteca: excluir ---------- */
  $$("[data-media-delete]").forEach((btn) => btn.addEventListener("click", async () => {
    if (!confirm("Excluir esta imagem? Se algum campo do site a usa, a imagem deixará de aparecer. (Ela vai para a lixeira do Drive.)")) return;
    btn.disabled = true;
    try { await api(btn.dataset.url, { method: "POST" }); btn.closest("li").remove(); }
    catch (err) { alert(err.message); btn.disabled = false; }
  }));

  /* ---------- Listas: ordenar e ativar/desativar ---------- */
  $$("[data-sortable]").forEach((ul) => {
    const status = $("[data-sort-status]");
    const say = (m, bad) => { if (status) { status.textContent = m; status.style.color = bad ? "var(--destructive)" : ""; } };
    const save = async () => {
      const ids = $$("li[data-id]", ul).map((li) => li.dataset.id);
      say("Salvando ordem…");
      try { await api(ul.dataset.orderUrl, { method: "POST", body: JSON.stringify({ ids }) }); say("Ordem salva."); }
      catch (err) { say(err.message, true); }
    };
    let dragging = null;
    ul.addEventListener("dragstart", (e) => {
      dragging = e.target.closest("li[data-id]");
      if (!dragging) return;
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", dragging.dataset.id);
      setTimeout(() => dragging && dragging.classList.add("opacity-40"), 0);
    });
    ul.addEventListener("dragover", (e) => {
      if (!dragging) return;
      e.preventDefault();
      const others = $$("li[data-id]:not(.opacity-40)", ul);
      const after = others.find((li) => e.clientY < li.getBoundingClientRect().top + li.offsetHeight / 2);
      ul.insertBefore(dragging, after || null);
    });
    ul.addEventListener("dragend", () => {
      if (!dragging) return;
      dragging.classList.remove("opacity-40"); dragging = null; save();
    });
    ul.addEventListener("click", (e) => {
      const mv = e.target.closest("[data-move]");
      if (!mv) return;
      const li = mv.closest("li[data-id]");
      if (mv.dataset.move === "up" && li.previousElementSibling) ul.insertBefore(li, li.previousElementSibling);
      else if (mv.dataset.move === "down" && li.nextElementSibling) ul.insertBefore(li.nextElementSibling, li);
      else return;
      save();
    });
    ul.addEventListener("change", async (e) => {
      const t = e.target.closest("[data-toggle]");
      if (!t) return;
      const li = t.closest("li[data-id]");
      const url = ul.dataset.toggleUrl.replace("__ID__", li.dataset.id);
      try {
        await api(url, { method: "POST", body: JSON.stringify({ ativo: t.checked }) });
        li.classList.toggle("opacity-60", !t.checked);
        say(t.checked ? "Item visível no site." : "Item oculto do site.");
      } catch (err) { t.checked = !t.checked; say(err.message, true); }
    });
  });
})();
