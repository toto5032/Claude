def test_create_category(client, auth_header):
    response = client.post(
        "/categories/",
        json={"name": "Electronics", "description": "Electronic items"},
        headers=auth_header,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Electronics"
    assert data["description"] == "Electronic items"


def test_list_categories(client, auth_header):
    client.post("/categories/", json={"name": "Cat A"}, headers=auth_header)
    client.post("/categories/", json={"name": "Cat B"}, headers=auth_header)
    response = client.get("/categories/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_category(client, auth_header):
    create = client.post("/categories/", json={"name": "Books"}, headers=auth_header)
    cat_id = create.json()["id"]
    response = client.get(f"/categories/{cat_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Books"


def test_get_category_not_found(client):
    response = client.get("/categories/999")
    assert response.status_code == 404


def test_update_category(client, auth_header):
    create = client.post("/categories/", json={"name": "Old Name"}, headers=auth_header)
    cat_id = create.json()["id"]
    response = client.patch(
        f"/categories/{cat_id}", json={"name": "New Name"}, headers=auth_header
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_delete_category(client, auth_header):
    create = client.post(
        "/categories/", json={"name": "To Delete"}, headers=auth_header
    )
    cat_id = create.json()["id"]
    response = client.delete(f"/categories/{cat_id}", headers=auth_header)
    assert response.status_code == 204
    response = client.get(f"/categories/{cat_id}")
    assert response.status_code == 404


def test_create_item_with_category(client, auth_header):
    cat = client.post("/categories/", json={"name": "Tools"}, headers=auth_header)
    cat_id = cat.json()["id"]
    item = client.post(
        "/items/", json={"name": "Hammer", "category_id": cat_id}, headers=auth_header
    )
    assert item.status_code == 201
    assert item.json()["category_id"] == cat_id
