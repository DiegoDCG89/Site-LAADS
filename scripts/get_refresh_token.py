"""Autoriza o app a usar SUA conta Google (Sheets + Drive) e imprime o GOOGLE_REFRESH_TOKEN.

Pré-requisitos (veja o README, passo 2):  pip install -r requirements-dev.txt
Uso:
    python scripts/get_refresh_token.py --client-secret client_secret.json
Uma janela do navegador abre; entre com a conta dona da planilha e da pasta do Drive.
"""
import argparse
import json

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ap = argparse.ArgumentParser()
ap.add_argument("--client-secret", default="client_secret.json", help="JSON baixado do Google Cloud (cliente OAuth tipo 'App para computador')")
args = ap.parse_args()

flow = InstalledAppFlow.from_client_secrets_file(args.client_secret, SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
cfg = json.load(open(args.client_secret))
cfg = cfg.get("installed") or cfg.get("web") or {}
if not creds.refresh_token:
    raise SystemExit("O Google não devolveu refresh token. Remova o acesso do app em myaccount.google.com/permissions e tente de novo.")
print("\nCadastre no .env e no Vercel:\n")
print("GOOGLE_CLIENT_ID=" + cfg.get("client_id", ""))
print("GOOGLE_CLIENT_SECRET=" + cfg.get("client_secret", ""))
print("GOOGLE_REFRESH_TOKEN=" + creds.refresh_token)
