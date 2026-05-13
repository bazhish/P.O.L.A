import os
import sys
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from models.usuario import Usuario
from services import aluno_service, auth_service, falta_service, nota_service
from services import ocorrencia_service, sala_service
from utils.db import carregar_db, criar_db_vazio, normalizar_db, salvar_db
from utils.security import gerar_senha_hash, senha_inicial_padrao
from utils.sessions import limpar_sessoes
from utils.validators import CATEGORIAS, PRIORIDADES


class EngineTestCase(unittest.TestCase):
    def setUp(self):
        limpar_sessoes()

    def criar_contexto(self):
        db = criar_db_vazio(incluir_admin=False)
        adm = Usuario("Admin", "ADM", senha_hash=gerar_senha_hash("admin123"))
        professor = Usuario("Prof", "PROFESSOR", senha_hash=gerar_senha_hash("prof1234"))
        coordenador = Usuario("Coord", "COORDENADOR", senha_hash=gerar_senha_hash("coord123"))
        diretor = Usuario("Diretor", "DIRETOR", senha_hash=gerar_senha_hash("diretor123"))
        db["usuarios"] = [
            adm.para_dict(),
            professor.para_dict(),
            coordenador.para_dict(),
            diretor.para_dict(),
        ]
        adm, _ = auth_service.autenticar(db, "Admin", "admin123")
        professor, _ = auth_service.autenticar(db, "Prof", "prof1234")
        coordenador, _ = auth_service.autenticar(db, "Coord", "coord123")
        diretor, _ = auth_service.autenticar(db, "Diretor", "diretor123")
        self.assertIsNotNone(adm)
        self.assertIsNotNone(professor)
        self.assertIsNotNone(coordenador)
        self.assertIsNotNone(diretor)
        return db, adm, professor, coordenador, diretor

    def test_normalizacao_migra_dados_antigos_para_ids_e_senha(self):
        dados = {
            "usuarios": [
                {"nome": "admin", "papel": "ADM"},
                {"nome": "professor1", "papel": "PROF"},
            ],
            "salas": [{"nome": "1A"}],
            "alunos": [{"nome": "Ana", "sala": "1A"}],
            "ocorrencias": [{
                "aluno": "Ana",
                "descricao": "Teste",
                "categoria": CATEGORIAS[0],
                "prioridade": PRIORIDADES[0],
                "criado_por": "admin",
            }],
            "notas": [{"aluno": "Ana", "disciplina": "Matematica", "valor": 8}],
            "faltas": [{"aluno": "Ana", "data": "2026-04-30"}],
        }

        normalizado, alterado = normalizar_db(dados)

        self.assertTrue(alterado)
        self.assertIn("id", normalizado["usuarios"][0])
        self.assertIn("senha_hash", normalizado["usuarios"][0])
        self.assertTrue(normalizado["usuarios"][0]["precisa_trocar_senha"])
        self.assertEqual(normalizado["usuarios"][1]["papel"], "PROFESSOR")
        self.assertIn("sala_id", normalizado["alunos"][0])
        self.assertIn("aluno_id", normalizado["ocorrencias"][0])
        self.assertIn("data_hora", normalizado["ocorrencias"][0]["historico"][0])
        self.assertEqual(
            normalizado["notas"][0]["aluno_id"],
            normalizado["alunos"][0]["id"],
        )
        usuario, _ = auth_service.autenticar(
            normalizado,
            "admin",
            senha_inicial_padrao(),
        )
        self.assertIsNotNone(usuario)

    def test_autenticacao_exige_senha_e_nao_expoe_hash_ao_listar(self):
        db, adm, *_ = self.criar_contexto()

        ok, msg = auth_service.criar_usuario(
            db,
            adm,
            "Maria",
            "COORDENADOR",
            "senha123",
        )
        self.assertTrue(ok, msg)

        usuario, msg = auth_service.autenticar(db, "Maria", "senha123")
        self.assertIsNotNone(usuario, msg)

        usuario, msg = auth_service.autenticar(db, "Maria", "errada123")
        self.assertIsNone(usuario)
        self.assertIn("senha", msg)

        ok, msg, usuarios = auth_service.listar_usuarios(db, adm)
        self.assertTrue(ok, msg)
        self.assertTrue(all("senha_hash" not in item for item in usuarios))
        self.assertTrue(all("password_hash" not in item for item in usuarios))

    def test_autenticacao_bloqueia_bypass_e_login_invalido_sem_crash(self):
        db, adm, professor, *_ = self.criar_contexto()

        usuario, mensagem = auth_service.autenticar(db, "Prof", "senha_errada")
        self.assertIsNone(usuario)
        self.assertIn("senha", mensagem)

        usuario, mensagem = auth_service.autenticar([], "Prof", "prof1234")
        self.assertIsNone(usuario)
        self.assertIn("negado", mensagem)

        forjado = Usuario("Forjado", "ADM", senha_hash=gerar_senha_hash("forjado123"))
        sucesso, mensagem = sala_service.criar_sala(db, forjado, "Sala Forjada")
        self.assertFalse(sucesso)
        self.assertIn("nao autenticado", mensagem)

        professor.sessao_token = "token-forjado"
        sucesso, mensagem, _ = ocorrencia_service.listar_ocorrencias(db, professor)
        self.assertFalse(sucesso)
        self.assertIn("nao autenticado", mensagem)

        professor, _ = auth_service.autenticar(db, "Prof", "prof1234")
        professor.permissoes = ["ADM"]
        sucesso, mensagem = sala_service.criar_sala(db, professor, "Sala Permissao Forjada")
        self.assertFalse(sucesso)
        self.assertIn("nao autenticado", mensagem)

        ok, mensagem, token, usuario_logado = auth_service.login(db, "Admin", "admin123")
        self.assertTrue(ok, mensagem)
        self.assertIsInstance(token, str)
        self.assertEqual(usuario_logado.papel, "ADM")

        ok, mensagem = auth_service.logout(usuario_logado)
        self.assertTrue(ok, mensagem)
        sucesso, mensagem, _ = sala_service.listar_salas(db, usuario_logado)
        self.assertFalse(sucesso)
        self.assertIn("nao autenticado", mensagem)

        sucesso, mensagem = auth_service.criar_usuario(
            db,
            adm,
            "Papel Invalido",
            "SECRETARIA",
            "senha123",
        )
        self.assertFalse(sucesso)
        self.assertIn("Papel invalido", mensagem)

    def test_edicao_de_usuario_invalida_sessao_antiga(self):
        db, adm, professor, *_ = self.criar_contexto()

        indice_professor, _ = auth_service.buscar_usuario(db, "Prof")
        self.assertIsNotNone(indice_professor)

        sucesso, mensagem = auth_service.editar_usuario(
            db,
            adm,
            indice_professor,
            "Prof Novo",
            "PROFESSOR",
        )
        self.assertTrue(sucesso, mensagem)

        sucesso, mensagem, _ = sala_service.listar_salas(db, professor)
        self.assertFalse(sucesso)
        self.assertIn("nao autenticado", mensagem)

        professor_novo, mensagem = auth_service.autenticar(db, "Prof Novo", "prof1234")
        self.assertIsNotNone(professor_novo, mensagem)
        sucesso, mensagem, _ = sala_service.listar_salas(db, professor_novo)
        self.assertTrue(sucesso, mensagem)

    def test_ids_preservam_relacoes_ao_renomear_aluno_e_sala(self):
        db, adm, professor, *_ = self.criar_contexto()
        self.assertTrue(sala_service.criar_sala(db, adm, "1A")[0])
        self.assertTrue(aluno_service.criar_aluno(db, adm, "Ana", "1A")[0])
        aluno_id = db["alunos"][0]["id"]
        sala_id = db["salas"][0]["id"]

        self.assertTrue(ocorrencia_service.criar_ocorrencia(
            db,
            professor,
            "Ana",
            "Descricao valida",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )[0])
        self.assertTrue(nota_service.adicionar_nota(db, professor, "Ana", "Portugues", 9)[0])
        self.assertTrue(falta_service.adicionar_falta(db, professor, "Ana", "2026-04-30")[0])

        self.assertTrue(aluno_service.editar_aluno(db, adm, 0, "Ana Clara", "1A")[0])
        self.assertEqual(db["alunos"][0]["id"], aluno_id)
        self.assertEqual(db["ocorrencias"][0]["aluno_id"], aluno_id)
        self.assertEqual(db["ocorrencias"][0]["aluno"], "Ana Clara")
        self.assertEqual(db["notas"][0]["aluno"], "Ana Clara")
        self.assertEqual(db["faltas"][0]["aluno"], "Ana Clara")

        self.assertTrue(sala_service.editar_sala(db, adm, 0, "1B")[0])
        self.assertEqual(db["salas"][0]["id"], sala_id)
        self.assertEqual(db["alunos"][0]["sala_id"], sala_id)
        self.assertEqual(db["alunos"][0]["sala"], "1B")

    def test_permissoes_e_transicoes_continuam_validas(self):
        db, adm, professor, coordenador, diretor = self.criar_contexto()
        self.assertTrue(sala_service.criar_sala(db, adm, "1A")[0])
        self.assertTrue(aluno_service.criar_aluno(db, adm, "Ana", "1A")[0])
        self.assertFalse(sala_service.criar_sala(db, professor, "1B")[0])

        self.assertTrue(ocorrencia_service.criar_ocorrencia(
            db,
            professor,
            "Ana",
            "Descricao valida",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )[0])
        self.assertFalse(
            ocorrencia_service.atualizar_status_ocorrencia(
                db,
                professor,
                0,
                "EM_ANALISE",
            )[0]
        )
        self.assertTrue(
            ocorrencia_service.atualizar_status_ocorrencia(
                db,
                coordenador,
                0,
                "EM_ANALISE",
            )[0]
        )
        self.assertTrue(
            ocorrencia_service.atualizar_status_ocorrencia(
                db,
                coordenador,
                0,
                "RESOLVIDA",
            )[0]
        )
        self.assertTrue(
            ocorrencia_service.atualizar_status_ocorrencia(
                db,
                diretor,
                0,
                "ENCERRADA",
            )[0]
        )
        self.assertIn("data_hora", db["ocorrencias"][0]["historico"][-1])

    def test_ocorrencia_rejeita_entradas_invalidas_sem_persistir(self):
        db, adm, professor, *_ = self.criar_contexto()
        diretor = Usuario("Diretor Extra", "DIRETOR")
        self.assertTrue(sala_service.criar_sala(db, adm, "1A")[0])
        self.assertTrue(aluno_service.criar_aluno(db, adm, "Ana", "1A")[0])

        casos_invalidos = [
            ("", CATEGORIAS[0], PRIORIDADES[0]),
            ("   ", CATEGORIAS[0], PRIORIDADES[0]),
            (None, CATEGORIAS[0], PRIORIDADES[0]),
            (123, CATEGORIAS[0], PRIORIDADES[0]),
            ("x" * 1001, CATEGORIAS[0], PRIORIDADES[0]),
            ("Descricao valida", "Categoria inexistente", PRIORIDADES[0]),
            ("Descricao valida", CATEGORIAS[0], "urgente"),
        ]

        for descricao, categoria, prioridade in casos_invalidos:
            with self.subTest(descricao=repr(descricao), categoria=categoria, prioridade=prioridade):
                quantidade_antes = len(db["ocorrencias"])
                sucesso, _ = ocorrencia_service.criar_ocorrencia(
                    db,
                    professor,
                    "Ana",
                    descricao,
                    categoria,
                    prioridade,
                )
                self.assertFalse(sucesso)
                self.assertEqual(len(db["ocorrencias"]), quantidade_antes)

        sucesso, _ = ocorrencia_service.criar_ocorrencia(
            db,
            professor,
            "Aluno inexistente",
            "Descricao valida",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )
        self.assertFalse(sucesso)

        sucesso, _ = ocorrencia_service.criar_ocorrencia(
            db,
            diretor,
            "Ana",
            "Descricao valida",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )
        self.assertFalse(sucesso)

        db_minimo = {"alunos": [dict(db["alunos"][0])]}
        sucesso, mensagem = ocorrencia_service.criar_ocorrencia(
            db_minimo,
            professor,
            "Ana",
            "Descricao valida",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )
        self.assertTrue(sucesso, mensagem)
        self.assertEqual(len(db_minimo["ocorrencias"]), 1)

    def test_ocorrencia_bloqueia_transicoes_invalidas_e_spam(self):
        db, adm, professor, coordenador, diretor = self.criar_contexto()
        self.assertTrue(sala_service.criar_sala(db, adm, "1A")[0])
        self.assertTrue(aluno_service.criar_aluno(db, adm, "Ana", "1A")[0])
        self.assertTrue(ocorrencia_service.criar_ocorrencia(
            db,
            professor,
            "Ana",
            "Descricao valida",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )[0])

        historico_inicial = list(db["ocorrencias"][0]["historico"])
        usuario_invalido = type(
            "UsuarioInvalido",
            (),
            {"nome": "Secretaria", "papel": "SECRETARIA"},
        )()
        tentativas_invalidas = [
            (usuario_invalido, "EM_ANALISE"),
            (professor, "EM_ANALISE"),
            (diretor, "EM_ANALISE"),
            (coordenador, "RESOLVIDA"),
            (coordenador, "ENCERRADA"),
            (adm, "ENCERRADA"),
            (coordenador, "INVALIDO"),
            (coordenador, None),
        ]

        for usuario, status in tentativas_invalidas * 3:
            with self.subTest(papel=usuario.papel, status=status):
                sucesso, _ = ocorrencia_service.atualizar_status_ocorrencia(
                    db,
                    usuario,
                    0,
                    status,
                )
                self.assertFalse(sucesso)
                self.assertEqual(db["ocorrencias"][0]["status"], "REGISTRADA")
                self.assertEqual(db["ocorrencias"][0]["historico"], historico_inicial)

        self.assertTrue(ocorrencia_service.atualizar_status_ocorrencia(
            db,
            coordenador,
            0,
            "EM_ANALISE",
        )[0])
        tamanho_historico = len(db["ocorrencias"][0]["historico"])

        for _ in range(5):
            sucesso, _ = ocorrencia_service.atualizar_status_ocorrencia(
                db,
                coordenador,
                0,
                "EM_ANALISE",
            )
            self.assertFalse(sucesso)
            self.assertEqual(len(db["ocorrencias"][0]["historico"]), tamanho_historico)

        self.assertTrue(ocorrencia_service.atualizar_status_ocorrencia(
            db,
            coordenador,
            0,
            "RESOLVIDA",
        )[0])
        self.assertTrue(ocorrencia_service.atualizar_status_ocorrencia(
            db,
            diretor,
            0,
            "ENCERRADA",
        )[0])
        encerrado_historico = len(db["ocorrencias"][0]["historico"])
        sucesso, _ = ocorrencia_service.atualizar_status_ocorrencia(
            db,
            diretor,
            0,
            "ENCERRADA",
        )
        self.assertFalse(sucesso)
        self.assertEqual(len(db["ocorrencias"][0]["historico"]), encerrado_historico)

    def test_ocorrencia_operacoes_malformadas_nao_quebram_nem_mutam(self):
        _, _, _, coordenador, _ = self.criar_contexto()

        self.assertEqual(
            ocorrencia_service.listar_ocorrencias([], coordenador),
            (False, "Banco de dados invalido", []),
        )
        self.assertTrue(ocorrencia_service.listar_ocorrencias({}, coordenador)[0])
        self.assertFalse(ocorrencia_service.atualizar_status_ocorrencia(
            {},
            coordenador,
            0,
            "EM_ANALISE",
        )[0])

        casos = [
            [],
            {"ocorrencias": "bad"},
            {"ocorrencias": ("bad",)},
            {"ocorrencias": ["bad"]},
            {"ocorrencias": [{"status": "REGISTRADA", "historico": []}]},
            {"ocorrencias": [{"status": "REGISTRADA", "historico": {}}]},
            {"ocorrencias": [{"status": "REGISTRADA", "historico": None}]},
            {"ocorrencias": [{"status": "REGISTRADA", "historico": [123]}]},
        ]

        for dados in casos:
            with self.subTest(dados=repr(dados)):
                sucesso, _ = ocorrencia_service.atualizar_status_ocorrencia(
                    dados,
                    coordenador,
                    0,
                    "EM_ANALISE",
                )
                self.assertFalse(sucesso)
                if isinstance(dados, dict) and isinstance(dados.get("ocorrencias"), list):
                    registro = dados["ocorrencias"][0]
                    if isinstance(registro, dict):
                        self.assertEqual(registro["status"], "REGISTRADA")

    def test_ocorrencia_listagem_e_historico_nao_vazam_referencias_mutaveis(self):
        db, adm, professor, coordenador, _ = self.criar_contexto()
        self.assertTrue(sala_service.criar_sala(db, adm, "1A")[0])
        self.assertTrue(aluno_service.criar_aluno(db, adm, "Ana", "1A")[0])
        self.assertTrue(ocorrencia_service.criar_ocorrencia(
            db,
            professor,
            "Ana",
            "Descricao valida",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )[0])

        sucesso, _, ocorrencias = ocorrencia_service.listar_ocorrencias(db, coordenador)
        self.assertTrue(sucesso)
        ocorrencias[0]["status"] = "ENCERRADA"
        ocorrencias[0]["historico"][0]["status"] = "ENCERRADA"
        self.assertEqual(db["ocorrencias"][0]["status"], "REGISTRADA")
        self.assertEqual(db["ocorrencias"][0]["historico"][0]["status"], "REGISTRADA")

        sucesso, _, ocorrencias_aluno = ocorrencia_service.listar_ocorrencias_aluno(
            db,
            coordenador,
            "ana",
        )
        self.assertTrue(sucesso)
        self.assertEqual(len(ocorrencias_aluno), 1)
        ocorrencias_aluno[0]["historico"][0]["status"] = "ENCERRADA"
        self.assertEqual(db["ocorrencias"][0]["historico"][0]["status"], "REGISTRADA")

        sucesso, _, historico = ocorrencia_service.obter_historico(db, coordenador, 0)
        self.assertTrue(sucesso)
        historico[0]["status"] = "ENCERRADA"
        self.assertEqual(db["ocorrencias"][0]["historico"][0]["status"], "REGISTRADA")

        sucesso, _, dados_aluno = aluno_service.visualizar_aluno(db, professor, "Ana")
        self.assertTrue(sucesso)
        dados_aluno["ocorrencias"][0]["status"] = "ENCERRADA"
        dados_aluno["ocorrencias"][0]["historico"][0]["status"] = "ENCERRADA"
        self.assertEqual(db["ocorrencias"][0]["status"], "REGISTRADA")
        self.assertEqual(db["ocorrencias"][0]["historico"][0]["status"], "REGISTRADA")

    def test_listagens_publicas_nao_vazam_referencias_mutaveis(self):
        db, adm, professor, *_ = self.criar_contexto()
        self.assertTrue(sala_service.criar_sala(db, adm, "1A")[0])
        self.assertTrue(aluno_service.criar_aluno(db, adm, "Ana", "1A")[0])
        self.assertTrue(nota_service.adicionar_nota(db, professor, "Ana", "Matematica", 9)[0])
        self.assertTrue(falta_service.adicionar_falta(db, professor, "Ana", "2026-04-30")[0])

        sucesso, _, salas = sala_service.listar_salas(db, professor)
        self.assertTrue(sucesso)
        salas[0]["nome"] = "Mutada"
        self.assertEqual(db["salas"][0]["nome"], "1A")

        sucesso, _, alunos = aluno_service.listar_alunos(db, professor)
        self.assertTrue(sucesso)
        alunos[0]["nome"] = "Mutada"
        self.assertEqual(db["alunos"][0]["nome"], "Ana")

        sucesso, _, notas = nota_service.listar_notas(db, professor)
        self.assertTrue(sucesso)
        notas[0]["valor"] = 0
        self.assertEqual(db["notas"][0]["valor"], 9.0)

        sucesso, _, faltas = falta_service.listar_faltas(db, professor)
        self.assertTrue(sucesso)
        faltas[0]["data"] = "2026-01-01"
        self.assertEqual(db["faltas"][0]["data"], "2026-04-30")

        sucesso, _, usuarios = auth_service.listar_usuarios(db, adm)
        self.assertTrue(sucesso)
        usuarios[0]["nome"] = "Mutado"
        self.assertNotEqual(db["usuarios"][0]["nome"], "Mutado")
        self.assertTrue(all("senha_hash" not in usuario for usuario in usuarios))
        self.assertTrue(all("password_hash" not in usuario for usuario in usuarios))

    def test_ocorrencia_persiste_status_e_historico_apos_salvar_e_carregar(self):
        db, adm, professor, coordenador, diretor = self.criar_contexto()
        self.assertTrue(sala_service.criar_sala(db, adm, "1A")[0])
        self.assertTrue(aluno_service.criar_aluno(db, adm, "Ana", "1A")[0])
        self.assertTrue(ocorrencia_service.criar_ocorrencia(
            db,
            professor,
            "Ana",
            "Descricao valida",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )[0])
        self.assertTrue(ocorrencia_service.atualizar_status_ocorrencia(
            db,
            coordenador,
            0,
            "EM_ANALISE",
        )[0])
        self.assertTrue(ocorrencia_service.atualizar_status_ocorrencia(
            db,
            coordenador,
            0,
            "RESOLVIDA",
        )[0])
        self.assertTrue(ocorrencia_service.atualizar_status_ocorrencia(
            db,
            diretor,
            0,
            "ENCERRADA",
        )[0])

        with TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "polar.json"
            salvar_db(db, caminho)
            carregado = carregar_db(caminho)

        ocorrencia = carregado["ocorrencias"][0]
        self.assertEqual(ocorrencia["status"], "ENCERRADA")
        self.assertEqual([item["status"] for item in ocorrencia["historico"]], [
            "REGISTRADA",
            "EM_ANALISE",
            "RESOLVIDA",
            "ENCERRADA",
        ])

    def test_concorrencia_com_multiplos_logins_criacoes_e_transicoes(self):
        db, adm, professor, coordenador, diretor = self.criar_contexto()
        self.assertTrue(sala_service.criar_sala(db, adm, "1A")[0])
        self.assertTrue(aluno_service.criar_aluno(db, adm, "Ana", "1A")[0])

        erros = []
        tokens = []
        lock_resultados = threading.Lock()

        def login_worker(nome, senha):
            try:
                usuario, mensagem = auth_service.autenticar(db, nome, senha)
                with lock_resultados:
                    self.assertIsNotNone(usuario, mensagem)
                    tokens.append(usuario.sessao_token)
            except Exception as erro:
                with lock_resultados:
                    erros.append(erro)

        threads = [
            threading.Thread(target=login_worker, args=("Prof", "prof1234")),
            threading.Thread(target=login_worker, args=("Coord", "coord123")),
            threading.Thread(target=login_worker, args=("Diretor", "diretor123")),
            threading.Thread(target=login_worker, args=("Admin", "admin123")),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(erros, [])
        self.assertEqual(len(tokens), 4)
        self.assertEqual(len(set(tokens)), 4)

        def criar_ocorrencia_worker(indice):
            try:
                sucesso, mensagem = ocorrencia_service.criar_ocorrencia(
                    db,
                    professor,
                    "Ana",
                    f"Descricao concorrente {indice}",
                    CATEGORIAS[indice % len(CATEGORIAS)],
                    PRIORIDADES[indice % len(PRIORIDADES)],
                )
                if not sucesso:
                    raise AssertionError(mensagem)
            except Exception as erro:
                with lock_resultados:
                    erros.append(erro)

        threads = [threading.Thread(target=criar_ocorrencia_worker, args=(indice,)) for indice in range(30)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(erros, [])
        self.assertEqual(len(db["ocorrencias"]), 30)
        self.assertTrue(all(item["status"] == "REGISTRADA" for item in db["ocorrencias"]))
        self.assertTrue(all(len(item["historico"]) == 1 for item in db["ocorrencias"]))

        def fechar_ocorrencia_worker(indice):
            try:
                for status, usuario in (
                    ("EM_ANALISE", coordenador),
                    ("RESOLVIDA", coordenador),
                    ("ENCERRADA", diretor),
                ):
                    sucesso, mensagem = ocorrencia_service.atualizar_status_ocorrencia(
                        db,
                        usuario,
                        indice,
                        status,
                    )
                    if not sucesso:
                        raise AssertionError(mensagem)
            except Exception as erro:
                with lock_resultados:
                    erros.append(erro)

        threads = [threading.Thread(target=fechar_ocorrencia_worker, args=(indice,)) for indice in range(30)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(erros, [])
        for ocorrencia in db["ocorrencias"]:
            self.assertEqual(ocorrencia["status"], "ENCERRADA")
            self.assertEqual([item["status"] for item in ocorrencia["historico"]], [
                "REGISTRADA",
                "EM_ANALISE",
                "RESOLVIDA",
                "ENCERRADA",
            ])

    def test_corrida_no_mesmo_status_so_aplica_uma_transicao(self):
        db, adm, professor, coordenador, diretor = self.criar_contexto()
        self.assertTrue(sala_service.criar_sala(db, adm, "1A")[0])
        self.assertTrue(aluno_service.criar_aluno(db, adm, "Ana", "1A")[0])
        self.assertTrue(ocorrencia_service.criar_ocorrencia(
            db,
            professor,
            "Ana",
            "Descricao valida",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )[0])

        resultados = []
        lock_resultados = threading.Lock()

        def tentar_status(usuario, status):
            sucesso, _ = ocorrencia_service.atualizar_status_ocorrencia(db, usuario, 0, status)
            with lock_resultados:
                resultados.append(sucesso)

        threads = [
            threading.Thread(target=tentar_status, args=(coordenador, "EM_ANALISE"))
            for _ in range(20)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(resultados.count(True), 1)
        self.assertEqual(db["ocorrencias"][0]["status"], "EM_ANALISE")
        self.assertEqual(len(db["ocorrencias"][0]["historico"]), 2)

        resultados.clear()
        threads = [
            threading.Thread(target=tentar_status, args=(coordenador, "RESOLVIDA"))
            for _ in range(20)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(resultados.count(True), 1)
        self.assertEqual(db["ocorrencias"][0]["status"], "RESOLVIDA")
        self.assertEqual(len(db["ocorrencias"][0]["historico"]), 3)

        resultados.clear()
        threads = [
            threading.Thread(target=tentar_status, args=(diretor, "ENCERRADA"))
            for _ in range(20)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(resultados.count(True), 1)
        self.assertEqual(db["ocorrencias"][0]["status"], "ENCERRADA")
        self.assertEqual(len(db["ocorrencias"][0]["historico"]), 4)

    def test_json_corrompido_e_dados_parcialmente_validos_nao_quebram(self):
        with TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "polar.json"
            caminho.write_text("{ json quebrado", encoding="utf-8")

            db = carregar_db(caminho)

            self.assertIn("usuarios", db)
            self.assertTrue(any(usuario["papel"] == "ADM" for usuario in db["usuarios"]))
            backups = list(Path(diretorio).glob("polar.json.corrompido-*"))
            self.assertEqual(len(backups), 1)

        dados = {
            "usuarios": [
                {"username": "Coord Alias", "role": "COORDENADOR"},
                {"nome": "", "papel": "PROFESSOR"},
                "usuario quebrado",
            ],
            "salas": [{"nome": "1A"}, {"nome": ""}],
            "alunos": [{"nome": "Ana", "sala": "1A"}, {"nome": "", "sala": "1A"}],
            "ocorrencias": [{
                "aluno": "Ana",
                "descricao": "Descricao valida",
                "categoria": CATEGORIAS[0],
                "prioridade": PRIORIDADES[0],
                "criado_por": "Coord Alias",
            }, {"aluno": "", "descricao": ""}],
            "notas": [{"aluno": "Ana", "disciplina": "Matematica", "valor": 8}, {"aluno": "Ana"}],
            "faltas": [{"aluno": "Ana", "data": "2026-04-30"}, {"aluno": "Ana", "data": "30/04/2026"}],
        }

        normalizado, alterado = normalizar_db(dados)

        self.assertTrue(alterado)
        self.assertTrue(any(usuario["username"] == "Coord Alias" for usuario in normalizado["usuarios"]))
        self.assertEqual(len(normalizado["alunos"]), 1)
        self.assertEqual(len(normalizado["ocorrencias"]), 1)
        self.assertEqual(len(normalizado["notas"]), 1)
        self.assertEqual(len(normalizado["faltas"]), 1)

    def test_cargo_coordenador_e_diretor_nao_concedem_adm_sem_permissao_explicita(self):
        db = criar_db_vazio(incluir_admin=False)
        adm = Usuario("Admin", "ADM", senha_hash=gerar_senha_hash("admin123"))
        coordenador = Usuario("Coord", "COORDENADOR", senha_hash=gerar_senha_hash("coord123"))
        diretor = Usuario("Diretor", "DIRETOR", senha_hash=gerar_senha_hash("diretor123"))
        coord_admin = Usuario(
            "Coord Admin",
            "COORDENADOR",
            senha_hash=gerar_senha_hash("coordadmin123"),
            permissoes=["ADM"],
        )
        db["usuarios"] = [
            adm.para_dict(),
            coordenador.para_dict(),
            diretor.para_dict(),
            coord_admin.para_dict(),
        ]

        adm, _ = auth_service.autenticar(db, "Admin", "admin123")
        coordenador, _ = auth_service.autenticar(db, "Coord", "coord123")
        diretor, _ = auth_service.autenticar(db, "Diretor", "diretor123")
        coord_admin, _ = auth_service.autenticar(db, "Coord Admin", "coordadmin123")

        self.assertFalse(sala_service.criar_sala(db, coordenador, "Coord Sala")[0])
        self.assertFalse(sala_service.criar_sala(db, diretor, "Diretor Sala")[0])
        self.assertFalse(auth_service.criar_usuario(
            db,
            coordenador,
            "Novo Prof",
            "PROFESSOR",
            "senha1234",
        )[0])

        self.assertTrue(sala_service.criar_sala(db, coord_admin, "Sala ADM Explicito")[0])
        self.assertTrue(auth_service.criar_usuario(
            db,
            coord_admin,
            "Professor Novo",
            "PROFESSOR",
            "senha1234",
        )[0])
        self.assertEqual(coord_admin.papel, "COORDENADOR")
        self.assertIn("ADM", coord_admin.permissoes)

        indice_coord_admin, _ = auth_service.buscar_usuario(db, "Coord Admin")
        self.assertTrue(auth_service.alterar_permissoes(db, adm, indice_coord_admin, [])[0])
        self.assertFalse(sala_service.criar_sala(db, coord_admin, "Sessao Antiga")[0])

    def test_login_invalido_bloqueia_temporariamente_usuario(self):
        db, _, *_ = self.criar_contexto()

        for _ in range(auth_service.MAX_TENTATIVAS_LOGIN):
            usuario, mensagem = auth_service.autenticar(db, "Prof", "senha_errada")
            self.assertIsNone(usuario)
            self.assertIn("Acesso negado", mensagem)

        usuario, mensagem = auth_service.autenticar(db, "Prof", "prof1234")
        self.assertIsNone(usuario)
        self.assertIn("bloqueado", mensagem)

        _, registro = auth_service.buscar_usuario(db, "Prof")
        self.assertGreaterEqual(registro.get("login_falhas", 0), auth_service.MAX_TENTATIVAS_LOGIN)
        self.assertTrue(registro.get("bloqueado_ate"))

    def test_cli_python_rejeita_sem_auth_json_invalido_e_nao_usa_adm_fake(self):
        db = criar_db_vazio(incluir_admin=False)
        adm = Usuario("Admin", "ADM", senha_hash=gerar_senha_hash("admin123"))
        db["usuarios"] = [adm.para_dict()]

        with TemporaryDirectory() as diretorio:
            caminho = Path(diretorio) / "polar.json"
            salvar_db(db, caminho)
            antigo = os.environ.get("POLAR_DB_PATH")
            os.environ["POLAR_DB_PATH"] = str(caminho)
            try:
                resposta = sala_service._executar_cli([
                    "sala_service.py",
                    "criar",
                    '{"nome": "Sala sem auth"}',
                ])
                self.assertEqual(resposta["status"], "erro")
                self.assertIn("Credenciais", resposta["mensagem"])
                self.assertEqual(carregar_db(caminho)["salas"], [])

                resposta = sala_service._executar_cli([
                    "sala_service.py",
                    "criar",
                    "{ json quebrado",
                ])
                self.assertEqual(resposta["status"], "erro")
                self.assertIn("JSON", resposta["mensagem"])

                resposta = sala_service._executar_cli([
                    "sala_service.py",
                    "criar",
                    '{"nome": "Sala OK", "auth": {"nome": "Admin", "senha": "admin123"}}',
                ])
                self.assertEqual(resposta["status"], "sucesso")
                self.assertEqual(carregar_db(caminho)["salas"][0]["nome"], "Sala OK")
            finally:
                if antigo is None:
                    os.environ.pop("POLAR_DB_PATH", None)
                else:
                    os.environ["POLAR_DB_PATH"] = antigo

    def test_remocao_de_sala_e_aluno_preserva_integridade(self):
        db, adm, professor, *_ = self.criar_contexto()
        self.assertTrue(sala_service.criar_sala(db, adm, "1A")[0])
        self.assertTrue(aluno_service.criar_aluno(db, adm, "Ana", "1A")[0])

        self.assertFalse(aluno_service.remover_aluno_da_sala(db, professor, 0)[0])
        self.assertTrue(aluno_service.remover_aluno_da_sala(db, adm, 0)[0])
        self.assertEqual(db["alunos"][0]["sala"], "Sem sala")

        indice_sala_original, _ = sala_service.buscar_sala(db, "1A")
        self.assertTrue(sala_service.remover_sala(db, adm, indice_sala_original)[0])
        self.assertIsNone(sala_service.buscar_sala(db, "1A")[1])

        self.assertTrue(ocorrencia_service.criar_ocorrencia(
            db,
            professor,
            "Ana",
            "Descricao unica para integridade",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )[0])
        self.assertFalse(aluno_service.remover_aluno(db, adm, 0)[0])

    def test_ocorrencia_bloqueia_spam_duplicado(self):
        db, adm, professor, *_ = self.criar_contexto()
        self.assertTrue(sala_service.criar_sala(db, adm, "1A")[0])
        self.assertTrue(aluno_service.criar_aluno(db, adm, "Ana", "1A")[0])

        self.assertTrue(ocorrencia_service.criar_ocorrencia(
            db,
            professor,
            "Ana",
            "Descricao repetida para spam",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )[0])
        sucesso, mensagem = ocorrencia_service.criar_ocorrencia(
            db,
            professor,
            "Ana",
            "Descricao repetida para spam",
            CATEGORIAS[0],
            PRIORIDADES[0],
        )
        self.assertFalse(sucesso)
        self.assertIn("duplicada", mensagem)
        self.assertEqual(len(db["ocorrencias"]), 1)

    def test_normalizacao_corrige_ids_duplicados(self):
        dados = {
            "usuarios": [
                {"id": "11111111111111111111111111111111", "nome": "Admin", "papel": "ADM", "senha_hash": gerar_senha_hash("admin123")},
                {"id": "11111111111111111111111111111111", "nome": "Coord", "papel": "COORDENADOR", "senha_hash": gerar_senha_hash("coord123")},
            ],
            "salas": [
                {"id": "22222222222222222222222222222222", "nome": "1A"},
                {"id": "22222222222222222222222222222222", "nome": "1B"},
            ],
            "alunos": [
                {"id": "33333333333333333333333333333333", "nome": "Ana", "sala": "1A"},
                {"id": "33333333333333333333333333333333", "nome": "Bia", "sala": "1B"},
            ],
            "ocorrencias": [],
            "notas": [],
            "faltas": [],
        }

        normalizado, alterado = normalizar_db(dados)

        self.assertTrue(alterado)
        for chave in ("usuarios", "salas", "alunos"):
            ids = [item["id"] for item in normalizado[chave]]
            self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
