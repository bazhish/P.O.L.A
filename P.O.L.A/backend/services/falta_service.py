from models.falta import Falta
from services.aluno_service import buscar_aluno
from utils.validators import exigir_permissao


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
