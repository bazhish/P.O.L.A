from copy import deepcopy

from models.falta import Falta
from services.aluno_service import buscar_aluno
from utils.cli import autenticar_solicitante, parse_comando_json
from utils.db import DB_LOCK
from utils.responses import imprimir_resposta, resposta_erro, resposta_servico
from utils.validators import exigir_permissao

import sys
from utils.db import carregar_db, salvar_db

def adicionar_falta(db, usuario, aluno, data):
    permitido, mensagem = exigir_permissao(usuario, "falta_criar")
    if not permitido:
        return False, mensagem

    if not isinstance(db, dict):
        return False, "Banco de dados invalido"

    with DB_LOCK:
        faltas = db.get("faltas")
        if faltas is None:
            db["faltas"] = []
            faltas = db["faltas"]
        if not isinstance(faltas, list):
            return False, "Lista de faltas invalida"

        _, aluno_db = buscar_aluno(db, aluno)
        if aluno_db is None:
            return False, "Aluno nao cadastrado"

        try:
            falta = Falta(
                aluno_db["nome"],
                data,
                aluno_id=aluno_db.get("id"),
            ).para_dict()
        except ValueError as erro:
            return False, str(erro)

        faltas.append(falta)
        return True, "Falta adicionada"


def listar_faltas(db, usuario, aluno=None):
    permitido, mensagem = exigir_permissao(usuario, "falta_visualizar")
    if not permitido:
        return False, mensagem, []

    with DB_LOCK:
        faltas = db.get("faltas", []) if isinstance(db, dict) else []
        if not isinstance(faltas, list) or not all(isinstance(falta, dict) for falta in faltas):
            return False, "Lista de faltas invalida", []
        if aluno:
            faltas = [
                falta for falta in faltas
                if falta.get("aluno") == aluno or falta.get("aluno_id") == aluno
            ]

    return True, "Faltas listadas", deepcopy(faltas)




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
            sucesso, mensagem = adicionar_falta(
                db,
                usuario,
                body["aluno"],
                body["data"],
            )
            if sucesso:
                salvar_db(db)
            return resposta_servico(sucesso, mensagem)

        if comando == "listar":
            sucesso, mensagem, dados = listar_faltas(db, usuario, body.get("aluno"))
            return resposta_servico(sucesso, mensagem, dados=dados)

        return resposta_erro("Comando invalido")
    except (KeyError, TypeError, ValueError):
        return resposta_erro("Entrada invalida")
    except Exception:
        return resposta_erro("Erro interno ao executar comando")


if __name__ == "__main__":
    imprimir_resposta(_executar_cli())
