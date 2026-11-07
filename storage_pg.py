from sqlalchemy import text
def add_link(engine, code, original_url, expires_at=None):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO links (code, original_url, expires_at)
                VALUES (:code, :original_url, :expires_at)
            """),
            {
                "code": code,
                "original_url": original_url,
                "expires_at": expires_at,
            },
        )
def get_link(engine, code):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT code, original_url, clicks, created_at, expires_at FROM links WHERE code = :code"), {"code": code})
        row = result.one_or_none()
    return row
def increment_clicks(engine, code):
    with engine.begin() as conn:
        result = conn.execute(text("UPDATE links SET clicks = clicks + 1 WHERE code = :code"), {"code": code})
    return result.rowcount == 1
def delete_link(engine, code):
    with engine.begin() as conn:
        result = conn.execute(text("DELETE FROM links WHERE code = :code"), {"code": code})
    return result.rowcount == 1


def create_user(engine, username, hashed_password):
    with engine.begin() as conn:
        result = conn.execute(
            text("""
            INSERT INTO users (username, hashed_password)
            VALUES (:username, :hashed_password)
            RETURNING id, username, created_at
            """),
            {
                "username": username,
                "hashed_password": hashed_password,
            }
        )
        row = result.mappings().one()
    return row

def get_user_by_username(engine, username):
    with engine.begin() as conn:
        result = conn.execute(
            text("""
            SELECT id, username, hashed_password, created_at
            FROM users 
            WHERE username = :username
            """),
            {"username": username}
        )
        row = result.mappings().one_or_none()
        if row is None:
            return None
        return dict(row)

def get_user_by_id(engine, user_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT id, username, created_at
            FROM users 
            WHERE id = :user_id
            """),
            {"user_id": user_id}
        )
        row = result.mappings().one_or_none()
        if row is None:
            return None
        return dict(row)