import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from models.usuario import Usuario
from services import aluno_service, auth_service, falta_service, nota_service
from services import ocorrencia_service, sala_service
from utils.db import criar_db_vazio, normalizar_db
from utils.security import gerar_senha_hash, senha_inicial_padrao
from utils.validators import CATEGORIAS, PRIORIDADES


class EngineTestCase(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
