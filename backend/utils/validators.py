import os
from datetime import datetime


ROLES = ("PROFESSOR", "COORDENADOR", "DIRETOR", "ADM")

STATUS_VALIDOS = ("REGISTRADA", "EM_ANALISE", "RESOLVIDA", "ENCERRADA")

CATEGORIAS = (
    "Comportamento inadequado",
    "Atraso",
    "Falta",
    "Nao fez atividade",
    "Desrespeito ao professor",
    "Uso de celular",
    "Briga",
    "Bullying",
    "Conversas paralelas",
    "Dano ao patrimonio",
)

PRIORIDADES = ("baixa", "media", "alta")

CATEGORIAS_LEGADAS = {
    "Não fez atividade": "Nao fez atividade",
    "NÃ£o fez atividade": "Nao fez atividade",
    "Dano ao patrimônio": "Dano ao patrimonio",
    "Dano ao patrimÃ´nio": "Dano ao patrimonio",
    "Conversa paralelas": "Conversas paralelas",
}

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
    "ADM": {
        ("REGISTRADA", "EM_ANALISE"),
        ("EM_ANALISE", "RESOLVIDA"),
        ("RESOLVIDA", "ENCERRADA"),
    },
}

PERMISSOES = {
    "PROFESSOR": {
        "ocorrencia_criar",
        "ocorrencia_visualizar",
        "aluno_visualizar",
        "sala_visualizar",
        "nota_criar",
        "nota_visualizar",
        "falta_criar",
        "falta_visualizar",
    },
    "COORDENADOR": {
        "ocorrencia_criar",
        "ocorrencia_visualizar",
        "ocorrencia_atualizar",
        "aluno_visualizar",
        "sala_visualizar",
        "nota_criar",
        "nota_visualizar",
        "falta_criar",
        "falta_visualizar",
    },
    "DIRETOR": {
        "ocorrencia_visualizar",
        "ocorrencia_atualizar",
        "aluno_visualizar",
        "sala_visualizar",
        "nota_visualizar",
        "falta_visualizar",
    },
    "ADM": {"*"},
}

DEBUG_ATIVO = os.getenv("POLAR_DEBUG") == "1"
<<<<<<< HEAD
=======
TAMANHO_MAX_NOME = 120
TAMANHO_MAX_DESCRICAO = 1000
PERMISSAO_ADM_EXPLICITA = "ADM"
PERMISSOES_CONHECIDAS = {
    permissao
    for permissoes_papel in PERMISSOES.values()
    for permissao in permissoes_papel
}
PERMISSOES_CONHECIDAS.add(PERMISSAO_ADM_EXPLICITA)
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466


def log_info(mensagem):
    print(f"[INFO] {mensagem}")


def log_error(mensagem):
    print(f"[ERROR] {mensagem}")


def log_debug(mensagem):
    if DEBUG_ATIVO:
        print(f"[DEBUG] {mensagem}")


def normalizar_texto(valor):
    if not isinstance(valor, str):
        return ""
    return " ".join(valor.strip().split())


def validar_nome(valor):
    return bool(normalizar_texto(valor))


def validar_papel(papel):
    return isinstance(papel, str) and papel.upper().strip() in ROLES


def normalizar_papel(papel):
    return papel.upper().strip()


def normalizar_permissao(permissao):
    if not isinstance(permissao, str):
        return ""

    permissao = normalizar_texto(permissao)
    if permissao.upper() in {"ADM", "ADMIN", "ADMINISTRADOR", "*"}:
        return PERMISSAO_ADM_EXPLICITA
    return permissao.lower()


def normalizar_permissoes(permissoes):
    if permissoes is None:
        return []

    if isinstance(permissoes, str):
        permissoes = [permissoes]

    if not isinstance(permissoes, (list, tuple, set)):
        return []

    normalizadas = []
    for permissao in permissoes:
        permissao = normalizar_permissao(permissao)
        if permissao and permissao not in normalizadas:
            normalizadas.append(permissao)
    return normalizadas


