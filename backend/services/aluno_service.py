from models.aluno import Aluno
from services.sala_service import buscar_sala
from utils.validators import exigir_permissao, normalizar_texto

import sys
import json
from utils.db import carregar_db, salvar_db


def buscar_aluno(db, nome):
    nome = normalizar_texto(nome).lower()
    for indice, aluno in enumerate(db.get("alunos", [])):
        if normalizar_texto(aluno.get("nome", "")).lower() == nome:
            return indice, aluno
    return None, None


def listar_alunos(db, usuario):
    permitido, mensagem = exigir_permissao(usuario, "aluno_visualizar")
    if not permitido:
        return False, mensagem, []
    return True, "Alunos listados", list(db.get("alunos", []))


def listar_alunos_por_sala(db, usuario, sala):
    permitido, mensagem = exigir_permissao(usuario, "aluno_visualizar")
    if not permitido:
        return False, mensagem, []

    sala = normalizar_texto(sala)
    alunos = [aluno for aluno in db.get("alunos", []) if aluno.get("sala") == sala]
    return True, "Alunos da sala listados", alunos


def criar_aluno(db, usuario, nome, sala):
    permitido, mensagem = exigir_permissao(usuario, "aluno_criar")
    if not permitido:
        return False, mensagem

    if buscar_aluno(db, nome)[1] is not None:
        return False, "Aluno ja cadastrado"

    if buscar_sala(db, sala)[1] is None:
        return False, "Sala nao cadastrada"

    try:
        aluno = Aluno(nome, sala).para_dict()
    except ValueError as erro:
        return False, str(erro)

    db["alunos"].append(aluno)
    return True, "Aluno criado"


def editar_aluno(db, usuario, indice, novo_nome, nova_sala):
    permitido, mensagem = exigir_permissao(usuario, "aluno_editar")
    if not permitido:
        return False, mensagem

    alunos = db.get("alunos", [])
    if not isinstance(indice, int) or not 0 <= indice < len(alunos):
        return False, "Aluno selecionado invalido"

    if buscar_sala(db, nova_sala)[1] is None:
        return False, "Sala nao cadastrada"

    existente_indice, _ = buscar_aluno(db, novo_nome)
    if existente_indice is not None and existente_indice != indice:
        return False, "Outro aluno ja usa esse nome"

    nome_antigo = alunos[indice]["nome"]

    try:
        aluno = Aluno(novo_nome, nova_sala).para_dict()
    except ValueError as erro:
        return False, str(erro)

    alunos[indice] = aluno

    if nome_antigo != aluno["nome"]:
        for ocorrencia in db.get("ocorrencias", []):
            if ocorrencia.get("aluno") == nome_antigo:
                ocorrencia["aluno"] = aluno["nome"]
        for nota in db.get("notas", []):
            if nota.get("aluno") == nome_antigo:
                nota["aluno"] = aluno["nome"]
        for falta in db.get("faltas", []):
            if falta.get("aluno") == nome_antigo:
                falta["aluno"] = aluno["nome"]

    return True, "Aluno atualizado"


def visualizar_aluno(db, usuario, nome):
    permitido, mensagem = exigir_permissao(usuario, "aluno_visualizar")
    if not permitido:
        return False, mensagem, None

    _, aluno = buscar_aluno(db, nome)
    if aluno is None:
        return False, "Aluno nao encontrado", None

    nome_aluno = aluno["nome"]
    dados = {
        "aluno": aluno,
        "ocorrencias": [
            item for item in db.get("ocorrencias", []) if item.get("aluno") == nome_aluno
        ],
        "notas": [
            item for item in db.get("notas", []) if item.get("aluno") == nome_aluno
        ],
        "faltas": [
            item for item in db.get("faltas", []) if item.get("aluno") == nome_aluno
        ],
    }

    return True, "Aluno carregado", dados

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

        # ===== CRIAR =====
        if comando == "criar":
            body = json.loads(sys.argv[2])

            sucesso, mensagem = criar_aluno(
                db,
                usuario,
                body["nome"],
                body["sala"]
            )

            if sucesso:
                salvar_db(db)

            resposta({
                "sucesso": sucesso,
                "mensagem": mensagem
            })

        # ===== LISTAR =====
        elif comando == "listar":
            sucesso, mensagem, dados = listar_alunos(db, usuario)

            resposta({
                "sucesso": sucesso,
                "dados": dados,
                "mensagem": mensagem
            })

        # ===== EDITAR =====
        elif comando == "editar":
            body = json.loads(sys.argv[2])

            sucesso, mensagem = editar_aluno(
                db,
                usuario,
                body["indice"],
                body["nome"],
                body["sala"]
            )

            if sucesso:
                salvar_db(db)

            resposta({
                "sucesso": sucesso,
                "mensagem": mensagem
            })

        # ===== VISUALIZAR =====
        elif comando == "visualizar":
            body = json.loads(sys.argv[2])

            sucesso, mensagem, dados = visualizar_aluno(
                db,
                usuario,
                body["nome"]
            )

            resposta({
                "sucesso": sucesso,
                "dados": dados,
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
