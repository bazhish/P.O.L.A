import sys
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from models.usuario import Usuario
from utils.cli import obter_credenciais, parse_comando_json
from utils.db import carregar_db, salvar_db
from utils.db import DB_LOCK
from utils.security import gerar_senha_hash, validar_senha, verificar_senha
from utils.sessions import (
    atualizar_sessao,
    contexto_autenticado,
    criar_sessao,
    encerrar_sessao,
    invalidar_sessoes_usuario,
)
from utils.responses import imprimir_resposta, resposta_erro, resposta_servico, resposta_sucesso
from utils.validators import (
    PERMISSAO_ADM_EXPLICITA,
    exigir_permissao,
    normalizar_papel,
    normalizar_permissoes,
    normalizar_texto,
)


MAX_TENTATIVAS_LOGIN = 5
BLOQUEIO_LOGIN_SEGUNDOS = 300


def buscar_usuario(db, nome):
    if not isinstance(db, dict):
        return None, None

    nome = normalizar_texto(nome).lower()
    usuarios = db.get("usuarios", [])
    if not isinstance(usuarios, list):
        return None, None

    for indice, usuario in enumerate(usuarios):
        if not isinstance(usuario, dict):
            continue
        username = usuario.get("nome", usuario.get("username", ""))
        if normalizar_texto(username).lower() == nome:
            return indice, usuario
    return None, None


def buscar_usuario_por_id(db, id):
    if not isinstance(db, dict):
        return None, None

    if not id:
        return None, None
    usuarios = db.get("usuarios", [])
    if not isinstance(usuarios, list):
        return None, None

    for indice, usuario in enumerate(usuarios):
        if not isinstance(usuario, dict):
            continue
        if usuario.get("id") == id:
            return indice, usuario
    return None, None


def _agora_utc():
    return datetime.now(timezone.utc)


def _parse_data_utc(valor):
    if not isinstance(valor, str) or not valor:
        return None
    try:
        data = datetime.fromisoformat(valor)
    except ValueError:
        return None
    if data.tzinfo is None:
        data = data.replace(tzinfo=timezone.utc)
    return data.astimezone(timezone.utc)


def _usuario_tem_adm_registro(usuario):
    if not isinstance(usuario, dict):
        return False

    papel = normalizar_papel(usuario.get("papel", usuario.get("role", "")))
    permissoes = normalizar_permissoes(usuario.get("permissoes", []))
    return papel == "ADM" or PERMISSAO_ADM_EXPLICITA in permissoes


def _total_adms(usuarios):
    return sum(1 for usuario in usuarios if _usuario_tem_adm_registro(usuario))


def _bloqueio_ativo(usuario):
    bloqueado_ate = _parse_data_utc(usuario.get("bloqueado_ate"))
    if not bloqueado_ate:
        usuario.pop("bloqueado_ate", None)
        return False

    if bloqueado_ate > _agora_utc():
        return True

    usuario.pop("bloqueado_ate", None)
    usuario["login_falhas"] = 0
    return False


def _registrar_login_invalido(usuario):
    try:
        falhas = int(usuario.get("login_falhas") or 0) + 1
    except (TypeError, ValueError):
        falhas = 1
    usuario["login_falhas"] = falhas

    if falhas >= MAX_TENTATIVAS_LOGIN:
        usuario["bloqueado_ate"] = (
            _agora_utc() + timedelta(seconds=BLOQUEIO_LOGIN_SEGUNDOS)
        ).isoformat()
        return "Acesso negado: muitas tentativas invalidas. Usuario temporariamente bloqueado"

    return "Acesso negado: senha invalida"


def _registrar_login_valido(usuario):
    usuario["login_falhas"] = 0
    usuario.pop("bloqueado_ate", None)
    usuario["ultimo_login"] = _agora_utc().isoformat()


def autenticar(db, nome, senha):
    nome = normalizar_texto(nome)

    if not nome:
        return None, "Usuario invalido"

    if not isinstance(senha, str) or not senha:
        return None, "Acesso negado: senha invalida"

    try:
        with DB_LOCK:
            _, usuario = buscar_usuario(db, nome)
            if usuario is None:
                return None, "Acesso negado: usuario nao cadastrado"

            if _bloqueio_ativo(usuario):
                return None, "Acesso negado: usuario temporariamente bloqueado"

            senha_hash = usuario.get("senha_hash") or usuario.get("password_hash")
            if not verificar_senha(senha, senha_hash):
                return None, _registrar_login_invalido(usuario)

            _registrar_login_valido(usuario)

            contexto = Usuario.de_dict(usuario)
    except (AttributeError, ValueError, TypeError):
        return None, "Acesso negado: usuario invalido"

    criar_sessao(contexto)
    return contexto, "Login autorizado"


def login(db, username, senha):
    usuario, mensagem = autenticar(db, username, senha)
    if usuario is None:
        return False, mensagem, None, None
    return True, mensagem, usuario.sessao_token, usuario


def logout(usuario_ou_token):
    if encerrar_sessao(usuario_ou_token):
        return True, "Sessao encerrada"
    return False, "Sessao nao encontrada"


