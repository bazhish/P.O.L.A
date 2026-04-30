from utils.ids import garantir_id
from utils.validators import normalizar_texto, validar_nome, validar_nota_valor


class Nota:
    def __init__(self, aluno, disciplina, valor, id=None, aluno_id=None):
        aluno = normalizar_texto(aluno)
        disciplina = normalizar_texto(disciplina)
        valor = float(valor)

        if not validar_nome(aluno):
            raise ValueError("Aluno e obrigatorio")

        if not validar_nome(disciplina):
            raise ValueError("Disciplina e obrigatoria")

        if not validar_nota_valor(valor):
            raise ValueError("Nota deve estar entre 0 e 10")

        self.id = garantir_id(id)
        self.aluno = aluno
        self.aluno_id = aluno_id
        self.disciplina = disciplina
        self.valor = valor

    def para_dict(self):
        dados = {
            "id": self.id,
            "aluno": self.aluno,
            "disciplina": self.disciplina,
            "valor": self.valor,
        }
        if self.aluno_id:
            dados["aluno_id"] = self.aluno_id
        return dados

    @classmethod
    def de_dict(cls, dados):
        return cls(
            dados.get("aluno", ""),
            dados.get("disciplina", ""),
            dados.get("valor", -1),
            id=dados.get("id"),
            aluno_id=dados.get("aluno_id"),
        )
