from datetime import datetime

from pydantic import BaseModel


class SongCreate(BaseModel):
    title: str
    artist: str
    youtube_url: str
    genre: str | None = None
    reason: str | None = None


class SongUpdate(BaseModel):
    title: str | None = None
    artist: str | None = None
    genre: str | None = None
    status: str | None = None
    reason: str | None = None


class SongResponse(BaseModel):
    id: int
    title: str
    artist: str
    youtube_url: str
    youtube_video_id: str
    thumbnail_url: str | None = None
    genre: str | None = None
    status: str
    reason: str | None = None
    suggested_by_id: int | None = None
    created_at: datetime
    member_vote_count: int = 0
    fan_vote_count: int = 0

    model_config = {"from_attributes": True}


class SongCommentCreate(BaseModel):
    content: str


class SongCommentResponse(BaseModel):
    id: int
    content: str
    song_id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
