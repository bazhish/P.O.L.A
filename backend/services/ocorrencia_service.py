import time
import tracemalloc

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


def executar_teste_estresse():
    from models.aluno import Aluno
    from models.usuario import Usuario
    from services.sala_service import criar_sala

    quantidade = 50_000
    db = criar_db_vazio(incluir_admin=False)
    adm = Usuario("stress_adm", "ADM")
    professor = Usuario("stress_professor", "PROFESSOR")
    coordenador = Usuario("stress_coordenador", "COORDENADOR")
    diretor = Usuario("stress_diretor", "DIRETOR")

    db["usuarios"].extend([
        adm.para_dict(),
        professor.para_dict(),
        coordenador.para_dict(),
        diretor.para_dict(),
    ])

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
