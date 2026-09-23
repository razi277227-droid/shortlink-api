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
