CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE links (
    code TEXT PRIMARY KEY,
    original_url TEXT NOT NULL,
    user_id BIGINT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE visits (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    link_code TEXT NOT NULL,
    visited_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (link_code) REFERENCES links(code)
);
INSERT INTO users (name)
VALUES ('Alex'), ('Maria'), ('Ivan');
INSERT INTO links (code, original_url, user_id)
VALUES ('google', 'https://google.com', 1),
    ('python', 'https://python.org', 1),
    ('yandex', 'https://yandex.ru', 2),
    ('github', 'https://github.com', 2),
    ('sqlite', 'https://sqlite.org', 3);
INSERT INTO visits (link_code)
VALUES ('google'),
    ('google'),
    ('google'),
    ('google'),
    ('python'),
    ('python'),
    ('yandex'),
    ('github');