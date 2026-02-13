-- SCD2 history of all scraped rider data
-- depends:

CREATE TABLE riders_scraped (
    id          BIGSERIAL PRIMARY KEY,
    source      TEXT NOT NULL DEFAULT 'uci',
    source_url  TEXT NOT NULL,
    name        TEXT NOT NULL,
    nationality TEXT,
    birth_date  TEXT,
    sanctions   TEXT,
    valid_from  TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to    TIMESTAMPTZ,
    is_current  BOOLEAN NOT NULL DEFAULT TRUE,
    scraped_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    row_hash    TEXT NOT NULL
);

CREATE UNIQUE INDEX idx_riders_scraped_current
    ON riders_scraped (source, source_url) WHERE is_current;

CREATE INDEX idx_riders_scraped_source_url
    ON riders_scraped (source, source_url);

-- Manual corrections, enrichment, and fully manual entries
CREATE TABLE riders_overrides (
    id              BIGSERIAL PRIMARY KEY,
    source          TEXT,
    source_url      TEXT,
    name            TEXT,
    nationality     TEXT,
    birth_date      TEXT,
    sanctions       TEXT,
    team            TEXT,
    instagram       TEXT,
    notes           TEXT,
    is_manual_entry BOOLEAN NOT NULL DEFAULT FALSE,
    manual_key      TEXT UNIQUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      TEXT,
    reason          TEXT
);

CREATE UNIQUE INDEX idx_riders_overrides_source_url
    ON riders_overrides (source, source_url) WHERE source_url IS NOT NULL;

-- Merged view: overrides win field-by-field, manual entries included via UNION ALL
CREATE VIEW riders_current AS
SELECT
    s.source,
    s.source_url,
    COALESCE(o.name, s.name)            AS name,
    COALESCE(o.nationality, s.nationality) AS nationality,
    COALESCE(o.birth_date, s.birth_date)   AS birth_date,
    COALESCE(o.sanctions, s.sanctions)     AS sanctions,
    o.team,
    o.instagram,
    o.notes,
    s.scraped_at,
    s.valid_from
FROM riders_scraped s
LEFT JOIN riders_overrides o ON o.source = s.source AND o.source_url = s.source_url
WHERE s.is_current

UNION ALL

SELECT
    NULL            AS source,
    o.manual_key    AS source_url,
    o.name,
    o.nationality,
    o.birth_date,
    o.sanctions,
    o.team,
    o.instagram,
    o.notes,
    NULL            AS scraped_at,
    o.created_at    AS valid_from
FROM riders_overrides o
WHERE o.is_manual_entry;
