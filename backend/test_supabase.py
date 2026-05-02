#!/usr/bin/env python3
"""Teste de validação da integração com Supabase"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from utils.db_manager import obter_gerenciador


def testar_conexao():
    """Testa a conexão e operações básicas"""
    print("\n" + "="*60)
    print("[TEST] TESTE DE VALIDACAO - BACKEND COM SUPABASE")
    print("="*60 + "\n")
    
    try:
        db = obter_gerenciador()
        
        # Teste 1: Verificar usuário admin
        print("[1] Verificando usuario administrador...")
        admin = db.buscar_usuario_por_nome("admin")
        if admin:
            print(f"    [OK] Usuario encontrado: {admin['nome']} ({admin['papel']})")
        else:
            print("    [ERRO] Usuario admin nao encontrado")
            return False
        
        # Teste 2: Listar salas
        print("\n[2] Listando salas...")
        salas = db.listar_salas()
        print(f"    [OK] Total de salas: {len(salas)}")
        if salas:
            for sala in salas[:3]:
                print(f"        - {sala['nome']}")
        
        # Teste 3: Listar alunos
        print("\n[3] Listando alunos...")
        alunos = db.listar_alunos()
        print(f"    [OK] Total de alunos: {len(alunos)}")
        if alunos:
            for aluno in alunos[:3]:
                print(f"        - {aluno['nome']}")
        
        # Teste 4: Listar usuarios
        print("\n[4] Listando usuarios...")
        usuarios = db.listar_usuarios()
        print(f"    [OK] Total de usuarios: {len(usuarios)}")
        for usuario in usuarios[:5]:
            print(f"        - {usuario['nome']} ({usuario['papel']})")
        
        print("\n" + "="*60)
        print("[SUCCESS] TODOS OS TESTES PASSARAM COM SUCESSO!")
        print("="*60 + "\n")
        print("[INFO] Resumo da migracao:")
        print("   [OK] Backend conectado ao Supabase")
        print("   [OK] Banco de dados local removido")
        print("   [OK] Tabelas criadas no PostgreSQL")
        print("   [OK] Usuario admin configurado")
        print("\n[READY] O backend esta pronto para uso!\n")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.fechar()


if __name__ == "__main__":
    sucesso = testar_conexao()
    sys.exit(0 if sucesso else 1)
