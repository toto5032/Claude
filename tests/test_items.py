def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_item(client):
    payload = {"name": "Test Item", "description": "A test"}
    response = client.post("/items/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "A test"
    assert data["is_active"] is True


def test_list_items(client):
    client.post("/items/", json={"name": "Item 1"})
    client.post("/items/", json={"name": "Item 2"})
    response = client.get("/items/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_item(client):
    create = client.post("/items/", json={"name": "Test"})
    item_id = create.json()["id"]
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test"


def test_get_item_not_found(client):
    response = client.get("/items/999")
    assert response.status_code == 404


def test_update_item(client):
    create = client.post("/items/", json={"name": "Original"})
    item_id = create.json()["id"]
    response = client.patch(f"/items/{item_id}", json={"name": "Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


def test_delete_item(client):
    create = client.post("/items/", json={"name": "To Delete"})
    item_id = create.json()["id"]
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 204
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 404
