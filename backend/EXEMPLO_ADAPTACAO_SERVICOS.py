"""
EXEMPLO DE ADAPTAÇÃO DE SERVIÇO PARA SUPABASE

Este arquivo mostra como adaptar os serviços existentes 
para usar o novo GerenciadorBD em vez do banco JSON local.

ANTES (usando JSON):
    def listar_alunos(db, usuario):
        return True, "Alunos listados", list(db.get("alunos", []))

DEPOIS (usando PostgreSQL):
    def listar_alunos(usuario):
        db = obter_gerenciador()
        return True, "Alunos listados", db.listar_alunos()
"""

from utils.db_manager import obter_gerenciador
from utils.validators import exigir_permissao


# ==================== EXEMPLO: ALUNO SERVICE ====================

def buscar_aluno_por_nome(nome):
    """Busca aluno por nome no banco de dados PostgreSQL"""
    db = obter_gerenciador()
    aluno = db.buscar_aluno_por_nome(nome)
    return aluno


def buscar_aluno_por_id(id):
    """Busca aluno por ID no banco de dados PostgreSQL"""
    db = obter_gerenciador()
    aluno = db.buscar_aluno_por_id(id)
    return aluno


def listar_alunos(usuario):
    """Lista todos os alunos"""
    permitido, mensagem = exigir_permissao(usuario, "aluno_visualizar")
    if not permitido:
        return False, mensagem, []
    
    db = obter_gerenciador()
    alunos = db.listar_alunos()
    return True, "Alunos listados", alunos


def listar_alunos_por_sala(usuario, sala_id):
    """Lista alunos de uma sala específica"""
    permitido, mensagem = exigir_permissao(usuario, "aluno_visualizar")
    if not permitido:
        return False, mensagem, []
    
    db = obter_gerenciador()
    alunos = db.listar_alunos_por_sala(sala_id)
    return True, f"Alunos da sala {sala_id} listados", alunos


def criar_aluno(usuario, nome, sala_id=None, matricula=None):
    """Cria novo aluno"""
    permitido, mensagem = exigir_permissao(usuario, "aluno_criar")
    if not permitido:
        return False, mensagem, None
    
    db = obter_gerenciador()
    try:
        novo_aluno = db.criar_aluno(nome, sala_id, matricula)
        return True, f"Aluno '{nome}' criado com sucesso", novo_aluno
    except Exception as e:
        return False, f"Erro ao criar aluno: {str(e)}", None


def atualizar_aluno(usuario, id, **kwargs):
    """Atualiza dados do aluno"""
    permitido, mensagem = exigir_permissao(usuario, "aluno_editar")
    if not permitido:
        return False, mensagem
    
    db = obter_gerenciador()
    try:
        if db.atualizar_aluno(id, **kwargs):
            return True, "Aluno atualizado com sucesso"
        else:
            return False, "Aluno não encontrado"
    except Exception as e:
        return False, f"Erro ao atualizar: {str(e)}"


def deletar_aluno(usuario, id):
    """Deleta aluno"""
    permitido, mensagem = exigir_permissao(usuario, "aluno_deletar")
    if not permitido:
        return False, mensagem
    
    db = obter_gerenciador()
    try:
        if db.deletar_aluno(id):
            return True, "Aluno deletado com sucesso"
        else:
            return False, "Aluno não encontrado"
    except Exception as e:
        return False, f"Erro ao deletar: {str(e)}"


# ==================== EXEMPLO: USUARIO SERVICE ====================

def buscar_usuario_por_nome(nome):
    """Busca usuário por nome"""
    db = obter_gerenciador()
    return db.buscar_usuario_por_nome(nome)


def buscar_usuario_por_id(id):
    """Busca usuário por ID"""
    db = obter_gerenciador()
    return db.buscar_usuario_por_id(id)


def listar_usuarios(usuario):
    """Lista todos os usuários"""
    permitido, mensagem = exigir_permissao(usuario, "usuario_visualizar")
    if not permitido:
        return False, mensagem, []
    
    db = obter_gerenciador()
    usuarios = db.listar_usuarios()
    return True, "Usuários listados", usuarios


def criar_usuario(usuario, nome, papel, senha_hash):
    """Cria novo usuário"""
    permitido, mensagem = exigir_permissao(usuario, "usuario_criar")
    if not permitido:
        return False, mensagem, None
    
    db = obter_gerenciador()
    try:
        novo_usuario = db.criar_usuario(nome, papel, senha_hash)
        return True, f"Usuário '{nome}' criado", novo_usuario
    except Exception as e:
        return False, f"Erro: {str(e)}", None


# ==================== EXEMPLO: SALA SERVICE ====================

def buscar_sala_por_nome(nome):
    """Busca sala por nome"""
    db = obter_gerenciador()
    return db.buscar_sala_por_nome(nome)


def listar_salas(usuario):
    """Lista todas as salas"""
    permitido, mensagem = exigir_permissao(usuario, "sala_visualizar")
    if not permitido:
        return False, mensagem, []
    
    db = obter_gerenciador()
    salas = db.listar_salas()
    return True, "Salas listadas", salas


def criar_sala(usuario, nome, ano_letivo=None):
    """Cria nova sala"""
    permitido, mensagem = exigir_permissao(usuario, "sala_criar")
    if not permitido:
        return False, mensagem, None
    
    db = obter_gerenciador()
    try:
        nova_sala = db.criar_sala(nome, ano_letivo)
        return True, f"Sala '{nome}' criada", nova_sala
    except Exception as e:
        return False, f"Erro: {str(e)}", None


# ==================== MUDANÇAS PRINCIPAIS ====================
"""
1. REMOVER: Parâmetro 'db' das funções (não mais necessário)
   ANTES: def listar_alunos(db, usuario):
   DEPOIS: def listar_alunos(usuario):

2. OBTER CONEXÃO: Usar gerenciador no início da função
   db = obter_gerenciador()

3. OPERAÇÕES: Usar métodos do gerenciador
   ANTES: db.get("alunos", [])
   DEPOIS: db.listar_alunos()

4. TRATAMENTO DE ERRO: Encapsular em try/except
   try:
       resultado = db.criar_aluno(...)
   except Exception as e:
       return False, str(e), None

5. FECHAMENTO: O gerenciador cuida da conexão
   (Não é necessário chamar db.fechar() em cada função)
"""
