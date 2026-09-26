import sqlite3
import pytest
from storage import init_db, add_link, delete_link, get_link, increment_clicks
@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    init_db(path)
    return str(path)
def test_init_db(tmp_path):
    path = tmp_path / "test.db"
    assert not path.exists()
    init_db(path)
    assert path.exists()
def test_add_get_link(db_path):
    add_link(db_path, 'abc123', 'https://google.com')
    link = get_link(db_path, 'abc123')
    assert link is not None
    assert link[0] == 'abc123'
    assert link[1] == 'https://google.com'
    assert link[2] == 0
    assert link[3] is not None
def test_get_unknown_link_returns_none(db_path):
    link = get_link(db_path, 'abc123')
    assert link is None
def test_add_clicks(db_path):
    add_link(db_path, 'abc123', 'https://google.com')
    increment_clicks(db_path, 'abc123')
    link = get_link(db_path, 'abc123')
    assert link[2]==1
def test_duplicate_code_raises_integrity_error(db_path):
    add_link(db_path, "abc123", "https://example.com")
    with pytest.raises(sqlite3.IntegrityError):
        add_link(db_path, "abc123", "https://example.com")
def test_delete_link(db_path):
    assert delete_link(db_path, 'unknown') is False
    add_link(db_path, 'abc123', 'https://google.com')
    link = get_link(db_path, 'abc123')
    assert link is not None
    assert delete_link(db_path, 'abc123') is True
    link = get_link(db_path, 'abc123')
    assert link is None
    assert get_link(db_path, 'abc123') is None
