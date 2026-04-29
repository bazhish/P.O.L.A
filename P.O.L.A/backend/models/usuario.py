from utils.validators import normalizar_papel, normalizar_texto, validar_nome, validar_papel


class Usuario:
    def __init__(self, nome, papel):
        nome = normalizar_texto(nome)
        papel = normalizar_papel(papel)

        if not validar_nome(nome):
            raise ValueError("Nome de usuario e obrigatorio")

        if not validar_papel(papel):
            raise ValueError(f"Papel invalido: {papel}")

        self.nome = nome
        self.nome_usuario = nome
        self.papel = papel

    def para_dict(self):
        return {
            "nome": self.nome,
            "papel": self.papel,
        }

    @classmethod
    def de_dict(cls, dados):
        return cls(dados.get("nome", dados.get("nome_usuario", "")), dados.get("papel", ""))
