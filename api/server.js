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
app.patch("/occurrences/:id", (req, res) => {
  const { id } = req.params;
  const { status } = req.body;

  const occ = occurrences.find(o => o.id == id);

  if (!occ) {
    return res.status(404).json({ error: "Não encontrada" });
  }

  occ.status = status;

  res.json(occ);
});

app.listen(3000, () => {
  console.log("API rodando na porta 3000");
});
