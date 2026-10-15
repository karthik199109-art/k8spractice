CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

INSERT INTO users (name)
SELECT seed.name
FROM (VALUES
    ('Karthik'),
    ('Azure Engineer'),
    ('Kubernetes Engineer')
) AS seed(name)
WHERE NOT EXISTS (
    SELECT 1
    FROM users
    WHERE users.name = seed.name
);