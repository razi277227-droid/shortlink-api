import pytest
from sqlalchemy import text
import main
from helpers import register, login, bearer


def create_link(client):
    response = client.post("/links", json={"url": "https://example.com"})
    assert response.status_code == 201
    return response.json()["code"]


@pytest.fixture
def intruder_headers(auth_client):
    register(auth_client, "intruder", "intruder-pass")
    token = login(auth_client, "intruder", "intruder-pass")
    return bearer(token)


def test_intruder_cannot_see_stats(auth_client, intruder_headers):
    code = create_link(auth_client)
    foreign = auth_client.get(f"/links/{code}/stats", headers=intruder_headers)
    missing = auth_client.get(f"/links/nope123/stats", headers=intruder_headers)
    assert foreign.status_code == 404
    assert foreign.json() == missing.json()


def test_without_token_returns_401(client):
    response = client.post("/links", json={"url": "https://example.com"})
    assert response.status_code == 401


def test_custom_links_without_token_returns_401(client):
    code = "my_code"
    response = client.post("/customlinks", json={"url": "https://example.com", "my_code": code})
    assert response.status_code == 401


def test_redirect_without_token_returns_307(auth_client):
    response = auth_client.post("/links", json={"url": "https://example.com"})
    assert response.status_code == 201
    auth_client.headers.pop("Authorization")
    code = response.json()["code"]
    redirect = auth_client.get(f"/r/{code}", follow_redirects=False)
    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://example.com/"


def test_owner_can_see_stats_200(auth_client):
    code = create_link(auth_client)
    response = auth_client.get(f"/links/{code}/stats")
    assert response.status_code == 200
    assert response.json()["url"] == "https://example.com/"


def test_owner_can_delete_own_link_204(auth_client):
    code = create_link(auth_client)
    response = auth_client.delete(f"/links/{code}")
    assert response.status_code == 204
    deleted = auth_client.get(f"/r/{code}", follow_redirects=False)
    assert deleted.status_code == 404


def test_enemy_cannot_delete_owner_link_404(auth_client, intruder_headers):
    code = create_link(auth_client)
    response = auth_client.delete(f"/links/{code}", headers=intruder_headers)
    assert response.status_code == 404
    redirect = auth_client.get(f"/r/{code}", follow_redirects=False)
    assert redirect.status_code == 307


def test_orphan_link_id_hidden_from_everyone(auth_client):
    with main.engine.begin() as conn:
        conn.execute(text("INSERT INTO links (code, original_url) VALUES ('orphan', 'https://example.com')"))
    stats = auth_client.get(f"/links/orphan/stats")
    assert stats.status_code == 404
    delete = auth_client.delete("/links/orphan")
    assert delete.status_code == 404

    redirect = auth_client.get(f"/r/orphan", follow_redirects=False)
    assert redirect.status_code == 307


def test_cascade_delete_all_links(auth_client):
    code = create_link(auth_client)
    with main.engine.begin() as conn:
        conn.execute(text("DELETE FROM users WHERE username = 'owner'"))
    redirect = auth_client.get(f"/r/{code}", follow_redirects=False)
    assert redirect.status_code == 404
