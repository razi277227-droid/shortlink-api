import pytest
from fastapi.testclient import TestClient
from main import app, links
@pytest.fixture(autouse=True)
def clear_links():
    links.clear()
@pytest.fixture(autouse=True)
def client():
    return TestClient(app)
def test_create_link_return_201(client: TestClient):
    response = client.post("/links", json={"url": "https://google.com"})
    assert response.status_code == 201
    assert response.json()["short_url"].startswith("/r/")
def test_invalid_url_return_422(client: TestClient):
    response = client.post("/links", json={"url": "not fucking url"})
    assert response.status_code == 422
def test_unknown_code_return_404(client: TestClient):
    response = client.get("/links/unknown/stats")
    assert response.status_code == 404
def test_redirect_has_correct_location(client: TestClient):
    create_response = client.post("/links", json={"url": "https://google.com"})
    code = create_response.json()["code"]
    response = client.get(f"/r/{code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["Location"] == "https://google.com/"
def test_clicks_raises(client: TestClient):
    create_response = client.post("/links", json={"url": "https://google.com"})
    code = create_response.json()["code"]
    client.get(f"/r/{code}", follow_redirects=False)
    counter = client.get(f"/links/{code}/stats").json()["clicks"]
    assert counter == 1
def test_custom_links(client: TestClient):
    response = client.post("/customlinks", json = {"url": "https://google.com", "my_code": "pidor"})
    assert response.status_code == 201
def test_custom_links_low(client: TestClient):
    response = client.post("/customlinks", json={"url": "https://google.com", "my_code": "pi"})
    assert response.status_code == 422
def test_custom_links_large(client: TestClient):
    response = client.post("/customlinks", json={"url": "https://google.com", "my_code": "qwertyuiopasdfghjklzxcvbnm"})
    assert response.status_code == 422
def test_link_delete(client: TestClient):
    response = client.post("/links", json={"url": "https://google.com"})
    code = response.json()["code"]
    del_response = client.delete(f"/links/{code}")
    assert del_response.status_code == 204
    status_response = client.get(f"/links/{code}/stats")
    assert status_response.status_code == 404

def test_custom_link_banned_symbols1(client: TestClient):
    response = client.post("/customlinks", json={"url": "https://google.com", "my_code": "!!abc"})
    assert response.status_code == 422
def test_custom_link_banned_symbols2(client: TestClient):
    response = client.post("/customlinks", json={"url": "https://google.com", "my_code": " abc"})
    assert response.status_code == 422
def test_custom_link_banned_symbols3(client: TestClient):
    response = client.post("/customlinks", json={"url": "https://google.com", "my_code": "abc "})
    assert response.status_code == 422
def test_custom_link_povtory(client: TestClient):
    response1 = client.post("/customlinks", json={"url": "https://google.com", "my_code": "abc"})
    response2 = client.post("/customlinks", json={"url": "https://yandex.com", "my_code": "abc"})
    assert response2.status_code == 409