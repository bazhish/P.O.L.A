import getpass
import os
from datetime import datetime

from utils.security import validar_senha


ROLES = ("PROFESSOR", "COORDENADOR", "DIRETOR", "ADM")

PAPEIS_LEGADOS = {
    "PROF": "PROFESSOR",
    "ADMIN": "ADM",
    "ADMINISTRADOR": "ADM",
}

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
        "aluno_criar",
        "aluno_editar",
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
        "aluno_editar",
        "aluno_visualizar",
        "sala_visualizar",
        "nota_visualizar",
        "falta_visualizar",
    },
    "ADM": {"*"},
}

DEBUG_ATIVO = os.getenv("POLAR_DEBUG") == "1"
TAMANHO_MAX_NOME = 120
TAMANHO_MAX_DESCRICAO = 1000


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


def _tem_caractere_controle(valor):
    return any(ord(caractere) < 32 for caractere in valor)


def validar_nome(valor):
    valor = normalizar_texto(valor)
    return bool(valor) and len(valor) <= TAMANHO_MAX_NOME and not _tem_caractere_controle(valor)


def validar_descricao(valor):
    valor = normalizar_texto(valor)
    return bool(valor) and len(valor) <= TAMANHO_MAX_DESCRICAO and not _tem_caractere_controle(valor)


def validar_papel(papel):
    return isinstance(papel, str) and normalizar_papel(papel) in ROLES


def normalizar_papel(papel):
    papel = papel.upper().strip()
    return PAPEIS_LEGADOS.get(papel, papel)


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
    permissoes = PERMISSOES.get(normalizar_papel(papel), set())
    return "*" in permissoes or permissao in permissoes


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


def entrada_senha_segura(prompt="Senha: ", confirmar=False):
    while True:
        senha = getpass.getpass(prompt)
        if not validar_senha(senha):
            log_error("Senha deve ter pelo menos 6 caracteres")
            continue

        if confirmar:
            confirmacao = getpass.getpass("Confirmar senha: ")
            if senha != confirmacao:
                log_error("As senhas nao conferem")
                continue

        return senha


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
