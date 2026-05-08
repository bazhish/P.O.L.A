let salaAtual =
    localStorage.getItem("salaSelecionada");

document.getElementById("tituloSala")
    .innerText = salaAtual;

document.getElementById("nomeSala")
    .innerText = "Sala selecionada: " + salaAtual;

/* DADOS */

let alunos = [
    "João",
    "Maria",
    "Carlos"
];

let ocorrencias = [
    {
        aluno: "João",
        ocorrencia: "Uso de celular"
    },

    {
        aluno: "Maria",
        ocorrencia: "Atraso"
    }
];

/* VOLTAR */

function voltar() {

    window.location.href =
        "diretor.html";

}

/* VISUALIZAR ALUNOS */

function atualizarListaAlunos() {

    let lista =
        document.getElementById("listaAlunos");

    lista.innerHTML = "";

    alunos.forEach(function(aluno) {

        lista.innerHTML += `
            <li>${aluno}</li>
        `;

    });

}

atualizarListaAlunos();

/* EDITAR ALUNO */

function editarAluno() {

    let antigo =
        document.getElementById("editarAlunoAntigo").value;

    let novo =
        document.getElementById("editarAlunoNovo").value;

    let index =
        alunos.indexOf(antigo);

    if (index !== -1) {

        alunos[index] = novo;

    }

    atualizarListaAlunos();

    document.getElementById("editarAlunoAntigo").value = "";

    document.getElementById("editarAlunoNovo").value = "";

}

/* VISUALIZAR OCORRÊNCIAS */

function atualizarListaOcorrencias() {

    let lista =
        document.getElementById("listaOcorrencias");

    lista.innerHTML = "";

    ocorrencias.forEach(function(item, index) {

        lista.innerHTML += `
            <li>
                ${index} - ${item.aluno} - ${item.ocorrencia}
            </li>
        `;

    });

}

atualizarListaOcorrencias();

/* ATUALIZAR OCORRÊNCIA */

function atualizarOcorrencia() {

    let index =
        document.getElementById("ocorrenciaIndex").value;

    let nova =
        document.getElementById("novaOcorrencia").value;

    if (ocorrencias[index]) {

        ocorrencias[index].ocorrencia = nova;

    }

    atualizarListaOcorrencias();

}

/* VISUALIZAR NOTAS */

document.getElementById("listaNotas").innerHTML = `
    <li>João - Nota: 8</li>
    <li>Maria - Nota: 9</li>
    <li>Carlos - Nota: 7</li>
`;

/* VISUALIZAR FALTAS */

document.getElementById("listaFaltas").innerHTML = `
    <li>João - Faltas: 2</li>
    <li>Maria - Faltas: 1</li>
    <li>Carlos - Faltas: 0</li>
`;