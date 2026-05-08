function abrirSala(nomeSala) {

    localStorage.setItem("salaSelecionada", nomeSala);

    window.location.href =
        "coordenador_sala.html";

}