"""Fachada de persistencia JSON da engine POLAR.

Esta camada mantem a engine preparada para trocar a implementacao de
persistencia no futuro, sem acoplar os servicos de negocio diretamente a um
banco SQL/Supabase neste momento.
"""

from utils.db import carregar_db, criar_db_vazio, normalizar_db, salvar_db


def carregar(caminho=None):
    return carregar_db(caminho)


def salvar(dados, caminho=None):
    salvar_db(dados, caminho)
    return True, "Banco de dados salvo"


def validar_integridade(dados):
    normalizado, alterado = normalizar_db(dados)
    return True, "Banco de dados validado", {
        "normalizado": normalizado,
        "alterado": alterado,
    }


def novo_banco(incluir_admin=True):
    return criar_db_vazio(incluir_admin=incluir_admin)
