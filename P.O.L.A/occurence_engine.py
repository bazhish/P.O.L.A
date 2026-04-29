import json
import os
import sys
import tempfile
import time
import tracemalloc
from datetime import datetime


# =========================
# CONFIG
# =========================

CATEGORIAS = [
    "Comportamento inadequado",
    "Atraso",
    "Falta",
    "Não fez atividade",
    "Desrespeito ao professor",
    "Uso de celular",
    "Briga",
    "Bullying",
    "Conversas paralelas",
    "Dano ao patrimônio",
]

PRIORIDADES = ["baixa", "media", "alta"]

PAPEIS_PERMITIDOS = ("PROFESSOR", "COORDENADOR", "DIRETOR")
STATUS_VALIDOS = ("REGISTRADA", "EM_ANALISE", "RESOLVIDA", "ENCERRADA")

TRANSICOES_ESPERADAS = {
    "REGISTRADA": "EM_ANALISE",
    "EM_ANALISE": "RESOLVIDA",
    "RESOLVIDA": "ENCERRADA",
}

TRANSICOES_POR_PAPEL = {
    "PROFESSOR": set(),
    "COORDENADOR": {
        ("REGISTRADA", "EM_ANALISE"),
        ("EM_ANALISE", "RESOLVIDA"),
    },
    "DIRETOR": {
        ("RESOLVIDA", "ENCERRADA"),
    },
}

ARQUIVO_DB = "banco_dados.json"
DEBUG_ATIVO = os.getenv("POLAR_DEBUG") == "1"


# =========================
# UTILS: LOGGING
# =========================

def log_info(mensagem):
    print(f"[INFO] {mensagem}")


def log_error(mensagem):
    print(f"[ERROR] {mensagem}")


def log_debug(mensagem):
    if DEBUG_ATIVO:
        print(f"[DEBUG] {mensagem}")


# =========================
# UTILS: VALIDATION
# =========================

def validar_categoria(indice):
    return isinstance(indice, int) and 0 <= indice < len(CATEGORIAS)


def validar_prioridade(indice):
    return isinstance(indice, int) and 0 <= indice < len(PRIORIDADES)


def validar_papel(papel):
    return papel in PAPEIS_PERMITIDOS


def validar_status(status):
    return status in STATUS_VALIDOS


def validar_transicao_status(papel, atual, novo):
    if not validar_papel(papel):
        return False, f"Papel desconhecido rejeitado: {papel}"

    if not validar_status(atual):
        return False, f"Status atual inválido: {atual}"

    if not validar_status(novo):
        return False, f"Novo status inválido: {novo}"

    esperado = TRANSICOES_ESPERADAS.get(atual)
    if esperado is None:
        return False, "Ocorrência já está encerrada"

    if novo != esperado:
        return False, f"Transição inválida: {atual} deve ir para {esperado}"

    if (atual, novo) not in TRANSICOES_POR_PAPEL[papel]:
        return False, f"{papel} não pode alterar de {atual} para {novo}"

    return True, "Transição permitida"


def entrada_int_segura(prompt, limite_max):
    while True:
        valor_bruto = input(prompt).strip()

        try:
            valor = int(valor_bruto)
        except ValueError:
            log_error("Digite um número válido")
            continue

        if 0 <= valor <= limite_max:
            return valor

        log_error(f"Escolha um número entre 0 e {limite_max}")


def entrada_texto_obrigatoria(prompt):
    while True:
        valor = input(prompt).strip()
        if valor:
            return valor

        log_error("Este campo é obrigatório")


# =========================
# UTILS: DATABASE
# =========================

def criar_db_vazio():
    return {"usuarios": [], "ocorrencias": []}


def normalizar_historico(historico, status):
    if not isinstance(historico, list):
        return [{"acao": "Histórico recriado", "status": status}]

    itens_validos = []
    for item in historico:
        if not isinstance(item, dict):
            continue

        acao = item.get("acao")
        status_item = item.get("status")
        if isinstance(acao, str) and validar_status(status_item):
            itens_validos.append({"acao": acao, "status": status_item})

    if not itens_validos:
        itens_validos.append({"acao": "Histórico recriado", "status": status})

    return itens_validos


