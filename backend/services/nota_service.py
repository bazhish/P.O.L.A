from models.nota import Nota
from services.aluno_service import buscar_aluno
from utils.validators import exigir_permissao


def adicionar_nota(db, usuario, aluno, disciplina, valor):
    permitido, mensagem = exigir_permissao(usuario, "nota_criar")
    if not permitido:
        return False, mensagem

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

    db["notas"].append(nota)
    return True, "Nota adicionada"


def listar_notas(db, usuario, aluno=None):
    permitido, mensagem = exigir_permissao(usuario, "nota_visualizar")
    if not permitido:
        return False, mensagem, []

    notas = list(db.get("notas", []))
    if aluno:
        notas = [
            nota for nota in notas
            if nota.get("aluno") == aluno or nota.get("aluno_id") == aluno
        ]

    return True, "Notas listadas", notas
