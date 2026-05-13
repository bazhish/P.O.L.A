import sys

from services import aluno_service, auth_service, falta_service, nota_service
from services import ocorrencia_service, sala_service
from utils.db import carregar_db, salvar_db
from utils.validators import (
    CATEGORIAS,
    PRIORIDADES,
    ROLES,
    STATUS_VALIDOS,
    entrada_float_segura,
    entrada_int_segura,
    entrada_texto_segura,
    log_error,
    log_info,
    tem_permissao,
)


def escolher_item(itens, titulo, formatador):
    if not itens:
        log_info("Nenhum item disponivel")
        return None, None

    print(f"\n{titulo}")
    for indice, item in enumerate(itens, start=1):
        print(f"{indice} - {formatador(item)}")
    print("0 - Cancelar")

    escolha = entrada_int_segura("Escolha: ", len(itens))
    if escolha == 0:
        return None, None
    return escolha - 1, itens[escolha - 1]


def selecionar_papel(permitir_cancelar=True, permitir_manter=False, papel_atual=None):
    print("\nPapeis:")
    if permitir_manter and papel_atual:
        print(f"0 - Manter {papel_atual}")
    elif permitir_cancelar:
        print("0 - Cancelar")

    for indice, papel in enumerate(ROLES, start=1):
        print(f"{indice} - {papel}")

    limite_min = 0 if permitir_cancelar or permitir_manter else 1
    escolha = entrada_int_segura("Escolha papel: ", len(ROLES), limite_min)
    if escolha == 0:
        return papel_atual if permitir_manter else None
    return ROLES[escolha - 1]


def fazer_login(db):
    print("\nLOGIN")
    papel = selecionar_papel(permitir_cancelar=True)
    if papel is None:
        return None

    nome = entrada_texto_segura("Usuario: ")
    usuario, mensagem = auth_service.autenticar(db, nome, papel)
    if usuario is None:
        log_error(mensagem)
        return None

    log_info(mensagem)
    return usuario


def exibir_ocorrencias(ocorrencias):
    if not ocorrencias:
        log_info("Nenhuma ocorrencia cadastrada")
        return

    print("\nOCORRENCIAS")
    for indice, ocorrencia in enumerate(ocorrencias, start=1):
        print(
            f"{indice} - {ocorrencia['aluno']} | {ocorrencia['status']} | "
            f"{ocorrencia['categoria']} | {ocorrencia['prioridade']}"
        )


def selecionar_ocorrencia(db, usuario):
    sucesso, mensagem, ocorrencias = ocorrencia_service.listar_ocorrencias(db, usuario)
    if not sucesso:
        log_error(mensagem)
        return None, None
    return escolher_item(
        ocorrencias,
        "Selecionar ocorrencia",
        lambda item: (
            f"{item['aluno']} | {item['status']} | "
            f"{item['categoria']} | {item['prioridade']}"
        ),
    )


def selecionar_aluno(db, usuario, alunos=None):
    if alunos is None:
        sucesso, mensagem, alunos = aluno_service.listar_alunos(db, usuario)
        if not sucesso:
            log_error(mensagem)
            return None, None

    return escolher_item(
        alunos,
        "Selecionar aluno",
        lambda item: f"{item['nome']} | Sala: {item['sala']}",
    )


def selecionar_sala(db, usuario):
    sucesso, mensagem, salas = sala_service.listar_salas(db, usuario)
    if not sucesso:
        log_error(mensagem)
        return None, None

    return escolher_item(
        salas,
        "Selecionar sala",
        lambda item: item["nome"],
    )


def selecionar_categoria():
    print("\nCategorias:")
    for indice, categoria in enumerate(CATEGORIAS, start=1):
        print(f"{indice} - {categoria}")
    escolha = entrada_int_segura("Escolha categoria: ", len(CATEGORIAS), 1)
    return CATEGORIAS[escolha - 1]


def selecionar_prioridade():
    print("\nPrioridades:")
    for indice, prioridade in enumerate(PRIORIDADES, start=1):
        print(f"{indice} - {prioridade}")
    escolha = entrada_int_segura("Escolha prioridade: ", len(PRIORIDADES), 1)
    return PRIORIDADES[escolha - 1]


def selecionar_status():
    opcoes = STATUS_VALIDOS[1:]
    print("\nNovo status:")
    print("0 - Cancelar")
    for indice, status in enumerate(opcoes, start=1):
        print(f"{indice} - {status}")
    escolha = entrada_int_segura("Escolha: ", len(opcoes))
    if escolha == 0:
        return None
    return opcoes[escolha - 1]


