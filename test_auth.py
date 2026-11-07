from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import text

import auth
import main

LOGIN_ERROR = {"detail": "Incorrect username or password"}
TOKEN_ERROR = {"detail": "Could not validate credentials"}


def register(client, username, password):
    response = client.post("/users", json={"username": username, "password": password})
    assert response.status_code == 201
    return response.json()


def login(client, username, password):
    response = client.post("/auth/token", data={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def make_payload(sub, **overrides):
    now = datetime.now(timezone.utc)
    payload = {"sub": sub, "iat": now, "exp": now + timedelta(minutes=15)}
    payload.update(overrides)
    return payload


def tamper_signature(token):
    header, payload, signature = token.split(".")
    middle = len(signature) // 2
    new_char = "A" if signature[middle] != "A" else "B"
    signature = signature[:middle] + new_char + signature[middle + 1:]
    return f"{header}.{payload}.{signature}"


def test_login_returns_only_token_fields(client):
    user = register(client, "alice", "alice-pass")
    response = client.post("/auth/token", data={"username": "alice", "password": "alice-pass"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type"}
    assert body["token_type"] == "bearer"

    payload = auth.decode_access_token(body["access_token"])
    assert payload["sub"] == str(user["id"])
    assert payload["exp"] - payload["iat"] == 15 * 60


def test_wrong_password_and_unknown_user_look_the_same(client):
    register(client, "alice", "alice-pass")
    wrong_password = client.post("/auth/token", data={"username": "alice", "password": "wrong"})
    unknown_user = client.post("/auth/token", data={"username": "unk", "password": "alice-pass"})

    for response in (wrong_password, unknown_user):
        assert response.status_code == 401
        assert response.json() == LOGIN_ERROR
        assert response.headers["WWW-Authenticate"] == "Bearer"


def test_me_returns_current_user(client):
    user = register(client, "alice", "alice-pass")
    token = login(client, "alice", "alice-pass")
    response = client.get("/users/me", headers=bearer(token))
    assert response.status_code == 200
    assert response.json() == user


def test_each_user_gets_own_profile(client):
    alice = register(client, "alice", "alice-pass")
    bob = register(client, "bob", "bob-pass")
    alice_token = login(client, "alice", "alice-pass")
    bob_token = login(client, "bob", "bob-pass")

    assert client.get("/users/me", headers=bearer(alice_token)).json() == alice
    assert client.get("/users/me", headers=bearer(bob_token)).json() == bob


def test_handmade_valid_token_is_accepted(client, rsa_keys):
    user = register(client, "alice", "alice-pass")
    private_pem, _ = rsa_keys
    token = jwt.encode(make_payload(str(user["id"])), private_pem, algorithm="RS256")

    response = client.get("/users/me", headers=bearer(token))
    assert response.status_code == 200


def test_me_without_token_returns_401(client):
    response = client.get("/users/me")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "make_bad_token",
    [
        pytest.param(lambda ctx: "abc", id="random-string"),
        pytest.param(lambda ctx: tamper_signature(ctx["token"]), id="tampered-signature"),
        pytest.param(
            lambda ctx: auth.create_access_token(ctx["user_id"], timedelta(seconds=-1)),
            id="expired",
        ),

        pytest.param(
            lambda ctx: jwt.encode(
                {"sub": str(ctx["user_id"]), "iat": datetime.now(timezone.utc)},
                ctx["private_pem"],
                algorithm="RS256",
            ),
            id="missing-exp",
        ),
        pytest.param(lambda ctx: jwt.encode(make_payload("abc"), ctx["private_pem"], algorithm="RS256"), id="sub-not-number"),
        pytest.param(
            lambda ctx: jwt.encode(
                make_payload(str(ctx["user_id"])), ctx["other_private_pem"], algorithm="RS256"
            ),
            id="foreign-key",
        ),
        pytest.param(
            lambda ctx: jwt.encode(
                make_payload(str(ctx["user_id"])), ctx["private_pem"], algorithm="RS384"
            ),
            id="rs384-same-key",
        ),
    ],
)
def test_bad_token_returns_401(client, rsa_keys, other_rsa_keys, make_bad_token):
    user = register(client, "alice", "alice-pass")
    ctx = {
        "user_id": user["id"],
        "token": login(client, "alice", "alice-pass"),
        "private_pem": rsa_keys[0],
        "other_private_pem": other_rsa_keys[0],
    }

    response = client.get("/users/me", headers=bearer(make_bad_token(ctx)))
    assert response.status_code == 401
    assert response.json() == TOKEN_ERROR
    assert response.headers["WWW-Authenticate"] == "Bearer"

def test_deleted_user_token_returns_401(client):
    register(client, "alice", "alice-pass")
    token = login(client, "alice", "alice-pass")
    assert client.get("/users/me", headers=bearer(token)).status_code == 200

    with main.engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE username = :username"), {"username": "alice"})
    response = client.get("/users/me", headers=bearer(token))
    assert response.status_code == 401
    assert response.json() == TOKEN_ERROR

