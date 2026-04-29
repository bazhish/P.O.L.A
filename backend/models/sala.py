from utils.validators import normalizar_texto, validar_nome


class Sala:
    def __init__(self, nome):
        nome = normalizar_texto(nome)
        if not validar_nome(nome):
            raise ValueError("Nome da sala e obrigatorio")
        self.nome = nome

    def para_dict(self):
        return {"nome": self.nome}

    @classmethod
    def de_dict(cls, dados):
        return cls(dados.get("nome", ""))
