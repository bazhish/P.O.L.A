from models.sala import Sala
from utils.validators import exigir_permissao, normalizar_texto

import sys
import json
from utils.db import carregar_db, salvar_db


def listar_salas(db, usuario):
    permitido, mensagem = exigir_permissao(usuario, "sala_visualizar")
    if not permitido:
        return False, mensagem, []
    return True, "Salas listadas", list(db.get("salas", []))


def buscar_sala(db, nome):
    nome = normalizar_texto(nome).lower()
    for indice, sala in enumerate(db.get("salas", [])):
        if normalizar_texto(sala.get("nome", "")).lower() == nome:
            return indice, sala
    return None, None


def criar_sala(db, usuario, nome):
    permitido, mensagem = exigir_permissao(usuario, "sala_criar")
    if not permitido:
        return False, mensagem

    if buscar_sala(db, nome)[1] is not None:
        return False, "Sala ja cadastrada"

    try:
        sala = Sala(nome).para_dict()
    except ValueError as erro:
        return False, str(erro)

    db["salas"].append(sala)
    return True, "Sala criada"


def editar_sala(db, usuario, indice, novo_nome):
    permitido, mensagem = exigir_permissao(usuario, "sala_editar")
    if not permitido:
        return False, mensagem

    salas = db.get("salas", [])
    if not isinstance(indice, int) or not 0 <= indice < len(salas):
        return False, "Sala selecionada invalida"

    existente_indice, _ = buscar_sala(db, novo_nome)
    if existente_indice is not None and existente_indice != indice:
        return False, "Outra sala ja usa esse nome"

    try:
        nova_sala = Sala(novo_nome).para_dict()
    except ValueError as erro:
        return False, str(erro)

    nome_antigo = salas[indice]["nome"]
    salas[indice] = nova_sala

    for aluno in db.get("alunos", []):
        if aluno.get("sala") == nome_antigo:
            aluno["sala"] = nova_sala["nome"]

    return True, "Sala atualizada"

class UsuarioFake:
    nome = "API"
    papel = "ADM"


def resposta(data):
    print(json.dumps(data))


if __name__ == "__main__":
    db = carregar_db()
    usuario = UsuarioFake()

    try:
        comando = sys.argv[1]

        # ===== CRIAR SALA =====
        if comando == "criar":
            body = json.loads(sys.argv[2])

            sucesso, mensagem = criar_sala(
                db,
                usuario,
                body["nome"]
            )

            if sucesso:
                salvar_db(db)

            resposta({
                "sucesso": sucesso,
                "mensagem": mensagem
            })

        # ===== LISTAR SALAS =====
        elif comando == "listar":
            sucesso, mensagem, dados = listar_salas(db, usuario)

            resposta({
                "sucesso": sucesso,
                "dados": dados,
                "mensagem": mensagem
            })

        # ===== EDITAR SALA =====
        elif comando == "editar":
            body = json.loads(sys.argv[2])

            sucesso, mensagem = editar_sala(
                db,
                usuario,
                body["indice"],
                body["nome"]
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
