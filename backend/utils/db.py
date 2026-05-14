import json
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from models.aluno import Aluno
from models.falta import Falta
from models.nota import Nota
from models.ocorrencia import Ocorrencia
from models.sala import Sala
from models.usuario import Usuario
from utils.security import gerar_senha_hash, senha_inicial_padrao
from utils.validators import log_error, log_info, normalizar_texto


BASE_DIR = Path(__file__).resolve().parents[1]
ARQUIVO_DB_PADRAO = BASE_DIR / "banco_dados.json"
ARQUIVO_DB = Path(os.getenv("POLAR_DB_PATH") or ARQUIVO_DB_PADRAO)
SALA_PADRAO = "Sem sala"
USUARIO_BOOTSTRAP = {"nome": "admin", "papel": "ADM"}
DB_LOCK = threading.RLock()


def usar_supabase():
    return os.getenv("POLAR_STORAGE", "json").strip().lower() == "supabase"


def resolver_caminho_db(caminho=None):
    return Path(caminho or os.getenv("POLAR_DB_PATH") or ARQUIVO_DB_PADRAO)


def criar_usuario_bootstrap():
    return Usuario(
        USUARIO_BOOTSTRAP["nome"],
        USUARIO_BOOTSTRAP["papel"],
        senha_hash=gerar_senha_hash(senha_inicial_padrao()),
        precisa_trocar_senha=True,
    ).para_dict()


def criar_db_vazio(incluir_admin=True):
    usuarios = [criar_usuario_bootstrap()] if incluir_admin else []
    return {
        "usuarios": usuarios,
        "alunos": [],
        "salas": [],
        "ocorrencias": [],
        "notas": [],
        "faltas": [],
    }


def _adicionar_unico_por_nome(lista, item):
    nome = normalizar_texto(item.get("nome", "")).lower()
    if not nome:
        return False
    if any(normalizar_texto(existente.get("nome", "")).lower() == nome for existente in lista):
        return False
    lista.append(item)
    return True


def _buscar_por_nome(lista, nome):
    nome = normalizar_texto(nome).lower()
    for item in lista:
        if normalizar_texto(item.get("nome", "")).lower() == nome:
            return item
    return None


def _buscar_por_id(lista, id):
    if not id:
        return None
    for item in lista:
        if item.get("id") == id:
            return item
    return None


def _buscar_por_id_ou_nome(lista, id, nome):
    return _buscar_por_id(lista, id) or _buscar_por_nome(lista, nome)


def _normalizar_usuarios(dados):
    usuarios = []
    alterado = False

    for item in dados if isinstance(dados, list) else []:
        try:
            usuario = Usuario.de_dict(item).para_dict()
        except (AttributeError, ValueError):
            alterado = True
            continue

        if not usuario.get("senha_hash"):
            usuario["senha_hash"] = gerar_senha_hash(senha_inicial_padrao())
            usuario["precisa_trocar_senha"] = True
            alterado = True

        if not _adicionar_unico_por_nome(usuarios, usuario):
            alterado = True

    if not any(usuario["papel"] == "ADM" for usuario in usuarios):
        usuarios.insert(0, criar_usuario_bootstrap())
        alterado = True
        log_info("Usuario bootstrap criado: admin / ADM")

    return usuarios, alterado


def _normalizar_salas(dados):
    salas = []
    alterado = False

    for item in dados if isinstance(dados, list) else []:
        try:
            sala = Sala.de_dict(item).para_dict()
        except (AttributeError, ValueError):
            alterado = True
            continue

        if not _adicionar_unico_por_nome(salas, sala):
            alterado = True

    return salas, alterado


def _garantir_sala(salas, nome):
    nome = normalizar_texto(nome) or SALA_PADRAO
    if _buscar_por_nome(salas, nome) is None:
        salas.append(Sala(nome).para_dict())
        return True
    return False


def _normalizar_alunos(dados, salas):
    alunos = []
    alterado = False

    for item in dados if isinstance(dados, list) else []:
        if not isinstance(item, dict):
            alterado = True
            continue

        sala = normalizar_texto(item.get("sala", "")) or SALA_PADRAO
        alterado = _garantir_sala(salas, sala) or alterado
        sala_db = _buscar_por_id_ou_nome(salas, item.get("sala_id"), sala)
        if sala_db is None:
            sala_db = _buscar_por_nome(salas, sala) or _buscar_por_nome(salas, SALA_PADRAO) or {
                "nome": SALA_PADRAO,
                "id": None,
            }

        try:
            aluno = Aluno(
                item.get("nome", ""),
                sala_db["nome"],
                id=item.get("id"),
                sala_id=sala_db.get("id"),
            ).para_dict()
        except ValueError:
            alterado = True
            continue

        if not _adicionar_unico_por_nome(alunos, aluno):
            alterado = True

    return alunos, alterado


def _garantir_aluno(alunos, salas, nome):
    nome = normalizar_texto(nome)
    if not nome:
        return False

    if any(aluno["nome"].lower() == nome.lower() for aluno in alunos):
        return False

    _garantir_sala(salas, SALA_PADRAO)
    sala = _buscar_por_nome(salas, SALA_PADRAO)
    sala_id = sala.get("id") if sala else None
    alunos.append(Aluno(nome, SALA_PADRAO, sala_id=sala_id).para_dict())
    return True


