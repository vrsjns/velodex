-- Exclude riders not seen for 7 days from the merged view
-- depends: 0001.initial-schema

DROP VIEW riders_current;

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
  AND s.scraped_at > now() - INTERVAL '7 days'

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
