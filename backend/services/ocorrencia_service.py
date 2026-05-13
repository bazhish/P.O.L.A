import sys
import time
import tracemalloc

from copy import deepcopy
from datetime import datetime, timedelta, timezone

from utils.db import carregar_db, salvar_db
from models.ocorrencia import Ocorrencia
from services.aluno_service import buscar_aluno
from utils.cli import autenticar_solicitante, parse_comando_json
from utils.db import DB_LOCK, criar_db_vazio
from utils.ids import garantir_id
from utils.responses import imprimir_resposta, resposta_erro, resposta_servico
from utils.validators import (
    CATEGORIAS,
    PRIORIDADES,
    exigir_permissao,
    log_info,
    normalizar_texto,
    validar_transicao_status,
    validar_status,
)


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


def listar_ocorrencias(db, usuario):
    permitido, mensagem = exigir_permissao(usuario, "ocorrencia_visualizar")
    if not permitido:
        return False, mensagem, []

    with DB_LOCK:
        ocorrencias, erro = _obter_ocorrencias(db)
        if erro:
            return False, erro, []
        if ocorrencias is None or not all(_registro_ocorrencia_valido(ocorrencia) for ocorrencia in ocorrencias):
            return False, "Registro de ocorrencia invalido", []

        return True, "Ocorrencias listadas", _copiar_ocorrencias(ocorrencias)


def listar_ocorrencias_aluno(db, usuario, aluno):
    permitido, mensagem = exigir_permissao(usuario, "ocorrencia_visualizar")
    if not permitido:
        return False, mensagem, []

    with DB_LOCK:
        ocorrencias_db, erro = _obter_ocorrencias(db)
        if erro:
            return False, erro, []
        if ocorrencias_db is None or not all(_registro_ocorrencia_valido(ocorrencia) for ocorrencia in ocorrencias_db):
            return False, "Registro de ocorrencia invalido", []

        aluno_nome = normalizar_texto(aluno).lower()
        ocorrencias = [
            ocorrencia for ocorrencia in ocorrencias_db
            if (
                normalizar_texto(ocorrencia.get("aluno", "")).lower() == aluno_nome
                or ocorrencia.get("aluno_id") == aluno
            )
        ]
        return True, "Ocorrencias do aluno listadas", _copiar_ocorrencias(ocorrencias)


def criar_ocorrencia(db, usuario, aluno, descricao, categoria, prioridade):
    permitido, mensagem = exigir_permissao(usuario, "ocorrencia_criar")
    if not permitido:
        return False, mensagem

    with DB_LOCK:
        ocorrencias, erro = _obter_ocorrencias(db, criar=True)
        if erro or ocorrencias is None:
            return False, erro or "Erro ao obter ocorrencias"

        _, aluno_db = buscar_aluno(db, aluno)
        if aluno_db is None:
            return False, "Aluno nao cadastrado"

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


def atualizar_status_ocorrencia(db, usuario, indice, novo_status):
    permitido, mensagem = exigir_permissao(usuario, "ocorrencia_atualizar")
    if not permitido:
        return False, mensagem

    with DB_LOCK:
        ocorrencias, erro = _obter_ocorrencias(db)
        if erro or ocorrencias is None:
            return False, erro or "Erro ao obter ocorrencias"

        if not isinstance(indice, int) or not 0 <= indice < len(ocorrencias):
            return False, "Ocorrencia selecionada invalida"

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


def encerrar_ocorrencia(db, usuario, indice):
    return atualizar_status_ocorrencia(db, usuario, indice, "ENCERRADA")


def obter_historico(db, usuario, indice):
    permitido, mensagem = exigir_permissao(usuario, "ocorrencia_visualizar")
    if not permitido:
        return False, mensagem, []

    with DB_LOCK:
        ocorrencias, erro = _obter_ocorrencias(db)
        if erro or ocorrencias is None:
            return False, erro or "Erro ao obter ocorrencias", []

        if not isinstance(indice, int) or not 0 <= indice < len(ocorrencias):
            return False, "Ocorrencia selecionada invalida", []

        registro = ocorrencias[indice]
        if not _registro_ocorrencia_valido(registro):
            return False, "Registro de ocorrencia invalido", []

        historico = registro.get("historico", [])
        if not _historico_valido(historico):
            return False, "Historico da ocorrencia invalido", []

        return True, "Historico carregado", deepcopy(historico)



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


