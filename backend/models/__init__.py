"""Domain models for POLAR."""

from models.aluno import Aluno
from models.falta import Falta
from models.nota import Nota
from models.ocorrencia import Ocorrencia
from models.sala import Sala
from models.usuario import Administrador, Coordenador, Diretor, Professor, Usuario


__all__ = [
    "Administrador",
    "Aluno",
    "Coordenador",
    "Diretor",
    "Falta",
    "Nota",
    "Ocorrencia",
    "Professor",
    "Sala",
    "Usuario",
]
