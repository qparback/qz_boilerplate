-- Initial schema. Runs on first container start (when pgdata volume is empty).
-- After first start, schema changes go through Alembic migrations.
--
-- Conventions:
--   - UUID primary keys (pgcrypto's gen_random_uuid is built-in to PG 13+)
--   - TEXT instead of VARCHAR (no length constraints in PG anyway)
--   - TIMESTAMPTZ everywhere (UTC under the hood)
--   - Indexes on foreign keys and frequently-filtered columns

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── AI Prompts ──────────────────────────────────────────────────────────────
-- All prompts live here. Code never hardcodes prompt text — it loads by `key`.
CREATE TABLE IF NOT EXISTS prompts (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    key         TEXT        UNIQUE NOT NULL,
    name        TEXT        NOT NULL,
    description TEXT,
    content     TEXT        NOT NULL,
    model       TEXT        NOT NULL DEFAULT 'claude-sonnet-4-6',
    temperature REAL        NOT NULL DEFAULT 0.7,
    max_tokens  INTEGER     NOT NULL DEFAULT 2000,
    active      BOOLEAN     NOT NULL DEFAULT TRUE,
    version     INTEGER     NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Application logs ────────────────────────────────────────────────────────
-- Important operations and errors. Optional — controlled by LOG_TO_DB env var.
CREATE TABLE IF NOT EXISTS app_logs (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    level       TEXT        NOT NULL CHECK (level IN ('DEBUG','INFO','WARNING','ERROR','CRITICAL')),
    service     TEXT        NOT NULL,
    operation   TEXT        NOT NULL,
    message     TEXT        NOT NULL,
    details     JSONB,
    request_id  TEXT,
    duration_ms INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_app_logs_level      ON app_logs(level);
CREATE INDEX IF NOT EXISTS idx_app_logs_service    ON app_logs(service);
CREATE INDEX IF NOT EXISTS idx_app_logs_created_at ON app_logs(created_at DESC);

-- ─── Audit log ───────────────────────────────────────────────────────────────
-- Every data mutation. Append-only, no updates.
CREATE TABLE IF NOT EXISTS audit_log (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    operation   TEXT        NOT NULL CHECK (operation IN ('CREATE','UPDATE','DELETE')),
    resource    TEXT        NOT NULL,
    resource_id TEXT,
    actor_key   TEXT,
    ip_address  TEXT,
    request_id  TEXT,
    old_values  JSONB,
    new_values  JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource   ON audit_log(resource, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);

-- ─── Email log ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS email_log (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email_type          TEXT        NOT NULL,
    recipient_email     TEXT        NOT NULL,
    subject             TEXT,
    postmark_message_id TEXT,
    status              TEXT        NOT NULL DEFAULT 'sent' CHECK (status IN ('sent','failed','bounced')),
    error_message       TEXT,
    metadata            JSONB,
    sent_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_email_log_recipient ON email_log(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_log_sent_at   ON email_log(sent_at DESC);

-- ─── Memory files ────────────────────────────────────────────────────────────
-- Per-context markdown files for Claude memory. Composite unique on (context, file).
CREATE TABLE IF NOT EXISTS memory_files (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    context_key TEXT        NOT NULL,
    file_key    TEXT        NOT NULL,
    content     TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (context_key, file_key)
);
CREATE INDEX IF NOT EXISTS idx_memory_files_context ON memory_files(context_key);

-- ─── Hello messages ──────────────────────────────────────────────────────────
-- Smoke-test table. Demonstrates the model/router/schema pattern and gives
-- /v1/hello/db something to read. Safe to drop when you have real resources.
CREATE TABLE IF NOT EXISTS hello_messages (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    message    TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Roadmap ─────────────────────────────────────────────────────────────────
-- Shown in the admin UI. Free-form, mostly informational.
CREATE TABLE IF NOT EXISTS roadmap_items (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    phase       TEXT        NOT NULL,
    title       TEXT        NOT NULL,
    description TEXT,
    status      TEXT        NOT NULL DEFAULT 'planned' CHECK (status IN ('planned','in_progress','done','cancelled')),
    priority    INTEGER     NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Seed data ───────────────────────────────────────────────────────────────
INSERT INTO prompts (key, name, description, content) VALUES
    (
        'example_system',
        'Example System Prompt',
        'Replace with a real prompt for your project.',
        'You are a helpful assistant. Be concise and accurate.'
    ),
    (
        'example_user_template',
        'Example User Template',
        'Use {placeholders} that get filled at runtime via render_prompt().',
        'Please help with the following: {task}\n\nContext: {context}'
    )
ON CONFLICT (key) DO NOTHING;

INSERT INTO hello_messages (message) VALUES
    ('hello world from db')
ON CONFLICT DO NOTHING;

INSERT INTO roadmap_items (phase, title, description, status, priority) VALUES
    ('MVP',     'Boilerplate setup',         'Initial project scaffolding from CLAUDE.md spec', 'done',        0),
    ('MVP',     'First real resource',       'Replace example resources with your domain model', 'planned',    1),
    ('Phase 2', 'Define your roadmap here',  'Add real items for your project',                   'planned',  100)
ON CONFLICT DO NOTHING;
