from utils.ids import garantir_id
from utils.validators import normalizar_texto, validar_nome


class Aluno:
    def __init__(self, nome, sala, id=None, sala_id=None):
        nome = normalizar_texto(nome)
        sala = normalizar_texto(sala)

        if not validar_nome(nome):
            raise ValueError("Nome do aluno e obrigatorio")

        if not validar_nome(sala):
            raise ValueError("Sala do aluno e obrigatoria")

        self.id = garantir_id(id)
        self.nome = nome
        self.sala = sala
        self.sala_id = sala_id

    def para_dict(self):
        dados = {
            "id": self.id,
            "nome": self.nome,
            "sala": self.sala,
        }
        if self.sala_id:
            dados["sala_id"] = self.sala_id
        return dados

    @classmethod
    def de_dict(cls, dados):
        return cls(
            dados.get("nome", ""),
            dados.get("sala", ""),
            id=dados.get("id"),
            sala_id=dados.get("sala_id"),
        )
