"""Phase 2 Tests: Repertoire (Song CRUD + YouTube + Voting + Comments)."""

YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
SONG_DATA = {
    "title": "Never Gonna Give You Up",
    "artist": "Rick Astley",
    "youtube_url": YOUTUBE_URL,
    "genre": "pop",
    "reason": "명곡이라서",
}


# ── YouTube URL Parser ──


class TestYouTubeParser:
    def test_standard_url(self):
        from app.youtube import extract_video_id, get_embed_url, get_thumbnail_url

        vid = extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"
        assert "dQw4w9WgXcQ" in get_thumbnail_url(vid)
        assert "dQw4w9WgXcQ" in get_embed_url(vid)

    def test_short_url(self):
        from app.youtube import extract_video_id

        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_embed_url(self):
        from app.youtube import extract_video_id

        vid = extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        from app.youtube import extract_video_id

        vid = extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ")
        assert vid == "dQw4w9WgXcQ"

    def test_invalid_url_returns_none(self):
        from app.youtube import extract_video_id

        assert extract_video_id("https://example.com") is None
        assert extract_video_id("not a url") is None


# ── Song CRUD ──


class TestSongCreate:
    def test_authenticated_user_can_suggest_song(self, client, fan_header):
        """로그인한 사용자는 곡을 추천할 수 있다."""
        resp = client.post("/repertoire/", json=SONG_DATA, headers=fan_header)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Never Gonna Give You Up"
        assert data["youtube_video_id"] == "dQw4w9WgXcQ"
        assert data["status"] == "candidate"
        assert data["thumbnail_url"] is not None

    def test_unauthenticated_cannot_suggest(self, client):
        """비로그인은 곡 추천 불가 (401)."""
        resp = client.post("/repertoire/", json=SONG_DATA)
        assert resp.status_code == 401

    def test_invalid_youtube_url_rejected(self, client, fan_header):
        """유효하지 않은 YouTube URL은 400 에러."""
        data = {**SONG_DATA, "youtube_url": "https://example.com/notube"}
        resp = client.post("/repertoire/", json=data, headers=fan_header)
        assert resp.status_code == 400


