import json
import os

# CONFIG
CATEGORIAS = [
    "Comportamento inadequado",
    "Atraso",
    "Falta",
    "Não fez atividade",
    "Desrespeito ao professor",
    "Uso de celular",
    "Briga",
    "Bullying",
    "Conversa paralelas",
    "Dano ao patrimônio"
]
PRIORIDADES = ["baixa", "media", "alta"]
ARQUIVO_DB = "banco_dados.json"

# BANCO DE DADOS SIMPLES
def carregar_db():
    if not os.path.exists(ARQUIVO_DB):
        return {"usuarios":[],"ocorrencias":[]}
    with open(ARQUIVO_DB,"r") as f:
        return json.load(f)
    
def salvar_db(dados):
    with open(ARQUIVO_DB, "w") as f:
        json.dump(dados,f,indent=4)

# ENTIDADES
class Usuario:
    def __init__(self, nome_usuario, papel):
        self.nome_usuario = nome_usuario
        self.papel = papel

class Professor(Usuario):
    def __init__(self, nome_usuario):
        super().__init__(nome_usuario, "PROFESSOR")


class Coordenador(Usuario):
    def __init__(self, nome_usuario):
        super().__init__(nome_usuario, "COORDENADOR")


class Diretor(Usuario):
    def __init__(self, nome_usuario):
        super().__init__(nome_usuario, "DIRETOR")


class Aluno:
    def __init__(self, nome):
        self.nome = nome


class Ocorrencia:
    def __init__(self, aluno, descricao, categoria, prioridade, criado_por):
        if not categoria or not prioridade:
            raise Exception("Categoria e prioridade são obrigatórias")

        self.aluno = aluno
        self.descricao = descricao
        self.categoria = categoria
        self.prioridade = prioridade
        self.status = "REGISTRADA"
        self.criado_por = criado_por
        self.historico = []

        self.registrar_log("Criada")

    def registrar_log(self, acao):
        self.historico.append({
            "acao": acao,
            "status": self.status
        })

    def atualizar_status(self, novo_status, usuario):
        print(f"[DEBUG] Tentando mudar status para {novo_status} como {usuario.papel}")

        if usuario.papel == "PROFESSOR":
            print("Professor não pode alterar status")
            return

        if usuario.papel == "COORDENADOR":
            if novo_status not in ["EM_ANALISE", "RESOLVIDA"]:
                print("Coordenador só pode ir até RESOLVIDA")
                return

        if usuario.papel == "DIRETOR":
            if novo_status != "ENCERRADA":
                print("Diretor só pode ENCERRAR")
                return

        self.status = novo_status
        self.registrar_log(f"Alterado por {usuario.nome_usuario}")
        print("Status atualizado")


# LOGIN SIMULADO
def login():
    print("\nLOGIN")
    print("1 - Professor")
    print("2 - Coordenador")
    print("3 - Diretor")

    escolha = input("Escolha: ")

    nome_usuario = input("Usuário: ")

    if escolha == "1":
        return Professor(nome_usuario)
    elif escolha == "2":
        return Coordenador(nome_usuario)
    elif escolha == "3":
        return Diretor(nome_usuario)
    else:
        print("Opção inválida")
        return None


# FUNÇÕES DO SISTEMA
def criar_ocorrencia(usuario, db):
    print("\nNOVA OCORRÊNCIA")

    nome_aluno = input("Nome do aluno: ")
    descricao = input("Descrição: ")

    print("\nCategorias:")
    for i, c in enumerate(CATEGORIAS):
        print(f"{i} - {c}")
    indice_categoria = int(input("Escolha categoria: "))

    print("\nPrioridade:")
    for i, p in enumerate(PRIORIDADES):
        print(f"{i} - {p}")
    indice_prioridade = int(input("Escolha prioridade: "))

    try:
        ocorrencia = Ocorrencia(
            nome_aluno,
            descricao,
            CATEGORIAS[indice_categoria],
            PRIORIDADES[indice_prioridade],
            usuario.nome_usuario
        )

        db["ocorrencias"].append(ocorrencia.__dict__)
        salvar_db(db)

        print("Ocorrência registrada")

    except Exception as e:
        print("Erro:", e)


def listar_ocorrencias(db):
    print("\OCORRÊNCIAS")
    for i, o in enumerate(db["ocorrencias"]):
        print(f"{i} - {o['aluno']} | {o['status']} | {o['categoria']}")


def atualizar_ocorrencia(usuario, db):
    listar_ocorrencias(db)

    indice = int(input("Escolha ocorrência: "))
    dados_ocorrencia = db["ocorrencias"][indice]

    ocorrencia = Ocorrencia(
        dados_ocorrencia["aluno"],
        dados_ocorrencia["descricao"],
        dados_ocorrencia["categoria"],
        dados_ocorrencia["prioridade"],
        dados_ocorrencia["criado_por"]
    )
    ocorrencia.status = dados_ocorrencia["status"]
    ocorrencia.historico = dados_ocorrencia["historico"]

    print("\nNovo status:")
    print("1 - EM_ANALISE")
    print("2 - RESOLVIDA")
    print("3 - ENCERRADA")

    escolha = input("Escolha: ")

    mapa_status = {
        "1": "EM_ANALISE",
        "2": "RESOLVIDA",
        "3": "ENCERRADA"
    }

    ocorrencia.atualizar_status(mapa_status[escolha], usuario)

    db["ocorrencias"][indice] = ocorrencia.__dict__
    salvar_db(db)


# LOOP PRINCIPAL
def main():
    db = carregar_db()

    usuario = login()
    if not usuario:
        return

    while True:
        print("\nMENU")

        if usuario.papel == "PROFESSOR":
            print("1 - Criar ocorrência")
            print("2 - Ver ocorrências")

        else:
            print("1 - Ver ocorrências")
            print("2 - Atualizar ocorrência")

        print("0 - Sair")

        opcao = input("Escolha: ")

        if opcao == "0":
            break

        if usuario.papel == "PROFESSOR":
            if opcao == "1":
                criar_ocorrencia(usuario, db)
            elif opcao == "2":
                listar_ocorrencias(db)

        else:
            if opcao == "1":
                listar_ocorrencias(db)
            elif opcao == "2":
                atualizar_ocorrencia(usuario, db)

main()