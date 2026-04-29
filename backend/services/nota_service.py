from models.nota import Nota
from services.aluno_service import buscar_aluno
from utils.validators import exigir_permissao


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
