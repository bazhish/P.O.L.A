from models.sala import Sala
from utils.validators import exigir_permissao, normalizar_texto


def listar_salas(db, usuario):
    permitido, mensagem = exigir_permissao(usuario, "sala_visualizar")
    if not permitido:
        return False, mensagem, []
    return True, "Salas listadas", list(db.get("salas", []))


def buscar_sala(db, nome):
    nome = normalizar_texto(nome).lower()
    for indice, sala in enumerate(db.get("salas", [])):
        if normalizar_texto(sala.get("nome", "")).lower() == nome:
            return indice, sala
    return None, None


def buscar_sala_por_id(db, id):
    if not id:
        return None, None
    for indice, sala in enumerate(db.get("salas", [])):
        if sala.get("id") == id:
            return indice, sala
    return None, None


def criar_sala(db, usuario, nome):
    permitido, mensagem = exigir_permissao(usuario, "sala_criar")
    if not permitido:
        return False, mensagem

    if buscar_sala(db, nome)[1] is not None:
        return False, "Sala ja cadastrada"

    try:
        sala = Sala(nome).para_dict()
    except ValueError as erro:
        return False, str(erro)

    db["salas"].append(sala)
    return True, "Sala criada"


def editar_sala(db, usuario, indice, novo_nome):
    permitido, mensagem = exigir_permissao(usuario, "sala_editar")
    if not permitido:
        return False, mensagem

    salas = db.get("salas", [])
    if not isinstance(indice, int) or not 0 <= indice < len(salas):
        return False, "Sala selecionada invalida"

    existente_indice, _ = buscar_sala(db, novo_nome)
    if existente_indice is not None and existente_indice != indice:
        return False, "Outra sala ja usa esse nome"

    try:
        nova_sala = Sala(novo_nome, id=salas[indice].get("id")).para_dict()
    except ValueError as erro:
        return False, str(erro)

    nome_antigo = salas[indice]["nome"]
    salas[indice] = nova_sala

    for aluno in db.get("alunos", []):
        if aluno.get("sala_id") == nova_sala["id"] or aluno.get("sala") == nome_antigo:
            aluno["sala"] = nova_sala["nome"]
            aluno["sala_id"] = nova_sala["id"]

    return True, "Sala atualizada"
