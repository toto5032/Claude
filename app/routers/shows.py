from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.show import SetlistItem, Show
from app.models.song import Song
from app.models.user import User
from app.schemas.show import (
    SetlistItemCreate,
    SetlistItemResponse,
    ShowCreate,
    ShowResponse,
    ShowUpdate,
)

router = APIRouter(prefix="/shows", tags=["shows"])

VALID_STATUSES = {"upcoming", "completed", "cancelled"}


# ── Show CRUD ──


@router.get("/", response_model=list[ShowResponse])
def list_shows(
    status: str | None = None,
    db: Session = Depends(get_db),
) -> list[Show]:
    query = db.query(Show)
    if status and status in VALID_STATUSES:
        query = query.filter(Show.status == status)
    return list(query.order_by(Show.show_date.desc()).all())


@router.get("/{show_id}", response_model=ShowResponse)
def get_show(show_id: int, db: Session = Depends(get_db)) -> Show:
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show


@router.post("/", response_model=ShowResponse, status_code=201)
def create_show(
    show_in: ShowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Show:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    show = Show(**show_in.model_dump(), created_by_id=current_user.id)
    db.add(show)
    db.commit()
    db.refresh(show)
    return show


@router.patch("/{show_id}", response_model=ShowResponse)
def update_show(
    show_id: int,
    show_in: ShowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Show:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    for field, value in show_in.model_dump(exclude_unset=True).items():
        if field == "status" and value not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status: {value}")
        setattr(show, field, value)
    db.commit()
    db.refresh(show)
    return show


@router.delete("/{show_id}", status_code=204)
def delete_show(
    show_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    db.delete(show)
    db.commit()


# ── Setlist ──


@router.get("/{show_id}/setlist", response_model=list[SetlistItemResponse])
def get_setlist(show_id: int, db: Session = Depends(get_db)) -> list[dict]:
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    items = (
        db.query(SetlistItem)
        .filter(SetlistItem.show_id == show_id)
        .order_by(SetlistItem.play_order)
        .all()
    )
    result = []
    for item in items:
        song = db.query(Song).filter(Song.id == item.song_id).first()
        result.append(
            {
                "id": item.id,
                "show_id": item.show_id,
                "song_id": item.song_id,
                "play_order": item.play_order,
                "notes": item.notes,
                "song_title": song.title if song else None,
                "song_artist": song.artist if song else None,
            }
        )
    return result


@router.post("/{show_id}/setlist", response_model=SetlistItemResponse, status_code=201)
def add_setlist_item(
    show_id: int,
    item_in: SetlistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    show = db.query(Show).filter(Show.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    song = db.query(Song).filter(Song.id == item_in.song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    item = SetlistItem(
        show_id=show_id,
        song_id=item_in.song_id,
        play_order=item_in.play_order,
        notes=item_in.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "id": item.id,
        "show_id": item.show_id,
        "song_id": item.song_id,
        "play_order": item.play_order,
        "notes": item.notes,
        "song_title": song.title,
        "song_artist": song.artist,
    }


@router.delete("/{show_id}/setlist/{item_id}", status_code=204)
def remove_setlist_item(
    show_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    item = (
        db.query(SetlistItem)
        .filter(SetlistItem.id == item_id, SetlistItem.show_id == show_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Setlist item not found")
    db.delete(item)
    db.commit()
