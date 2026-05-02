import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

for arquivo_env in (BASE_DIR / ".env", BASE_DIR / "env"):
    load_dotenv(arquivo_env)


def parametros_conexao():
    url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
    if url:
        return url

    host = os.getenv("DB_HOST")
    password = os.getenv("DB_PASSWORD")

    if not host or not password:
        raise RuntimeError(
            "Configure DB_HOST e DB_PASSWORD em database/.env "
            "ou defina DATABASE_URL/SUPABASE_DB_URL."
        )

    return {
        "host": host,
        "dbname": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": password,
        "port": os.getenv("DB_PORT", "5432"),
        "sslmode": os.getenv("DB_SSLMODE", "require"),
    }


def conectar():
    parametros = parametros_conexao()
    if isinstance(parametros, str):
        return psycopg.connect(parametros)
    return psycopg.connect(**parametros)
