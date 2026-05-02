import os
from pathlib import Path
from datetime import datetime
import psycopg
from dotenv import load_dotenv

# Carregar variáveis de ambiente
BASE_DIR = Path(__file__).resolve().parents[1]
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)


class ConexaoBD:
    """Gerenciador de conexão com Supabase PostgreSQL"""
    
    _conexao = None
    
    @classmethod
    def obter_conexao(cls):
        """Obtém ou cria uma conexão com o banco de dados"""
        if cls._conexao is None:
            cls._conexao = cls._conectar()
        return cls._conexao
    
    @classmethod
    def _conectar(cls):
        """Conecta ao banco de dados Supabase"""
        parametros = {
            "host": os.getenv("DB_HOST"),
            "dbname": os.getenv("DB_NAME", "postgres"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "sslmode": os.getenv("DB_SSLMODE", "require"),
        }
        
        if not parametros["host"] or not parametros["password"]:
            raise RuntimeError(
                "Configure DB_HOST e DB_PASSWORD no arquivo .env do backend"
            )
        
        try:
            conn = psycopg.connect(**parametros)
            print("✓ Conectado ao banco de dados Supabase")
            return conn
        except Exception as e:
            raise RuntimeError(f"Erro ao conectar ao banco de dados: {e}")
    
    @classmethod
    def fechar(cls):
        """Fecha a conexão com o banco de dados"""
        if cls._conexao:
            cls._conexao.close()
            cls._conexao = None


def conectar():
    """Função compatível para conectar ao banco"""
    return ConexaoBD.obter_conexao()


def criar_tabelas_iniciais():
    """Cria as tabelas iniciais no banco de dados"""
    conn = ConexaoBD.obter_conexao()
    cursor = conn.cursor()
    
    try:
        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.usuarios (
                id BIGSERIAL PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE,
                papel TEXT NOT NULL,
                senha_hash TEXT,
                precisa_trocar_senha BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Tabela de salas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.salas (
                id BIGSERIAL PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE,
                ano_letivo INT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Tabela de alunos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.alunos (
                id BIGSERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                sala_id BIGINT,
                matricula TEXT UNIQUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (sala_id) REFERENCES salas(id)
            )
        """)
        
        # Tabela de notas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.notas (
                id BIGSERIAL PRIMARY KEY,
                aluno_id BIGINT NOT NULL,
                disciplina TEXT,
                valor FLOAT,
                periodo TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (aluno_id) REFERENCES alunos(id)
            )
        """)
        
        # Tabela de faltas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.faltas (
                id BIGSERIAL PRIMARY KEY,
                aluno_id BIGINT NOT NULL,
                data DATE,
                justificada BOOLEAN DEFAULT FALSE,
                observacoes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (aluno_id) REFERENCES alunos(id)
            )
        """)
        
        # Tabela de ocorrências
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS public.ocorrencias (
                id BIGSERIAL PRIMARY KEY,
                aluno_id BIGINT NOT NULL,
                tipo TEXT,
                descricao TEXT,
                status TEXT,
                prioridade TEXT,
                data TIMESTAMPTZ DEFAULT NOW(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                FOREIGN KEY (aluno_id) REFERENCES alunos(id)
            )
        """)
        
        conn.commit()
        print("✓ Tabelas criadas/verificadas com sucesso")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Erro ao criar tabelas: {e}")
        raise
    finally:
        cursor.close()


def inserir_usuario_admin(nome="admin", senha_hash=None):
    """Insere usuário admin se não existir"""
    conn = ConexaoBD.obter_conexao()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM usuarios WHERE papel = %s", ("ADM",))
        if cursor.fetchone():
            print("✓ Usuário ADM já existe")
            return
        
        cursor.execute(
            """INSERT INTO usuarios (nome, papel, senha_hash, precisa_trocar_senha)
               VALUES (%s, %s, %s, %s)""",
            (nome, "ADM", senha_hash, True)
        )
        conn.commit()
        print(f"✓ Usuário admin '{nome}' criado com sucesso")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Erro ao inserir usuário admin: {e}")
        raise
    finally:
        cursor.close()
