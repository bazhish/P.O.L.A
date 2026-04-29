const express = require("express");
const app = express();

app.use(express.json());

let occurrences = [];

// criar ocorrência
app.post("/occurrences", (req, res) => {
  const { student, description } = req.body;

  const newOccurrence = {
    id: occurrences.length + 1,
    student,
    description,
    status: "REGISTRADA"
  };

  occurrences.push(newOccurrence);

  res.json(newOccurrence);
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