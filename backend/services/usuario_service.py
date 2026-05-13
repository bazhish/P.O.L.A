"""Servicos de gestao de usuarios.

Mantem a administracao de usuarios separada do fluxo de autenticacao, sem
quebrar a API antiga que ainda importa funcoes por auth_service.
"""

from services.auth_service import (
    alterar_permissoes,
    buscar_usuario,
    buscar_usuario_por_id,
    criar_usuario,
    editar_usuario,
    listar_usuarios,
    remover_usuario,
)


__all__ = [
    "alterar_permissoes",
    "buscar_usuario",
    "buscar_usuario_por_id",
    "criar_usuario",
    "editar_usuario",
    "listar_usuarios",
    "remover_usuario",
]