def listar_usuarios(db, solicitante):
    permitido, mensagem = exigir_permissao(solicitante, "usuario_visualizar")
    if not permitido:
        return False, mensagem, []

    with DB_LOCK:
        usuarios_db = db.get("usuarios", []) if isinstance(db, dict) else []
        if not isinstance(usuarios_db, list):
            return False, "Lista de usuarios invalida", []

        usuarios = []
        for usuario in usuarios_db:
            if not isinstance(usuario, dict):
                return False, "Registro de usuario invalido", []
            item = deepcopy(usuario)
            item.pop("senha_hash", None)
            item.pop("password_hash", None)
            usuarios.append(item)

    return True, "Usuarios listados", usuarios


def criar_usuario(db, solicitante, nome, papel, senha, permissoes=None):
    permitido, mensagem = exigir_permissao(solicitante, "usuario_criar")
    if not permitido:
        return False, mensagem

    if not isinstance(db, dict):
        return False, "Banco de dados invalido"

    if not validar_senha(senha):
        return False, "Senha deve ter entre 8 e 128 caracteres"

    with DB_LOCK:
        usuarios = db.get("usuarios")
        if usuarios is None:
            db["usuarios"] = []
            usuarios = db["usuarios"]
        if not isinstance(usuarios, list):
            return False, "Lista de usuarios invalida"

        if buscar_usuario(db, nome)[1] is not None:
            return False, "Usuario ja cadastrado"

        try:
            usuario = Usuario(
                nome,
                papel,
                senha_hash=gerar_senha_hash(senha),
                permissoes=permissoes,
            ).para_dict()
        except ValueError as erro:
            return False, str(erro)

        usuarios.append(usuario)
    return True, "Usuario criado"


def editar_usuario(db, solicitante, indice, novo_nome, novo_papel, nova_senha=None, novas_permissoes=None):
    permitido, mensagem = exigir_permissao(solicitante, "usuario_editar")
    if not permitido:
        return False, mensagem

    if not isinstance(db, dict):
        return False, "Banco de dados invalido"

    with DB_LOCK:
        usuarios = db.get("usuarios", [])
        if not isinstance(usuarios, list):
            return False, "Lista de usuarios invalida"
        if not isinstance(indice, int) or not 0 <= indice < len(usuarios):
            return False, "Usuario selecionado invalido"
        if not isinstance(usuarios[indice], dict):
            return False, "Registro de usuario invalido"

        usuario_atual = usuarios[indice]
        nome_atual = usuario_atual.get("nome", usuario_atual.get("username", ""))

        existente_indice, _ = buscar_usuario(db, novo_nome)
        if existente_indice is not None and existente_indice != indice:
            return False, "Outro usuario ja usa esse nome"

        try:
            senha_hash = usuario_atual.get("senha_hash") or usuario_atual.get("password_hash")
            precisa_trocar_senha = usuario_atual.get("precisa_trocar_senha", False)
            if nova_senha:
                if not validar_senha(nova_senha):
                    return False, "Senha deve ter entre 8 e 128 caracteres"
                senha_hash = gerar_senha_hash(nova_senha)
                precisa_trocar_senha = False

            permissoes = (
                normalizar_permissoes(novas_permissoes)
                if novas_permissoes is not None
                else normalizar_permissoes(usuario_atual.get("permissoes", []))
            )

            atualizado = Usuario(
                novo_nome,
                novo_papel,
                senha_hash=senha_hash,
                id=usuario_atual.get("id"),
                precisa_trocar_senha=precisa_trocar_senha,
                permissoes=permissoes,
                login_falhas=usuario_atual.get("login_falhas", 0),
                bloqueado_ate=usuario_atual.get("bloqueado_ate"),
                ultimo_login=usuario_atual.get("ultimo_login"),
            ).para_dict()
        except ValueError as erro:
            return False, str(erro)

        usuarios_simulados = list(usuarios)
        usuarios_simulados[indice] = atualizado
        if _usuario_tem_adm_registro(usuario_atual) and _total_adms(usuarios_simulados) < 1:
            return False, "Nao e permitido remover o ultimo acesso ADM"

        usuarios[indice] = atualizado

    if solicitante.nome == nome_atual:
        solicitante.nome = atualizado["nome"]
        solicitante.nome_usuario = atualizado["nome"]
        solicitante.papel = atualizado["papel"]
        solicitante.id = atualizado["id"]
        solicitante.senha_hash = atualizado.get("senha_hash")
        solicitante.permissoes = atualizado.get("permissoes", [])
        atualizar_sessao(solicitante)
    else:
        invalidar_sessoes_usuario(atualizado["id"])

    return True, "Usuario atualizado"


