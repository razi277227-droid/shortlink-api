-- Создаём таблицу ссылок
CREATE TABLE links (
    code TEXT PRIMARY KEY,
    original_url TEXT NOT NULL,
    clicks INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Добавляем три ссылки
INSERT INTO links (code, original_url)
VALUES ('google', 'https://google.com');

INSERT INTO links (code, original_url)
VALUES ('github', 'https://github.com');

INSERT INTO links (code, original_url)
VALUES ('3KxwU1', 'https://yandex.ru');

-- Показываем все ссылки
SELECT * FROM links;

-- Находим ссылку по коду
SELECT * FROM links
WHERE code = '3KxwU1';

-- Увеличиваем количество переходов на один
UPDATE links
SET clicks = clicks + 1
WHERE code = 'google';

-- Показываем две самые посещаемые ссылки
SELECT * FROM links
ORDER BY clicks DESC
LIMIT 2;

-- Удаляем одну ссылку
DELETE FROM links
WHERE code = 'github';

-- Намеренно пробуем добавить повторяющийся PRIMARY KEY
INSERT INTO links (code, original_url)
VALUES ('google', 'https://yandex.ru');