from utils.ids import garantir_id
from utils.validators import normalizar_texto, validar_data, validar_nome


class Falta:
    def __init__(self, aluno, data, id=None, aluno_id=None):
        aluno = normalizar_texto(aluno)
        data = normalizar_texto(data)

        if not validar_nome(aluno):
            raise ValueError("Aluno e obrigatorio")

        if not validar_data(data):
            raise ValueError("Data deve estar no formato AAAA-MM-DD")

        self.id = garantir_id(id)
        self.aluno = aluno
        self.aluno_id = aluno_id
        self.data = data

    def para_dict(self):
        dados = {
            "id": self.id,
            "aluno": self.aluno,
            "data": self.data,
        }
        if self.aluno_id:
            dados["aluno_id"] = self.aluno_id
        return dados

    @classmethod
    def de_dict(cls, dados):
        return cls(
            dados.get("aluno", ""),
            dados.get("data", ""),
            id=dados.get("id"),
            aluno_id=dados.get("aluno_id"),
        )
