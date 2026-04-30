from utils.ids import garantir_id
from utils.validators import normalizar_papel, normalizar_texto, validar_nome, validar_papel


class Usuario:
    def __init__(self, nome, papel, senha_hash=None, id=None, precisa_trocar_senha=False):
        nome = normalizar_texto(nome)
        papel = normalizar_papel(papel)
        id = garantir_id(id)

        if not validar_nome(nome):
            raise ValueError("Nome de usuario e obrigatorio")

        if not validar_papel(papel):
            raise ValueError(f"Papel invalido: {papel}")

        self.nome = nome
        self.nome_usuario = nome
        self.papel = papel
        self.id = id
        self.senha_hash = senha_hash
        self.precisa_trocar_senha = bool(precisa_trocar_senha)

    def para_dict(self):
        dados = {
            "id": self.id,
            "nome": self.nome,
            "papel": self.papel,
        }
        if self.senha_hash:
            dados["senha_hash"] = self.senha_hash
        if self.precisa_trocar_senha:
            dados["precisa_trocar_senha"] = True
        return dados

    @classmethod
    def de_dict(cls, dados):
        return cls(
            dados.get("nome", dados.get("nome_usuario", "")),
            dados.get("papel", ""),
            senha_hash=dados.get("senha_hash"),
            id=dados.get("id"),
            precisa_trocar_senha=dados.get("precisa_trocar_senha", False),
        )