def executar_teste_estresse():
    from models.aluno import Aluno
    from models.usuario import Usuario
    from services.auth_service import autenticar
    from services.sala_service import criar_sala
    from utils.security import gerar_senha_hash

    quantidade = 50_000
    db = criar_db_vazio(incluir_admin=False)
    adm = Usuario("stress_adm", "ADM", senha_hash=gerar_senha_hash("stress_adm123"))
    professor = Usuario(
        "stress_professor",
        "PROFESSOR",
        senha_hash=gerar_senha_hash("stress_professor123"),
    )
    coordenador = Usuario(
        "stress_coordenador",
        "COORDENADOR",
        senha_hash=gerar_senha_hash("stress_coordenador123"),
    )
    diretor = Usuario("stress_diretor", "DIRETOR", senha_hash=gerar_senha_hash("stress_diretor123"))

    db["usuarios"].extend([
        adm.para_dict(),
        professor.para_dict(),
        coordenador.para_dict(),
        diretor.para_dict(),
    ])
    adm, _ = autenticar(db, "stress_adm", "stress_adm123")
    professor, _ = autenticar(db, "stress_professor", "stress_professor123")
    coordenador, _ = autenticar(db, "stress_coordenador", "stress_coordenador123")
    diretor, _ = autenticar(db, "stress_diretor", "stress_diretor123")

    assert adm is not None, "Falha na autenticacao do ADM"
    assert professor is not None, "Falha na autenticacao do PROFESSOR"
    assert coordenador is not None, "Falha na autenticacao do COORDENADOR"
    assert diretor is not None, "Falha na autenticacao do DIRETOR"

    tracemalloc.start()
    inicio_total = time.perf_counter()

    criar_sala(db, adm, "1A")

    inicio_alunos = time.perf_counter()
    for indice in range(quantidade):
        db["alunos"].append(Aluno(f"Aluno {indice}", "1A").para_dict())
    tempo_alunos = time.perf_counter() - inicio_alunos

    inicio_ocorrencias = time.perf_counter()
    for indice in range(quantidade):
        db["ocorrencias"].append(Ocorrencia(
            aluno=f"Aluno {indice}",
            descricao=f"Ocorrencia de teste {indice}",
            categoria=CATEGORIAS[indice % len(CATEGORIAS)],
            prioridade=PRIORIDADES[indice % len(PRIORIDADES)],
            criado_por=professor.nome,
        ).para_dict())
    tempo_ocorrencias = time.perf_counter() - inicio_ocorrencias

    inicio_transicoes = time.perf_counter()
    for indice in range(quantidade):
        for status, usuario in (
            ("EM_ANALISE", coordenador),
            ("RESOLVIDA", coordenador),
            ("ENCERRADA", diretor),
        ):
            sucesso, mensagem = atualizar_status_ocorrencia(db, usuario, indice, status)
            if not sucesso:
                raise RuntimeError(mensagem)
    tempo_transicoes = time.perf_counter() - inicio_transicoes

    tempo_total = time.perf_counter() - inicio_total
    memoria_atual, pico_memoria = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    resultado = {
        "alunos": quantidade,
        "ocorrencias": quantidade,
        "transicoes": quantidade * 3,
        "tempo_alunos_seg": round(tempo_alunos, 3),
        "tempo_ocorrencias_seg": round(tempo_ocorrencias, 3),
        "tempo_transicoes_seg": round(tempo_transicoes, 3),
        "tempo_total_seg": round(tempo_total, 3),
        "memoria_atual_mb": round(memoria_atual / 1024 / 1024, 2),
        "pico_memoria_mb": round(pico_memoria / 1024 / 1024, 2),
    }

    log_info("Teste de estresse concluido")
    for chave, valor in resultado.items():
        print(f"{chave}: {valor}")

    return resultado
