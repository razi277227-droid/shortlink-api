import pytest
from sqlalchemy import text
import main
from helpers import register, login, bearer
from datetime import datetime, timedelta, timezone

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)
def my_id(client):
    response = client.get("/users/me")
    return response.json()["id"]

def create_link(client):
    response = client.post("/links", json={"url": "https://example.com"})
    assert response.status_code == 201
    return response.json()["code"]

def insert_link(code, owner_id, created_at, expires_at=None):
    original_url = "https://google.com"
    with main.engine.begin() as conn:
        conn.execute(text("""
        INSERT INTO links (owner_id, code, original_url, created_at, expires_at)
        VALUES (:owner_id, :code, :original_url, :created_at, :expires_at)
        """),
        {"code": code, "original_url": original_url, "created_at": created_at, "expires_at": expires_at, "owner_id": owner_id}
        )


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

def test_list_links_newest_first(auth_client):
    owner = my_id(auth_client)
    insert_link("ccc", owner, BASE)
    insert_link("aaa", owner, BASE + timedelta(minutes=1))
    insert_link("bbb", owner, BASE + timedelta(minutes=2))
    response = auth_client.get("/links")
    assert response.status_code == 200
    got = [item["code"] for item in response.json()["items"]]
    assert got == ["bbb", "aaa", "ccc"]

def test_list_links_sorted_by_code_if_same_time(auth_client):
    owner = my_id(auth_client)
    insert_link("aaa", owner, BASE)
    insert_link("bbb", owner, BASE)
    response = auth_client.get("/links")
    assert response.status_code == 200
    got = [item["code"] for item in response.json()["items"]]
    assert got == ["bbb", "aaa"]

def test_list_links_limit(auth_client):
    [create_link(auth_client) for _ in range(3)]
    response = auth_client.get("/links?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2

def test_list_links_offset_no_duplicates2(auth_client):
    codes = ["aaa", "bbb", "ccc", "ddd", "eee"]
    owner = my_id(auth_client)
    for i in range(len(codes)):
        insert_link(codes[i], owner, BASE + timedelta(minutes=i))
    page1 = auth_client.get(f"/links?limit=2&offset=0")
    page2 = auth_client.get(f"/links?limit=2&offset=2")
    page3 = auth_client.get(f"/links?limit=2&offset=4")
    assert len(page1.json()["items"]) == len(page2.json()["items"]) == 2
    assert len(page3.json()["items"]) == 1
    assert page1.json()["total"] == page2.json()["total"] == page3.json()["total"] == 5
    items = page1.json()["items"]+page2.json()["items"]+page3.json()["items"]
    got = [item["code"] for item in items]
    assert got == codes[::-1]

def test_list_links_expired_flag(auth_client):
    owner = my_id(auth_client)
    insert_link("old", owner, BASE, expires_at=BASE)
    insert_link("forever", owner, BASE + timedelta(minutes=1))
    response = auth_client.get("/links")
    assert response.status_code == 200
    flags={item["code"]: item["expired"] for item in response.json()["items"]}
    assert flags == {"old": True, "forever": False}


def test_list_links_other_users_sees_empty_200(auth_client):
    [create_link(auth_client) for _ in range(2)]
    register(auth_client, "other", "other-pass")
    token = login(auth_client, "other", "other-pass")
    response = auth_client.get("/links", headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []

def test_links_without_token_returns_401(client):
    response = client.get("/links")
    assert response.status_code == 401

@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_list_links_invalid_params_returns_422(auth_client, query):
    response = auth_client.get(f"/links?{query}")
    assert response.status_code == 422

