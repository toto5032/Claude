def test_home_page(client):
    resp = client.get("/pages/", follow_redirects=False)
    assert resp.status_code == 200


def test_login_page(client):
    resp = client.get("/pages/login")
    assert resp.status_code == 200
    assert "Login" in resp.text


def test_register_page(client):
    resp = client.get("/pages/register")
    assert resp.status_code == 200
    assert "Register" in resp.text


def test_items_page_public(client):
    resp = client.get("/pages/items")
    assert resp.status_code == 200
    assert "Items" in resp.text


def test_categories_page_public(client):
    resp = client.get("/pages/categories")
    assert resp.status_code == 200
    assert "Categories" in resp.text


def test_login_flow(client):
    # Register
    client.post(
        "/pages/register",
        data={"username": "webuser", "email": "web@test.com", "password": "pass123"},
        follow_redirects=False,
    )
    # Login
    resp = client.post(
        "/pages/login",
        data={"username": "webuser", "password": "pass123"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "access_token" in resp.cookies


def test_login_invalid(client):
    resp = client.post(
        "/pages/login",
        data={"username": "nobody", "password": "wrong"},
    )
    assert resp.status_code == 200
    assert "Invalid credentials" in resp.text


def test_crud_item_via_pages(client):
    # Register and get cookie
    resp = client.post(
        "/pages/register",
        data={"username": "cruduser", "email": "crud@test.com", "password": "pass"},
        follow_redirects=False,
    )
    cookies = resp.cookies

    # Create item
    resp = client.post(
        "/pages/items/new",
        data={"name": "Page Item", "description": "desc", "category_id": ""},
        cookies=cookies,
        follow_redirects=False,
    )
    assert resp.status_code == 303

    # Verify item appears
    resp = client.get("/pages/items", cookies=cookies)
    assert "Page Item" in resp.text


def test_crud_category_via_pages(client):
    resp = client.post(
        "/pages/register",
        data={"username": "catuser", "email": "cat@test.com", "password": "pass"},
        follow_redirects=False,
    )
    cookies = resp.cookies

    resp = client.post(
        "/pages/categories/new",
        data={"name": "Page Cat", "description": ""},
        cookies=cookies,
        follow_redirects=False,
    )
    assert resp.status_code == 303

    resp = client.get("/pages/categories", cookies=cookies)
    assert "Page Cat" in resp.text


def test_root_redirects(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 307
