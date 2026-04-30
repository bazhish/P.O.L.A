from uuid import uuid4


def gerar_id():
    return uuid4().hex


def id_valido(valor):
    return isinstance(valor, str) and bool(valor.strip())


def garantir_id(valor=None):
    return valor.strip() if id_valido(valor) else gerar_id()
