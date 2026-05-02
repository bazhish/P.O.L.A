# Database no Supabase

Esta pasta conecta o CRUD de usuários ao PostgreSQL do Supabase.

## Configurar

Crie `database/.env` com base em `database/.env.example`, ou mantenha um arquivo local `database/env` com as mesmas variáveis.

```bash
DB_HOST=db.<project-ref>.supabase.co
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=sua-senha-do-banco
DB_PORT=5432
DB_SSLMODE=require
```

## Instalar dependências

```bash
python -m pip install -r database/requirements.txt
```

## Criar tabela no Supabase

```bash
python database/setup.py
```

## Rodar o CRUD

```bash
python database/main.py
```
