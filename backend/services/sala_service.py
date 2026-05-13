from models.sala import Sala
<<<<<<< HEAD
=======
from utils.cli import autenticar_solicitante, parse_comando_json
from utils.db import DB_LOCK
from utils.responses import imprimir_resposta, resposta_erro, resposta_servico
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466
from utils.validators import exigir_permissao, normalizar_texto

import sys
from utils.db import carregar_db, salvar_db


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
        nova_sala = Sala(novo_nome).para_dict()
    except ValueError as erro:
        return False, str(erro)

    nome_antigo = salas[indice]["nome"]
    salas[indice] = nova_sala

    for aluno in db.get("alunos", []):
        if aluno.get("sala") == nome_antigo:
            aluno["sala"] = nova_sala["nome"]

    return True, "Sala atualizada"

<<<<<<< HEAD
class UsuarioFake:
    nome = "API"
    papel = "ADM"


def resposta(data):
    print(json.dumps(data))
=======

def remover_sala(db, usuario, indice):
    permitido, mensagem = exigir_permissao(usuario, "sala_remover")
    if not permitido:
        return False, mensagem

    if not isinstance(db, dict):
        return False, "Banco de dados invalido"

    with DB_LOCK:
        salas = db.get("salas", [])
        if not isinstance(salas, list):
            return False, "Lista de salas invalida"
        if not isinstance(indice, int) or not 0 <= indice < len(salas):
            return False, "Sala selecionada invalida"
        if not isinstance(salas[indice], dict):
            return False, "Registro de sala invalido"

        sala = salas[indice]
        alunos = db.get("alunos", [])
        if isinstance(alunos, list):
            for aluno in alunos:
                if not isinstance(aluno, dict):
                    continue
                if aluno.get("sala_id") == sala.get("id") or aluno.get("sala") == sala.get("nome"):
                    return False, "Nao e permitido remover sala com alunos vinculados"

        salas.pop(indice)
        return True, "Sala removida"


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
            sucesso, mensagem = criar_sala(db, usuario, body["nome"])
            if sucesso:
                salvar_db(db)
            return resposta_servico(sucesso, mensagem)

        if comando == "listar":
            sucesso, mensagem, dados = listar_salas(db, usuario)
            return resposta_servico(sucesso, mensagem, dados=dados)

        if comando == "editar":
            sucesso, mensagem = editar_sala(db, usuario, body["indice"], body["nome"])
            if sucesso:
                salvar_db(db)
            return resposta_servico(sucesso, mensagem)

        if comando == "remover":
            sucesso, mensagem = remover_sala(db, usuario, body["indice"])
            if sucesso:
                salvar_db(db)
            return resposta_servico(sucesso, mensagem)

        return resposta_erro("Comando invalido")
    except (KeyError, TypeError, ValueError):
        return resposta_erro("Entrada invalida")
    except Exception:
        return resposta_erro("Erro interno ao executar comando")
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466


if __name__ == "__main__":
    imprimir_resposta(_executar_cli())
