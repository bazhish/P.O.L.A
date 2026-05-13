import json

from utils.validators import normalizar_texto


MAX_ARG_BYTES = 1_000_000


def parse_comando_json(argv, exige_payload=False):
    if not isinstance(argv, (list, tuple)) or len(argv) < 2:
        return None, {}, "Comando ausente"

    comando = normalizar_texto(argv[1]).lower()
    if not comando:
        return None, {}, "Comando invalido"

    if len(argv) < 3:
        if exige_payload:
            return comando, {}, "JSON de entrada ausente"
        return comando, {}, None

    bruto = argv[2]
    if not isinstance(bruto, str):
        return comando, {}, "JSON de entrada invalido"

    if len(bruto.encode("utf-8", errors="ignore")) > MAX_ARG_BYTES:
        return comando, {}, "JSON de entrada excede o tamanho permitido"

    try:
        payload = json.loads(bruto)
    except json.JSONDecodeError:
        return comando, {}, "JSON de entrada invalido"

    if not isinstance(payload, dict):
        return comando, {}, "JSON de entrada deve ser um objeto"

    return comando, payload, None


def obter_credenciais(payload):
    if not isinstance(payload, dict):
        return None, None

    auth = payload.get("auth")
    if not isinstance(auth, dict):
        auth = {}

    nome = (
        auth.get("nome")
        or auth.get("username")
        or auth.get("usuario")
        or payload.get("solicitante_nome")
        or payload.get("requester_name")
    )
    senha = (
        auth.get("senha")
        or auth.get("password")
        or payload.get("solicitante_senha")
        or payload.get("requester_password")
    )
    return nome, senha


def autenticar_solicitante(db, payload):
    from services.auth_service import autenticar

    nome, senha = obter_credenciais(payload)
    if not nome or not senha:
        return None, "Credenciais do solicitante ausentes"
    return autenticar(db, nome, senha)
