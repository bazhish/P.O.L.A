import json
import os
from datetime import datetime, timezone
from urllib import error, parse, request
from uuid import NAMESPACE_URL, uuid5

from utils.validators import log_error, log_info, normalizar_texto


class SupabaseConfigError(RuntimeError):
    pass


class SupabaseRequestError(RuntimeError):
    pass


def supabase_configurado():
    return bool(_supabase_url() and _supabase_key())


def _supabase_url():
    return (os.getenv("SUPABASE_URL") or "").rstrip("/")


def _supabase_key():
    return (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_KEY")
        or ""
    )


def _rest_url():
    url = _supabase_url()
    if not url:
        raise SupabaseConfigError("SUPABASE_URL nao configurada")
    return f"{url}/rest/v1"


def _headers(prefer=None):
    key = _supabase_key()
    if not key:
        raise SupabaseConfigError("SUPABASE_SERVICE_ROLE_KEY nao configurada")

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _request(method, endpoint, params=None, body=None, prefer=None):
    params = params or {}
    query = f"?{parse.urlencode(params, doseq=True)}" if params else ""
    url = f"{_rest_url()}/{endpoint}{query}"
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    requisicao = request.Request(
        url,
        data=data,
        method=method,
        headers=_headers(prefer=prefer),
    )

    timeout = int(os.getenv("SUPABASE_TIMEOUT", "20"))
    try:
        with request.urlopen(requisicao, timeout=timeout) as resposta:
            conteudo = resposta.read().decode("utf-8")
            if not conteudo:
                return None
            return json.loads(conteudo)
    except error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="replace")
        raise SupabaseRequestError(
            f"Erro Supabase {erro.code} em {method} {endpoint}: {detalhe}"
        ) from erro
    except error.URLError as erro:
        raise SupabaseRequestError(f"Falha ao conectar no Supabase: {erro}") from erro


def _select(tabela, order=None):
    params = {"select": "*"}
    if order:
        params["order"] = order
    return _request("GET", tabela, params=params) or []


def _upsert(tabela, registros, conflito="id"):
    registros = [r for r in registros if isinstance(r, dict) and r.get("id")]
    if not registros:
        return
    return _request(
        "POST",
        tabela,
        params={"on_conflict": conflito},
        body=registros,
        prefer="resolution=merge-duplicates,return=minimal",
    )


def _delete(tabela, filtros):
    return _request("DELETE", tabela, params=filtros, prefer="return=minimal")


def _texto(valor):
    return normalizar_texto(valor) or None


