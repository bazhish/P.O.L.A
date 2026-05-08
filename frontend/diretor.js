function abrirSala(nomeSala) {

    localStorage.setItem("salaSelecionada", nomeSala);

    window.location.href =
        "diretor_sala.html";

}