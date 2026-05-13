<<<<<<< HEAD
import time
import tracemalloc
import sys
import json
=======
import sys
import time
import tracemalloc

from copy import deepcopy
from datetime import datetime, timedelta, timezone
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466

from utils.db import carregar_db, salvar_db
from models.ocorrencia import Ocorrencia
from services.aluno_service import buscar_aluno
<<<<<<< HEAD
from utils.db import criar_db_vazio
=======
from utils.cli import autenticar_solicitante, parse_comando_json
from utils.db import DB_LOCK, criar_db_vazio
from utils.ids import garantir_id
from utils.responses import imprimir_resposta, resposta_erro, resposta_servico
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466
from utils.validators import (
    CATEGORIAS,
    PRIORIDADES,
    exigir_permissao,
    log_info,
    validar_transicao_status,
)


<<<<<<< HEAD
=======
SPAM_DUPLICADO_SEGUNDOS = 300
SPAM_JANELA_SEGUNDOS = 60
SPAM_LIMITE_POR_USUARIO = 60


def _obter_ocorrencias(db, criar=False):
    if not isinstance(db, dict):
        return None, "Banco de dados invalido"

    ocorrencias = db.get("ocorrencias")
    if ocorrencias is None:
        if criar:
            db["ocorrencias"] = []
            return db["ocorrencias"], None
        return [], None

    if not isinstance(ocorrencias, list):
        return None, "Lista de ocorrencias invalida"

    return ocorrencias, None


def _registro_ocorrencia_valido(registro):
    return isinstance(registro, dict)


def _historico_valido(historico):
    if not isinstance(historico, list):
        return False
    if not historico:
        return False

    for item in historico:
        if not isinstance(item, dict):
            return False
        if not validar_status(item.get("status")):
            return False

    return True


def _copiar_ocorrencias(ocorrencias):
    return deepcopy(ocorrencias)


def _parse_data(valor):
    if not isinstance(valor, str) or not valor:
        return None
    try:
        data = datetime.fromisoformat(valor)
    except ValueError:
        return None
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)
    return data.astimezone(timezone.utc)


def _data_criacao(registro):
    data = _parse_data(registro.get("criado_em"))
    if data:
        return data

    historico = registro.get("historico")
    if isinstance(historico, list) and historico:
        primeiro = historico[0]
        if isinstance(primeiro, dict):
            return _parse_data(primeiro.get("data_hora"))
    return None


def _validar_spam_ocorrencia(ocorrencias, nova_ocorrencia, usuario):
    agora = datetime.now(timezone.utc)
    inicio_duplicado = agora - timedelta(seconds=SPAM_DUPLICADO_SEGUNDOS)
    inicio_janela = agora - timedelta(seconds=SPAM_JANELA_SEGUNDOS)
    criadas_na_janela = 0
    usuario_id = getattr(usuario, "id", None)

    for ocorrencia in ocorrencias:
        if not isinstance(ocorrencia, dict):
            continue

        criada_em = _data_criacao(ocorrencia)
        mesmo_autor = (
            ocorrencia.get("criado_por_id") == usuario_id
            or normalizar_texto(ocorrencia.get("criado_por", "")).lower()
            == normalizar_texto(getattr(usuario, "nome", "")).lower()
        )

        if mesmo_autor and criada_em and criada_em >= inicio_janela:
            criadas_na_janela += 1

        if criada_em and criada_em < inicio_duplicado:
            continue

        mesma_ocorrencia = (
            ocorrencia.get("aluno_id") == nova_ocorrencia.get("aluno_id")
            and normalizar_texto(ocorrencia.get("descricao", "")).lower()
            == normalizar_texto(nova_ocorrencia.get("descricao", "")).lower()
            and ocorrencia.get("categoria") == nova_ocorrencia.get("categoria")
            and ocorrencia.get("prioridade") == nova_ocorrencia.get("prioridade")
            and mesmo_autor
        )
        if mesma_ocorrencia:
            return False, "Ocorrencia duplicada em intervalo curto"

    if criadas_na_janela >= SPAM_LIMITE_POR_USUARIO:
        return False, "Limite de ocorrencias por minuto atingido"

    return True, "Ocorrencia permitida"


>>>>>>> 7379759222222ab49d36193d4788c9bc75502466
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

<<<<<<< HEAD
    db["ocorrencias"].append(ocorrencia)
    return True, "Ocorrencia registrada"
=======
        try:
            ocorrencia = Ocorrencia(
                aluno=aluno_db["nome"],
                descricao=descricao,
                categoria=categoria,
                prioridade=prioridade,
                criado_por=usuario.nome,
                aluno_id=aluno_db.get("id"),
                criado_por_id=getattr(usuario, "id", None),
            ).para_dict()
        except ValueError as erro:
            return False, str(erro)

        nova_ocorrencia = ocorrencia
        permitido_spam, mensagem_spam = _validar_spam_ocorrencia(
            ocorrencias,
            nova_ocorrencia,
            usuario,
        )
        if not permitido_spam:
            return False, mensagem_spam

        ocorrencias.append(nova_ocorrencia)
        return True, "Ocorrencia registrada"
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466


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

