from db import conectar


def criar_usuario(nome, idade):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.usuarios (nome, idade)
                VALUES (%s, %s)
                RETURNING id
                """,
                (nome, idade),
            )
            usuario_id = cursor.fetchone()[0]

    print(f"Usuário criado com sucesso! ID: {usuario_id}")


def listar_usuarios():
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute("SELECT id, nome, idade FROM public.usuarios ORDER BY id")
            dados = cursor.fetchall()

    print("\n--- USUÁRIOS ---")
    if not dados:
        print("Nenhum usuário cadastrado.")
        return

    for id, nome, idade in dados:
        print(f"ID: {id} | Nome: {nome} | Idade: {idade}")


def atualizar_usuario(id, novo_nome, nova_idade):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.usuarios
                SET nome = %s, idade = %s
                WHERE id = %s
                """,
                (novo_nome, nova_idade, id),
            )
            atualizado = cursor.rowcount

    if atualizado:
        print("Usuário atualizado!")
    else:
        print("Usuário não encontrado.")


def deletar_usuario(id):
    with conectar() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                "DELETE FROM public.usuarios WHERE id = %s",
                (id,),
            )
            deletado = cursor.rowcount

    if deletado:
        print("Usuário deletado!")
    else:
        print("Usuário não encontrado.")
