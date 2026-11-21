// Gera laads/icons.json com o miolo (paths) dos ícones Lucide usados no site e no seletor do painel.
// Para adicionar um ícone: inclua o nome (kebab-case) na lista abaixo e rode `npm run build:icons`.
import { readFileSync, writeFileSync } from "node:fs";

const NAMES = [
  // usados no site original
  "calendar", "code-xml", "award", "briefcase", "mail", "instagram", "map-pin", "target", "eye",
  "heart", "menu", "x", "arrow-right", "terminal", "cpu", "radio", "zap", "chevron-up", "radar",
  // extras para o seletor do painel
  "github", "linkedin", "youtube", "twitter", "facebook", "globe", "phone", "message-circle",
  "users", "user", "book-open", "graduation-cap", "rocket", "lightbulb", "star", "trophy",
  "shield-check", "database", "server", "cloud", "smartphone", "monitor", "laptop", "git-branch",
  "bug", "brain", "sparkles", "flag", "handshake", "building-2", "clock", "link", "send",
  "megaphone", "puzzle", "layers", "palette", "wrench", "settings", "lock", "mic", "video",
  "camera", "coffee", "gift", "thumbs-up", "check", "circle-check", "info", "bell", "house",
  "map", "navigation", "file-text", "download", "external-link", "calendar-days", "ticket",
  "network", "bot", "plus", "chart-no-axes-column", "code", "layout-dashboard", "life-buoy", "compass",
];

const icons = {};
for (const name of NAMES) {
  const svg = readFileSync(`node_modules/lucide-static/icons/${name}.svg`, "utf8");
  const inner = svg
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/^[\s\S]*?<svg[^>]*>/, "")
    .replace(/<\/svg>\s*$/, "")
    .replace(/\s+/g, " ")
    .trim();
  icons[name] = inner;
}
writeFileSync("laads/icons.json", JSON.stringify(icons, null, 0));
console.log(`${Object.keys(icons).length} ícones gravados em laads/icons.json`);
