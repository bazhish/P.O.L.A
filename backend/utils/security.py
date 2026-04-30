import hashlib
import hmac
import os
import secrets


HASH_ALGORITMO = "pbkdf2_sha256"
ITERACOES_PADRAO = 210_000
TAMANHO_SALT = 16
TAMANHO_HASH = 32
SENHA_INICIAL_PADRAO = "admin123"
SENHA_MINIMA = 6


def senha_inicial_padrao():
    return os.getenv("POLAR_BOOTSTRAP_PASSWORD") or SENHA_INICIAL_PADRAO


def validar_senha(valor):
    return isinstance(valor, str) and len(valor) >= SENHA_MINIMA


def gerar_senha_hash(senha, iteracoes=ITERACOES_PADRAO):
    if not validar_senha(senha):
        raise ValueError(f"Senha deve ter pelo menos {SENHA_MINIMA} caracteres")

    salt = secrets.token_hex(TAMANHO_SALT)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt.encode("ascii"),
        iteracoes,
        dklen=TAMANHO_HASH,
    ).hex()
    return f"{HASH_ALGORITMO}${iteracoes}${salt}${digest}"


def verificar_senha(senha, senha_hash):
    if not isinstance(senha, str) or not isinstance(senha_hash, str):
        return False

    try:
        algoritmo, iteracoes, salt, digest = senha_hash.split("$", 3)
        iteracoes = int(iteracoes)
    except (TypeError, ValueError):
        return False

    if algoritmo != HASH_ALGORITMO or iteracoes <= 0:
        return False

    calculado = hashlib.pbkdf2_hmac(
        "sha256",
        senha.encode("utf-8"),
        salt.encode("ascii"),
        iteracoes,
        dklen=TAMANHO_HASH,
    ).hex()
    return hmac.compare_digest(calculado, digest)