def _normalizar_ocorrencias(dados, alunos, salas, usuarios):
    ocorrencias = []
    alterado = False

    for item in dados if isinstance(dados, list) else []:
        try:
            ocorrencia = Ocorrencia.de_dict(item).para_dict()
        except (AttributeError, ValueError):
            alterado = True
            continue

        alterado = _garantir_aluno(alunos, salas, ocorrencia["aluno"]) or alterado
        aluno = _buscar_por_id_ou_nome(alunos, ocorrencia.get("aluno_id"), ocorrencia["aluno"])
        if aluno:
            ocorrencia["aluno"] = aluno["nome"]
            ocorrencia["aluno_id"] = aluno.get("id")

        usuario = _buscar_por_id_ou_nome(
            usuarios,
            ocorrencia.get("criado_por_id"),
            ocorrencia.get("criado_por"),
        )
        if usuario:
            ocorrencia["criado_por"] = usuario["nome"]
            ocorrencia["criado_por_id"] = usuario.get("id")

        ocorrencias.append(ocorrencia)

    return ocorrencias, alterado


def _normalizar_notas(dados, alunos, salas):
    notas = []
    alterado = False

    for item in dados if isinstance(dados, list) else []:
        try:
            nota = Nota.de_dict(item).para_dict()
        except (AttributeError, TypeError, ValueError):
            alterado = True
            continue

        alterado = _garantir_aluno(alunos, salas, nota["aluno"]) or alterado
        aluno = _buscar_por_id_ou_nome(alunos, nota.get("aluno_id"), nota["aluno"])
        if aluno:
            nota["aluno"] = aluno["nome"]
            nota["aluno_id"] = aluno.get("id")
        notas.append(nota)

    return notas, alterado


def _normalizar_faltas(dados, alunos, salas):
    faltas = []
    alterado = False

    for item in dados if isinstance(dados, list) else []:
        try:
            falta = Falta.de_dict(item).para_dict()
        except (AttributeError, ValueError):
            alterado = True
            continue

        alterado = _garantir_aluno(alunos, salas, falta["aluno"]) or alterado
        aluno = _buscar_por_id_ou_nome(alunos, falta.get("aluno_id"), falta["aluno"])
        if aluno:
            falta["aluno"] = aluno["nome"]
            falta["aluno_id"] = aluno.get("id")
        faltas.append(falta)

    return faltas, alterado


def normalizar_db(dados):
    if not isinstance(dados, dict):
        return criar_db_vazio(), True

    alterado = False

    usuarios, mudou = _normalizar_usuarios(dados.get("usuarios", []))
    alterado = alterado or mudou

    salas, mudou = _normalizar_salas(dados.get("salas", []))
    alterado = alterado or mudou

    alunos, mudou = _normalizar_alunos(dados.get("alunos", []), salas)
    alterado = alterado or mudou

    ocorrencias, mudou = _normalizar_ocorrencias(
        dados.get("ocorrencias", []),
        alunos,
        salas,
        usuarios,
    )
    alterado = alterado or mudou

    notas, mudou = _normalizar_notas(dados.get("notas", []), alunos, salas)
    alterado = alterado or mudou

    faltas, mudou = _normalizar_faltas(dados.get("faltas", []), alunos, salas)
    alterado = alterado or mudou

    normalizado = {
        "usuarios": usuarios,
        "alunos": alunos,
        "salas": salas,
        "ocorrencias": ocorrencias,
        "notas": notas,
        "faltas": faltas,
    }

    return normalizado, alterado or normalizado != dados


def _salvar_db_json(dados, caminho=None):
    caminho = resolver_caminho_db(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    fd, temporario = tempfile.mkstemp(
        prefix=".polar-",
        suffix=".tmp",
        dir=str(caminho.parent),
        text=True,
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")
        os.replace(temporario, caminho)
    except Exception:
        if os.path.exists(temporario):
            os.remove(temporario)
        raise


def salvar_db(dados, caminho=None):
    with DB_LOCK:
        dados_normalizados, _ = normalizar_db(dados)
        _salvar_db_json(dados_normalizados, caminho)

        if usar_supabase():
            try:
                from utils.supabase_storage import salvar_db_supabase
                salvar_db_supabase(dados_normalizados)
            except Exception as erro:
                log_error(f"Falha ao sincronizar com Supabase: {erro}")
                raise


def _recriar_db_corrompido(caminho):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup = caminho.with_name(f"{caminho.name}.corrompido-{timestamp}")

    try:
        os.replace(caminho, backup)
        log_error(f"JSON corrompido detectado. Backup criado em {backup}")
    except OSError as erro:
        log_error(f"JSON corrompido detectado, mas o backup falhou: {erro}")

    db = criar_db_vazio()
    salvar_db(db, caminho)
    return db


def _carregar_db_json(caminho=None):
    caminho = resolver_caminho_db(caminho)

    if not caminho.exists():
        db = criar_db_vazio()
        salvar_db(db, caminho)
        return db

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except json.JSONDecodeError:
        return _recriar_db_corrompido(caminho)
    except OSError as erro:
        log_error(f"Nao foi possivel ler o banco de dados: {erro}")
        return criar_db_vazio()

    normalizado, alterado = normalizar_db(dados)
    if alterado:
        log_info("Banco normalizado para a estrutura academica atual")
        salvar_db(normalizado, caminho)

    return normalizado


def carregar_db(caminho=None):
    with DB_LOCK:
        if usar_supabase() and caminho is None:
            try:
                from utils.supabase_storage import carregar_db_supabase
                dados = carregar_db_supabase()
                normalizado, alterado = normalizar_db(dados)
                if alterado:
                    salvar_db(normalizado)
                return normalizado
            except Exception as erro:
                log_error(f"Falha ao carregar Supabase. Usando JSON local: {erro}")

        return _carregar_db_json(caminho)
