from models.usuario import Usuario
from utils.validators import exigir_permissao, normalizar_papel, normalizar_texto, validar_papel

import sys
import json
from utils.db import carregar_db, salvar_db


def buscar_usuario(db, nome):
    nome = normalizar_texto(nome).lower()
    for indice, usuario in enumerate(db.get("usuarios", [])):
        if normalizar_texto(usuario.get("nome", "")).lower() == nome:
            return indice, usuario
    return None, None


def autenticar(db, nome, papel):
    nome = normalizar_texto(nome)
    papel = normalizar_papel(papel)

    if not nome or not validar_papel(papel):
        return None, "Usuario ou papel invalido"

    _, usuario = buscar_usuario(db, nome)
    if usuario is None:
        return None, "Acesso negado: usuario nao cadastrado"

    if usuario.get("papel") != papel:
        return None, "Acesso negado: papel nao confere com o cadastro"

    return Usuario.de_dict(usuario), "Login autorizado"


def listar_usuarios(db, solicitante):
    permitido, mensagem = exigir_permissao(solicitante, "usuario_visualizar")
    if not permitido:
        return False, mensagem, []
    return True, "Usuarios listados", list(db.get("usuarios", []))


def criar_usuario(db, solicitante, nome, papel):
    permitido, mensagem = exigir_permissao(solicitante, "usuario_criar")
    if not permitido:
        return False, mensagem

    if buscar_usuario(db, nome)[1] is not None:
        return False, "Usuario ja cadastrado"

    try:
        usuario = Usuario(nome, papel).para_dict()
    except ValueError as erro:
        return False, str(erro)

    db["usuarios"].append(usuario)
    return True, "Usuario criado"


def editar_usuario(db, solicitante, indice, novo_nome, novo_papel):
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
        atualizado = Usuario(novo_nome, novo_papel).para_dict()
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

    return True, "Usuario atualizado"


class UsuarioFake:
    nome = "API"
    papel = "ADM"


def resposta(data):
    print(json.dumps(data))


if __name__ == "__main__":
    db = carregar_db()
    solicitante = UsuarioFake()

    try:
        comando = sys.argv[1]

        # ===== LOGIN =====
        if comando == "login":
            body = json.loads(sys.argv[2])

            usuario, mensagem = autenticar(
                db,
                body["nome"],
                body["papel"]
            )

            resposta({
                "sucesso": usuario is not None,
                "usuario": usuario.__dict__ if usuario else None,
                "mensagem": mensagem
            })

        # ===== LISTAR USUARIOS =====
        elif comando == "listar":
            sucesso, mensagem, dados = listar_usuarios(db, solicitante)

            resposta({
                "sucesso": sucesso,
                "dados": dados,
                "mensagem": mensagem
            })

        # ===== CRIAR USUARIO =====
        elif comando == "criar":
            body = json.loads(sys.argv[2])

            sucesso, mensagem = criar_usuario(
                db,
                solicitante,
                body["nome"],
                body["papel"]
            )

            if sucesso:
                salvar_db(db)

            resposta({
                "sucesso": sucesso,
                "mensagem": mensagem
            })

        # ===== EDITAR USUARIO =====
        elif comando == "editar":
            body = json.loads(sys.argv[2])

            sucesso, mensagem = editar_usuario(
                db,
                solicitante,
                body["indice"],
                body["nome"],
                body["papel"]
            )

            if sucesso:
                salvar_db(db)

            resposta({
                "sucesso": sucesso,
                "mensagem": mensagem
            })

        else:
            resposta({
                "sucesso": False,
                "mensagem": "Comando inválido"
            })

    except Exception as e:
        resposta({
            "sucesso": False,
            "mensagem": str(e)
        })
