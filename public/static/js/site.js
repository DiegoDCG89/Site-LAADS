/* LaADS: comportamento do site público (porta dos componentes React originais para JS puro). */
(() => {
  "use strict";
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ---------- Reveal: aparece ao entrar na tela ---------- */
  (() => {
    const els = $$("[data-reveal]");
    if (reduced || !("IntersectionObserver" in window)) {
      els.forEach((el) => el.setAttribute("data-shown", "true"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => {
        if (e.isIntersecting) { e.target.setAttribute("data-shown", "true"); io.unobserve(e.target); }
      }),
      { threshold: 0.15, rootMargin: "0px 0px -8% 0px" }
    );
    els.forEach((el) => io.observe(el));
  })();

  /* ---------- Typewriter ---------- */
  $$("[data-typewriter]").forEach((el) => {
    const text = el.getAttribute("data-typewriter") || "";
    if (reduced) return;
    el.textContent = "";
    let i = 0;
    const tick = () => {
      i += 1;
      el.textContent = text.slice(0, i);
      if (i < text.length) setTimeout(tick, 45);
    };
    setTimeout(tick, 200);
  });

  /* ---------- Console: linhas surgindo uma a uma ---------- */
  $$("[data-console]").forEach((box) => {
    const lines = $$("[data-console-line]", box);
    if (reduced) return;
    lines.forEach((l) => (l.hidden = true));
    let n = 0;
    const id = setInterval(() => {
      if (n >= lines.length) return clearInterval(id);
      lines[n++].hidden = false;
    }, 420);
  });

  /* ---------- CountUp ---------- */
  $$("[data-countup]").forEach((el) => {
    const to = parseInt(el.getAttribute("data-countup"), 10);
    const suffix = el.getAttribute("data-suffix") || "";
    if (reduced || Number.isNaN(to) || !("IntersectionObserver" in window)) return;
    el.textContent = "0" + suffix;
    const io = new IntersectionObserver((entries) => {
      if (!entries[0].isIntersecting) return;
      io.disconnect();
      const start = performance.now();
      const tick = (now) => {
        const t = Math.min(1, (now - start) / 1400);
        el.textContent = Math.round(to * (1 - Math.pow(1 - t, 3))) + suffix;
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }, { threshold: 0.4 });
    io.observe(el);
  });

  /* ---------- NeuralCanvas: malha de partículas ---------- */
  $$("canvas[data-neural]").forEach((canvas) => {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const css = getComputedStyle(document.documentElement);
    const gold = (css.getPropertyValue("--primary") || "#e6c26a").trim();
    const cyan = (css.getPropertyValue("--electric") || "#67e8f9").trim();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const link = 138;
    const pointer = { x: -9999, y: -9999 };
    let w = 0, h = 0, parts = [], frame = 0, visible = true;

    const build = () => {
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = Math.max(1, Math.floor(w * dpr));
      canvas.height = Math.max(1, Math.floor(h * dpr));
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.max(26, Math.min(78, Math.round((w * h) / 24000)));
      parts = Array.from({ length: count }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.26, vy: (Math.random() - 0.5) * 0.26,
        r: Math.random() * 1.6 + 0.7, gold: Math.random() > 0.6,
      }));
    };
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      for (let i = 0; i < parts.length; i++) {
        const p = parts[i];
        for (let j = i + 1; j < parts.length; j++) {
          const q = parts[j];
          const d = Math.hypot(p.x - q.x, p.y - q.y);
          if (d < link) {
            ctx.globalAlpha = (1 - d / link) * 0.3;
            ctx.strokeStyle = p.gold || q.gold ? gold : cyan;
            ctx.lineWidth = 0.6;
            ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
          }
        }
        const pd = Math.hypot(p.x - pointer.x, p.y - pointer.y);
        if (pd < 190) {
          ctx.globalAlpha = (1 - pd / 190) * 0.55;
          ctx.strokeStyle = cyan; ctx.lineWidth = 0.9;
          ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(pointer.x, pointer.y); ctx.stroke();
        }
        ctx.globalAlpha = 0.9;
        ctx.fillStyle = p.gold ? gold : cyan;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = 1;
    };
    const step = () => {
      if (visible) {
        for (const p of parts) {
          p.x += p.vx; p.y += p.vy;
          if (p.x < 0 || p.x > w) p.vx *= -1;
          if (p.y < 0 || p.y > h) p.vy *= -1;
        }
        draw();
      }
      frame = requestAnimationFrame(step);
    };
    build();
    if (reduced) { draw(); }
    else {
      frame = requestAnimationFrame(step);
      window.addEventListener("pointermove", (e) => {
        const b = canvas.getBoundingClientRect();
        pointer.x = e.clientX - b.left; pointer.y = e.clientY - b.top;
      }, { passive: true });
      if ("IntersectionObserver" in window) {  // pausa quando fora da tela (economiza bateria)
        new IntersectionObserver((en) => { visible = en[0].isIntersecting; }).observe(canvas);
      }
    }
    window.addEventListener("resize", () => { build(); draw(); });
  });

  /* ---------- Boot: tela de abertura ---------- */
  (() => {
    const boot = $("#boot");
    if (!boot || reduced) return;
    let lines = [];
    try { lines = JSON.parse(boot.getAttribute("data-lines") || "[]"); } catch (_) { return; }
    const box = $("[data-boot-lines]", boot), bar = $("[data-boot-bar]", boot), pct = $("[data-boot-pct]", boot);
    boot.hidden = false;
    lines.forEach((text, i) => setTimeout(() => {
      const p = document.createElement("p");
      p.className = "py-0.5 text-muted-foreground";
      const mark = document.createElement("span");
      mark.className = "text-primary";
      mark.textContent = "> ";
      p.append(mark, document.createTextNode(text));
      box.appendChild(p);
      const v = (i + 1) / lines.length;
      bar.style.width = v * 100 + "%";
      pct.textContent = Math.round(v * 100) + "%";
    }, 170 * (i + 1)));
    setTimeout(() => { boot.hidden = true; }, 1500);
  })();

  /* ---------- HUD: progresso de rolagem e relógio ---------- */
  (() => {
    const line = $("[data-progress-line]"), rail = $("[data-progress-rail]"), pct = $("[data-progress-pct]");
    const onScroll = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const p = max > 0 ? Math.min(1, window.scrollY / max) : 0;
      if (line) line.style.width = p * 100 + "%";
      if (rail) rail.style.height = p * 100 + "%";
      if (pct) pct.textContent = String(Math.round(p * 100)).padStart(3, "0") + "%";
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    const clock = $("[data-clock]");
    if (clock) {
      const tick = () => { clock.textContent = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" }); };
      tick(); setInterval(tick, 1000);
    }
  })();

  /* ---------- Menu: seção ativa + versão mobile ---------- */
  (() => {
    const links = $$("[data-nav-link]");
    if (links.length && "IntersectionObserver" in window) {
      const mark = (id) => links.forEach((a) => a.setAttribute("data-active", String(a.dataset.navLink === id)));
      mark(links[0].dataset.navLink);
      const io = new IntersectionObserver((entries) => {
        const v = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (v && v.target.id) mark(v.target.id);
      }, { threshold: [0.25, 0.5, 0.75], rootMargin: "-20% 0px -55% 0px" });
      links.forEach((a) => { const s = document.getElementById(a.dataset.navLink); if (s) io.observe(s); });
    }
    const toggle = $("[data-menu-toggle]"), menu = $("#mobile-menu");
    if (!toggle || !menu) return;
    const set = (open) => {
      menu.hidden = !open;
      toggle.setAttribute("aria-expanded", String(open));
      $("[data-menu-open]", toggle).hidden = open;
      $("[data-menu-close]", toggle).hidden = !open;
    };
    toggle.addEventListener("click", () => set(menu.hidden));
    $$("[data-menu-link]", menu).forEach((a) => a.addEventListener("click", () => set(false)));
  })();

  /* ---------- Formulários (envio sem recarregar a página) ---------- */
  $$("form[data-ajax-form]").forEach((form) => {
    const status = $("[data-form-status]", form);
    const btn = $("[data-submit]", form);
    const label = btn.textContent;
    const say = (msg, bad) => {
      status.textContent = msg;
      status.classList.toggle("text-primary", !bad);
      status.classList.toggle("text-destructive", !!bad);
    };
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      if (!form.reportValidity()) return;
      btn.disabled = true; btn.textContent = "enviando…"; say("", false);
      try {
        const res = await fetch(form.action, {
          method: "POST", body: new FormData(form), headers: { "X-Requested-With": "fetch" },
        });
        const data = await res.json().catch(() => ({}));
        if (res.ok && data.ok) {
          form.reset();
          say("> " + (form.dataset.success || "enviado com sucesso."), false);
        } else {
          const msgs = Object.values(data.errors || {});
          say(msgs.length ? msgs.join(" ") : "Não foi possível enviar agora. Tente novamente.", true);
        }
      } catch (_) {
        say("Sem conexão. Verifique sua internet e tente de novo.", true);
      } finally {
        btn.disabled = false; btn.textContent = label;
      }
    });
  });
})();
