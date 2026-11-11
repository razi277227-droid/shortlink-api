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