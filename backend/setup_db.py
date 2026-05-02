#!/usr/bin/env python3
"""Script de migração e setup do banco de dados Supabase"""

import sys
from pathlib import Path

# Adicionar o diretório ao path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from utils.db_cloud import ConexaoBD, criar_tabelas_iniciais, inserir_usuario_admin
from utils.security import gerar_senha_hash, senha_inicial_padrao


def verificar_banco():
    """Verifica e setup do banco de dados"""
    print("\n" + "="*50)
    print("🔧 SETUP DO BANCO DE DADOS SUPABASE")
    print("="*50 + "\n")
    
    try:
        # Conectar ao banco
        print("📡 Conectando ao banco de dados...")
        conn = ConexaoBD.obter_conexao()
        print("✓ Conexão estabelecida\n")
        
        # Criar tabelas
        print("📊 Criando tabelas iniciais...")
        criar_tabelas_iniciais()
        print()
        
        # Inserir usuário admin
        print("👤 Criando usuário administrador...")
        senha_hash = gerar_senha_hash(senha_inicial_padrao())
        inserir_usuario_admin(nome="admin", senha_hash=senha_hash)
        print()
        
        # Verificar dados
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        total_usuarios = cursor.fetchone()[0]
        cursor.close()
        
        print("="*50)
        print(f"✓ Setup concluído com sucesso!")
        print(f"✓ Total de usuários: {total_usuarios}")
        print("="*50 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Erro no setup: {e}")
        return False
    finally:
        ConexaoBD.fechar()


if __name__ == "__main__":
    sucesso = verificar_banco()
    sys.exit(0 if sucesso else 1)
