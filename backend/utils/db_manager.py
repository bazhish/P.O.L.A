"""Gerenciador de operações com banco de dados PostgreSQL (Supabase)"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, cast
import psycopg
from models.usuario import Usuario
from models.aluno import Aluno
from models.sala import Sala
from models.nota import Nota
from models.falta import Falta
from models.ocorrencia import Ocorrencia
from utils.db_cloud import ConexaoBD
from utils.validators import normalizar_texto


class GerenciadorBD:
    """Gerenciador centralizado para operações com o banco de dados"""
    
    def __init__(self):
        self.conn = None
    
    def obter_conexao(self):
        """Obtém conexão com o banco"""
        if not self.conn:
            self.conn = ConexaoBD.obter_conexao()
        return self.conn
    
    def fechar(self):
        """Fecha a conexão"""
        if self.conn:
            ConexaoBD.fechar()
            self.conn = None
    
    # ==================== USUÁRIOS ====================
    
    def buscar_usuario_por_nome(self, nome: str) -> Optional[Dict]:
        """Busca usuário por nome"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, nome, papel, senha_hash, precisa_trocar_senha FROM usuarios WHERE LOWER(nome) = LOWER(%s)",
                (normalizar_texto(nome),)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "nome": row[1],
                    "papel": row[2],
                    "senha_hash": row[3],
                    "precisa_trocar_senha": row[4],
                }
            return None
        finally:
            cursor.close()
    
    def buscar_usuario_por_id(self, id: int) -> Optional[Dict]:
        """Busca usuário por ID"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, nome, papel, senha_hash, precisa_trocar_senha FROM usuarios WHERE id = %s",
                (id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "nome": row[1],
                    "papel": row[2],
                    "senha_hash": row[3],
                    "precisa_trocar_senha": row[4],
                }
            return None
        finally:
            cursor.close()
    
    def listar_usuarios(self) -> List[Dict]:
        """Lista todos os usuários"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, nome, papel, senha_hash, precisa_trocar_senha FROM usuarios ORDER BY nome"
            )
            usuarios = []
            for row in cursor.fetchall():
                usuarios.append({
                    "id": row[0],
                    "nome": row[1],
                    "papel": row[2],
                    "senha_hash": row[3],
                    "precisa_trocar_senha": row[4],
                })
            return usuarios
        finally:
            cursor.close()
    
    def criar_usuario(self, nome: str, papel: str, senha_hash: str) -> Dict:
        """Cria novo usuário"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO usuarios (nome, papel, senha_hash, precisa_trocar_senha)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id, nome, papel, precisa_trocar_senha""",
                (nome, papel, senha_hash, True)
            )
            row = cursor.fetchone()
            conn.commit()
            row = cast(Tuple, row)
            return {
                "id": row[0],
                "nome": row[1],
                "papel": row[2],
                "precisa_trocar_senha": row[3],
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def atualizar_usuario(self, id: int, **kwargs) -> bool:
        """Atualiza dados do usuário"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            campos = []
            valores = []
            for chave, valor in kwargs.items():
                campos.append(f"{chave} = %s")
                valores.append(valor)
            
            if not campos:
                return False
            
            valores.append(id)
            query = f"UPDATE usuarios SET {', '.join(campos)}, updated_at = NOW() WHERE id = %s"
            cursor.execute(query, valores)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def deletar_usuario(self, id: int) -> bool:
        """Deleta usuário"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    # ==================== SALAS ====================
    
    def buscar_sala_por_nome(self, nome: str) -> Optional[Dict]:
        """Busca sala por nome"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, nome, ano_letivo FROM salas WHERE LOWER(nome) = LOWER(%s)",
                (normalizar_texto(nome),)
            )
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "nome": row[1], "ano_letivo": row[2]}
            return None
        finally:
            cursor.close()
    
    def listar_salas(self) -> List[Dict]:
        """Lista todas as salas"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, nome, ano_letivo FROM salas ORDER BY nome")
            salas = []
            for row in cursor.fetchall():
                salas.append({"id": row[0], "nome": row[1], "ano_letivo": row[2]})
            return salas
        finally:
            cursor.close()
    
    def criar_sala(self, nome: str, ano_letivo: Optional[int] = None) -> Dict:
        """Cria nova sala"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO salas (nome, ano_letivo)
                   VALUES (%s, %s)
                   RETURNING id, nome, ano_letivo""",
                (nome, ano_letivo)
            )
            row = cursor.fetchone()
            row = cast(Tuple, row)
            conn.commit()
            return {"id": row[0], "nome": row[1], "ano_letivo": row[2]}
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    # ==================== ALUNOS ====================
    
    def buscar_aluno_por_nome(self, nome: str) -> Optional[Dict]:
        """Busca aluno por nome"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """SELECT id, nome, sala_id, matricula FROM alunos 
                   WHERE LOWER(nome) = LOWER(%s) LIMIT 1""",
                (normalizar_texto(nome),)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "nome": row[1],
                    "sala_id": row[2],
                    "matricula": row[3],
                }
            return None
        finally:
            cursor.close()
    
    def buscar_aluno_por_id(self, id: int) -> Optional[Dict]:
        """Busca aluno por ID"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, nome, sala_id, matricula FROM alunos WHERE id = %s",
                (id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "nome": row[1],
                    "sala_id": row[2],
                    "matricula": row[3],
                }
            return None
        finally:
            cursor.close()
    
    def listar_alunos(self) -> List[Dict]:
        """Lista todos os alunos"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, nome, sala_id, matricula FROM alunos ORDER BY nome")
            alunos = []
            for row in cursor.fetchall():
                alunos.append({
                    "id": row[0],
                    "nome": row[1],
                    "sala_id": row[2],
                    "matricula": row[3],
                })
            return alunos
        finally:
            cursor.close()
    
    def listar_alunos_por_sala(self, sala_id: int) -> List[Dict]:
        """Lista alunos por sala"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, nome, sala_id, matricula FROM alunos WHERE sala_id = %s ORDER BY nome",
                (sala_id,)
            )
            alunos = []
            for row in cursor.fetchall():
                alunos.append({
                    "id": row[0],
                    "nome": row[1],
                    "sala_id": row[2],
                    "matricula": row[3],
                })
            return alunos
        finally:
            cursor.close()
    
    def criar_aluno(self, nome: str, sala_id: Optional[int] = None, matricula: Optional[str] = None) -> Dict:
        """Cria novo aluno"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO alunos (nome, sala_id, matricula)
                   VALUES (%s, %s, %s)
                   RETURNING id, nome, sala_id, matricula""",
                (nome, sala_id, matricula)
            )
            row = cursor.fetchone()
            row = cast(Tuple, row)
            conn.commit()
            return {
                "id": row[0],
                "nome": row[1],
                "sala_id": row[2],
                "matricula": row[3],
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def atualizar_aluno(self, id: int, **kwargs) -> bool:
        """Atualiza dados do aluno"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            campos = []
            valores = []
            for chave, valor in kwargs.items():
                campos.append(f"{chave} = %s")
                valores.append(valor)
            
            if not campos:
                return False
            
            valores.append(id)
            query = f"UPDATE alunos SET {', '.join(campos)}, updated_at = NOW() WHERE id = %s"
            cursor.execute(query, valores)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def deletar_aluno(self, id: int) -> bool:
        """Deleta aluno"""
        conn = self.obter_conexao()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM alunos WHERE id = %s", (id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()


# Instância global
db_manager = GerenciadorBD()


def obter_gerenciador() -> GerenciadorBD:
    """Retorna o gerenciador de banco de dados"""
    return db_manager
