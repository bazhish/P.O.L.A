from utils.ids import garantir_id
from utils.validators import (
    normalizar_papel,
    normalizar_permissoes,
    normalizar_texto,
    validar_nome,
    validar_papel,
)

class Usuario:
    def __init__(
        self,
        nome,
        papel,
        senha_hash=None,
        id=None,
        precisa_trocar_senha=False,
        permissoes=None,
        login_falhas=0,
        bloqueado_ate=None,
        ultimo_login=None,
    ):
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
        self.permissoes = normalizar_permissoes(permissoes)
        try:
            self.login_falhas = max(0, int(login_falhas or 0))
        except (TypeError, ValueError):
            self.login_falhas = 0
        self.bloqueado_ate = bloqueado_ate
        self.ultimo_login = ultimo_login

    def para_dict(self):
        dados = {
            "id": self.id,
            "nome": self.nome,
            "papel": self.papel,
            "username": self.nome,
            "role": self.papel,
        }
        if self.senha_hash:
            dados["senha_hash"] = self.senha_hash
            dados["password_hash"] = self.senha_hash
        if self.precisa_trocar_senha:
            dados["precisa_trocar_senha"] = True
        if self.permissoes:
            dados["permissoes"] = list(self.permissoes)
        if self.login_falhas:
            dados["login_falhas"] = self.login_falhas
        if self.bloqueado_ate:
            dados["bloqueado_ate"] = self.bloqueado_ate
        if self.ultimo_login:
            dados["ultimo_login"] = self.ultimo_login
        return dados

    @classmethod
    def de_dict(cls, dados):
        return cls(
            dados.get("nome", dados.get("username", dados.get("nome_usuario", ""))),
            dados.get("papel", dados.get("role", "")),
            senha_hash=dados.get("senha_hash", dados.get("password_hash")),
            id=dados.get("id"),
            precisa_trocar_senha=dados.get("precisa_trocar_senha", False),
            permissoes=dados.get("permissoes", []),
            login_falhas=dados.get("login_falhas", 0),
            bloqueado_ate=dados.get("bloqueado_ate"),
            ultimo_login=dados.get("ultimo_login"),
        )


class Professor(Usuario):
    def __init__(self, nome, **kwargs):
        super().__init__(nome, "PROFESSOR", **kwargs)


class Coordenador(Usuario):
    def __init__(self, nome, **kwargs):
        super().__init__(nome, "COORDENADOR", **kwargs)


class Diretor(Usuario):
    def __init__(self, nome, **kwargs):
        super().__init__(nome, "DIRETOR", **kwargs)


class Administrador(Usuario):
    def __init__(self, nome, **kwargs):
        super().__init__(nome, "ADM", **kwargs)
