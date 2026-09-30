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
SELECT owner_name, AVG(visits_count) FROM (SELECT u.name AS owner_name, l.code, COUNT(v.id) AS visits_count FROM links AS l LEFT JOIN users AS u ON l.user_id = u.id LEFT JOIN visits AS v ON v.link_code = l.code GROUP BY u.name, l.code) AS stat GROUP BY owner_name ORDER BY visits_count DESC;
SELECT u.name, COUNT(l.original_url) AS links_count FROM users AS u LEFT JOIN links AS l ON u.id = l.user_id GROUP BY u.id HAVING links_count=0;
SELECT u.name, COUNT(v.id) AS counts FROM users AS u LEFT JOIN links AS l ON l.user_id = u.id LEFT JOIN visits AS v ON v.link_code = l.code GROUP BY u.name HAVING counts > 1;
SELECT owner_name, AVG(visits_count) AS avg_visits FROM (SELECT u.name AS owner_name, l.code, COUNT(v.id) AS visits_count FROM links AS l LEFT JOIN users AS u ON l.user_id = u.id LEFT JOIN visits AS v ON v.link_code = l.code GROUP BY u.name, l.code) AS stat GROUP BY owner_name HAVING avg_visits > 1 ORDER BY avg_visits DESC;
SELECT l.code, COUNT(v.id) AS visits_count FROM links AS l LEFT JOIN visits AS v ON l.code = v.link_code GROUP BY l.code HAVING visits_count = (SELECT COUNT(v2.id) FROM links AS l2 LEFT JOIN visits AS v2 ON l2.code = v2.link_code GROUP BY l2.code ORDER BY COUNT(v2.id) DESC LIMIT 1);
SELECT u.name AS owner_name, COUNT(v.id) AS total_count FROM users AS u LEFT JOIN links AS l ON l.user_id = u.id LEFT JOIN visits AS v ON l.code = v.link_code GROUP BY u.name HAVING total_count = (SELECT COUNT(v2.id) FROM users AS u2 LEFT JOIN links AS l2 ON u2.id = l2.user_id LEFT JOIN visits AS v2 ON l2.code = v2.link_code GROUP BY u2.id ORDER BY COUNT(v2.id) DESC LIMIT 1);
SELECT DATE(visited_at) AS visit_date, COUNT(*) FROM visits GROUP BY visit_date ORDER BY visit_date;
WITH link_stats AS (SELECT u.name AS owner_name, u.id AS user_id, l.code, COUNT(v.id) AS visits_count FROM users AS u LEFT JOIN links AS l ON u.id = l.user_id LEFT JOIN visits AS v ON l.code = v.link_code GROUP BY l.code, u.name), owner_averages AS (SELECT user_id, AVG(visits_count) AS average_visits FROM link_stats GROUP BY user_id) SELECT ls.owner_name, ls.code, ls.visits_count FROM link_stats AS ls JOIN owner_averages AS oa ON ls.user_id = oa.user_id WHERE ls.visits_count > oa.average_visits ORDER BY ls.owner_name, ls.code;
SELECT u.name AS owner_name, COUNT(v.id) AS visits_count FROM users AS u LEFT JOIN links AS l ON u.id = l.user_id LEFT JOIN visits AS v ON l.code = v.link_code GROUP BY u.name HAVING visits_count >= 3;
WITH link_stats AS (
    SELECT
        u.id AS user_id,
        COUNT(l.code) AS total_links
    FROM users AS u
    LEFT JOIN links AS l
        ON u.id = l.user_id
    GROUP BY u.id
)
SELECT
    u2.name,
    ls.total_links,
    COUNT(v.id) AS total_visits
FROM users AS u2
JOIN link_stats AS ls
    ON ls.user_id = u2.id
LEFT JOIN links AS l2
    ON l2.user_id = u2.id
LEFT JOIN visits AS v
    ON v.link_code = l2.code
GROUP BY u2.id, u2.name, ls.total_links;
SELECT u.name, COUNT(DISTINCT l.code) AS total_links, COUNT(v.id) AS total_visits FROM users AS u LEFT JOIN links AS l ON l.user_id = u.id LEFT JOIN visits AS v ON v.link_code = l.code GROUP BY u.id, u.name;
SELECT u.name AS owner_name, COUNT(l.code) AS links_count FROM users AS u LEFT JOIN links AS l ON l.user_id = u.id GROUP BY u.name HAVING links_count = (SELECT COUNT(l2.code) FROM users AS u2 LEFT JOIN links AS l2 ON l2.user_id = u2.id GROUP BY u2.name, u2.id ORDER BY COUNT(l2.code) DESC LIMIT 1);
