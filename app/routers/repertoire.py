from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.song import Song, SongComment, SongFanVote, SongVote
from app.models.user import User
from app.schemas.song import (
    SongCommentCreate,
    SongCommentResponse,
    SongCreate,
    SongResponse,
    SongUpdate,
)
from app.youtube import extract_video_id, get_thumbnail_url

router = APIRouter(prefix="/repertoire", tags=["repertoire"])

VALID_STATUSES = {"candidate", "practicing", "ready", "archived"}


def _song_to_response(song: Song, db: Session) -> SongResponse:
    member_votes = (
        db.query(SongVote)
        .filter(SongVote.song_id == song.id, SongVote.vote_type == "up")
        .count()
    )
    fan_votes = db.query(SongFanVote).filter(SongFanVote.song_id == song.id).count()
    return SongResponse(
        id=song.id,
        title=song.title,
        artist=song.artist,
        youtube_url=song.youtube_url,
        youtube_video_id=song.youtube_video_id,
        thumbnail_url=song.thumbnail_url,
        genre=song.genre,
        status=song.status,
        reason=song.reason,
        suggested_by_id=song.suggested_by_id,
        created_at=song.created_at,
        member_vote_count=member_votes,
        fan_vote_count=fan_votes,
    )


# ── Song CRUD ──


@router.get("/", response_model=list[SongResponse])
def list_songs(
    status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[SongResponse]:
    query = db.query(Song)
    if status and status in VALID_STATUSES:
        query = query.filter(Song.status == status)
    songs = query.order_by(Song.created_at.desc()).all()
    return [_song_to_response(s, db) for s in songs]


@router.get("/{song_id}", response_model=SongResponse)
def get_song(song_id: int, db: Session = Depends(get_db)) -> SongResponse:
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return _song_to_response(song, db)


@router.post("/", response_model=SongResponse, status_code=201)
def suggest_song(
    song_in: SongCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongResponse:
    video_id = extract_video_id(song_in.youtube_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    song = Song(
        title=song_in.title,
        artist=song_in.artist,
        youtube_url=song_in.youtube_url,
        youtube_video_id=video_id,
        thumbnail_url=get_thumbnail_url(video_id),
        genre=song_in.genre,
        reason=song_in.reason,
        suggested_by_id=current_user.id,
    )
    db.add(song)
    db.commit()
    db.refresh(song)
    return _song_to_response(song, db)


@router.patch("/{song_id}", response_model=SongResponse)
def update_song(
    song_id: int,
    song_in: SongUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongResponse:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    for field, value in song_in.model_dump(exclude_unset=True).items():
        if field == "status" and value not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status: {value}")
        setattr(song, field, value)
    db.commit()
    db.refresh(song)
    return _song_to_response(song, db)


@router.delete("/{song_id}", status_code=204)
def delete_song(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    db.delete(song)
    db.commit()


# ── Member Vote ──


@router.post("/{song_id}/vote", status_code=200)
def toggle_member_vote(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    if current_user.role not in ("admin", "member"):
        raise HTTPException(status_code=403, detail="Members only")
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    existing = (
        db.query(SongVote)
        .filter(SongVote.song_id == song_id, SongVote.user_id == current_user.id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "vote_removed"}
    vote = SongVote(song_id=song_id, user_id=current_user.id, vote_type="up")
    db.add(vote)
    db.commit()
    return {"status": "voted"}


# ── Fan Vote ──


@router.post("/{song_id}/fan-vote", status_code=200)
def toggle_fan_vote(
    song_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    existing = (
        db.query(SongFanVote)
        .filter(SongFanVote.song_id == song_id, SongFanVote.user_id == current_user.id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "vote_removed"}
    vote = SongFanVote(song_id=song_id, user_id=current_user.id)
    db.add(vote)
    db.commit()
    return {"status": "voted"}


# ── Song Comments ──


@router.get("/{song_id}/comments", response_model=list[SongCommentResponse])
def list_song_comments(
    song_id: int, db: Session = Depends(get_db)
) -> list[SongComment]:
    return list(
        db.query(SongComment)
        .filter(SongComment.song_id == song_id)
        .order_by(SongComment.created_at.desc())
        .all()
    )


@router.post("/{song_id}/comments", response_model=SongCommentResponse, status_code=201)
def create_song_comment(
    song_id: int,
    comment_in: SongCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SongComment:
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    comment = SongComment(
        content=comment_in.content,
        song_id=song_id,
        user_id=current_user.id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/comments/{comment_id}", status_code=204)
def delete_song_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    comment = db.query(SongComment).filter(SongComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(comment)
    db.commit()
