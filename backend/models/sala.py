from utils.ids import garantir_id
from utils.validators import normalizar_texto, validar_nome


class Sala:
    def __init__(self, nome, id=None):
        nome = normalizar_texto(nome)
        if not validar_nome(nome):
            raise ValueError("Nome da sala e obrigatorio")
        self.id = garantir_id(id)
        self.nome = nome

    def para_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
        }

    @classmethod
    def de_dict(cls, dados):
        return cls(dados.get("nome", ""), id=dados.get("id"))
