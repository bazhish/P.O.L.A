from copy import deepcopy

from models.nota import Nota
from services.aluno_service import buscar_aluno
from utils.cli import autenticar_solicitante, parse_comando_json
from utils.db import DB_LOCK
from utils.responses import imprimir_resposta, resposta_erro, resposta_servico
from utils.validators import exigir_permissao

import sys
from utils.db import carregar_db, salvar_db


def adicionar_nota(db, usuario, aluno, disciplina, valor):
    permitido, mensagem = exigir_permissao(usuario, "nota_criar")
    if not permitido:
        return False, mensagem

    if not isinstance(db, dict):
        return False, "Banco de dados invalido"

    with DB_LOCK:
        notas = db.get("notas")
        if notas is None:
            db["notas"] = []
            notas = db["notas"]
        if not isinstance(notas, list):
            return False, "Lista de notas invalida"

        _, aluno_db = buscar_aluno(db, aluno)
        if aluno_db is None:
            return False, "Aluno nao cadastrado"

        try:
            nota = Nota(
                aluno_db["nome"],
                disciplina,
                valor,
                aluno_id=aluno_db.get("id"),
            ).para_dict()
        except (TypeError, ValueError) as erro:
            return False, str(erro)

        notas.append(nota)
        return True, "Nota adicionada"


def listar_notas(db, usuario, aluno=None):
    permitido, mensagem = exigir_permissao(usuario, "nota_visualizar")
    if not permitido:
        return False, mensagem, []

    with DB_LOCK:
        notas = db.get("notas", []) if isinstance(db, dict) else []
        if not isinstance(notas, list) or not all(isinstance(nota, dict) for nota in notas):
            return False, "Lista de notas invalida", []
        if aluno:
            notas = [
                nota for nota in notas
                if nota.get("aluno") == aluno or nota.get("aluno_id") == aluno
            ]

    return True, "Notas listadas", deepcopy(notas)



def _executar_cli(argv=None):
    argv = sys.argv if argv is None else argv
    db = carregar_db()
    comando, body, erro = parse_comando_json(argv)

    try:
        if erro:
            return resposta_erro(erro)

        usuario, mensagem_auth = autenticar_solicitante(db, body)
        if usuario is None:
            return resposta_erro(mensagem_auth)

        if comando == "criar":
            sucesso, mensagem = adicionar_nota(
                db,
                usuario,
                body["aluno"],
                body["disciplina"],
                body["valor"],
            )
            if sucesso:
                salvar_db(db)
            return resposta_servico(sucesso, mensagem)

        if comando == "listar":
            sucesso, mensagem, dados = listar_notas(db, usuario, body.get("aluno"))
            return resposta_servico(sucesso, mensagem, dados=dados)

        return resposta_erro("Comando invalido")
    except (KeyError, TypeError, ValueError):
        return resposta_erro("Entrada invalida")
    except Exception:
        return resposta_erro("Erro interno ao executar comando")


if __name__ == "__main__":
    imprimir_resposta(_executar_cli())
