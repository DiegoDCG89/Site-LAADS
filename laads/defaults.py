"""Conteúdo inicial das listas = exatamente o que o site original (index.tsx) exibia.

Usado em dois momentos:
1. Enquanto a planilha não está configurada ou a aba ainda não existe, o site mostra isto.
2. Ao "Inicializar planilha" (painel ou scripts/setup_sheets.py), estas linhas são gravadas nas abas.
"""
from __future__ import annotations

DEFAULT_ROWS: dict[str, list[dict[str, str]]] = {
    "eventos": [
        {"data": "05 DEZ", "tipo": "Workshop", "titulo": "React do zero ao deploy",
         "local": "Lab 3 · 19h", "vagas": "32 vagas", "link": "#faca-parte", "imagem": ""},
        {"data": "12 DEZ", "tipo": "Palestra", "titulo": "Carreira em tecnologia: do estágio ao sênior",
         "local": "Auditório · 20h", "vagas": "120 vagas", "link": "#faca-parte", "imagem": ""},
        {"data": "20 JAN", "tipo": "Hackathon", "titulo": "LaADS Hack 24h",
         "local": "Bloco de Tecnologia", "vagas": "60 vagas", "link": "#faca-parte", "imagem": ""},
    ],
    "stats_hero": [
        {"valor": "180+", "rotulo": "membros"},
        {"valor": "40+", "rotulo": "projetos"},
        {"valor": "12", "rotulo": "parceiros"},
    ],
    "hud_metrics": [
        {"rotulo": "latência", "valor": "12ms"},
        {"rotulo": "uptime", "valor": "99.9%"},
        {"rotulo": "squads", "valor": "08"},
        {"rotulo": "versão", "valor": "2026.11"},
    ],
    "console": [
        {"texto": "$ laads init --turma 2026"},
        {"texto": "> modulos carregados: eventos · mentoria · squads"},
        {"texto": "> parcerias ativas: 12 empresas conectadas"},
        {"texto": "> membros online: 180"},
        {"texto": "$ status: PRONTO PARA CONSTRUIR"},
    ],
    "ticker": [{"texto": t} for t in (
        "front-end", "back-end", "dados & ia", "ux/ui", "devops",
        "seguranca", "mobile", "cloud", "open source",
    )],
    "beneficios": [
        {"icone": "code-xml", "texto": "Projetos reais em squads, com mentoria de veteranos."},
        {"icone": "award", "texto": "Certificados de participação para currículo e horas complementares."},
        {"icone": "briefcase", "texto": "Acesso direto a vagas de estágio das empresas parceiras."},
    ],
    "squads": [{"nome": n} for n in ("Front-end", "Back-end", "Dados & IA", "UX/UI")],
    "stats_sobre": [
        {"valor": "2026", "sufixo": "", "rotulo": "Fundação", "animar": "NÃO"},
        {"valor": "180", "sufixo": "+", "rotulo": "Membros", "animar": "SIM"},
        {"valor": "40", "sufixo": "+", "rotulo": "Projetos", "animar": "SIM"},
    ],
    "pilares": [
        {"icone": "target", "titulo": "Missão",
         "texto": "Aproximar teoria e prática por meio de projetos reais, colaboração e experiências que "
                  "conectam a academia ao mercado."},
        {"icone": "eye", "titulo": "Visão",
         "texto": "Ser referência entre ligas acadêmicas de tecnologia da região, pela qualidade dos projetos "
                  "e formação de talentos."},
        {"icone": "heart", "titulo": "Valores",
         "texto": "Colaboração, aprendizado contínuo, protagonismo e inclusão — porque todo especialista já "
                  "foi iniciante um dia."},
    ],
    "parceiros": [],
    "contatos": [
        {"icone": "mail", "rotulo": "e-mail", "valor": "contato@laads.edu.br", "link": "mailto:contato@laads.edu.br"},
        {"icone": "instagram", "rotulo": "instagram", "valor": "@la.ads", "link": "https://instagram.com/la.ads"},
        {"icone": "map-pin", "rotulo": "local", "valor": "Bloco de Tecnologia, sala 14", "link": ""},
    ],
}
