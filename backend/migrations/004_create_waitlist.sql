-- Landing-page waitlist signups. Distinct from `users`: these are anonymous,
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE IF NOT EXISTS waitlist_signups (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email      CITEXT NOT NULL UNIQUE,
    source     TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
