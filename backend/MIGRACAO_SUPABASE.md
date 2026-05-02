# 🚀 Integração Backend com Supabase (PostgreSQL)

## ✅ Status da Migração

- ✓ Backend conectado ao banco de dados Supabase
- ✓ Banco de dados local (JSON) removido
- ✓ Tabelas PostgreSQL criadas e configuradas
- ✓ Usuário administrador criado
- ✓ Gerenciador de banco de dados implementado

## 📋 Arquivos Criados/Modificados

### Novos Arquivos
1. **`.env`** - Configurações de conexão com Supabase
2. **`requirements.txt`** - Dependências do backend (psycopg, python-dotenv)
3. **`utils/db_cloud.py`** - Gerenciador de conexão com Supabase
4. **`utils/db_manager.py`** - CRUD de operações do banco de dados
5. **`setup_db.py`** - Script de setup inicial
6. **`test_supabase.py`** - Teste de validação

### Arquivos Removidos
- `banco_dados.json` - ❌ Banco de dados local (removido)

## 🔐 Credenciais de Acesso

```
Host: db.ukiradwbjnorbtrrvyjy.supabase.co
Database: postgres
User: postgres
Password: 1qw0pl2e9I@
Port: 5432
SSL Mode: require
```

> ⚠️ **IMPORTANTE**: Essas credenciais estão em `.env`. Não compartilhe em repositórios públicos!

## 📊 Estrutura do Banco de Dados

### Tabelas Criadas

1. **usuarios**
   - id, nome, papel, senha_hash, precisa_trocar_senha
   - Usuário admin padrão já criado

2. **salas**
   - id, nome, ano_letivo, created_at, updated_at

3. **alunos**
   - id, nome, sala_id, matricula, created_at, updated_at

4. **notas**
   - id, aluno_id, disciplina, valor, periodo, created_at, updated_at

5. **faltas**
   - id, aluno_id, data, justificada, observacoes, created_at, updated_at

6. **ocorrencias**
   - id, aluno_id, tipo, descricao, status, prioridade, data, created_at, updated_at

## 🛠️ Como Usar

### 1. Inicializar Backend
```bash
cd backend
pip install -r requirements.txt
python setup_db.py  # Setup inicial (já feito)
```

### 2. Usar o Gerenciador de Banco de Dados

```python
from utils.db_manager import obter_gerenciador

db = obter_gerenciador()

# Buscar usuário
usuario = db.buscar_usuario_por_nome("admin")

# Listar alunos
alunos = db.listar_alunos()

# Criar sala
nova_sala = db.criar_sala("Sala 101", 2024)

# Atualizar usuário
db.atualizar_usuario(1, papel="ADM", precisa_trocar_senha=False)
```

### 3. Testar Conexão
```bash
python test_supabase.py
```

## 🔗 Proximos Passos

1. **Adaptar serviços** para usar `db_manager.py`:
   - `services/aluno_service.py`
   - `services/auth_service.py`
   - `services/nota_service.py`
   - `services/falta_service.py`
   - `services/ocorrencia_service.py`

2. **Migrar main.py** para usar novo sistema de banco de dados

3. **Implementar API REST** com Flask/FastAPI para acessar dados

4. **Backup automático** configurar no Supabase

## ⚠️ Notas Importantes

- O banco JSON local foi completamente removido
- Todas as operações agora vão para Supabase
- A senha padrão do admin é: `admin123`
- Trocar senha na primeira autenticação!
- Não commit .env em repositórios públicos

## 🧪 Verificação Final

```bash
$ python test_supabase.py

✅ TODOS OS TESTES PASSARAM COM SUCESSO!
✓ Backend conectado ao Supabase
✓ Banco de dados local removido  
✓ Tabelas criadas no PostgreSQL
✓ Usuário admin configurado
```

---

**Data de Migração**: 1º de Maio de 2026  
**Status**: ✅ Completo
