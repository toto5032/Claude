"""Phase 1 Tests: User role extension + Member CRUD API."""


# ── User Role Extension ──


class TestUserRoles:
    def test_register_default_role_is_fan(self, client):
        """신규 가입 시 기본 역할은 fan이어야 한다."""
        client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "testpass",
            },
        )
        resp = client.post(
            "/auth/login",
            data={"username": "newuser", "password": "testpass"},
        )
        token = resp.json()["access_token"]
        me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["role"] == "fan"

    def test_user_has_extended_fields(self, client, db):
        """User 모델에 display_name, bio, avatar_url 필드가 있어야 한다."""
        from app.models.user import User

        client.post(
            "/auth/register",
            json={
                "username": "extuser",
                "email": "ext@test.com",
                "password": "testpass",
            },
        )
        user = db.query(User).filter(User.username == "extuser").first()
        assert hasattr(user, "display_name")
        assert hasattr(user, "bio")
        assert hasattr(user, "avatar_url")
        assert user.role == "fan"


# ── Member CRUD (Admin Only Write) ──


MEMBER_DATA = {
    "name": "김기타",
    "role_in_band": "기타",
    "bio": "리드 기타 담당",
    "sort_order": 1,
}


class TestMemberList:
    def test_list_members_empty(self, client):
        """멤버 목록 조회 (빈 목록)."""
        resp = client.get("/members/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_members_returns_sorted(self, client, admin_header):
        """멤버 목록이 sort_order 순으로 정렬되어야 한다."""
        client.post(
            "/members/",
            json={**MEMBER_DATA, "name": "드러머", "sort_order": 2},
            headers=admin_header,
        )
        client.post(
            "/members/",
            json={**MEMBER_DATA, "name": "기타", "sort_order": 1},
            headers=admin_header,
        )
        client.post(
            "/members/",
            json={**MEMBER_DATA, "name": "보컬", "sort_order": 0},
            headers=admin_header,
        )
        resp = client.get("/members/")
        names = [m["name"] for m in resp.json()]
        assert names == ["보컬", "기타", "드러머"]


class TestMemberCreate:
    def test_admin_can_create_member(self, client, admin_header):
        """관리자는 멤버를 생성할 수 있다."""
        resp = client.post("/members/", json=MEMBER_DATA, headers=admin_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "김기타"
        assert data["role_in_band"] == "기타"

    def test_fan_cannot_create_member(self, client, fan_header):
        """팬은 멤버를 생성할 수 없다 (403)."""
        resp = client.post("/members/", json=MEMBER_DATA, headers=fan_header)
        assert resp.status_code == 403

    def test_member_cannot_create_member(self, client, member_header):
        """일반 멤버는 멤버를 생성할 수 없다 (403)."""
        resp = client.post("/members/", json=MEMBER_DATA, headers=member_header)
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create_member(self, client):
        """비로그인 사용자는 멤버를 생성할 수 없다 (401)."""
        resp = client.post("/members/", json=MEMBER_DATA)
        assert resp.status_code == 401


class TestMemberGet:
    def test_get_member_by_id(self, client, admin_header):
        """ID로 멤버를 조회할 수 있다."""
        create = client.post("/members/", json=MEMBER_DATA, headers=admin_header)
        member_id = create.json()["id"]
        resp = client.get(f"/members/{member_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "김기타"

    def test_get_member_not_found(self, client):
        """존재하지 않는 멤버 조회 시 404."""
        resp = client.get("/members/9999")
        assert resp.status_code == 404


class TestMemberUpdate:
    def test_admin_can_update_member(self, client, admin_header):
        """관리자는 멤버 정보를 수정할 수 있다."""
        create = client.post("/members/", json=MEMBER_DATA, headers=admin_header)
        member_id = create.json()["id"]
        resp = client.patch(
            f"/members/{member_id}",
            json={"name": "박기타", "bio": "수정됨"},
            headers=admin_header,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "박기타"
        assert resp.json()["bio"] == "수정됨"

    def test_fan_cannot_update_member(self, client, admin_header, fan_header):
        """팬은 멤버를 수정할 수 없다."""
        create = client.post("/members/", json=MEMBER_DATA, headers=admin_header)
        member_id = create.json()["id"]
        resp = client.patch(
            f"/members/{member_id}",
            json={"name": "해킹"},
            headers=fan_header,
        )
        assert resp.status_code == 403


class TestMemberDelete:
    def test_admin_can_delete_member(self, client, admin_header):
        """관리자는 멤버를 삭제할 수 있다."""
        create = client.post("/members/", json=MEMBER_DATA, headers=admin_header)
        member_id = create.json()["id"]
        resp = client.delete(f"/members/{member_id}", headers=admin_header)
        assert resp.status_code == 204
        # 삭제 후 조회하면 404
        assert client.get(f"/members/{member_id}").status_code == 404

    def test_fan_cannot_delete_member(self, client, admin_header, fan_header):
        """팬은 멤버를 삭제할 수 없다."""
        create = client.post("/members/", json=MEMBER_DATA, headers=admin_header)
        member_id = create.json()["id"]
        resp = client.delete(f"/members/{member_id}", headers=fan_header)
        assert resp.status_code == 403
