from utils.validators import normalizar_texto, validar_nome


class Aluno:
    def __init__(self, nome, sala):
        nome = normalizar_texto(nome)
        sala = normalizar_texto(sala)

        if not validar_nome(nome):
            raise ValueError("Nome do aluno e obrigatorio")

        if not validar_nome(sala):
            raise ValueError("Sala do aluno e obrigatoria")

        self.nome = nome
        self.sala = sala

    def para_dict(self):
        return {
            "nome": self.nome,
            "sala": self.sala,
        }

    @classmethod
    def de_dict(cls, dados):
        return cls(dados.get("nome", ""), dados.get("sala", ""))