def menu_ocorrencias(db, usuario):
    while True:
        print("\nMENU OCORRENCIAS")
        print("1 - Listar ocorrencias")
        print("2 - Criar ocorrencia")
        print("3 - Atualizar status")
        print("4 - Ver historico")
        print("0 - Voltar")

        opcao = entrada_int_segura("Escolha: ", 4)

        if opcao == 0:
            return

        if opcao == 1:
            sucesso, mensagem, ocorrencias = ocorrencia_service.listar_ocorrencias(db, usuario)
            if sucesso:
                exibir_ocorrencias(ocorrencias)
            else:
                log_error(mensagem)

        elif opcao == 2:
            _, aluno = selecionar_aluno(db, usuario)
            if aluno is None:
                continue

            descricao = entrada_texto_segura("Descricao: ")
            categoria = selecionar_categoria()
            prioridade = selecionar_prioridade()
            sucesso, mensagem = ocorrencia_service.criar_ocorrencia(
                db,
                usuario,
                aluno["nome"],
                descricao,
                categoria,
                prioridade,
            )
            if sucesso:
                salvar_db(db)
                log_info(mensagem)
            else:
                log_error(mensagem)

        elif opcao == 3:
            indice, _ = selecionar_ocorrencia(db, usuario)
            if indice is None:
                continue
            novo_status = selecionar_status()
            if novo_status is None:
                continue

            sucesso, mensagem = ocorrencia_service.atualizar_status_ocorrencia(
                db,
                usuario,
                indice,
                novo_status,
            )
            if sucesso:
                salvar_db(db)
                log_info(mensagem)
            else:
                log_error(mensagem)

        elif opcao == 4:
            indice, _ = selecionar_ocorrencia(db, usuario)
            if indice is None:
                continue
            sucesso, mensagem, historico = ocorrencia_service.obter_historico(
                db,
                usuario,
                indice,
            )
            if not sucesso:
                log_error(mensagem)
                continue

            print("\nHISTORICO")
            for item in historico:
                print(f"- {item.get('acao')} | {item.get('status')}")


def exibir_aluno(db, usuario, nome):
    sucesso, mensagem, dados = aluno_service.visualizar_aluno(db, usuario, nome)
    if not sucesso:
        log_error(mensagem)
        return

    aluno = dados["aluno"]
    print("\nALUNO")
    print(f"Nome: {aluno['nome']}")
    print(f"Sala: {aluno['sala']}")

    print("\nOcorrencias:")
    if dados["ocorrencias"]:
        for ocorrencia in dados["ocorrencias"]:
            print(f"- {ocorrencia['status']} | {ocorrencia['categoria']} | {ocorrencia['prioridade']}")
    else:
        print("- Nenhuma")

    print("\nNotas:")
    if dados["notas"]:
        for nota in dados["notas"]:
            print(f"- {nota['disciplina']}: {nota['valor']}")
    else:
        print("- Nenhuma")

    print("\nFaltas:")
    if dados["faltas"]:
        for falta in dados["faltas"]:
            print(f"- {falta['data']}")
    else:
        print("- Nenhuma")


def menu_sala(db, usuario, sala):
    while True:
        print(f"\nSALA {sala['nome']}")
        print("1 - Listar alunos")
        print("2 - Selecionar aluno")
        print("0 - Voltar")

        opcao = entrada_int_segura("Escolha: ", 2)
        if opcao == 0:
            return

        sucesso, mensagem, alunos = aluno_service.listar_alunos_por_sala(
            db,
            usuario,
            sala["nome"],
        )
        if not sucesso:
            log_error(mensagem)
            continue

        if opcao == 1:
            if not alunos:
                log_info("Nenhum aluno nesta sala")
                continue
            for aluno in alunos:
                print(f"- {aluno['nome']}")

        elif opcao == 2:
            _, aluno = selecionar_aluno(db, usuario, alunos)
            if aluno is not None:
                exibir_aluno(db, usuario, aluno["nome"])


