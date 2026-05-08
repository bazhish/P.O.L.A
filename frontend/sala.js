let salaAtual =
    localStorage.getItem("salaSelecionada");

document.getElementById("tituloSala")
    .innerText = salaAtual;

const salas = {

    "Sala A": [
        "João",
        "Maria",
        "Carlos"
    ],

    "Sala B": [
        "Ana",
        "Pedro",
        "Lucas"
    ],

    "Sala C": [
        "Fernanda",
        "Julia",
        "Mateus"
    ],

    "Sala D": [
        "Rafael",
        "Bianca",
        "Gustavo"
    ]

};

let lista =
    document.getElementById("listaAlunos");

salas[salaAtual].forEach(function(aluno) {

    lista.innerHTML += `
        <hr>

        <h3>${aluno}</h3>

        <button onclick="selecionarAluno('${aluno}')">
            Selecionar
        </button>
    `;

});

function selecionarAluno(nomeAluno) {

    document.getElementById("painelFuncoes")
        .style.display = "block";

    document.getElementById("nomeAluno")
        .innerText = nomeAluno;

}

function voltar() {

    window.location.href = "professor.html";

}

function salvarNota() {

    let nota =
        document.getElementById("notaInput").value;

    let lista =
        document.getElementById("listaNotas");

    lista.innerHTML += `
        <li>
            Nota: ${nota}
        </li>
    `;

    document.getElementById("notaInput").value = "";

}

function salvarFalta() {

    let falta =
        document.getElementById("faltaInput").value;

    let lista =
        document.getElementById("listaFaltas");

    lista.innerHTML += `
        <li>
            Faltas: ${falta}
        </li>
    `;

    document.getElementById("faltaInput").value = "";

}

function salvarOcorrencia() {

    let ocorrencia =
        document.getElementById("ocorrenciaInput").value;

    if (ocorrencia === "") {

        alert("Selecione uma ocorrência");

        return;
    }

    let lista =
        document.getElementById("listaOcorrencias");

    lista.innerHTML += `
        <li>
            ${ocorrencia}
        </li>
    `;

    document.getElementById("ocorrenciaInput").value = "";

}