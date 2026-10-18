-- Run once in Supabase: SQL Editor > New query > paste > Run.
-- One table holds every task, note, sprint and team setting as a JSON document.
create table if not exists rc_docs (
  collection text not null,
  id         text not null,
  data       jsonb not null,
  version    integer not null default 1,
  updated_at timestamptz not null default now(),
  primary key (collection, id)
);

-- Lock the table: with no policies, only the secret service_role key
-- (kept in Streamlit secrets, never in the code) can read or write it.
alter table rc_docs enable row level security;