def menu_salas(db, usuario):
    while True:
        print("\nMENU SALAS")
        print("1 - Listar salas")
        print("2 - Criar sala")
        print("3 - Editar sala")
        print("4 - Selecionar sala")
        print("0 - Voltar")

        opcao = entrada_int_segura("Escolha: ", 4)
        if opcao == 0:
            return

        if opcao == 1:
            sucesso, mensagem, salas = sala_service.listar_salas(db, usuario)
            if sucesso:
                if not salas:
                    log_info("Nenhuma sala cadastrada")
                for sala in salas:
                    print(f"- {sala['nome']}")
            else:
                log_error(mensagem)

        elif opcao == 2:
            nome = entrada_texto_segura("Nome da sala: ")
            sucesso, mensagem = sala_service.criar_sala(db, usuario, nome)
            if sucesso:
                salvar_db(db)
                log_info(mensagem)
            else:
                log_error(mensagem)

        elif opcao == 3:
            indice, sala = selecionar_sala(db, usuario)
            if sala is None:
                continue
            novo_nome = entrada_texto_segura("Novo nome da sala: ")
            sucesso, mensagem = sala_service.editar_sala(db, usuario, indice, novo_nome)
            if sucesso:
                salvar_db(db)
                log_info(mensagem)
            else:
                log_error(mensagem)

        elif opcao == 4:
            _, sala = selecionar_sala(db, usuario)
            if sala is not None:
                menu_sala(db, usuario, sala)


def menu_alunos(db, usuario):
    while True:
        print("\nMENU ALUNOS")
        print("1 - Listar alunos")
        print("2 - Adicionar aluno")
        print("3 - Editar aluno")
        print("4 - Ver aluno")
        print("0 - Voltar")

        opcao = entrada_int_segura("Escolha: ", 4)
        if opcao == 0:
            return

        if opcao == 1:
            sucesso, mensagem, alunos = aluno_service.listar_alunos(db, usuario)
            if sucesso:
                if not alunos:
                    log_info("Nenhum aluno cadastrado")
                for aluno in alunos:
                    print(f"- {aluno['nome']} | Sala: {aluno['sala']}")
            else:
                log_error(mensagem)

        elif opcao == 2:
            _, sala = selecionar_sala(db, usuario)
            if sala is None:
                continue
            nome = entrada_texto_segura("Nome do aluno: ")
            sucesso, mensagem = aluno_service.criar_aluno(db, usuario, nome, sala["nome"])
            if sucesso:
                salvar_db(db)
                log_info(mensagem)
            else:
                log_error(mensagem)

        elif opcao == 3:
            indice, aluno = selecionar_aluno(db, usuario)
            if aluno is None:
                continue
            novo_nome = entrada_texto_segura(
                f"Novo nome [{aluno['nome']}]: ",
                obrigatorio=False,
            ) or aluno["nome"]

            trocar_sala = entrada_int_segura("Trocar sala? 1 - Sim | 0 - Nao: ", 1)
            nova_sala = aluno["sala"]
            if trocar_sala == 1:
                _, sala = selecionar_sala(db, usuario)
                if sala is None:
                    continue
                nova_sala = sala["nome"]

            sucesso, mensagem = aluno_service.editar_aluno(
                db,
                usuario,
                indice,
                novo_nome,
                nova_sala,
            )
            if sucesso:
                salvar_db(db)
                log_info(mensagem)
            else:
                log_error(mensagem)

        elif opcao == 4:
            _, aluno = selecionar_aluno(db, usuario)
            if aluno is not None:
                exibir_aluno(db, usuario, aluno["nome"])


def menu_notas(db, usuario):
    while True:
        print("\nMENU NOTAS")
        print("1 - Adicionar nota")
        print("2 - Listar notas")
        print("3 - Listar notas por aluno")
        print("0 - Voltar")

        opcao = entrada_int_segura("Escolha: ", 3)
        if opcao == 0:
            return

        if opcao == 1:
            _, aluno = selecionar_aluno(db, usuario)
            if aluno is None:
                continue
            disciplina = entrada_texto_segura("Disciplina: ")
            valor = entrada_float_segura("Valor da nota (0-10): ")
            sucesso, mensagem = nota_service.adicionar_nota(
                db,
                usuario,
                aluno["nome"],
                disciplina,
                valor,
            )
            if sucesso:
                salvar_db(db)
                log_info(mensagem)
            else:
                log_error(mensagem)

        elif opcao in (2, 3):
            aluno_nome = None
            if opcao == 3:
                _, aluno = selecionar_aluno(db, usuario)
                if aluno is None:
                    continue
                aluno_nome = aluno["nome"]

            sucesso, mensagem, notas = nota_service.listar_notas(db, usuario, aluno_nome)
            if not sucesso:
                log_error(mensagem)
                continue
            if not notas:
                log_info("Nenhuma nota cadastrada")
            for nota in notas:
                print(f"- {nota['aluno']} | {nota['disciplina']}: {nota['valor']}")


