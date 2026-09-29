PRAGMA foreign_keys = ON;
INSERT INTO links (code, original_url, user_id)
VALUES ("test_999", "https://google999.com", 999);
BEGIN;
INSERT INTO users (name)
VALUES ("Pavel");
INSERT INTO links (code, original_url, user_id)
VALUES ('pavel_link', "https://example.com/pavel", last_insert_rowid());
COMMIT;
SELECT COUNT(*) FROM users WHERE name = 'Pavel';
SELECT COUNT(*) FROM links WHERE code = 'pavel_link';
BEGIN;
INSERT INTO users (name)
VALUES ("Elena");
INSERT INTO links (code, original_url, user_id)
VALUES ('elena_link', "https://example.com/elena", last_insert_rowid());
ROLLBACK;
SELECT COUNT(*) AS elena_users
FROM users
WHERE name = 'Elena';

SELECT COUNT(*) AS elena_links
FROM links
WHERE code = 'elena_link';
DELETE FROM users
WHERE name = 'Alex';
