import pytest
import main
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta, timezone
from security import verify_password
from storage_pg import get_user_by_username


def test_create_link_return_201(auth_client: TestClient):
    response = auth_client.post("/links", json={"url": "https://google.com"})
    assert response.status_code == 201
    assert response.json()["short_url"].startswith("/r/")


def test_invalid_url_return_422(auth_client: TestClient):
    response = auth_client.post("/links", json={"url": "not a url"})
    assert response.status_code == 422


def test_unknown_code_return_404(auth_client: TestClient):
    response = auth_client.get("/links/unknown/stats")
    assert response.status_code == 404


def test_redirect_has_correct_location(auth_client: TestClient):
    create_response = auth_client.post("/links", json={"url": "https://google.com"})
    code = create_response.json()["code"]
    response = auth_client.get(f"/r/{code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["Location"] == "https://google.com/"


def test_clicks_raises(auth_client: TestClient):
    create_response = auth_client.post("/links", json={"url": "https://google.com"})
    code = create_response.json()["code"]
    auth_client.get(f"/r/{code}", follow_redirects=False)
    counter = auth_client.get(f"/links/{code}/stats").json()["clicks"]
    assert counter == 1


def test_custom_links(auth_client: TestClient):
    response = auth_client.post("/customlinks", json={"url": "https://google.com", "my_code": "mycode"})
    assert response.status_code == 201


def test_custom_links_low(auth_client: TestClient):
    response = auth_client.post("/customlinks", json={"url": "https://google.com", "my_code": "pi"})
    assert response.status_code == 422


def test_custom_links_large(auth_client: TestClient):
    response = auth_client.post("/customlinks", json={"url": "https://google.com", "my_code": "qwertyuiopasdfghjklzxcvbnm"})
    assert response.status_code == 422


def test_link_delete(auth_client: TestClient):
    response = auth_client.post("/links", json={"url": "https://google.com"})
    code = response.json()["code"]
    del_response = auth_client.delete(f"/links/{code}")
    assert del_response.status_code == 204
    status_response = auth_client.get(f"/links/{code}/stats")
    assert status_response.status_code == 404


def test_custom_link_banned_symbols1(auth_client: TestClient):
    response = auth_client.post("/customlinks", json={"url": "https://google.com", "my_code": "!!abc"})
    assert response.status_code == 422


def test_custom_link_banned_symbols2(auth_client: TestClient):
    response = auth_client.post("/customlinks", json={"url": "https://google.com", "my_code": " abc"})
    assert response.status_code == 422


def test_custom_link_banned_symbols3(auth_client: TestClient):
    response = auth_client.post("/customlinks", json={"url": "https://google.com", "my_code": "abc "})
    assert response.status_code == 422


def test_custom_link_povtory(auth_client: TestClient):
    response1 = auth_client.post("/customlinks", json={"url": "https://google.com", "my_code": "abc"})
    response2 = auth_client.post("/customlinks", json={"url": "https://yandex.com", "my_code": "abc"})
    assert response2.status_code == 409


@pytest.fixture()
def fixed_now(monkeypatch):
    now = datetime(2030, 1, 1, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(main, "utc_now", lambda: now)
    return now


@pytest.mark.parametrize("extra_fields", [{}, {"expires_at": None}])
def test_link_without_expiration(auth_client, monkeypatch, fixed_now, extra_fields):
    response = auth_client.post("/links", json={"url": "https://google.com", **extra_fields})
    assert response.status_code == 201
    code = response.json()["code"]
    later = fixed_now + timedelta(seconds=1)
    monkeypatch.setattr(main, "utc_now", lambda: later)
    response = auth_client.get(f"/r/{code}", follow_redirects=False)
    assert response.status_code == 307
    response = auth_client.get(f"/links/{code}/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["expires_at"] is None
    assert stats["expired"] is False
    assert stats["clicks"] == 1


@pytest.mark.parametrize("endpoint, extra_fields", [("/links", {}), ("/customlinks", {"my_code": "invalid_time"}), ])
@pytest.mark.parametrize("expires_at", ["2030-01-01T11:00:00+00:00", "2030-01-01T12:00:00+00:00", "2030-01-01T13:00:00",
                                        "not-a-date", ])
def test_invalid_expiration(auth_client, fixed_now, endpoint, extra_fields, expires_at):
    response = auth_client.post(endpoint, json={"url": "https://google.com", "expires_at": expires_at, **extra_fields})
    assert response.status_code == 422


@pytest.mark.parametrize("endpoint, extra_fields", [("/links", {}), ("/customlinks", {"my_code": "timed-link"}), ])
@pytest.mark.parametrize("hours_later", [1, 2])
def test_link_expiration(auth_client, fixed_now, endpoint, hours_later, extra_fields, monkeypatch):
    expires_at = fixed_now + timedelta(hours=1)
    plus_three = timezone(timedelta(hours=3))
    response = auth_client.post(
        endpoint,
        json={
            "url": "https://google.com",
            "expires_at": expires_at.astimezone(plus_three).isoformat(),
            **extra_fields,
        },
    )
    assert response.status_code == 201
    code = response.json()["code"]

    response = auth_client.get(f"/links/{code}/stats")
    assert response.status_code == 200
    stats = response.json()
    assert datetime.fromisoformat(stats["expires_at"]) == expires_at
    assert stats["expired"] is False
    assert stats["clicks"] == 0

    response = auth_client.get(f"/r/{code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["Location"] == "https://google.com/"

    response = auth_client.get(f"/links/{code}/stats")
    assert response.status_code == 200
    assert response.json()["clicks"] == 1

    later = fixed_now + timedelta(hours=hours_later)
    monkeypatch.setattr(main, "utc_now", lambda: later)

    response = auth_client.get(f"/r/{code}", follow_redirects=False)
    assert response.status_code == 410
    assert response.json()["detail"] == "Link has expired"

    response = auth_client.get(f"/links/{code}/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["expired"] is True
    assert stats["clicks"] == 1
    assert datetime.fromisoformat(stats["expires_at"]) == expires_at

    # повтороное чтение статистики тоже не увеличивает счетчик
    response = auth_client.get(f"/links/{code}/stats")
    assert response.status_code == 200
    assert response.json()["clicks"] == 1


def test_register_user_returns_public_fields_and_save_hash(client):
    password = "  training password  "

    response = client.post("/users", json={
        "username": "student_01",
        "password": password,
    })
    assert response.status_code == 201
    data = response.json()
    assert set(data) == {"id", "username", "created_at"}
    assert isinstance(data["id"], int)
    assert data["id"]>0
    assert data["username"]=="student_01"
    created_at = datetime.fromisoformat(data["created_at"])
    assert created_at.utcoffset() is not None

    saved_user = get_user_by_username(main.engine, "student_01")
    assert saved_user is not None
    assert saved_user["id"] == data["id"]
    assert saved_user["username"] == data["username"]
    assert saved_user["created_at"] == created_at
    assert saved_user["hashed_password"] != password
    assert verify_password(password, saved_user["hashed_password"]) is True
    assert verify_password(password.strip(), saved_user["hashed_password"]) is False
def test_duplicate_username_returns_409(client):
    first_password = "first training password"
    first_response = client.post(
        "/users",
        json={
            "username": "student_01",
            "password": first_password,
        },
    )
    assert first_response.status_code == 201

    second_response = client.post(
        "/users",
        json={
            "username": "student_01",
            "password": "another training password",
        },
    )
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Username already exists"

    with main.engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM users WHERE username = :username"),
            {"username": "student_01"},
        ).scalar_one()
        assert count == 1

        saved_user = get_user_by_username(main.engine, "student_01")
        assert saved_user is not None
        assert saved_user["id"] == first_response.json()["id"]
        assert verify_password(
            first_password,
            saved_user["hashed_password"],
        ) is True

def test_different_users_can_have_same_passwords(client):
    password = "shared training password"
    first_response = client.post(
        "/users",
        json={"username": "student_01", "password": password},
    )
    second_response = client.post(
        "/users",
        json={"username": "student_02", "password": password},
    )
    assert first_response.status_code == 201
    assert second_response.status_code == 201

    assert first_response.json()["id"] != second_response.json()["id"]

    first_user = get_user_by_username(main.engine, "student_01")
    second_user = get_user_by_username(main.engine, "student_02")
    assert first_user is not None
    assert second_user is not None
    assert first_user["hashed_password"] != second_user["hashed_password"]
    assert verify_password(password, first_user["hashed_password"]) is True
    assert verify_password(password, second_user["hashed_password"]) is True

@pytest.mark.parametrize("username", [
    "ab",
    "a"*33,
    "Student",
    "student-name",
    "student name",
    "студент",
])
def test_invalid_username_returns_422(client, username):
    response = client.post(
        "/users",
        json={"username": username, "password": "some train pass"},
    )
    assert response.status_code == 422
    assert get_user_by_username(main.engine, username) is None

@pytest.mark.parametrize("password", ["a"*3, "a"*129])
def test_invalid_password_length_returns_422(client, password):
    response = client.post(
        "/users",
        json={"username": "student_01", "password": password},
    )
    assert response.status_code == 422
    assert get_user_by_username(main.engine, "student_01") is None

@pytest.mark.parametrize("username_length", [3, 32])
@pytest.mark.parametrize("password_length", [4, 128])
def test_registration_accepts_boundary_lengths(
    client, username_length, password_length
):
    username = "a" * username_length
    password = "x" * password_length

    response = client.post(
        "/users",
        json={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 201
    assert response.json()["username"] == username

    saved_user = get_user_by_username(main.engine, username)

    assert saved_user is not None
    assert verify_password(password, saved_user["hashed_password"]) is True
