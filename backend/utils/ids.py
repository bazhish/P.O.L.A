from uuid import uuid4
from uuid import UUID


def gerar_id():
    return uuid4().hex


def id_valido(valor):
    if not isinstance(valor, str):
        return False
    try:
        UUID(valor.strip())
        return True
    except (AttributeError, TypeError, ValueError):
        return False


def garantir_id(valor=None):
    if valor and id_valido(valor):
        return valor.strip()
    return gerar_id()
