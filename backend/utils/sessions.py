import secrets
import threading
from datetime import datetime, timezone


_SESSOES = {}
_LOCK = threading.RLock()


def _permissoes_sessao(usuario):
    permissoes = getattr(usuario, "permissoes", [])
    if isinstance(permissoes, str):
        permissoes = [permissoes]
    if not isinstance(permissoes, (list, tuple, set)):
        return tuple()
    return tuple(sorted(str(permissao).strip() for permissao in permissoes if str(permissao).strip()))


def criar_sessao(usuario):
    token = secrets.token_urlsafe(32)
    sessao = {
        "usuario_id": getattr(usuario, "id", None),
        "username": getattr(usuario, "nome", None),
        "role": getattr(usuario, "papel", None),
        "permissoes": _permissoes_sessao(usuario),
        "criada_em": datetime.now(timezone.utc).isoformat(),
    }

    with _LOCK:
        _SESSOES[token] = sessao

    usuario.autenticado = True
    usuario.sessao_token = token
    usuario.token = token
    return token


def contexto_autenticado(usuario):
    token = getattr(usuario, "sessao_token", None) or getattr(usuario, "token", None)
    if not isinstance(token, str) or not token:
        return False

    with _LOCK:
        sessao = _SESSOES.get(token)

    if not sessao:
        return False

    return (
        sessao.get("usuario_id") == getattr(usuario, "id", None)
        and sessao.get("username") == getattr(usuario, "nome", None)
        and sessao.get("role") == getattr(usuario, "papel", None)
        and tuple(sessao.get("permissoes", tuple())) == _permissoes_sessao(usuario)
    )


def encerrar_sessao(usuario_ou_token):
    token = usuario_ou_token
    if not isinstance(usuario_ou_token, str):
        token = (
            getattr(usuario_ou_token, "sessao_token", None)
            or getattr(usuario_ou_token, "token", None)
        )

    if not isinstance(token, str) or not token:
        return False

    with _LOCK:
        removido = _SESSOES.pop(token, None) is not None

    if not isinstance(usuario_ou_token, str):
        usuario_ou_token.autenticado = False
        usuario_ou_token.sessao_token = None
        usuario_ou_token.token = None

    return removido


def atualizar_sessao(usuario):
    token = getattr(usuario, "sessao_token", None) or getattr(usuario, "token", None)
    if not isinstance(token, str) or not token:
        return False

    with _LOCK:
        if token not in _SESSOES:
            return False
        _SESSOES[token].update({
            "usuario_id": getattr(usuario, "id", None),
            "username": getattr(usuario, "nome", None),
            "role": getattr(usuario, "papel", None),
            "permissoes": _permissoes_sessao(usuario),
        })
    return True


def invalidar_sessoes_usuario(usuario_id, exceto_token=None):
    with _LOCK:
        tokens = [
            token for token, sessao in _SESSOES.items()
            if sessao.get("usuario_id") == usuario_id and token != exceto_token
        ]
        for token in tokens:
            _SESSOES.pop(token, None)
    return len(tokens)


def limpar_sessoes():
    with _LOCK:
        _SESSOES.clear()


def total_sessoes_ativas():
    with _LOCK:
        return len(_SESSOES)
