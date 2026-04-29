from utils.validators import normalizar_texto, validar_data, validar_nome


class Falta:
    def __init__(self, aluno, data):
        aluno = normalizar_texto(aluno)
        data = normalizar_texto(data)

        if not validar_nome(aluno):
            raise ValueError("Aluno e obrigatorio")

        if not validar_data(data):
            raise ValueError("Data deve estar no formato AAAA-MM-DD")

        self.aluno = aluno
        self.data = data

    def para_dict(self):
        return {
            "aluno": self.aluno,
            "data": self.data,
        }

    @classmethod
    def de_dict(cls, dados):
        return cls(dados.get("aluno", ""), dados.get("data", ""))
