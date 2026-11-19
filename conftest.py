import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from helpers import register, login

import os
import auth
import main

def make_rsa_pair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private_pem, public_pem

@pytest.fixture(scope="session")
def rsa_keys() -> tuple[str, str]:
    return make_rsa_pair()

@pytest.fixture(scope="session")
def other_rsa_keys() -> tuple[str, str]:
    return make_rsa_pair()

@pytest.fixture
def client(monkeypatch, rsa_keys):
    private_pem, public_pem = rsa_keys
    monkeypatch.setattr(auth, "load_private_key", lambda: private_pem)
    monkeypatch.setattr(auth, "load_public_key", lambda: public_pem)
    test_database_url = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg:///shortlink_app_test")
    test_engine = create_engine(test_database_url)
    try:
        with test_engine.begin() as conn:
            database_name = conn.execute(text("SELECT current_database()")).scalar_one()
            if database_name != "shortlink_app_test":
                raise RuntimeError(f"Expected test database, but got {database_name}")
            conn.execute(text("DELETE FROM links"))
            conn.execute(text("DELETE FROM users"))
        monkeypatch.setattr(main, "engine", test_engine)

        with TestClient(main.app) as test_client:
            yield test_client
    finally:
        test_engine.dispose()

@pytest.fixture
def auth_client(client):
    register(client, "owner", "owner-pass")
    token = login(client, "owner", "owner-pass")
    client.headers["Authorization"] = f"Bearer {token}"
    return client