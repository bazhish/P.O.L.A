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



//nota




app.post("/grades", async (req, res) => {
  const { student, subject, value } = req.body;

  const resultado = await runPython(
    "../backend/services/nota_service.py",
    [
      "criar",
      JSON.stringify({
        aluno: student,
        disciplina: subject,
        valor: value
      })
    ]
  );

  res.json(resultado);
});


app.get("/grades", async (req, res) => {
  const resultado = await runPython(
    "../backend/services/nota_service.py",
    ["listar"]
  );

  res.json(resultado);
});



app.post("/grades/student", async (req, res) => {
  const { student } = req.body;

  const resultado = await runPython(
    "../backend/services/nota_service.py",
    [
      "listar",
      JSON.stringify({
        aluno: student
      })
    ]
  );

  res.json(resultado);
});



//faltas



app.post("/absences", async (req, res) => {
  const { student, date } = req.body;

  const resultado = await runPython(
    "../backend/services/falta_service.py",
    [
      "criar",
      JSON.stringify({
        aluno: student,
        data: date
      })
    ]
  );

  res.json(resultado);
});


app.get("/absences", async (req, res) => {
  const resultado = await runPython(
    "../backend/services/falta_service.py",
    ["listar"]
  );

  res.json(resultado);
});


app.post("/absences/student", async (req, res) => {
  const { student } = req.body;

  const resultado = await runPython(
    "../backend/services/falta_service.py",
    [
      "listar",
      JSON.stringify({
        aluno: student
      })
    ]
  );

  res.json(resultado);
});


//auth



app.post("/auth/login", async (req, res) => {
  const { name, role } = req.body;

  const resultado = await runPython(
    "../backend/services/auth_service.py",
    [
      "login",
      JSON.stringify({
        nome: name,
        papel: role
      })
    ]
  );

  res.json(resultado);
});


app.post("/users", async (req, res) => {
  const { name, role } = req.body;

  const resultado = await runPython(
    "../backend/services/auth_service.py",
    [
      "criar",
      JSON.stringify({
        nome: name,
        papel: role
      })
    ]
  );

  res.json(resultado);
});


app.patch("/users/:id", async (req, res) => {
  const { id } = req.params;
  const { name, role } = req.body;

  const resultado = await runPython(
    "../backend/services/auth_service.py",
    [
      "editar",
      JSON.stringify({
        indice: Number(id),
        nome: name,
        papel: role
      })
    ]
  );

  res.json(resultado);
});