class TestSongList:
    def test_list_songs_empty(self, client):
        """빈 곡 목록 조회."""
        resp = client.get("/repertoire/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_songs_filter_by_status(self, client, admin_header):
        """상태별 필터링이 동작해야 한다."""
        # 곡 생성 후 상태 변경
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        client.patch(
            f"/repertoire/{song_id}",
            json={"status": "ready"},
            headers=admin_header,
        )
        # ready 필터
        resp = client.get("/repertoire/?status=ready")
        assert len(resp.json()) == 1
        # candidate 필터 — 비어있어야 함
        resp = client.get("/repertoire/?status=candidate")
        assert len(resp.json()) == 0


class TestSongGet:
    def test_get_song_by_id(self, client, fan_header):
        """ID로 곡 상세 조회."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=fan_header)
        song_id = create.json()["id"]
        resp = client.get(f"/repertoire/{song_id}")
        assert resp.status_code == 200
        assert resp.json()["artist"] == "Rick Astley"

    def test_get_song_not_found(self, client):
        """존재하지 않는 곡 조회 시 404."""
        resp = client.get("/repertoire/9999")
        assert resp.status_code == 404


class TestSongUpdate:
    def test_admin_can_update_song(self, client, admin_header):
        """관리자는 곡 정보/상태를 변경할 수 있다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        resp = client.patch(
            f"/repertoire/{song_id}",
            json={"status": "practicing", "genre": "rock"},
            headers=admin_header,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "practicing"
        assert resp.json()["genre"] == "rock"

    def test_fan_cannot_update_song(self, client, admin_header, fan_header):
        """팬은 곡을 수정할 수 없다 (403)."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        resp = client.patch(
            f"/repertoire/{song_id}",
            json={"status": "ready"},
            headers=fan_header,
        )
        assert resp.status_code == 403

    def test_invalid_status_rejected(self, client, admin_header):
        """유효하지 않은 상태값은 400."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        resp = client.patch(
            f"/repertoire/{song_id}",
            json={"status": "invalid_status"},
            headers=admin_header,
        )
        assert resp.status_code == 400


class TestSongDelete:
    def test_admin_can_delete_song(self, client, admin_header):
        """관리자는 곡을 삭제할 수 있다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        resp = client.delete(f"/repertoire/{song_id}", headers=admin_header)
        assert resp.status_code == 204
        assert client.get(f"/repertoire/{song_id}").status_code == 404

    def test_fan_cannot_delete_song(self, client, admin_header, fan_header):
        """팬은 곡을 삭제할 수 없다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        resp = client.delete(f"/repertoire/{song_id}", headers=fan_header)
        assert resp.status_code == 403


# ── Member Vote (toggle) ──


class TestMemberVote:
    def test_member_can_vote(self, client, admin_header, member_header):
        """멤버는 곡에 투표할 수 있다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        resp = client.post(f"/repertoire/{song_id}/vote", headers=member_header)
        assert resp.status_code == 200
        assert resp.json()["status"] == "voted"

    def test_member_vote_toggle(self, client, admin_header, member_header):
        """같은 멤버가 다시 투표하면 취소된다 (토글)."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        client.post(f"/repertoire/{song_id}/vote", headers=member_header)
        resp = client.post(f"/repertoire/{song_id}/vote", headers=member_header)
        assert resp.json()["status"] == "vote_removed"

    def test_fan_cannot_member_vote(self, client, admin_header, fan_header):
        """팬은 멤버 투표를 할 수 없다 (403)."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        resp = client.post(f"/repertoire/{song_id}/vote", headers=fan_header)
        assert resp.status_code == 403

    def test_vote_count_reflected(self, client, admin_header, member_header):
        """투표 수가 곡 조회에 반영되어야 한다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        client.post(f"/repertoire/{song_id}/vote", headers=member_header)
        resp = client.get(f"/repertoire/{song_id}")
        assert resp.json()["member_vote_count"] == 1


# ── Fan Vote ──


class TestFanVote:
    def test_fan_can_vote(self, client, admin_header, fan_header):
        """팬은 팬 투표를 할 수 있다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        resp = client.post(f"/repertoire/{song_id}/fan-vote", headers=fan_header)
        assert resp.status_code == 200
        assert resp.json()["status"] == "voted"

    def test_fan_vote_toggle(self, client, admin_header, fan_header):
        """팬 투표도 토글 방식이다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        client.post(f"/repertoire/{song_id}/fan-vote", headers=fan_header)
        resp = client.post(f"/repertoire/{song_id}/fan-vote", headers=fan_header)
        assert resp.json()["status"] == "vote_removed"

    def test_fan_vote_count_reflected(self, client, admin_header, fan_header):
        """팬 투표 수가 곡 조회에 반영되어야 한다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        client.post(f"/repertoire/{song_id}/fan-vote", headers=fan_header)
        resp = client.get(f"/repertoire/{song_id}")
        assert resp.json()["fan_vote_count"] == 1


# ── Song Comments ──


class TestSongComments:
    def test_create_comment(self, client, admin_header, fan_header):
        """로그인 사용자는 댓글을 작성할 수 있다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        resp = client.post(
            f"/repertoire/{song_id}/comments",
            json={"content": "좋은 곡이네요!"},
            headers=fan_header,
        )
        assert resp.status_code == 201
        assert resp.json()["content"] == "좋은 곡이네요!"

    def test_list_comments(self, client, admin_header, fan_header):
        """곡의 댓글 목록을 조회할 수 있다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        client.post(
            f"/repertoire/{song_id}/comments",
            json={"content": "댓글1"},
            headers=fan_header,
        )
        client.post(
            f"/repertoire/{song_id}/comments",
            json={"content": "댓글2"},
            headers=fan_header,
        )
        resp = client.get(f"/repertoire/{song_id}/comments")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_owner_can_delete_comment(self, client, admin_header, fan_header):
        """댓글 작성자는 자신의 댓글을 삭제할 수 있다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        comment = client.post(
            f"/repertoire/{song_id}/comments",
            json={"content": "삭제할 댓글"},
            headers=fan_header,
        )
        comment_id = comment.json()["id"]
        resp = client.delete(
            f"/repertoire/comments/{comment_id}", headers=fan_header
        )
        assert resp.status_code == 204

    def test_admin_can_delete_any_comment(self, client, admin_header, fan_header):
        """관리자는 다른 사람의 댓글도 삭제할 수 있다."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        comment = client.post(
            f"/repertoire/{song_id}/comments",
            json={"content": "팬 댓글"},
            headers=fan_header,
        )
        comment_id = comment.json()["id"]
        resp = client.delete(
            f"/repertoire/comments/{comment_id}", headers=admin_header
        )
        assert resp.status_code == 204

    def test_other_user_cannot_delete_comment(
        self, client, admin_header, fan_header, member_header
    ):
        """다른 사용자는 남의 댓글을 삭제할 수 없다 (403)."""
        create = client.post("/repertoire/", json=SONG_DATA, headers=admin_header)
        song_id = create.json()["id"]
        comment = client.post(
            f"/repertoire/{song_id}/comments",
            json={"content": "팬 댓글"},
            headers=fan_header,
        )
        comment_id = comment.json()["id"]
        resp = client.delete(
            f"/repertoire/comments/{comment_id}", headers=member_header
        )
        assert resp.status_code == 403

    def test_comment_on_nonexistent_song(self, client, fan_header):
        """존재하지 않는 곡에 댓글 작성 시 404."""
        resp = client.post(
            "/repertoire/9999/comments",
            json={"content": "없는 곡"},
            headers=fan_header,
        )
        assert resp.status_code == 404