<<<<<<< HEAD
    registro["status"] = novo_status
    registro.setdefault("historico", []).append({
        "acao": f"Alterado por {usuario.nome}",
        "status": novo_status,
    })
    return True, "Status atualizado"
=======
        registro = ocorrencias[indice]
        if not _registro_ocorrencia_valido(registro):
            return False, "Registro de ocorrencia invalido"

        status_atual = registro.get("status")
        valido, mensagem = validar_transicao_status(usuario.papel, status_atual, novo_status)
        if not valido:
            return False, mensagem

        historico = registro.get("historico")
        if not _historico_valido(historico):
            return False, "Historico da ocorrencia invalido"

        agora = datetime.now(timezone.utc).isoformat()
        historico.append({
            "evento_id": garantir_id(),
            "acao": f"Alterado por {usuario.nome}",
            "status": novo_status,
            "usuario": usuario.nome,
            "usuario_id": getattr(usuario, "id", None),
            "data_hora": agora,
        })
        registro["status"] = novo_status
        registro["atualizado_em"] = agora
        return True, "Status atualizado"
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466


def encerrar_ocorrencia(db, usuario, indice):
    return atualizar_status_ocorrencia(db, usuario, indice, "ENCERRADA")


def obter_historico(db, usuario, indice):
    permitido, mensagem = exigir_permissao(usuario, "ocorrencia_visualizar")
    if not permitido:
        return False, mensagem, []

    ocorrencias = db.get("ocorrencias", [])
    if not isinstance(indice, int) or not 0 <= indice < len(ocorrencias):
        return False, "Ocorrencia selecionada invalida", []

    historico = ocorrencias[indice].get("historico", [])
    return True, "Historico carregado", list(historico)

<<<<<<< HEAD
class UsuarioFake:
    nome = "API"
    papel = "ADM"

def processador_ocorrencia(aluno, descricao):
    return f"Processado: {aluno} - {descricao}"

def resposta(data):
    print(json.dumps(data))


if __name__ == "__main__":
    db = carregar_db()

    try:
        comando = sys.argv[1]

        # 🔹 CRIAR OCORRÊNCIA
        if comando == "criar":
            body = json.loads(sys.argv[2])

            sucesso, mensagem = criar_ocorrencia(
                db,
                None,  # depois você pode colocar usuário real
                body["aluno"],
                body["descricao"],
                body["categoria"],
                body["prioridade"]
            )

            if sucesso:
                salvar_db(db)

            resposta({
                "sucesso": sucesso,
                "mensagem": mensagem
            })

        # 🔹 LISTAR
        elif comando == "listar":
            sucesso, mensagem, ocorrencias = listar_ocorrencias(db, UsuarioFake())

            resposta({
                "sucesso": sucesso,
                "dados": ocorrencias,
                "mensagem": mensagem
            })

        # 🔹 ATUALIZAR STATUS
        elif comando == "status":
            body = json.loads(sys.argv[2])

            sucesso, mensagem = atualizar_status_ocorrencia(
                db,
                None,
                body["indice"],
                body["status"]
            )

            if sucesso:
                salvar_db(db)

            resposta({
                "sucesso": sucesso,
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
=======

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
            sucesso, mensagem = criar_ocorrencia(
                db,
                usuario,
                body["aluno"],
                body["descricao"],
                body["categoria"],
                body["prioridade"],
            )
            if sucesso:
                salvar_db(db)
            return resposta_servico(sucesso, mensagem)

        if comando == "listar":
            aluno = body.get("aluno")
            if aluno:
                sucesso, mensagem, dados = listar_ocorrencias_aluno(db, usuario, aluno)
            else:
                sucesso, mensagem, dados = listar_ocorrencias(db, usuario)
            return resposta_servico(sucesso, mensagem, dados=dados)

        if comando == "status":
            sucesso, mensagem = atualizar_status_ocorrencia(
                db,
                usuario,
                body["indice"],
                body["status"],
            )
            if sucesso:
                salvar_db(db)
            return resposta_servico(sucesso, mensagem)

        if comando == "historico":
            sucesso, mensagem, dados = obter_historico(db, usuario, body["indice"])
            return resposta_servico(sucesso, mensagem, dados=dados)

        return resposta_erro("Comando invalido")
    except (KeyError, TypeError, ValueError):
        return resposta_erro("Entrada invalida")
    except Exception:
        return resposta_erro("Erro interno ao executar comando")


if __name__ == "__main__":
    imprimir_resposta(_executar_cli())
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466

if comando == "criar":
    body = json.loads(sys.argv[2])

    sucesso, mensagem = criar_ocorrencia(
        db,
        usuario,
        body["aluno"],
        body["descricao"],
        body["categoria"],
        body["prioridade"]
    )

    if sucesso:
        salvar_db(db)

    resposta({
        "sucesso": sucesso,
        "mensagem": mensagem
    })


elif comando == "listar":
    sucesso, mensagem, dados = listar_ocorrencias(db, usuario)

    resposta({
        "sucesso": sucesso,
        "dados": dados,
        "mensagem": mensagem
    })
