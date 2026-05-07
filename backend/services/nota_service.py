from models.nota import Nota
from services.aluno_service import buscar_aluno
from utils.validators import exigir_permissao

import sys
import json
from utils.db import carregar_db, salvar_db


def adicionar_nota(db, usuario, aluno, disciplina, valor):
    permitido, mensagem = exigir_permissao(usuario, "nota_criar")
    if not permitido:
        return False, mensagem

    if buscar_aluno(db, aluno)[1] is None:
        return False, "Aluno nao cadastrado"

    try:
        nota = Nota(aluno, disciplina, valor).para_dict()
    except (TypeError, ValueError) as erro:
        return False, str(erro)

    db["notas"].append(nota)
    return True, "Nota adicionada"


def listar_notas(db, usuario, aluno=None):
    permitido, mensagem = exigir_permissao(usuario, "nota_visualizar")
    if not permitido:
        return False, mensagem, []

    notas = list(db.get("notas", []))
    if aluno:
        notas = [nota for nota in notas if nota.get("aluno") == aluno]

    return True, "Notas listadas", notas


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

        # ===== ADICIONAR NOTA =====
        if comando == "criar":
            body = json.loads(sys.argv[2])

            sucesso, mensagem = adicionar_nota(
                db,
                usuario,
                body["aluno"],
                body["disciplina"],
                body["valor"]
            )

            if sucesso:
                salvar_db(db)

            resposta({
                "sucesso": sucesso,
                "mensagem": mensagem
            })

        # ===== LISTAR NOTAS =====
        elif comando == "listar":
            # pode ou não vir aluno
            aluno = None
            if len(sys.argv) > 2:
                body = json.loads(sys.argv[2])
                aluno = body.get("aluno")

            sucesso, mensagem, dados = listar_notas(
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
