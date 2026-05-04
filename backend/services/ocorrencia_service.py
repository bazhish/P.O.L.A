import time
import tracemalloc
import sys

from models.ocorrencia import Ocorrencia
from services.aluno_service import buscar_aluno
from utils.db import criar_db_vazio
from utils.validators import (
    CATEGORIAS,
    PRIORIDADES,
    exigir_permissao,
    log_info,
    validar_transicao_status,
)


def listar_ocorrencias(db, usuario):
    permitido, mensagem = exigir_permissao(usuario, "ocorrencia_visualizar")
    if not permitido:
        return False, mensagem, []
    return True, "Ocorrencias listadas", list(db.get("ocorrencias", []))


def listar_ocorrencias_aluno(db, usuario, aluno):
    permitido, mensagem = exigir_permissao(usuario, "ocorrencia_visualizar")
    if not permitido:
        return False, mensagem, []

    ocorrencias = [
        ocorrencia for ocorrencia in db.get("ocorrencias", [])
        if ocorrencia.get("aluno") == aluno
    ]
    return True, "Ocorrencias do aluno listadas", ocorrencias


def criar_ocorrencia(db, usuario, aluno, descricao, categoria, prioridade):
    permitido, mensagem = exigir_permissao(usuario, "ocorrencia_criar")
    if not permitido:
        return False, mensagem

    if buscar_aluno(db, aluno)[1] is None:
        return False, "Aluno nao cadastrado"

    try:
        ocorrencia = Ocorrencia(
            aluno=aluno,
            descricao=descricao,
            categoria=categoria,
            prioridade=prioridade,
            criado_por=usuario.nome,
        ).para_dict()
    except ValueError as erro:
        return False, str(erro)

    db["ocorrencias"].append(ocorrencia)
    return True, "Ocorrencia registrada"


def atualizar_status_ocorrencia(db, usuario, indice, novo_status):
    permitido, mensagem = exigir_permissao(usuario, "ocorrencia_atualizar")
    if not permitido:
        return False, mensagem

    ocorrencias = db.get("ocorrencias", [])
    if not isinstance(indice, int) or not 0 <= indice < len(ocorrencias):
        return False, "Ocorrencia selecionada invalida"

    registro = ocorrencias[indice]
    status_atual = registro.get("status")
    valido, mensagem = validar_transicao_status(usuario.papel, status_atual, novo_status)
    if not valido:
        return False, mensagem

    registro["status"] = novo_status
    registro.setdefault("historico", []).append({
        "acao": f"Alterado por {usuario.nome}",
        "status": novo_status,
    })
    return True, "Status atualizado"


def obter_historico(db, usuario, indice):
    permitido, mensagem = exigir_permissao(usuario, "ocorrencia_visualizar")
    if not permitido:
        return False, mensagem, []

    ocorrencias = db.get("ocorrencias", [])
    if not isinstance(indice, int) or not 0 <= indice < len(ocorrencias):
        return False, "Ocorrencia selecionada invalida", []

    historico = ocorrencias[indice].get("historico", [])
    return True, "Historico carregado", list(historico)

def processador_ocorrencia(aluno, descricao):
    return f"Processado: {aluno} - {descricao}"

if __name__ == "__main__":
    aluno = sys.argv[1]
    descricao = sys.argv[2]

    resultado = processador_ocorrencia(aluno, descricao)
    print(resultado)
