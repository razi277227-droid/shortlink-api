from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg:///shortlink_app_dev')
with engine.connect() as conn:
    result = conn.execute(text("SELECT current_database()"))
    print(result.scalar_one())
with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO links(code, original_url)
        VALUES(:code, :url)
    """),
                 {"code": "test1", "url": "https://example.com"}
    )
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT code, original_url, clicks, created_at
        FROM links
        WHERE code = :code
    """),
                          {'code': "test1"}
    )
    print(result.one())

with engine.begin() as conn:
    conn.execute(text("UPDATE links SET clicks = clicks + 1 WHERE code = :code"), {"code": "test1"})
with engine.connect() as conn:
    result = conn.execute(text("SELECT clicks FROM links WHERE code = :code"), {"code": "test1"})
    print(f"{result.scalar_one()=}")
try:
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO links (code, original_url) VALUES (:code, :original_url)"), {'code': "test_rollback2", "original_url": "https://goog.com"})
        conn.execute(text("UPDATE links SET clicks = clicks + 1 WHERE code = :code"), {"code": "test_rollback2"})
        raise RuntimeError("Проверка отката")
except RuntimeError as e:
    print("Ошбка тестовая", e)
with engine.connect() as conn:
    res = conn.execute(text('SELECT * FROM links WHERE code = :code'), {"code": "test_rollback2"})
    print(res.all())
with engine.begin() as conn:
    conn.execute(text("DELETE FROM links WHERE code = :code"), {"code": "test_rollback2"})
    conn.execute(text("DELETE FROM links WHERE code = :code"), {"code": "test1"})
with engine.connect() as conn:
    res = conn.execute(text("SELECT * FROM links WHERE code = :code"), {"code": "test1"})
    print(res.all())

