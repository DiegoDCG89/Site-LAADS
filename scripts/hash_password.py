"""Gera o valor de ADMIN_PASSWORD_HASH (assim a senha em texto não fica guardada em nenhum lugar).

Uso:  python scripts/hash_password.py
"""
import getpass
import sys

from werkzeug.security import generate_password_hash

pw = getpass.getpass("Nova senha do painel: ")
if len(pw) < 10:
    sys.exit("Use pelo menos 10 caracteres.")
if pw != getpass.getpass("Repita a senha: "):
    sys.exit("As senhas não conferem.")
print("\nCopie a linha abaixo para o .env e para as variáveis do Vercel (e apague ADMIN_PASSWORD):\n")
print("ADMIN_PASSWORD_HASH=" + generate_password_hash(pw, method="pbkdf2:sha256", salt_length=16))
