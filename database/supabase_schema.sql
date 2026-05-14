create extension if not exists pgcrypto;

create type papel_usuario as enum ('PROFESSOR', 'COORDENADOR', 'DIRETOR', 'ADM');
create type status_ocorrencia as enum ('REGISTRADA', 'EM_ANALISE', 'RESOLVIDA', 'ENCERRADA');
create type prioridade_ocorrencia as enum ('BAIXA', 'MEDIA', 'ALTA');

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create table if not exists profiles (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid unique references auth.users(id) on delete set null,
  nome text not null,
  username text unique,
  papel papel_usuario not null,
  role papel_usuario generated always as (papel) stored,
  senha_hash text,
  password_hash text,
  precisa_trocar_senha boolean not null default false,
  permissoes jsonb not null default '[]'::jsonb,
  login_falhas integer not null default 0,
  bloqueado_ate timestamptz,
  ultimo_login timestamptz,
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint profiles_nome_not_blank check (length(trim(nome)) > 0)
);

create table if not exists turmas (
  id uuid primary key default gen_random_uuid(),
  nome text not null unique,
  ano_letivo integer,
  turno text,
  ativa boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint turmas_nome_not_blank check (length(trim(nome)) > 0)
);

create table if not exists alunos (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  matricula text unique,
  turma_id uuid references turmas(id) on delete set null,
  sala text,
  responsavel_nome text,
  ativo boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint alunos_nome_not_blank check (length(trim(nome)) > 0)
);

create table if not exists categorias_ocorrencia (
  id uuid primary key default gen_random_uuid(),
  nome text not null unique,
  ativa boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists ocorrencias (
  id uuid primary key default gen_random_uuid(),
  aluno_id uuid references alunos(id) on delete restrict,
  aluno_nome text,
  criado_por_id uuid references profiles(id) on delete set null,
  criado_por_nome text,
  descricao text not null,
  categoria text not null,
  prioridade prioridade_ocorrencia not null,
  status status_ocorrencia not null default 'REGISTRADA',
  local_ocorrencia text,
  testemunhas text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint ocorrencias_descricao_not_blank check (length(trim(descricao)) > 0)
);

create table if not exists ocorrencia_historico (
  id uuid primary key default gen_random_uuid(),
  ocorrencia_id uuid not null references ocorrencias(id) on delete cascade,
  acao text not null,
  status status_ocorrencia not null,
  usuario text,
  usuario_id uuid references profiles(id) on delete set null,
  data_hora timestamptz not null default now(),
  created_at timestamptz not null default now(),
  constraint ocorrencia_historico_acao_not_blank check (length(trim(acao)) > 0)
);

create table if not exists notas (
  id uuid primary key default gen_random_uuid(),
  aluno_id uuid references alunos(id) on delete cascade,
  aluno_nome text,
  disciplina text not null,
  valor numeric(5,2) not null,
  bimestre integer check (bimestre between 1 and 4),
  peso numeric(5,2),
  registrado_por_id uuid references profiles(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint notas_valor_range check (valor >= 0 and valor <= 10)
);

create table if not exists faltas (
  id uuid primary key default gen_random_uuid(),
  aluno_id uuid references alunos(id) on delete cascade,
  aluno_nome text,
  disciplina text,
  bimestre integer check (bimestre between 1 and 4),
  data_falta date not null,
  quantidade integer not null default 1,
  registrado_por_id uuid references profiles(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint faltas_quantidade_positiva check (quantidade > 0)
);

create table if not exists user_permissions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references profiles(id) on delete cascade,
  permissao text not null,
  created_at timestamptz not null default now(),
  unique(user_id, permissao)
);

create table if not exists ocorrencia_testemunhas (
  id uuid primary key default gen_random_uuid(),
  ocorrencia_id uuid not null references ocorrencias(id) on delete cascade,
  nome text not null,
  created_at timestamptz not null default now()
);

create table if not exists ocorrencia_anexos (
  id uuid primary key default gen_random_uuid(),
  ocorrencia_id uuid not null references ocorrencias(id) on delete cascade,
  nome_arquivo text not null,
  url text not null,
  enviado_por_id uuid references profiles(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete set null,
  entidade text not null,
  entidade_id uuid,
  acao text not null,
  payload jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) on delete cascade,
  titulo text not null,
  mensagem text not null,
  lida boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists idx_profiles_papel on profiles(papel);
create index if not exists idx_alunos_turma_id on alunos(turma_id);
create index if not exists idx_ocorrencias_aluno_id on ocorrencias(aluno_id);
create index if not exists idx_ocorrencias_status on ocorrencias(status);
create index if not exists idx_ocorrencias_prioridade on ocorrencias(prioridade);
create index if not exists idx_ocorrencia_historico_ocorrencia on ocorrencia_historico(ocorrencia_id);
create index if not exists idx_notas_aluno_id on notas(aluno_id);
create index if not exists idx_faltas_aluno_id on faltas(aluno_id);

create trigger profiles_set_updated_at before update on profiles for each row execute function set_updated_at();
create trigger turmas_set_updated_at before update on turmas for each row execute function set_updated_at();
create trigger alunos_set_updated_at before update on alunos for each row execute function set_updated_at();
create trigger ocorrencias_set_updated_at before update on ocorrencias for each row execute function set_updated_at();
create trigger notas_set_updated_at before update on notas for each row execute function set_updated_at();
create trigger faltas_set_updated_at before update on faltas for each row execute function set_updated_at();

alter table profiles enable row level security;
alter table turmas enable row level security;
alter table alunos enable row level security;
alter table categorias_ocorrencia enable row level security;
alter table ocorrencias enable row level security;
alter table ocorrencia_historico enable row level security;
alter table notas enable row level security;
alter table faltas enable row level security;
alter table user_permissions enable row level security;
alter table ocorrencia_testemunhas enable row level security;
alter table ocorrencia_anexos enable row level security;
alter table audit_logs enable row level security;
alter table notifications enable row level security;

-- MVP: a API backend deve acessar com SUPABASE_SERVICE_ROLE_KEY.
-- As policies finas para acesso direto do frontend devem ser criadas somente quando o frontend não depender mais da API própria.