def menu_faltas(db, usuario):
    while True:
        print("\nMENU FALTAS")
        print("1 - Adicionar falta")
        print("2 - Listar faltas")
        print("3 - Listar faltas por aluno")
        print("0 - Voltar")

        opcao = entrada_int_segura("Escolha: ", 3)
        if opcao == 0:
            return

        if opcao == 1:
            _, aluno = selecionar_aluno(db, usuario)
            if aluno is None:
                continue
            data = entrada_texto_segura("Data (AAAA-MM-DD): ")
            sucesso, mensagem = falta_service.adicionar_falta(db, usuario, aluno["nome"], data)
            if sucesso:
                salvar_db(db)
                log_info(mensagem)
            else:
                log_error(mensagem)

        elif opcao in (2, 3):
            aluno_nome = None
            if opcao == 3:
                _, aluno = selecionar_aluno(db, usuario)
                if aluno is None:
                    continue
                aluno_nome = aluno["nome"]

            sucesso, mensagem, faltas = falta_service.listar_faltas(db, usuario, aluno_nome)
            if not sucesso:
                log_error(mensagem)
                continue
            if not faltas:
                log_info("Nenhuma falta cadastrada")
            for falta in faltas:
                print(f"- {falta['aluno']} | {falta['data']}")


def menu_usuarios(db, usuario):
    while True:
        print("\nMENU USUARIOS")
        print("1 - Listar usuarios")
        print("2 - Criar usuario")
        print("3 - Editar usuario")
        print("0 - Voltar")

        opcao = entrada_int_segura("Escolha: ", 3)
        if opcao == 0:
            return

        if opcao == 1:
            sucesso, mensagem, usuarios = auth_service.listar_usuarios(db, usuario)
            if sucesso:
                for item in usuarios:
                    print(f"- {item['nome']} | {item['papel']}")
            else:
                log_error(mensagem)

        elif opcao == 2:
            nome = entrada_texto_segura("Nome do usuario: ")
            papel = selecionar_papel(permitir_cancelar=True)
            if papel is None:
                continue
            sucesso, mensagem = auth_service.criar_usuario(db, usuario, nome, papel)
            if sucesso:
                salvar_db(db)
                log_info(mensagem)
            else:
                log_error(mensagem)

        elif opcao == 3:
            sucesso, mensagem, usuarios = auth_service.listar_usuarios(db, usuario)
            if not sucesso:
                log_error(mensagem)
                continue
            indice, item = escolher_item(
                usuarios,
                "Selecionar usuario",
                lambda usuario_db: f"{usuario_db['nome']} | {usuario_db['papel']}",
            )
            if item is None:
                continue

            novo_nome = entrada_texto_segura(
                f"Novo nome [{item['nome']}]: ",
                obrigatorio=False,
            ) or item["nome"]
            novo_papel = selecionar_papel(
                permitir_cancelar=True,
                permitir_manter=True,
                papel_atual=item["papel"],
            )
            if novo_papel is None:
                continue

            sucesso, mensagem = auth_service.editar_usuario(
                db,
                usuario,
                indice,
                novo_nome,
                novo_papel,
            )
            if sucesso:
                salvar_db(db)
                log_info(mensagem)
            else:
                log_error(mensagem)


def exibir_menu_principal(usuario):
    print("\nMAIN MENU")
    print("1 - Ocorrencias")
    print("2 - Salas")
    print("3 - Alunos")
    print("4 - Notas")
    print("5 - Faltas")
    if tem_permissao(usuario, "usuario_visualizar"):
        print("6 - Usuarios")
    print("0 - Sair")


def executar_cli():
    db = carregar_db()
    usuario = fazer_login(db)
    if usuario is None:
        log_error("Acesso encerrado")
        return

    while True:
        exibir_menu_principal(usuario)
        limite = 6 if tem_permissao(usuario, "usuario_visualizar") else 5
        opcao = entrada_int_segura("Escolha: ", limite)

        if opcao == 0:
            log_info("Sistema encerrado")
            return
        if opcao == 1:
            menu_ocorrencias(db, usuario)
        elif opcao == 2:
            menu_salas(db, usuario)
        elif opcao == 3:
            menu_alunos(db, usuario)
        elif opcao == 4:
            menu_notas(db, usuario)
        elif opcao == 5:
            menu_faltas(db, usuario)
        elif opcao == 6 and tem_permissao(usuario, "usuario_visualizar"):
            menu_usuarios(db, usuario)


def main(argv=None):
    argumentos = sys.argv[1:] if argv is None else argv

    if "--stress" in argumentos:
        ocorrencia_service.executar_teste_estresse()
        return

    try:
        executar_cli()
    except KeyboardInterrupt:
        print()
        log_info("Sistema encerrado pelo usuario")


if __name__ == "__main__":
    main()