def normalizar_ocorrencia(dados):
    if not isinstance(dados, dict):
        return None, True

    aluno = dados.get("aluno")
    descricao = dados.get("descricao")
    categoria = dados.get("categoria")
    prioridade = dados.get("prioridade")
    status = dados.get("status", "REGISTRADA")
    criado_por = dados.get("criado_por", "sistema")

    if not isinstance(aluno, str) or not aluno.strip():
        return None, True

    if not isinstance(descricao, str) or not descricao.strip():
        return None, True

    if categoria not in CATEGORIAS:
        return None, True

    if prioridade not in PRIORIDADES:
        return None, True

    if not validar_status(status):
        return None, True

    if not isinstance(criado_por, str) or not criado_por.strip():
        criado_por = "sistema"

    historico = normalizar_historico(dados.get("historico"), status)

    normalizada = {
        "aluno": aluno.strip(),
        "descricao": descricao.strip(),
        "categoria": categoria,
        "prioridade": prioridade,
        "status": status,
        "criado_por": criado_por.strip(),
        "historico": historico,
    }

    return normalizada, normalizada != dados


def normalizar_db(dados):
    if not isinstance(dados, dict):
        return criar_db_vazio(), True

    usuarios = dados.get("usuarios", [])
    if not isinstance(usuarios, list):
        usuarios = []
        alterado = True
    else:
        alterado = False

    ocorrencias = dados.get("ocorrencias", [])
    if not isinstance(ocorrencias, list):
        ocorrencias = []
        alterado = True

    ocorrencias_normalizadas = []
    for ocorrencia in ocorrencias:
        normalizada, ocorrencia_alterada = normalizar_ocorrencia(ocorrencia)
        if normalizada is None:
            alterado = True
            continue

        ocorrencias_normalizadas.append(normalizada)
        alterado = alterado or ocorrencia_alterada

    db_normalizado = {
        "usuarios": usuarios,
        "ocorrencias": ocorrencias_normalizadas,
    }

    return db_normalizado, alterado or db_normalizado != dados


