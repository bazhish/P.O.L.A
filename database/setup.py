from pathlib import Path

from db import conectar


SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def aplicar_schema():
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(schema_sql)

    print("Schema aplicado no Supabase com sucesso.")


if __name__ == "__main__":
    aplicar_schema()
