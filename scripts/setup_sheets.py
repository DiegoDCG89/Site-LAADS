"""Cria as abas na planilha e grava o conteúdo atual do site (equivale ao botão "Inicializar planilha").
Seguro para rodar várias vezes: nunca apaga nem sobrescreve dados existentes.

Uso:  python scripts/setup_sheets.py     (lê as variáveis do .env)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from laads import build_services  # noqa: E402
from laads.config import load_settings  # noqa: E402
from laads.setup import initialize  # noqa: E402

settings = load_settings()
if not settings.sheets_configured:
    sys.exit("Defina SPREADSHEET_ID e as credenciais do Google no .env primeiro.")
svc = build_services(settings)
if svc.init_error:
    sys.exit(svc.init_error)
info = svc.store.info()
print("Planilha:", info["title"], "|", info["url"])
report = initialize(svc.store)
print("Abas criadas:   ", ", ".join(report["created"]) or "nenhuma")
print("Abas preenchidas:", ", ".join(report["seeded"]) or "nenhuma")
print("Colunas ajustadas:", ", ".join(report["repaired"]) or "nenhuma")