def salvar_db(dados, caminho=ARQUIVO_DB):
    dados_normalizados, _ = normalizar_db(dados)
    pasta = os.path.dirname(os.path.abspath(caminho)) or "."
    os.makedirs(pasta, exist_ok=True)

    fd, temporario = tempfile.mkstemp(
        prefix=".polar-",
        suffix=".tmp",
        dir=pasta,
        text=True,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
            json.dump(dados_normalizados, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")

        os.replace(temporario, caminho)
    except Exception:
        if os.path.exists(temporario):
            os.remove(temporario)
        raise


def recriar_db_corrompido(caminho):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = f"{caminho}.corrompido-{timestamp}"

    try:
        os.replace(caminho, backup)
        log_error(f"Aviso: JSON corrompido detectado. Backup criado em {backup}")
    except OSError as erro:
        log_error(f"Aviso: JSON corrompido detectado, mas o backup falhou: {erro}")

    db_vazio = criar_db_vazio()
    salvar_db(db_vazio, caminho)
    return db_vazio


def carregar_db(caminho=ARQUIVO_DB):
    if not os.path.exists(caminho):
        return criar_db_vazio()

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except json.JSONDecodeError:
        return recriar_db_corrompido(caminho)
    except OSError as erro:
        log_error(f"Não foi possível ler o banco de dados: {erro}")
        return criar_db_vazio()

    dados_normalizados, alterado = normalizar_db(dados)
    if alterado:
        log_error("Aviso: banco tinha dados inválidos e foi normalizado")
        salvar_db(dados_normalizados, caminho)

    return dados_normalizados


# =========================
# ENTITIES
# =========================

class Usuario:
    def __init__(self, nome_usuario, papel):
        papel = papel.upper().strip()
        if not validar_papel(papel):
            raise ValueError(f"Papel inválido: {papel}")

        self.nome_usuario = nome_usuario.strip()
        self.papel = papel


class Professor(Usuario):
    def __init__(self, nome_usuario):
        super().__init__(nome_usuario, "PROFESSOR")


class Coordenador(Usuario):
    def __init__(self, nome_usuario):
        super().__init__(nome_usuario, "COORDENADOR")


class Diretor(Usuario):
    def __init__(self, nome_usuario):
        super().__init__(nome_usuario, "DIRETOR")


class Aluno:
    def __init__(self, nome):
        if not nome or not nome.strip():
            raise ValueError("Nome do aluno é obrigatório")

        self.nome = nome.strip()


class Ocorrencia:
    def __init__(self, aluno, descricao, categoria, prioridade, criado_por):
        if categoria not in CATEGORIAS:
            raise ValueError("Categoria inválida")

        if prioridade not in PRIORIDADES:
            raise ValueError("Prioridade inválida")

        if not descricao or not descricao.strip():
            raise ValueError("Descrição é obrigatória")

        if not criado_por or not criado_por.strip():
            raise ValueError("Usuário criador é obrigatório")

        self.aluno = Aluno(aluno).nome
        self.descricao = descricao.strip()
        self.categoria = categoria
        self.prioridade = prioridade
        self.status = "REGISTRADA"
        self.criado_por = criado_por.strip()
        self.historico = []
        self.registrar_log("Criada")

    def registrar_log(self, acao):
        self.historico.append({
            "acao": acao,
            "status": self.status,
        })

    def para_dict(self):
        return {
            "aluno": self.aluno,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "prioridade": self.prioridade,
            "status": self.status,
            "criado_por": self.criado_por,
            "historico": self.historico,
        }


# =========================
# SERVICES
# =========================

def validar_usuario(usuario):
    papel = getattr(usuario, "papel", None)
    if not validar_papel(papel):
        return False, f"Papel desconhecido rejeitado: {papel}"

    nome_usuario = getattr(usuario, "nome_usuario", "")
    if not isinstance(nome_usuario, str) or not nome_usuario.strip():
        return False, "Usuário inválido"

    return True, "Usuário válido"


def criar_ocorrencia_service(db, usuario, aluno, descricao, categoria, prioridade):
    usuario_valido, mensagem = validar_usuario(usuario)
    if not usuario_valido:
        return False, mensagem

    try:
        ocorrencia = Ocorrencia(
            aluno=aluno,
            descricao=descricao,
            categoria=categoria,
            prioridade=prioridade,
            criado_por=usuario.nome_usuario,
        )
    except ValueError as erro:
        return False, str(erro)

    db["ocorrencias"].append(ocorrencia.para_dict())
    return True, "Ocorrência registrada"


def atualizar_status_ocorrencia(registro, novo_status, usuario):
    usuario_valido, mensagem = validar_usuario(usuario)
    if not usuario_valido:
        return False, mensagem

    if not isinstance(registro, dict):
        return False, "Registro de ocorrência inválido"

    status_atual = registro.get("status")
    valido, mensagem = validar_transicao_status(usuario.papel, status_atual, novo_status)
    if not valido:
        return False, mensagem

    log_debug(
        f"Atualizando ocorrência de {status_atual} para {novo_status} "
        f"como {usuario.papel}"
    )

    registro["status"] = novo_status
    registro.setdefault("historico", []).append({
        "acao": f"Alterado por {usuario.nome_usuario}",
        "status": novo_status,
    })
    return True, "Status atualizado"


# =========================
# INTERFACE CLI
# =========================

def login():
    mapa_usuarios = {
        1: Professor,
        2: Coordenador,
        3: Diretor,
    }

    print("\nLOGIN")
    print("1 - Professor")
    print("2 - Coordenador")
    print("3 - Diretor")
    print("0 - Sair")

    escolha = entrada_int_segura("Escolha: ", 3)
    if escolha == 0:
        return None

    nome_usuario = entrada_texto_obrigatoria("Usuário: ")
    return mapa_usuarios[escolha](nome_usuario)


def exibir_categorias():
    print("\nCategorias:")
    for indice, categoria in enumerate(CATEGORIAS):
        print(f"{indice} - {categoria}")


def exibir_prioridades():
    print("\nPrioridade:")
    for indice, prioridade in enumerate(PRIORIDADES):
        print(f"{indice} - {prioridade}")


def criar_ocorrencia(usuario, db):
    print("\nNOVA OCORRÊNCIA")

    nome_aluno = entrada_texto_obrigatoria("Nome do aluno: ")
    descricao = entrada_texto_obrigatoria("Descrição: ")

    exibir_categorias()
    indice_categoria = entrada_int_segura("Escolha categoria: ", len(CATEGORIAS) - 1)
    if not validar_categoria(indice_categoria):
        log_error("Categoria inválida")
        return False

    exibir_prioridades()
    indice_prioridade = entrada_int_segura("Escolha prioridade: ", len(PRIORIDADES) - 1)
    if not validar_prioridade(indice_prioridade):
        log_error("Prioridade inválida")
        return False

    sucesso, mensagem = criar_ocorrencia_service(
        db=db,
        usuario=usuario,
        aluno=nome_aluno,
        descricao=descricao,
        categoria=CATEGORIAS[indice_categoria],
        prioridade=PRIORIDADES[indice_prioridade],
    )

    if not sucesso:
        log_error(mensagem)
        return False

    salvar_db(db)
    log_info(mensagem)
    return True


def listar_ocorrencias(db):
    print("\nOCORRÊNCIAS")

    ocorrencias = db.get("ocorrencias", [])
    if not ocorrencias:
        log_info("Nenhuma ocorrência cadastrada")
        return

    for indice, ocorrencia in enumerate(ocorrencias):
        print(
            f"{indice} - {ocorrencia['aluno']} | "
            f"{ocorrencia['status']} | {ocorrencia['categoria']}"
        )


def atualizar_ocorrencia(usuario, db):
    ocorrencias = db.get("ocorrencias", [])
    if not ocorrencias:
        log_info("Nenhuma ocorrência disponível para atualizar")
        return False

    listar_ocorrencias(db)
    indice = entrada_int_segura("Escolha ocorrência: ", len(ocorrencias) - 1)
    registro = ocorrencias[indice]

    print("\nNovo status:")
    print("1 - EM_ANALISE")
    print("2 - RESOLVIDA")
    print("3 - ENCERRADA")
    print("0 - Cancelar")

    mapa_status = {
        1: "EM_ANALISE",
        2: "RESOLVIDA",
        3: "ENCERRADA",
    }

    escolha = entrada_int_segura("Escolha: ", 3)
    if escolha == 0:
        log_info("Atualização cancelada")
        return False

    novo_status = mapa_status[escolha]
    sucesso, mensagem = atualizar_status_ocorrencia(registro, novo_status, usuario)

    if not sucesso:
        log_error(mensagem)
        return False

    salvar_db(db)
    log_info(mensagem)
    return True


def exibir_menu(usuario):
    print("\nMENU")

    if usuario.papel == "PROFESSOR":
        print("1 - Criar ocorrência")
        print("2 - Ver ocorrências")
    else:
        print("1 - Ver ocorrências")
        print("2 - Atualizar ocorrência")

    print("0 - Sair")


def executar_cli():
    db = carregar_db()
    usuario = login()
    if not usuario:
        log_info("Sistema encerrado")
        return

    while True:
        exibir_menu(usuario)
        opcao = entrada_int_segura("Escolha: ", 2)

        if opcao == 0:
            log_info("Sistema encerrado")
            break

        if usuario.papel == "PROFESSOR":
            if opcao == 1:
                criar_ocorrencia(usuario, db)
            elif opcao == 2:
                listar_ocorrencias(db)
            continue

        if opcao == 1:
            listar_ocorrencias(db)
        elif opcao == 2:
            atualizar_ocorrencia(usuario, db)


# =========================
# STRESS TEST
# =========================

def executar_teste_estresse():
    quantidade = 50_000
    db = criar_db_vazio()
    professor = Professor("stress_professor")
    coordenador = Coordenador("stress_coordenador")
    diretor = Diretor("stress_diretor")

    tracemalloc.start()
    inicio_total = time.perf_counter()

    inicio_criacao = time.perf_counter()
    for indice in range(quantidade):
        categoria = CATEGORIAS[indice % len(CATEGORIAS)]
        prioridade = PRIORIDADES[indice % len(PRIORIDADES)]
        sucesso, mensagem = criar_ocorrencia_service(
            db=db,
            usuario=professor,
            aluno=f"Aluno {indice}",
            descricao=f"Ocorrência de teste {indice}",
            categoria=categoria,
            prioridade=prioridade,
        )
        if not sucesso:
            raise RuntimeError(mensagem)
    tempo_criacao = time.perf_counter() - inicio_criacao

    inicio_transicoes = time.perf_counter()
    for ocorrencia in db["ocorrencias"]:
        for novo_status, usuario in (
            ("EM_ANALISE", coordenador),
            ("RESOLVIDA", coordenador),
            ("ENCERRADA", diretor),
        ):
            sucesso, mensagem = atualizar_status_ocorrencia(
                ocorrencia,
                novo_status,
                usuario,
            )
            if not sucesso:
                raise RuntimeError(mensagem)
    tempo_transicoes = time.perf_counter() - inicio_transicoes

    tempo_total = time.perf_counter() - inicio_total
    memoria_atual, pico_memoria = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    resultado = {
        "ocorrencias": quantidade,
        "transicoes": quantidade * 3,
        "tempo_criacao_seg": round(tempo_criacao, 3),
        "tempo_transicoes_seg": round(tempo_transicoes, 3),
        "tempo_total_seg": round(tempo_total, 3),
        "memoria_atual_mb": round(memoria_atual / 1024 / 1024, 2),
        "pico_memoria_mb": round(pico_memoria / 1024 / 1024, 2),
    }

    log_info("Teste de estresse concluído")
    for chave, valor in resultado.items():
        print(f"{chave}: {valor}")

    return resultado


def main(argv=None):
    argumentos = sys.argv[1:] if argv is None else argv

    if "--stress" in argumentos:
        executar_teste_estresse()
        return

    executar_cli()


if __name__ == "__main__":
    main()
