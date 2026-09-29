PRAGMA foreign_keys = ON;

CREATE TABLE users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE links(
        code TEXT PRIMARY KEY,
        original_url TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE TABLE visits(
    id INTEGER PRIMARY KEY,
    link_code TEXT NOT NULL,
    visited_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (link_code) REFERENCES links(code)
);
INSERT INTO users (name)
VALUES
    ('Alex'),
    ('Maria'),
    ('Ivan');

INSERT INTO links (code, original_url, user_id)
VALUES
    ('google', 'https://google.com', 1),
    ('python', 'https://python.com', 1),
    ('yandex', 'https://yandex.ru', 2),
    ('github', 'https://github.com', 2),
    ('sqlite', 'https://sqlite.org', 3);

INSERT INTO visits (link_code)
VALUES
    ('google'),
    ('google'),
    ('google'),
    ('google'),
    ('python'),
    ('python'),
    ('yandex'),
    ('github');
SELECT
    l.code,
    l.original_url,
    u.name AS owner_name
FROM links AS l
JOIN users AS u
    ON l.user_id = u.id;
SELECT
    l.code,
    l.original_url,
    v.id AS visit_id,
    v.visited_at
FROM links AS l
LEFT JOIN visits AS v
    ON l.code = v.link_code
ORDER BY l.code, v.id;
SELECT
    u.name,
    COUNT(l.code) AS links_count
FROM users AS u
LEFT JOIN links AS l
    ON u.id = l.user_id
GROUP BY u.id, u.name
ORDER BY links_count DESC, u.name;
SELECT l.code, COUNT(v.id) as visits_count
FROM links as l
LEFT JOIN visits as v on l.code = v.link_code
GROUP BY l.code ORDER BY visits_count DESC, l.code;

SELECT l.code
FROM links AS l
LEFT JOIN visits AS v ON l.code = v.link_code
GROUP BY l.code
ORDER BY COUNT(v.id) DESC, l.code LIMIT 2;
SELECT u.name FROM users AS u LEFT JOIN links AS l ON u.id = l.user_id GROUP BY u.name HAVING COUNT(l.user_id)>=2 ORDER BY COUNT(l.user_id) DESC;
SELECT l.code FROM links AS l LEFT JOIN visits AS v ON v.link_code = l.code WHERE v.id IS null;
SELECT l.code, COUNT(v.id) AS visits_count
FROM links AS l
LEFT JOIN visits AS v ON v.link_code = l.code
GROUP BY l.code HAVING COUNT(v.id) > (
    SELECT AVG(visits_count)
    FROM (SELECT COUNT(v2.id) AS visits_count FROM links AS l2 LEFT JOIN visits AS v2 ON
        v2.link_code = l2.code GROUP BY l2.code) AS counts
)
ORDER BY visits_count DESC, l.code;