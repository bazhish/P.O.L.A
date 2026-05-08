let salaAtual =
    localStorage.getItem("salaSelecionada");

document.getElementById("tituloSala")
    .innerText = salaAtual;

document.getElementById("nomeSala")
    .innerText = "Sala selecionada: " + salaAtual;

let alunos = [];

let ocorrencias = [];

/* VOLTAR */

function voltar() {

    window.location.href =
        "coordenador.html";

}

/* ALUNOS */

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

function criarAluno() {

    let nome =
        document.getElementById("criarAlunoInput").value;

    alunos.push(nome);

    atualizarListaAlunos();

    document.getElementById("criarAlunoInput").value = "";

}

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

}

/* NOTAS */

function salvarNota() {

    let aluno =
        document.getElementById("notaAluno").value;

    let nota =
        document.getElementById("notaInput").value;

    document.getElementById("listaNotas").innerHTML += `
        <li>
            ${aluno} - Nota: ${nota}
        </li>
    `;

    document.getElementById("notaAluno").value = "";

    document.getElementById("notaInput").value = "";

}

/* FALTAS */

function salvarFalta() {

    let aluno =
        document.getElementById("faltaAluno").value;

    let falta =
        document.getElementById("faltaInput").value;

    document.getElementById("listaFaltas").innerHTML += `
        <li>
            ${aluno} - Faltas: ${falta}
        </li>
    `;

    document.getElementById("faltaAluno").value = "";

    document.getElementById("faltaInput").value = "";

}

/* OCORRÊNCIAS */

function salvarOcorrencia() {

    let aluno =
        document.getElementById("ocorrenciaAluno").value;

    let ocorrencia =
        document.getElementById("ocorrenciaInput").value;

    if (ocorrencia === "") {

        alert("Selecione uma ocorrência");

        return;

    }

    ocorrencias.push({
        aluno,
        ocorrencia
    });

    atualizarListaOcorrencias();

    document.getElementById("ocorrenciaAluno").value = "";

    document.getElementById("ocorrenciaInput").value = "";

}

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