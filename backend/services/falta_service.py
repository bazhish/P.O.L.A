from models.falta import Falta
from services.aluno_service import buscar_aluno
from utils.validators import exigir_permissao


def adicionar_falta(db, usuario, aluno, data):
    permitido, mensagem = exigir_permissao(usuario, "falta_criar")
    if not permitido:
        return False, mensagem

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

    db["faltas"].append(falta)
    return True, "Falta adicionada"


def listar_faltas(db, usuario, aluno=None):
    permitido, mensagem = exigir_permissao(usuario, "falta_visualizar")
    if not permitido:
        return False, mensagem, []

    faltas = list(db.get("faltas", []))
    if aluno:
        faltas = [
            falta for falta in faltas
            if falta.get("aluno") == aluno or falta.get("aluno_id") == aluno
        ]

    return True, "Faltas listadas", faltas
