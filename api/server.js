const express = require("express");
const app = express();
const runPython = require("./utils/pythonRunner");

app.use(express.json());

let occurrences = [];

// criar ocorrência
app.post("/occurrences", async (req, res) => {
  const { student, description } = req.body;

  try {
    const resultado = await runPython(
      "../backend/services/ocorrencia_service.py",
      [
        "criar",
        JSON.stringify({
          aluno: student,
          descricao: description,
          categoria: "DISCIPLINA",
          prioridade: "ALTA"
        })
      ]
    );

    res.json(resultado);

  } catch (err) {
    res.status(500).json({ erro: err });
  }
});

// listar ocorrências
app.get("/occurrences", async (req, res) => {
  try {
    const resultado = await runPython(
      "../backend/services/ocorrencia_service.py",
      ["listar"]
    );

    res.json(resultado);

  } catch (err) {
    res.status(500).json({ erro: err });
  }
});

// atualizar status
app.patch("/occurrences/:id", async (req, res) => {
  const { id } = req.params;
  const { status } = req.body;

  try {
    const resultado = await runPython(
      "../backend/services/ocorrencia_service.py",
      [
        "status",
        JSON.stringify({
          indice: Number(id),
          status
        })
      ]
    );

    res.json(resultado);

  } catch (err) {
    res.status(500).json({ erro: err });
  }
});

app.listen(3000, () => {
  console.log("API rodando na porta 3000");
});



//aluno



app.post("/students", async (req, res) => {
  const { name, room } = req.body;

  const resultado = await runPython(
    "../backend/services/aluno_service.py",
    [
      "criar",
      JSON.stringify({
        nome: name,
        sala: room
      })
    ]
  );

  res.json(resultado);
});

app.get("/students", async (req, res) => {
  const resultado = await runPython(
    "../backend/services/aluno_service.py",
    ["listar"]
  );

  res.json(resultado);
});

app.patch("/students/:id", async (req, res) => {
  const { id } = req.params;
  const { name, room } = req.body;

  const resultado = await runPython(
    "../backend/services/aluno_service.py",
    [
      "editar",
      JSON.stringify({
        indice: Number(id),
        nome: name,
        sala: room
      })
    ]
  );

  res.json(resultado);
});

app.post("/students/view", async (req, res) => {
  const { name } = req.body;

  const resultado = await runPython(
    "../backend/services/aluno_service.py",
    [
      "visualizar",
      JSON.stringify({
        nome: name
      })
    ]
  );

  res.json(resultado);
});



//sala



app.post("/rooms", async (req, res) => {
  const { name } = req.body;

  const resultado = await runPython(
    "../backend/services/sala_service.py",
    [
      "criar",
      JSON.stringify({
        nome: name
      })
    ]
  );

  res.json(resultado);
});


app.get("/rooms", async (req, res) => {
  const resultado = await runPython(
    "../backend/services/sala_service.py",
    ["listar"]
  );

  res.json(resultado);
});


app.patch("/rooms/:id", async (req, res) => {
  const { id } = req.params;
  const { name } = req.body;

  const resultado = await runPython(
    "../backend/services/sala_service.py",
    [
      "editar",
      JSON.stringify({
        indice: Number(id),
        nome: name
      })
    ]
  );

  res.json(resultado);
});