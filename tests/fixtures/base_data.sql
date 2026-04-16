-- Test fixtures — known state for integration tests.
-- Loaded by `make test` after migrations, before pytest runs.

INSERT INTO prompts (key, name, content, model, temperature, max_tokens) VALUES
    ('test_prompt', 'Test Prompt', 'You are a test assistant.', 'claude-sonnet-4-6', 0.5, 100)
ON CONFLICT (key) DO NOTHING;
