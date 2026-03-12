"""Phase 3 Tests: Show management + Setlist system."""

YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
SONG_DATA = {
    "title": "Test Song",
    "artist": "Test Artist",
    "youtube_url": YOUTUBE_URL,
}
SHOW_DATA = {
    "title": "Spring Festival",
    "venue": "홍대 라이브홀",
    "address": "서울 마포구",
    "show_date": "2026-04-20",
    "show_time": "19:00:00",
    "description": "봄 페스티벌 공연",
    "ticket_price": "20000원",
    "status": "upcoming",
}


# ── Show CRUD ──


class TestShowCreate:
    def test_admin_can_create_show(self, client, admin_header):
        """관리자는 공연을 생성할 수 있다."""
        resp = client.post("/shows/", json=SHOW_DATA, headers=admin_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Spring Festival"
        assert data["venue"] == "홍대 라이브홀"
        assert data["status"] == "upcoming"

    def test_fan_cannot_create_show(self, client, fan_header):
        """팬은 공연을 생성할 수 없다 (403)."""
        resp = client.post("/shows/", json=SHOW_DATA, headers=fan_header)
        assert resp.status_code == 403

    def test_member_cannot_create_show(self, client, member_header):
        """일반 멤버는 공연을 생성할 수 없다 (403)."""
        resp = client.post("/shows/", json=SHOW_DATA, headers=member_header)
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create_show(self, client):
        """비로그인은 공연 생성 불가 (401)."""
        resp = client.post("/shows/", json=SHOW_DATA)
        assert resp.status_code == 401


class TestShowList:
    def test_list_shows_empty(self, client):
        """빈 공연 목록 조회."""
        resp = client.get("/shows/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_shows_filter_by_status(self, client, admin_header):
        """상태별 필터링."""
        client.post("/shows/", json=SHOW_DATA, headers=admin_header)
        client.post(
            "/shows/",
            json={**SHOW_DATA, "title": "Past Show", "status": "completed"},
            headers=admin_header,
        )
        resp = client.get("/shows/?status=upcoming")
        assert len(resp.json()) == 1
        assert resp.json()[0]["title"] == "Spring Festival"


class TestShowGet:
    def test_get_show_by_id(self, client, admin_header):
        """ID로 공연 상세 조회."""
        create = client.post("/shows/", json=SHOW_DATA, headers=admin_header)
        show_id = create.json()["id"]
        resp = client.get(f"/shows/{show_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Spring Festival"

    def test_get_show_not_found(self, client):
        """존재하지 않는 공연 조회 시 404."""
        resp = client.get("/shows/9999")
        assert resp.status_code == 404


class TestShowUpdate:
    def test_admin_can_update_show(self, client, admin_header):
        """관리자는 공연 정보를 수정할 수 있다."""
        create = client.post("/shows/", json=SHOW_DATA, headers=admin_header)
        show_id = create.json()["id"]
        resp = client.patch(
            f"/shows/{show_id}",
            json={"title": "Updated Festival", "status": "completed"},
            headers=admin_header,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Festival"
        assert resp.json()["status"] == "completed"

    def test_fan_cannot_update_show(self, client, admin_header, fan_header):
        """팬은 공연을 수정할 수 없다."""
        create = client.post("/shows/", json=SHOW_DATA, headers=admin_header)
        show_id = create.json()["id"]
        resp = client.patch(
            f"/shows/{show_id}",
            json={"title": "해킹"},
            headers=fan_header,
        )
        assert resp.status_code == 403

    def test_invalid_status_rejected(self, client, admin_header):
        """유효하지 않은 공연 상태값은 400."""
        create = client.post("/shows/", json=SHOW_DATA, headers=admin_header)
        show_id = create.json()["id"]
        resp = client.patch(
            f"/shows/{show_id}",
            json={"status": "invalid"},
            headers=admin_header,
        )
        assert resp.status_code == 400


class TestShowDelete:
    def test_admin_can_delete_show(self, client, admin_header):
        """관리자는 공연을 삭제할 수 있다."""
        create = client.post("/shows/", json=SHOW_DATA, headers=admin_header)
        show_id = create.json()["id"]
        resp = client.delete(f"/shows/{show_id}", headers=admin_header)
        assert resp.status_code == 204
        assert client.get(f"/shows/{show_id}").status_code == 404

    def test_fan_cannot_delete_show(self, client, admin_header, fan_header):
        """팬은 공연을 삭제할 수 없다."""
        create = client.post("/shows/", json=SHOW_DATA, headers=admin_header)
        show_id = create.json()["id"]
        resp = client.delete(f"/shows/{show_id}", headers=fan_header)
        assert resp.status_code == 403


# ── Setlist ──


class TestSetlist:
    def _create_show_and_song(self, client, admin_header):
        """헬퍼: 공연과 곡을 생성하고 ID를 반환."""
        show = client.post("/shows/", json=SHOW_DATA, headers=admin_header)
        song = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        return show.json()["id"], song.json()["id"]

    def test_add_song_to_setlist(self, client, admin_header):
        """관리자는 세트리스트에 곡을 추가할 수 있다."""
        show_id, song_id = self._create_show_and_song(client, admin_header)
        resp = client.post(
            f"/shows/{show_id}/setlist",
            json={"song_id": song_id, "play_order": 1, "notes": "오프닝"},
            headers=admin_header,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["song_id"] == song_id
        assert data["play_order"] == 1
        assert data["song_title"] == "Test Song"

    def test_get_setlist(self, client, admin_header):
        """세트리스트 조회가 play_order 순으로 정렬되어야 한다."""
        show_id, song_id = self._create_show_and_song(client, admin_header)
        # 두 번째 곡 추가
        song2 = client.post(
            "/repertoire/",
            json={**SONG_DATA, "title": "Second Song"},
            headers=admin_header,
        )
        song2_id = song2.json()["id"]
        client.post(
            f"/shows/{show_id}/setlist",
            json={"song_id": song2_id, "play_order": 1},
            headers=admin_header,
        )
        client.post(
            f"/shows/{show_id}/setlist",
            json={"song_id": song_id, "play_order": 2},
            headers=admin_header,
        )
        resp = client.get(f"/shows/{show_id}/setlist")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 2
        assert items[0]["play_order"] <= items[1]["play_order"]

    def test_remove_setlist_item(self, client, admin_header):
        """관리자는 세트리스트에서 곡을 제거할 수 있다."""
        show_id, song_id = self._create_show_and_song(client, admin_header)
        add = client.post(
            f"/shows/{show_id}/setlist",
            json={"song_id": song_id, "play_order": 1},
            headers=admin_header,
        )
        item_id = add.json()["id"]
        resp = client.delete(
            f"/shows/{show_id}/setlist/{item_id}", headers=admin_header
        )
        assert resp.status_code == 204
        # 삭제 후 세트리스트 비어있어야 함
        setlist = client.get(f"/shows/{show_id}/setlist")
        assert len(setlist.json()) == 0

    def test_fan_cannot_modify_setlist(self, client, admin_header, fan_header):
        """팬은 세트리스트를 수정할 수 없다."""
        show_id, song_id = self._create_show_and_song(client, admin_header)
        resp = client.post(
            f"/shows/{show_id}/setlist",
            json={"song_id": song_id, "play_order": 1},
            headers=fan_header,
        )
        assert resp.status_code == 403

    def test_setlist_with_nonexistent_show(self, client, admin_header):
        """존재하지 않는 공연의 세트리스트 조회 시 404."""
        resp = client.get("/shows/9999/setlist")
        assert resp.status_code == 404

    def test_setlist_with_nonexistent_song(self, client, admin_header):
        """존재하지 않는 곡을 세트리스트에 추가 시 404."""
        show = client.post("/shows/", json=SHOW_DATA, headers=admin_header)
        show_id = show.json()["id"]
        resp = client.post(
            f"/shows/{show_id}/setlist",
            json={"song_id": 9999, "play_order": 1},
            headers=admin_header,
        )
        assert resp.status_code == 404
