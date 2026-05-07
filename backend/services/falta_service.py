from models.falta import Falta
from services.aluno_service import buscar_aluno
from utils.validators import exigir_permissao

import sys
import json
from utils.db import carregar_db, salvar_db

def adicionar_falta(db, usuario, aluno, data):
    permitido, mensagem = exigir_permissao(usuario, "falta_criar")
    if not permitido:
        return False, mensagem

    if buscar_aluno(db, aluno)[1] is None:
        return False, "Aluno nao cadastrado"

    try:
        falta = Falta(aluno, data).para_dict()
    except ValueError as erro:
        return False, str(erro)

    db["faltas"].append(falta)
    return True, "Falta adicionada"


def listar_faltas(db, usuario, aluno=None):
    permitido, mensagem = exigir_permissao(usuario, "falta_visualizar")
    if not permitido:
        return False, mensagem, []

    faltas = list(db.get("faltas", []))
    if aluno:
        faltas = [falta for falta in faltas if falta.get("aluno") == aluno]

    return True, "Faltas listadas", faltas



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

        # ===== ADICIONAR FALTA =====
        if comando == "criar":
            body = json.loads(sys.argv[2])

            sucesso, mensagem = adicionar_falta(
                db,
                usuario,
                body["aluno"],
                body["data"]
            )

            if sucesso:
                salvar_db(db)

            resposta({
                "sucesso": sucesso,
                "mensagem": mensagem
            })

        # ===== LISTAR FALTAS =====
        elif comando == "listar":
            aluno = None
            if len(sys.argv) > 2:
                body = json.loads(sys.argv[2])
                aluno = body.get("aluno")

            sucesso, mensagem, dados = listar_faltas(
                db,
                usuario,
                aluno
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
