def _register(
    client, username="testuser", email="test@example.com", password="secret123"
):
    return client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )


def _login(client, username="testuser", password="secret123"):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )


def _auth_header(client, username="testuser", password="secret123"):
    token = _login(client, username, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register(client):
    resp = _register(client)
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "testuser"
    assert "hashed_password" not in data


def test_register_duplicate_username(client):
    _register(client)
    resp = _register(client, email="other@example.com")
    assert resp.status_code == 409


def test_register_duplicate_email(client):
    _register(client)
    resp = _register(client, username="other")
    assert resp.status_code == 409


def test_login_success(client):
    _register(client)
    resp = _login(client)
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"


def test_login_wrong_password(client):
    _register(client)
    resp = _login(client, password="wrong")
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = _login(client, username="nobody")
    assert resp.status_code == 401


def test_get_current_user(client):
    _register(client)
    headers = _auth_header(client)
    resp = client.get("/users/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_get_current_user_no_token(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_get_current_user_invalid_token(client):
    resp = client.get("/users/me", headers={"Authorization": "Bearer badtoken"})
    assert resp.status_code == 401


def test_protected_item_create_requires_auth(client):
    resp = client.post("/items/", json={"name": "Widget"})
    assert resp.status_code == 401


def test_protected_item_create_with_auth(client):
    _register(client)
    headers = _auth_header(client)
    resp = client.post("/items/", json={"name": "Widget"}, headers=headers)
    assert resp.status_code == 201


def test_protected_category_create_requires_auth(client):
    resp = client.post("/categories/", json={"name": "Books"})
    assert resp.status_code == 401


def test_protected_category_create_with_auth(client):
    _register(client)
    headers = _auth_header(client)
    resp = client.post("/categories/", json={"name": "Books"}, headers=headers)
    assert resp.status_code == 201


def test_public_endpoints_no_auth(client):
    assert client.get("/items/").status_code == 200
    assert client.get("/categories/").status_code == 200
    assert client.get("/health").status_code == 200
