const express = require("express");
const router = express.Router();
const controller = require("../controllers/ocorrencia.controller");

router.post("/", controller.criarOcorrencia);

module.exports = router;