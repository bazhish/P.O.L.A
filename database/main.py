from usuarios import (
    atualizar_usuario,
    criar_usuario,
    deletar_usuario,
    listar_usuarios,
)


def menu():
    while True:
        print("\n=== SISTEMA DE USUÁRIOS ===")
        print("1 - Criar usuário")
        print("2 - Listar usuários")
        print("3 - Atualizar usuário")
        print("4 - Deletar usuário")
        print("0 - Sair")

        opcao = input("Escolha: ")

        if opcao == "1":
            nome = input("Nome: ")
            idade = int(input("Idade: "))
            criar_usuario(nome, idade)

        elif opcao == "2":
            listar_usuarios()

        elif opcao == "3":
            id = int(input("ID do usuário: "))
            nome = input("Novo nome: ")
            idade = int(input("Nova idade: "))
            atualizar_usuario(id, nome, idade)

        elif opcao == "4":
            id = int(input("ID do usuário: "))
            deletar_usuario(id)

        elif opcao == "0":
            print("Saindo...")
            break

        else:
            print("Opção inválida!")


if __name__ == "__main__":
    menu()
