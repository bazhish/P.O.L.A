const express = require("express");
const app = express();
const { spawn } = require("child_process")

app.use(express.json());

let occurrences = [];

// criar ocorrência
app.post("/occurrences", (req, res) => {
  const { student, description } = req.body;

  const python = spawn("python", ["../backend/services/ocorrencia_service.py", student, description]);

  let resultado = "";

  python.stdout.on("data", (data) => {
    resultado += data.toString();
  });

  python.on("close", () => {
    const newOccurence = {
      id: occurrences.length + 1,
      stundent,
      description,
      status: "REGISTRADA", 
      processamento_python: resultado.trim()
    };

    occurrences.push(newOccurence);

    res.json(newOccurence);
  });
});

// listar ocorrências
app.get("/occurrences", (req, res) => {
  res.json(occurrences);
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
