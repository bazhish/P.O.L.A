import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from models.aluno import Aluno
from models.falta import Falta
from models.nota import Nota
from models.ocorrencia import Ocorrencia
from models.sala import Sala
from models.usuario import Usuario
<<<<<<< HEAD
=======
from utils.ids import gerar_id, id_valido
from utils.security import gerar_senha_hash, senha_inicial_padrao
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466
from utils.validators import log_error, log_info, normalizar_texto


BASE_DIR = Path(__file__).resolve().parents[1]
ARQUIVO_DB = BASE_DIR / "banco_dados.json"
SALA_PADRAO = "Sem sala"
USUARIO_BOOTSTRAP = {"nome": "admin", "papel": "ADM"}


def criar_db_vazio(incluir_admin=True):
    usuarios = [dict(USUARIO_BOOTSTRAP)] if incluir_admin else []
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


<<<<<<< HEAD
=======
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
    por_nome = _buscar_por_nome(lista, nome)
    por_id = _buscar_por_id(lista, id)
    if por_id and (not por_nome or por_id.get("nome") == por_nome.get("nome")):
        return por_id
    return por_nome or por_id


def _garantir_ids_unicos(lista):
    vistos = set()
    alterado = False

    for item in lista:
        if not isinstance(item, dict):
            continue

        id_atual = item.get("id")
        if not id_valido(id_atual) or id_atual in vistos:
            item["id"] = gerar_id()
            alterado = True

        vistos.add(item["id"])

    return alterado


>>>>>>> 7379759222222ab49d36193d4788c9bc75502466
def _normalizar_usuarios(dados):
    usuarios = []
    alterado = False

    for item in dados if isinstance(dados, list) else []:
        try:
            usuario = Usuario.de_dict(item).para_dict()
        except (AttributeError, ValueError):
            alterado = True
            continue

        if not _adicionar_unico_por_nome(usuarios, usuario):
            alterado = True

    if not any(usuario["papel"] == "ADM" for usuario in usuarios):
        usuarios.insert(0, dict(USUARIO_BOOTSTRAP))
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
    if not any(sala["nome"].lower() == nome.lower() for sala in salas):
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

        try:
            aluno = Aluno(item.get("nome", ""), sala).para_dict()
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
    alunos.append(Aluno(nome, SALA_PADRAO).para_dict())
    return True


def _normalizar_ocorrencias(dados, alunos, salas):
    ocorrencias = []
    alterado = False

    for item in dados if isinstance(dados, list) else []:
        try:
            ocorrencia = Ocorrencia.de_dict(item).para_dict()
        except (AttributeError, ValueError):
            alterado = True
            continue

        alterado = _garantir_aluno(alunos, salas, ocorrencia["aluno"]) or alterado
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
        faltas.append(falta)

    return faltas, alterado


def normalizar_db(dados):
    if not isinstance(dados, dict):
        return criar_db_vazio(), True

    alterado = False

    usuarios, mudou = _normalizar_usuarios(dados.get("usuarios", []))
    alterado = alterado or mudou
    alterado = _garantir_ids_unicos(usuarios) or alterado

    salas, mudou = _normalizar_salas(dados.get("salas", []))
    alterado = alterado or mudou
    alterado = _garantir_ids_unicos(salas) or alterado

    alunos, mudou = _normalizar_alunos(dados.get("alunos", []), salas)
    alterado = alterado or mudou
    alterado = _garantir_ids_unicos(alunos) or alterado

    ocorrencias, mudou = _normalizar_ocorrencias(dados.get("ocorrencias", []), alunos, salas)
    alterado = alterado or mudou
    alterado = _garantir_ids_unicos(ocorrencias) or alterado

    notas, mudou = _normalizar_notas(dados.get("notas", []), alunos, salas)
    alterado = alterado or mudou
    alterado = _garantir_ids_unicos(notas) or alterado

    faltas, mudou = _normalizar_faltas(dados.get("faltas", []), alunos, salas)
    alterado = alterado or mudou
    alterado = _garantir_ids_unicos(faltas) or alterado

    normalizado = {
        "usuarios": usuarios,
        "alunos": alunos,
        "salas": salas,
        "ocorrencias": ocorrencias,
        "notas": notas,
        "faltas": faltas,
    }

    return normalizado, alterado or normalizado != dados


def salvar_db(dados, caminho=ARQUIVO_DB):
    caminho = Path(caminho)
    dados_normalizados, _ = normalizar_db(dados)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    fd, temporario = tempfile.mkstemp(
        prefix=".polar-",
        suffix=".tmp",
        dir=str(caminho.parent),
        text=True,
    )

<<<<<<< HEAD
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
            json.dump(dados_normalizados, arquivo, ensure_ascii=False, indent=2)
            arquivo.write("\n")
        os.replace(temporario, caminho)
    except Exception:
        if os.path.exists(temporario):
            os.remove(temporario)
        raise
=======
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
                json.dump(dados_normalizados, arquivo, ensure_ascii=False, indent=2)
                arquivo.write("\n")
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, caminho)
        except Exception:
            if os.path.exists(temporario):
                os.remove(temporario)
            raise
>>>>>>> 7379759222222ab49d36193d4788c9bc75502466


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


def carregar_db(caminho=ARQUIVO_DB):
    caminho = Path(caminho)

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
