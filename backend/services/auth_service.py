from models.usuario import Usuario
from utils.security import gerar_senha_hash, validar_senha, verificar_senha
from utils.validators import exigir_permissao, normalizar_texto


def buscar_usuario(db, nome):
    nome = normalizar_texto(nome).lower()
    for indice, usuario in enumerate(db.get("usuarios", [])):
        if normalizar_texto(usuario.get("nome", "")).lower() == nome:
            return indice, usuario
    return None, None


def buscar_usuario_por_id(db, id):
    if not id:
        return None, None
    for indice, usuario in enumerate(db.get("usuarios", [])):
        if usuario.get("id") == id:
            return indice, usuario
    return None, None


def autenticar(db, nome, senha):
    nome = normalizar_texto(nome)

    if not nome:
        return None, "Usuario invalido"

    _, usuario = buscar_usuario(db, nome)
    if usuario is None:
        return None, "Acesso negado: usuario nao cadastrado"

    if not verificar_senha(senha, usuario.get("senha_hash")):
        return None, "Acesso negado: senha invalida"

    return Usuario.de_dict(usuario), "Login autorizado"


def listar_usuarios(db, solicitante):
    permitido, mensagem = exigir_permissao(solicitante, "usuario_visualizar")
    if not permitido:
        return False, mensagem, []
    usuarios = []
    for usuario in db.get("usuarios", []):
        item = dict(usuario)
        item.pop("senha_hash", None)
        usuarios.append(item)
    return True, "Usuarios listados", usuarios


def criar_usuario(db, solicitante, nome, papel, senha):
    permitido, mensagem = exigir_permissao(solicitante, "usuario_criar")
    if not permitido:
        return False, mensagem

    if buscar_usuario(db, nome)[1] is not None:
        return False, "Usuario ja cadastrado"

    if not validar_senha(senha):
        return False, "Senha deve ter pelo menos 6 caracteres"

    try:
        usuario = Usuario(nome, papel, senha_hash=gerar_senha_hash(senha)).para_dict()
    except ValueError as erro:
        return False, str(erro)

    db["usuarios"].append(usuario)
    return True, "Usuario criado"


def editar_usuario(db, solicitante, indice, novo_nome, novo_papel, nova_senha=None):
    permitido, mensagem = exigir_permissao(solicitante, "usuario_editar")
    if not permitido:
        return False, mensagem

    usuarios = db.get("usuarios", [])
    if not isinstance(indice, int) or not 0 <= indice < len(usuarios):
        return False, "Usuario selecionado invalido"

    usuario_atual = usuarios[indice]
    nome_atual = usuario_atual.get("nome", "")

    existente_indice, _ = buscar_usuario(db, novo_nome)
    if existente_indice is not None and existente_indice != indice:
        return False, "Outro usuario ja usa esse nome"

    try:
        senha_hash = usuario_atual.get("senha_hash")
        precisa_trocar_senha = usuario_atual.get("precisa_trocar_senha", False)
        if nova_senha:
            if not validar_senha(nova_senha):
                return False, "Senha deve ter pelo menos 6 caracteres"
            senha_hash = gerar_senha_hash(nova_senha)
            precisa_trocar_senha = False

        atualizado = Usuario(
            novo_nome,
            novo_papel,
            senha_hash=senha_hash,
            id=usuario_atual.get("id"),
            precisa_trocar_senha=precisa_trocar_senha,
        ).para_dict()
    except ValueError as erro:
        return False, str(erro)

    era_adm = usuario_atual.get("papel") == "ADM"
    deixara_de_ser_adm = atualizado["papel"] != "ADM"
    total_adms = sum(1 for usuario in usuarios if usuario.get("papel") == "ADM")
    if era_adm and deixara_de_ser_adm and total_adms <= 1:
        return False, "Nao e permitido remover o ultimo ADM"

    usuarios[indice] = atualizado
    if solicitante.nome == nome_atual:
        solicitante.nome = atualizado["nome"]
        solicitante.nome_usuario = atualizado["nome"]
        solicitante.papel = atualizado["papel"]
        solicitante.id = atualizado["id"]
        solicitante.senha_hash = atualizado.get("senha_hash")

    return True, "Usuario atualizado"


def alterar_senha(db, usuario, senha_atual, nova_senha):
    indice, registro = buscar_usuario_por_id(db, getattr(usuario, "id", None))
    if registro is None:
        indice, registro = buscar_usuario(db, getattr(usuario, "nome", ""))

    if registro is None:
        return False, "Usuario nao encontrado"

    if not verificar_senha(senha_atual, registro.get("senha_hash")):
        return False, "Senha atual invalida"

    if not validar_senha(nova_senha):
        return False, "Senha deve ter pelo menos 6 caracteres"

    registro["senha_hash"] = gerar_senha_hash(nova_senha)
    registro.pop("precisa_trocar_senha", None)
    usuario.senha_hash = registro["senha_hash"]
    usuario.precisa_trocar_senha = False
    return True, "Senha atualizada"
