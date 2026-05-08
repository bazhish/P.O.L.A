function abrirSala(nomeSala) {

    localStorage.setItem("salaSelecionada", nomeSala);

    window.location.href = "sala.html";

}