def _historico_id(ocorrencia_id, indice, item):
    base = json.dumps(
        {
            "ocorrencia_id": ocorrencia_id,
            "indice": indice,
            "acao": item.get("acao"),
            "status": item.get("status"),
            "data_hora": item.get("data_hora"),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return str(uuid5(NAMESPACE_URL, base))


def _data_agora():
    return datetime.now(timezone.utc).isoformat()


def _mapear_profiles(usuarios):
    registros = []
    for usuario in usuarios if isinstance(usuarios, list) else []:
        if not isinstance(usuario, dict) or not usuario.get("id"):
            continue
        registros.append({
            "id": usuario.get("id"),
            "nome": _texto(usuario.get("nome") or usuario.get("username")),
            "username": _texto(usuario.get("username") or usuario.get("nome")),
            "papel": usuario.get("papel") or usuario.get("role"),
            "role": usuario.get("role") or usuario.get("papel"),
            "senha_hash": usuario.get("senha_hash"),
            "password_hash": usuario.get("password_hash") or usuario.get("senha_hash"),
            "precisa_trocar_senha": bool(usuario.get("precisa_trocar_senha", False)),
            "permissoes": usuario.get("permissoes", []),
            "login_falhas": int(usuario.get("login_falhas") or 0),
            "bloqueado_ate": usuario.get("bloqueado_ate"),
            "ultimo_login": usuario.get("ultimo_login"),
            "ativo": bool(usuario.get("ativo", True)),
        })
    return registros


def _mapear_turmas(salas):
    registros = []
    for sala in salas if isinstance(salas, list) else []:
        if not isinstance(sala, dict) or not sala.get("id"):
            continue
        registros.append({
            "id": sala.get("id"),
            "nome": _texto(sala.get("nome")),
            "ativa": bool(sala.get("ativa", True)),
        })
    return registros


def _mapear_alunos(alunos):
    registros = []
    for aluno in alunos if isinstance(alunos, list) else []:
        if not isinstance(aluno, dict) or not aluno.get("id"):
            continue
        registros.append({
            "id": aluno.get("id"),
            "nome": _texto(aluno.get("nome")),
            "turma_id": aluno.get("sala_id") or aluno.get("turma_id"),
            "sala": _texto(aluno.get("sala")),
            "ativo": bool(aluno.get("ativo", True)),
        })
    return registros


def _mapear_ocorrencias(ocorrencias):
    registros = []
    historico = []
    for ocorrencia in ocorrencias if isinstance(ocorrencias, list) else []:
        if not isinstance(ocorrencia, dict) or not ocorrencia.get("id"):
            continue
        ocorrencia_id = ocorrencia.get("id")
        registros.append({
            "id": ocorrencia_id,
            "aluno_id": ocorrencia.get("aluno_id"),
            "aluno_nome": _texto(ocorrencia.get("aluno")),
            "criado_por_id": ocorrencia.get("criado_por_id"),
            "criado_por_nome": _texto(ocorrencia.get("criado_por")),
            "descricao": _texto(ocorrencia.get("descricao")),
            "categoria": ocorrencia.get("categoria"),
            "prioridade": ocorrencia.get("prioridade"),
            "status": ocorrencia.get("status", "REGISTRADA"),
        })
        for indice, item in enumerate(ocorrencia.get("historico", [])):
            if not isinstance(item, dict):
                continue
            historico.append({
                "id": _historico_id(ocorrencia_id, indice, item),
                "ocorrencia_id": ocorrencia_id,
                "acao": _texto(item.get("acao")) or "Atualizacao",
                "status": item.get("status"),
                "usuario": _texto(item.get("usuario")),
                "data_hora": item.get("data_hora") or _data_agora(),
            })
    return registros, historico


def _mapear_notas(notas):
    registros = []
    for nota in notas if isinstance(notas, list) else []:
        if not isinstance(nota, dict) or not nota.get("id"):
            continue
        registros.append({
            "id": nota.get("id"),
            "aluno_id": nota.get("aluno_id"),
            "aluno_nome": _texto(nota.get("aluno")),
            "disciplina": _texto(nota.get("disciplina")),
            "valor": nota.get("valor"),
        })
    return registros


def _mapear_faltas(faltas):
    registros = []
    for falta in faltas if isinstance(faltas, list) else []:
        if not isinstance(falta, dict) or not falta.get("id"):
            continue
        registros.append({
            "id": falta.get("id"),
            "aluno_id": falta.get("aluno_id"),
            "aluno_nome": _texto(falta.get("aluno")),
            "data_falta": falta.get("data"),
        })
    return registros


def salvar_db_supabase(db):
    if not supabase_configurado():
        raise SupabaseConfigError("Supabase nao configurado")

    _upsert("profiles", _mapear_profiles(db.get("usuarios", [])))
    _upsert("turmas", _mapear_turmas(db.get("salas", [])))
    _upsert("alunos", _mapear_alunos(db.get("alunos", [])))

    ocorrencias, historico = _mapear_ocorrencias(db.get("ocorrencias", []))
    _upsert("ocorrencias", ocorrencias)

    for ocorrencia in ocorrencias:
        _delete("ocorrencia_historico", {"ocorrencia_id": f"eq.{ocorrencia['id']}"})
    _upsert("ocorrencia_historico", historico)

    _upsert("notas", _mapear_notas(db.get("notas", [])))
    _upsert("faltas", _mapear_faltas(db.get("faltas", [])))
    log_info("Dados enviados ao Supabase")


def _limpar_nulos(dados):
    return {chave: valor for chave, valor in dados.items() if valor is not None}


def carregar_db_supabase():
    if not supabase_configurado():
        raise SupabaseConfigError("Supabase nao configurado")

    profiles = _select("profiles", order="created_at.asc")
    turmas = _select("turmas", order="created_at.asc")
    alunos_db = _select("alunos", order="created_at.asc")
    ocorrencias_db = _select("ocorrencias", order="created_at.asc")
    historico_db = _select("ocorrencia_historico", order="data_hora.asc")
    notas_db = _select("notas", order="created_at.asc")
    faltas_db = _select("faltas", order="created_at.asc")

    turma_por_id = {item.get("id"): item for item in turmas if isinstance(item, dict)}
    aluno_por_id = {item.get("id"): item for item in alunos_db if isinstance(item, dict)}
    usuario_por_id = {item.get("id"): item for item in profiles if isinstance(item, dict)}

    usuarios = []
    for usuario in profiles:
        usuarios.append(_limpar_nulos({
            "id": usuario.get("id"),
            "nome": usuario.get("nome") or usuario.get("username"),
            "username": usuario.get("username") or usuario.get("nome"),
            "papel": usuario.get("papel") or usuario.get("role"),
            "role": usuario.get("role") or usuario.get("papel"),
            "senha_hash": usuario.get("senha_hash"),
            "password_hash": usuario.get("password_hash") or usuario.get("senha_hash"),
            "precisa_trocar_senha": usuario.get("precisa_trocar_senha"),
            "permissoes": usuario.get("permissoes") or [],
            "login_falhas": usuario.get("login_falhas") or 0,
            "bloqueado_ate": usuario.get("bloqueado_ate"),
            "ultimo_login": usuario.get("ultimo_login"),
            "ativo": usuario.get("ativo", True),
        }))

    salas = [
        _limpar_nulos({
            "id": turma.get("id"),
            "nome": turma.get("nome"),
            "ativa": turma.get("ativa", True),
        })
        for turma in turmas
    ]

    alunos = []
    for aluno in alunos_db:
        turma_id = aluno.get("turma_id") or aluno.get("sala_id")
        turma = turma_por_id.get(turma_id, {})
        alunos.append(_limpar_nulos({
            "id": aluno.get("id"),
            "nome": aluno.get("nome"),
            "sala": aluno.get("sala") or turma.get("nome"),
            "sala_id": turma_id,
            "ativo": aluno.get("ativo", True),
        }))

    historico_por_ocorrencia = {}
    for item in historico_db:
        ocorrencia_id = item.get("ocorrencia_id")
        historico_por_ocorrencia.setdefault(ocorrencia_id, []).append(_limpar_nulos({
            "acao": item.get("acao"),
            "status": item.get("status"),
            "usuario": item.get("usuario"),
            "data_hora": item.get("data_hora"),
        }))

    ocorrencias = []
    for ocorrencia in ocorrencias_db:
        aluno = aluno_por_id.get(ocorrencia.get("aluno_id"), {})
        usuario = usuario_por_id.get(ocorrencia.get("criado_por_id"), {})
        ocorrencias.append(_limpar_nulos({
            "id": ocorrencia.get("id"),
            "aluno": ocorrencia.get("aluno_nome") or aluno.get("nome"),
            "aluno_id": ocorrencia.get("aluno_id"),
            "descricao": ocorrencia.get("descricao"),
            "categoria": ocorrencia.get("categoria"),
            "prioridade": ocorrencia.get("prioridade"),
            "status": ocorrencia.get("status"),
            "criado_por": ocorrencia.get("criado_por_nome") or usuario.get("nome"),
            "criado_por_id": ocorrencia.get("criado_por_id"),
            "historico": historico_por_ocorrencia.get(ocorrencia.get("id"), []),
        }))

    notas = []
    for nota in notas_db:
        aluno = aluno_por_id.get(nota.get("aluno_id"), {})
        notas.append(_limpar_nulos({
            "id": nota.get("id"),
            "aluno": nota.get("aluno_nome") or aluno.get("nome"),
            "aluno_id": nota.get("aluno_id"),
            "disciplina": nota.get("disciplina"),
            "valor": nota.get("valor"),
        }))

    faltas = []
    for falta in faltas_db:
        aluno = aluno_por_id.get(falta.get("aluno_id"), {})
        faltas.append(_limpar_nulos({
            "id": falta.get("id"),
            "aluno": falta.get("aluno_nome") or aluno.get("nome"),
            "aluno_id": falta.get("aluno_id"),
            "data": falta.get("data_falta"),
        }))

    log_info("Dados carregados do Supabase")
    return {
        "usuarios": usuarios,
        "alunos": alunos,
        "salas": salas,
        "ocorrencias": ocorrencias,
        "notas": notas,
        "faltas": faltas,
    }
