def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_item(client, auth_header):
    payload = {"name": "Test Item", "description": "A test"}
    response = client.post("/items/", json=payload, headers=auth_header)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "A test"
    assert data["is_active"] is True


def test_list_items(client, auth_header):
    client.post("/items/", json={"name": "Item 1"}, headers=auth_header)
    client.post("/items/", json={"name": "Item 2"}, headers=auth_header)
    response = client.get("/items/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_item(client, auth_header):
    create = client.post("/items/", json={"name": "Test"}, headers=auth_header)
    item_id = create.json()["id"]
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test"


def test_get_item_not_found(client):
    response = client.get("/items/999")
    assert response.status_code == 404


def test_update_item(client, auth_header):
    create = client.post("/items/", json={"name": "Original"}, headers=auth_header)
    item_id = create.json()["id"]
    response = client.patch(
        f"/items/{item_id}", json={"name": "Updated"}, headers=auth_header
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


def test_delete_item(client, auth_header):
    create = client.post("/items/", json={"name": "To Delete"}, headers=auth_header)
    item_id = create.json()["id"]
    response = client.delete(f"/items/{item_id}", headers=auth_header)
    assert response.status_code == 204
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 404
