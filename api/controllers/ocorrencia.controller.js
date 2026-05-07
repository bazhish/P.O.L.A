const runPython = require("../utils/pythonRunner");

exports.criarOcorrencia = async (req, res) => {
  const { student, description } = req.body;

  try {
    const resultado = await runPython(
      "../backend/services/ocorrencia_service.py",
      [student, description]
    );

    res.json({
      message: "Ocorrência criada",
      python: resultado
    });

  } catch (err) {
    res.status(500).json({ error: err });
  }
};