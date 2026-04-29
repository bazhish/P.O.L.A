# Polar

Sistema web para registro e gestão de ocorrências institucionais, focado
em substituir processos informais por um fluxo estruturado, rastreável e
auditável.

------------------------------------------------------------------------

## Visão Geral

O Polar está sendo desenvolvido como um MVP para resolver um problema real em
ambiente escolar: a falta de controle e histórico de ocorrências.

O sistema permite:

-   registrar ocorrências;
-   acompanhar o status;
-   manter histórico completo;
-   garantir responsabilidade institucional.

------------------------------------------------------------------------

## Funcionalidades (MVP)

-   Cadastro de usuários
-   Registro de ocorrências
-   Controle de status:
    -   Registrada
    -   Em análise
    -   Em atendimento
    -   Resolvida
    -   Encerrada
-   Histórico automático (auditável)
-   Consulta de ocorrências

------------------------------------------------------------------------

## Tecnologias

-   Node.js
-   Express
-   PostgreSQL
-   Prisma ORM
-   React (frontend)

------------------------------------------------------------------------

## Estrutura do Projeto

    polar/
      backend/
      frontend/
      docs/

------------------------------------------------------------------------

## Como Executar

### 1. Clonar repositório

    git clone <url-do-repo>
    cd polar

------------------------------------------------------------------------

### 2. Backend

    cd backend
    npm install
    npx prisma migrate dev
    node src/server.js

Servidor rodando em:

    http://localhost:3000

------------------------------------------------------------------------

### 3. Frontend

    cd frontend
    npm install
    npm run dev

------------------------------------------------------------------------

## Fluxo do Sistema

1.  Usuário registra uma ocorrência\
2.  Ocorrência entra como **Registrada**\
3.  Evolui para **Em análise → Em atendimento → Resolvida → Encerrada**\
4.  Todas as ações são registradas no histórico

------------------------------------------------------------------------

## Regras do Sistema

-   status não pode pular etapas
-   histórico é imutável
-   permissões baseadas em papel do usuário
-   ocorrências encerradas não podem ser alteradas

------------------------------------------------------------------------

## Objetivo do Projeto

Validar um modelo de gestão de ocorrências baseado em:

-   controle de fluxo
-   rastreabilidade
-   responsabilidade institucional

------------------------------------------------------------------------

## Status

Em desenvolvimento (MVP)

------------------------------------------------------------------------

## Licença

Uso acadêmico / educacional
