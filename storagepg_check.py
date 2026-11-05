from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from storage_pg import add_link, get_link, increment_clicks, delete_link
engine = create_engine("postgresql+psycopg:///shortlink_app_dev")
code = "check_" + uuid4().hex
url = "https://example.com/"
assert get_link(engine, code) is None
assert increment_clicks(engine, code) is False
assert delete_link(engine, code) is False
add_link(engine, code, url)
try:
    link = get_link(engine, code)
    assert link is not None
    assert link.code == code
    assert link.original_url == url
    assert link.clicks == 0
    assert link.created_at is not None
    updated = increment_clicks(engine, code)
    assert updated is True
    link = get_link(engine, code)
    assert link is not None
    assert link.clicks == 1
    try:
        add_link(engine, code, "https://another_example.com")
    except IntegrityError:
        pass
    else:
        raise AssertionError("Базаш разрешили шлюха")
    after_dub = get_link(engine, code)
    assert after_dub == link
    deleted = delete_link(engine, code)
    assert deleted is True
    assert get_link(engine, code) is None
    deleted_again = delete_link(engine, code)
    assert deleted_again is False
finally:
    delete_link(engine, code)
print("All passed nax")