def normalizar_categoria(valor):
    valor = normalizar_texto(valor)
    return CATEGORIAS_LEGADAS.get(valor, valor)


def normalizar_prioridade(valor):
    return normalizar_texto(valor).lower()


def validar_status(status):
    return isinstance(status, str) and status in STATUS_VALIDOS


def validar_categoria(valor):
    return normalizar_categoria(valor) in CATEGORIAS


def validar_categoria_indice(indice):
    return isinstance(indice, int) and 0 <= indice < len(CATEGORIAS)


def validar_prioridade(valor):
    return normalizar_prioridade(valor) in PRIORIDADES


def validar_prioridade_indice(indice):
    return isinstance(indice, int) and 0 <= indice < len(PRIORIDADES)


def validar_nota_valor(valor):
    return isinstance(valor, (int, float)) and 0 <= float(valor) <= 10


def validar_data(data):
    if not isinstance(data, str):
        return False
    try:
        datetime.strptime(data, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def tem_permissao(usuario, permissao):
    papel = getattr(usuario, "papel", None)
    if not validar_papel(papel):
        return False

    papel = normalizar_papel(papel)
    permissoes_base = PERMISSOES.get(papel, set())
    permissoes_explicitadas = set(normalizar_permissoes(getattr(usuario, "permissoes", [])))

    if papel == "ADM" or PERMISSAO_ADM_EXPLICITA in permissoes_explicitadas:
        return True

    return permissao in permissoes_base or permissao in permissoes_explicitadas


def exigir_permissao(usuario, permissao):
    if tem_permissao(usuario, permissao):
        return True, "Permissao concedida"
    papel = getattr(usuario, "papel", "DESCONHECIDO")
    return False, f"Acesso negado para {papel}"


def validar_transicao_status(papel, atual, novo):
    if not validar_papel(papel):
        return False, f"Papel desconhecido rejeitado: {papel}"

    papel = normalizar_papel(papel)

    if not validar_status(atual):
        return False, f"Status atual invalido: {atual}"

    if not validar_status(novo):
        return False, f"Novo status invalido: {novo}"

    esperado = TRANSICOES_ESPERADAS.get(atual)
    if esperado is None:
        return False, "Ocorrencia ja esta encerrada"

    if novo != esperado:
        return False, f"Transicao invalida: {atual} deve ir para {esperado}"

    if (atual, novo) not in TRANSICOES_POR_PAPEL[papel]:
        return False, f"{papel} nao pode alterar de {atual} para {novo}"

    return True, "Transicao permitida"


def entrada_texto_segura(prompt, obrigatorio=True):
    while True:
        valor = normalizar_texto(input(prompt))
        if valor or not obrigatorio:
            return valor
        log_error("Este campo e obrigatorio")


<<<<<<< HEAD
=======
def entrada_senha_segura(prompt="Senha: ", confirmar=False):
    while True:
        senha = getpass.getpass(prompt)
        if not validar_senha(senha):
            log_error("Senha deve ter entre 8 e 128 caracteres")
            continue

        if confirmar:
            confirmacao = getpass.getpass("Confirmar senha: ")
            if senha != confirmacao:
                log_error("As senhas nao conferem")
                continue

        return senha


>>>>>>> 7379759222222ab49d36193d4788c9bc75502466
def entrada_int_segura(prompt, limite_max, limite_min=0):
    while True:
        valor_bruto = input(prompt).strip()
        try:
            valor = int(valor_bruto)
        except ValueError:
            log_error("Digite um numero valido")
            continue

        if limite_min <= valor <= limite_max:
            return valor

        log_error(f"Escolha um numero entre {limite_min} e {limite_max}")


def entrada_float_segura(prompt, limite_min=0.0, limite_max=10.0):
    while True:
        valor_bruto = input(prompt).strip().replace(",", ".")
        try:
            valor = float(valor_bruto)
        except ValueError:
            log_error("Digite um numero valido")
            continue

        if limite_min <= valor <= limite_max:
            return valor

        log_error(f"Escolha um valor entre {limite_min} e {limite_max}")
