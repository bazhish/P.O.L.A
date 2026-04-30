from models.aluno import Aluno
from services.sala_service import buscar_sala
from utils.validators import exigir_permissao, normalizar_texto


def buscar_aluno(db, nome):
    nome = normalizar_texto(nome).lower()
    for indice, aluno in enumerate(db.get("alunos", [])):
        if normalizar_texto(aluno.get("nome", "")).lower() == nome:
            return indice, aluno
    return None, None


def buscar_aluno_por_id(db, id):
    if not id:
        return None, None
    for indice, aluno in enumerate(db.get("alunos", [])):
        if aluno.get("id") == id:
            return indice, aluno
    return None, None


def buscar_aluno_por_id_ou_nome(db, id=None, nome=None):
    indice, aluno = buscar_aluno_por_id(db, id)
    if aluno is not None:
        return indice, aluno
    return buscar_aluno(db, nome)


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
    alunos = [
        aluno for aluno in db.get("alunos", [])
        if aluno.get("sala") == sala or aluno.get("sala_id") == sala
    ]
    return True, "Alunos da sala listados", alunos


def criar_aluno(db, usuario, nome, sala):
    permitido, mensagem = exigir_permissao(usuario, "aluno_criar")
    if not permitido:
        return False, mensagem

    if buscar_aluno(db, nome)[1] is not None:
        return False, "Aluno ja cadastrado"

    _, sala_db = buscar_sala(db, sala)
    if sala_db is None:
        return False, "Sala nao cadastrada"

    try:
        aluno = Aluno(nome, sala_db["nome"], sala_id=sala_db.get("id")).para_dict()
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

    _, sala_db = buscar_sala(db, nova_sala)
    if sala_db is None:
        return False, "Sala nao cadastrada"

    existente_indice, _ = buscar_aluno(db, novo_nome)
    if existente_indice is not None and existente_indice != indice:
        return False, "Outro aluno ja usa esse nome"

    nome_antigo = alunos[indice]["nome"]
    id_aluno = alunos[indice].get("id")

    try:
        aluno = Aluno(
            novo_nome,
            sala_db["nome"],
            id=id_aluno,
            sala_id=sala_db.get("id"),
        ).para_dict()
    except ValueError as erro:
        return False, str(erro)

    alunos[indice] = aluno

    if nome_antigo != aluno["nome"]:
        for ocorrencia in db.get("ocorrencias", []):
            if ocorrencia.get("aluno_id") == id_aluno or ocorrencia.get("aluno") == nome_antigo:
                ocorrencia["aluno"] = aluno["nome"]
                ocorrencia["aluno_id"] = id_aluno
        for nota in db.get("notas", []):
            if nota.get("aluno_id") == id_aluno or nota.get("aluno") == nome_antigo:
                nota["aluno"] = aluno["nome"]
                nota["aluno_id"] = id_aluno
        for falta in db.get("faltas", []):
            if falta.get("aluno_id") == id_aluno or falta.get("aluno") == nome_antigo:
                falta["aluno"] = aluno["nome"]
                falta["aluno_id"] = id_aluno

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
