import sqlite3
def init_db(db_path: str):
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
            code TEXT PRIMARY KEY,
            original_url TEXT NOT NULL,
            clicks INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.commit()
    finally:
        connection.close()
def add_link(db_path: str, code: str, original_url: str):
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            INSERT INTO links (code, original_url)
            VALUES (?, ?)
            """,
            (code, original_url),
        )
        connection.commit()
    finally:
        connection.close()
def get_link(db_path: str, code: str):
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.execute(
            """
            SELECT * FROM links WHERE code = ?
            """,
            (code,),
        )
        return cursor.fetchone()
    finally:
        connection.close()
def increment_clicks(db_path: str, code: str):
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.execute(
            """
            UPDATE links SET clicks = clicks + 1 WHERE code = ?
            """,
            (code,),
        )
        connection.commit()
        return cursor.rowcount == 1
    finally:
        connection.close()
def delete_link(db_path: str, code: str):
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.execute(
            """
            DELETE FROM links WHERE code = ?
            """,
            (code,),
        )
        connection.commit()
        return cursor.rowcount == 1
    finally:
        connection.close()