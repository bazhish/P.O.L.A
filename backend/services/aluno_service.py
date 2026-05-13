from models.aluno import Aluno
from models.sala import Sala
from services.sala_service import buscar_sala
<<<<<<< HEAD
=======
from utils.cli import autenticar_solicitante, parse_comando_json
from utils.db import DB_LOCK, SALA_PADRAO
from utils.responses import imprimir_resposta, resposta_erro, resposta_servico
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466
from utils.validators import exigir_permissao, normalizar_texto

import sys
from utils.db import carregar_db, salvar_db


def buscar_aluno(db, nome):
    nome = normalizar_texto(nome).lower()
    for indice, aluno in enumerate(db.get("alunos", [])):
        if normalizar_texto(aluno.get("nome", "")).lower() == nome:
            return indice, aluno
    return None, None


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
    alunos = [aluno for aluno in db.get("alunos", []) if aluno.get("sala") == sala]
    return True, "Alunos da sala listados", alunos


def criar_aluno(db, usuario, nome, sala):
    permitido, mensagem = exigir_permissao(usuario, "aluno_criar")
    if not permitido:
        return False, mensagem

    if buscar_aluno(db, nome)[1] is not None:
        return False, "Aluno ja cadastrado"

    if buscar_sala(db, sala)[1] is None:
        return False, "Sala nao cadastrada"

    try:
        aluno = Aluno(nome, sala).para_dict()
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

    if buscar_sala(db, nova_sala)[1] is None:
        return False, "Sala nao cadastrada"

    existente_indice, _ = buscar_aluno(db, novo_nome)
    if existente_indice is not None and existente_indice != indice:
        return False, "Outro aluno ja usa esse nome"

    nome_antigo = alunos[indice]["nome"]

    try:
        aluno = Aluno(novo_nome, nova_sala).para_dict()
    except ValueError as erro:
        return False, str(erro)

    alunos[indice] = aluno

    if nome_antigo != aluno["nome"]:
        for ocorrencia in db.get("ocorrencias", []):
            if ocorrencia.get("aluno") == nome_antigo:
                ocorrencia["aluno"] = aluno["nome"]
        for nota in db.get("notas", []):
            if nota.get("aluno") == nome_antigo:
                nota["aluno"] = aluno["nome"]
        for falta in db.get("faltas", []):
            if falta.get("aluno") == nome_antigo:
                falta["aluno"] = aluno["nome"]

    return True, "Aluno atualizado"


def _garantir_sala_padrao(db):
    salas = db.get("salas")
    if salas is None:
        db["salas"] = []
        salas = db["salas"]
    if not isinstance(salas, list):
        return None

    _, sala_db = buscar_sala(db, SALA_PADRAO)
    if sala_db is None:
        sala_db = Sala(SALA_PADRAO).para_dict()
        salas.append(sala_db)
    return sala_db


def remover_aluno_da_sala(db, usuario, indice):
    permitido, mensagem = exigir_permissao(usuario, "aluno_editar")
    if not permitido:
        return False, mensagem

    if not isinstance(db, dict):
        return False, "Banco de dados invalido"

    with DB_LOCK:
        alunos = db.get("alunos", [])
        if not isinstance(alunos, list):
            return False, "Lista de alunos invalida"
        if not isinstance(indice, int) or not 0 <= indice < len(alunos):
            return False, "Aluno selecionado invalido"
        if not isinstance(alunos[indice], dict):
            return False, "Registro de aluno invalido"

        sala_padrao = _garantir_sala_padrao(db)
        if sala_padrao is None:
            return False, "Lista de salas invalida"

        alunos[indice]["sala"] = sala_padrao["nome"]
        alunos[indice]["sala_id"] = sala_padrao.get("id")
        return True, "Aluno removido da sala"


def remover_aluno(db, usuario, indice):
    permitido, mensagem = exigir_permissao(usuario, "aluno_remover")
    if not permitido:
        return False, mensagem

    if not isinstance(db, dict):
        return False, "Banco de dados invalido"

    with DB_LOCK:
        alunos = db.get("alunos", [])
        if not isinstance(alunos, list):
            return False, "Lista de alunos invalida"
        if not isinstance(indice, int) or not 0 <= indice < len(alunos):
            return False, "Aluno selecionado invalido"
        if not isinstance(alunos[indice], dict):
            return False, "Registro de aluno invalido"

        aluno = alunos[indice]
        aluno_id = aluno.get("id")
        nome = aluno.get("nome")
        for chave in ("ocorrencias", "notas", "faltas"):
            itens = db.get(chave, [])
            if not isinstance(itens, list):
                continue
            for item in itens:
                if not isinstance(item, dict):
                    continue
                if item.get("aluno_id") == aluno_id or item.get("aluno") == nome:
                    return False, "Nao e permitido remover aluno com registros vinculados"

        alunos.pop(indice)
        return True, "Aluno removido"


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

<<<<<<< HEAD
class UsuarioFake:
    nome = "API"
    papel = "ADM"


def resposta(data):
    print(json.dumps(data))


if __name__ == "__main__":
=======

def _executar_cli(argv=None):
    argv = sys.argv if argv is None else argv
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466
    db = carregar_db()
    comando, body, erro = parse_comando_json(argv)

    try:
        if erro:
            return resposta_erro(erro)

        usuario, mensagem_auth = autenticar_solicitante(db, body)
        if usuario is None:
            return resposta_erro(mensagem_auth)

        if comando == "criar":
            sucesso, mensagem = criar_aluno(db, usuario, body["nome"], body["sala"])
            if sucesso:
                salvar_db(db)
            return resposta_servico(sucesso, mensagem)

        if comando == "listar":
            sucesso, mensagem, dados = listar_alunos(db, usuario)
            return resposta_servico(sucesso, mensagem, dados=dados)

        if comando == "editar":
            sucesso, mensagem = editar_aluno(
                db,
                usuario,
                body["indice"],
                body["nome"],
                body["sala"],
            )
            if sucesso:
                salvar_db(db)
            return resposta_servico(sucesso, mensagem)

        if comando == "remover_sala":
            sucesso, mensagem = remover_aluno_da_sala(db, usuario, body["indice"])
            if sucesso:
                salvar_db(db)
            return resposta_servico(sucesso, mensagem)

        if comando == "remover":
            sucesso, mensagem = remover_aluno(db, usuario, body["indice"])
            if sucesso:
                salvar_db(db)
            return resposta_servico(sucesso, mensagem)

        if comando == "visualizar":
            sucesso, mensagem, dados = visualizar_aluno(db, usuario, body["nome"])
            return resposta_servico(sucesso, mensagem, dados=dados)

        return resposta_erro("Comando invalido")
    except (KeyError, TypeError, ValueError):
        return resposta_erro("Entrada invalida")
    except Exception:
        return resposta_erro("Erro interno ao executar comando")


if __name__ == "__main__":
    imprimir_resposta(_executar_cli())
