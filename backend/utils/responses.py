import json


def resposta_sucesso(mensagem, dados=None, **extras):
    resposta = {
        "status": "sucesso",
        "sucesso": True,
        "mensagem": mensagem,
    }
    if dados is not None:
        resposta["dados"] = dados
    resposta.update(extras)
    return resposta


def resposta_erro(mensagem, dados=None, **extras):
    resposta = {
        "status": "erro",
        "sucesso": False,
        "mensagem": mensagem,
    }
    if dados is not None:
        resposta["dados"] = dados
    resposta.update(extras)
    return resposta


def resposta_servico(sucesso, mensagem, dados=None, **extras):
    if sucesso:
        return resposta_sucesso(mensagem, dados=dados, **extras)
    return resposta_erro(mensagem, dados=dados, **extras)


def imprimir_resposta(resposta):
    print(json.dumps(resposta, ensure_ascii=False))
