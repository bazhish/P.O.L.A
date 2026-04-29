from utils.validators import (
    CATEGORIAS,
    PRIORIDADES,
    STATUS_VALIDOS,
    normalizar_categoria,
    normalizar_prioridade,
    normalizar_texto,
    validar_categoria,
    validar_nome,
    validar_prioridade,
    validar_status,
)


class Ocorrencia:
    def __init__(
        self,
        aluno,
        descricao,
        categoria,
        prioridade,
        criado_por,
        status="REGISTRADA",
        historico=None,
    ):
        aluno = normalizar_texto(aluno)
        descricao = normalizar_texto(descricao)
        categoria = normalizar_categoria(categoria)
        prioridade = normalizar_prioridade(prioridade)
        criado_por = normalizar_texto(criado_por)

        if not validar_nome(aluno):
            raise ValueError("Aluno e obrigatorio")

        if not validar_nome(descricao):
            raise ValueError("Descricao e obrigatoria")

        if not validar_categoria(categoria):
            raise ValueError("Categoria invalida")

        if not validar_prioridade(prioridade):
            raise ValueError("Prioridade invalida")

        if not validar_nome(criado_por):
            raise ValueError("Usuario criador e obrigatorio")

        if not validar_status(status):
            raise ValueError("Status invalido")

        self.aluno = aluno
        self.descricao = descricao
        self.categoria = categoria
        self.prioridade = prioridade
        self.status = status
        self.criado_por = criado_por
        self.historico = []

        if historico is None:
            self.adicionar_historico("Criada", status)
        else:
            self.historico = normalizar_historico(historico, status)

    def adicionar_historico(self, acao, status=None):
        status = status or self.status
        if not validar_status(status):
            raise ValueError("Status de historico invalido")

        self.historico.append({
            "acao": normalizar_texto(acao) or "Atualizacao",
            "status": status,
        })

    def para_dict(self):
        return {
            "aluno": self.aluno,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "prioridade": self.prioridade,
            "status": self.status,
            "criado_por": self.criado_por,
            "historico": [dict(item) for item in self.historico],
        }

    @classmethod
    def de_dict(cls, dados):
        categoria = dados.get("categoria")
        prioridade = dados.get("prioridade")
        status = dados.get("status", "REGISTRADA")
        categoria = normalizar_categoria(categoria)
        prioridade = normalizar_prioridade(prioridade)

        if categoria not in CATEGORIAS:
            raise ValueError("Categoria invalida")
        if prioridade not in PRIORIDADES:
            raise ValueError("Prioridade invalida")
        if status not in STATUS_VALIDOS:
            raise ValueError("Status invalido")

        return cls(
            aluno=dados.get("aluno", ""),
            descricao=dados.get("descricao", dados.get("descrição", "")),
            categoria=categoria,
            prioridade=prioridade,
            criado_por=dados.get("criado_por", "sistema"),
            status=status,
            historico=dados.get("historico"),
        )


def normalizar_historico(historico, status_atual):
    if not isinstance(historico, list):
        return [{"acao": "Historico recriado", "status": status_atual}]

    itens = []
    for item in historico:
        if not isinstance(item, dict):
            continue
        acao = normalizar_texto(item.get("acao", ""))
        status = item.get("status")
        if acao and validar_status(status):
            itens.append({"acao": acao, "status": status})

    if not itens:
        itens.append({"acao": "Historico recriado", "status": status_atual})

    return itens