def alterar_permissoes(db, solicitante, indice, permissoes):
    if not isinstance(db, dict):
        return False, "Banco de dados invalido"

    with DB_LOCK:
        usuarios = db.get("usuarios", [])
        if not isinstance(usuarios, list):
            return False, "Lista de usuarios invalida"
        if not isinstance(indice, int) or not 0 <= indice < len(usuarios):
            return False, "Usuario selecionado invalido"
        registro = usuarios[indice]
        if not isinstance(registro, dict):
            return False, "Registro de usuario invalido"

        return editar_usuario(
            db,
            solicitante,
            indice,
            registro.get("nome", registro.get("username", "")),
            registro.get("papel", registro.get("role", "")),
            novas_permissoes=permissoes,
        )


def remover_usuario(db, solicitante, indice):
    permitido, mensagem = exigir_permissao(solicitante, "usuario_remover")
    if not permitido:
        return False, mensagem

    if not isinstance(db, dict):
        return False, "Banco de dados invalido"

    with DB_LOCK:
        usuarios = db.get("usuarios", [])
        if not isinstance(usuarios, list):
            return False, "Lista de usuarios invalida"
        if not isinstance(indice, int) or not 0 <= indice < len(usuarios):
            return False, "Usuario selecionado invalido"
        if not isinstance(usuarios[indice], dict):
            return False, "Registro de usuario invalido"

        removido = usuarios[indice]
        usuarios_simulados = list(usuarios)
        usuarios_simulados.pop(indice)
        if _usuario_tem_adm_registro(removido) and _total_adms(usuarios_simulados) < 1:
            return False, "Nao e permitido remover o ultimo acesso ADM"

        usuarios.pop(indice)

    invalidar_sessoes_usuario(removido.get("id"))
    return True, "Usuario removido"


def _autenticar_solicitante_cli(db, payload):
    nome, senha = obter_credenciais(payload)
    if not nome or not senha:
        return None, "Credenciais do solicitante ausentes"
    return autenticar(db, nome, senha)



def alterar_senha(db, usuario, senha_atual, nova_senha):
    if not contexto_autenticado(usuario):
        return False, "Acesso negado: usuario nao autenticado"

    with DB_LOCK:
        indice, registro = buscar_usuario_por_id(db, getattr(usuario, "id", None))
        if registro is None:
            indice, registro = buscar_usuario(db, getattr(usuario, "nome", ""))

        if registro is None:
            return False, "Usuario nao encontrado"

        senha_hash = registro.get("senha_hash") or registro.get("password_hash")
        if not verificar_senha(senha_atual, senha_hash):
            return False, "Senha atual invalida"

        if not validar_senha(nova_senha):
            return False, "Senha deve ter entre 8 e 128 caracteres"

        registro["senha_hash"] = gerar_senha_hash(nova_senha)
        registro["password_hash"] = registro["senha_hash"]
        registro.pop("precisa_trocar_senha", None)
        usuario.senha_hash = registro["senha_hash"]

    usuario.precisa_trocar_senha = False
    return True, "Senha atualizada"


def _executar_cli(argv=None):
    argv = sys.argv if argv is None else argv
    db = carregar_db()
    comando, body, erro = parse_comando_json(argv)

    try:
        if erro:
            return resposta_erro(erro)

        if comando == "login":
            if not body:
                return resposta_erro("JSON de entrada ausente")

            usuario, mensagem = autenticar(
                db,
                body.get("nome") or body.get("username") or body.get("usuario"),
                body.get("senha") or body.get("password"),
            )
            salvar_db(db)
            if usuario is None:
                return resposta_erro(mensagem, usuario=None)
            return resposta_sucesso(
                mensagem,
                usuario={
                    "id": usuario.id,
                    "nome": usuario.nome,
                    "papel": usuario.papel,
                    "permissoes": usuario.permissoes,
                    "token": usuario.sessao_token,
                },
            )

        if comando not in {"listar", "criar", "editar", "permissoes", "remover"}:
            return resposta_erro("Comando invalido")

        solicitante, mensagem_auth = _autenticar_solicitante_cli(db, body)
        if solicitante is None:
            return resposta_erro(mensagem_auth)

        if comando == "listar":
            sucesso, mensagem, dados = listar_usuarios(db, solicitante)
            return resposta_servico(sucesso, mensagem, dados=dados)

        if comando == "criar":
            sucesso, mensagem = criar_usuario(
                db,
                solicitante,
                body["nome"],
                body["papel"],
                body.get("senha") or body.get("password"),
                body.get("permissoes"),
            )
        elif comando == "editar":
            sucesso, mensagem = editar_usuario(
                db,
                solicitante,
                body["indice"],
                body["nome"],
                body["papel"],
                body.get("senha") or body.get("password"),
                body.get("permissoes"),
            )
        elif comando == "permissoes":
            sucesso, mensagem = alterar_permissoes(
                db,
                solicitante,
                body["indice"],
                body.get("permissoes", []),
            )
        else:
            sucesso, mensagem = remover_usuario(db, solicitante, body["indice"])

        if sucesso:
            salvar_db(db)
        return resposta_servico(sucesso, mensagem)
    except (KeyError, TypeError, ValueError):
        return resposta_erro("Entrada invalida")
    except Exception:
        return resposta_erro("Erro interno ao executar comando")


if __name__ == "__main__":
    imprimir_resposta(_executar_cli())
