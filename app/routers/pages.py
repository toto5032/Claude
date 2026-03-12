from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt  # type: ignore[import-untyped]
from sqlalchemy.orm import Session, joinedload
from starlette.responses import Response

from app.auth import ALGORITHM, create_access_token, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.models.category import Category
from app.models.item import Item
from app.models.member import Member
from app.models.song import Song, SongComment, SongFanVote, SongVote
from app.models.user import User
from app.youtube import extract_video_id, get_thumbnail_url

router = APIRouter(prefix="/pages", tags=["pages"])
templates = Jinja2Templates(directory="app/templates")


def _current_user(request: Request, db: Session) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.username == username).first()


def _ctx(request: Request, db: Session, **kwargs: object) -> dict[str, object]:
    user = _current_user(request, db)
    return {"user": user, **kwargs}


def _render(request: Request, name: str, db: Session, **kwargs: object) -> HTMLResponse:
    return templates.TemplateResponse(request, name, _ctx(request, db, **kwargs))


# ── Home ──


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    members = db.query(Member).order_by(Member.sort_order).all()
    candidates_raw = (
        db.query(Song)
        .filter(Song.status == "candidate")
        .order_by(Song.created_at.desc())
        .limit(3)
        .all()
    )
    candidate_songs = []
    for s in candidates_raw:
        fan_votes = db.query(SongFanVote).filter(SongFanVote.song_id == s.id).count()
        candidate_songs.append(
            {
                "id": s.id,
                "title": s.title,
                "artist": s.artist,
                "thumbnail_url": s.thumbnail_url,
                "fan_vote_count": fan_votes,
            }
        )
    return _render(
        request, "home.html", db, members=members, candidate_songs=candidate_songs
    )


# ── Members ──


@router.get("/members", response_class=HTMLResponse)
def members_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    members = db.query(Member).order_by(Member.sort_order).all()
    return _render(request, "members.html", db, members=members)


# ── Auth ──


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return _render(request, "login.html", db)


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
) -> Response:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return _render(
            request,
            "login.html",
            db,
            flash_message="Invalid credentials",
            flash_type="error",
        )
    token = create_access_token(subject=user.username)
    response = RedirectResponse(url="/pages/items", status_code=303)
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return _render(request, "register.html", db)


@router.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    username: str = Form(),
    email: str = Form(),
    password: str = Form(),
    db: Session = Depends(get_db),
) -> Response:
    if db.query(User).filter(User.username == username).first():
        return _render(
            request,
            "register.html",
            db,
            flash_message="Username already taken",
            flash_type="error",
        )
    if db.query(User).filter(User.email == email).first():
        return _render(
            request,
            "register.html",
            db,
            flash_message="Email already registered",
            flash_type="error",
        )
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    token = create_access_token(subject=user.username)
    response = RedirectResponse(url="/pages/items", status_code=303)
    response.set_cookie("access_token", token, httponly=True, samesite="lax")
    return response


@router.get("/logout")
def logout() -> RedirectResponse:
    response = RedirectResponse(url="/pages/login", status_code=303)
    response.delete_cookie("access_token")
    return response


# ── Repertoire ──


@router.get("/repertoire", response_class=HTMLResponse)
def repertoire_list(
    request: Request,
    status: str | None = None,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    query = db.query(Song)
    if status and status in ("candidate", "practicing", "ready", "archived"):
        query = query.filter(Song.status == status)
    songs_raw = query.order_by(Song.created_at.desc()).all()
    songs = []
    for s in songs_raw:
        member_votes = (
            db.query(SongVote)
            .filter(SongVote.song_id == s.id, SongVote.vote_type == "up")
            .count()
        )
        fan_votes = db.query(SongFanVote).filter(SongFanVote.song_id == s.id).count()
        songs.append(
            {
                "id": s.id,
                "title": s.title,
                "artist": s.artist,
                "genre": s.genre,
                "status": s.status,
                "thumbnail_url": s.thumbnail_url,
                "member_vote_count": member_votes,
                "fan_vote_count": fan_votes,
            }
        )
    return _render(request, "repertoire.html", db, songs=songs, current_status=status)


@router.get("/repertoire/suggest", response_class=HTMLResponse)
def repertoire_suggest_page(
    request: Request, db: Session = Depends(get_db)
) -> Response:
    user = _current_user(request, db)
    if not user:
        return RedirectResponse(url="/pages/login", status_code=303)
    return _render(request, "repertoire_suggest.html", db)


@router.post("/repertoire/suggest")
def repertoire_suggest_submit(
    request: Request,
    youtube_url: str = Form(),
    title: str = Form(),
    artist: str = Form(),
    genre: str = Form(""),
    reason: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    user = _current_user(request, db)
    if not user:
        return RedirectResponse(url="/pages/login", status_code=303)
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return _render(
            request,
            "repertoire_suggest.html",
            db,
            flash_message="Invalid YouTube URL",
            flash_type="error",
        )
    song = Song(
        title=title,
        artist=artist,
        youtube_url=youtube_url,
        youtube_video_id=video_id,
        thumbnail_url=get_thumbnail_url(video_id),
        genre=genre or None,
        reason=reason or None,
        suggested_by_id=user.id,
    )
    db.add(song)
    db.commit()
    return RedirectResponse(url=f"/pages/repertoire/{song.id}", status_code=303)


@router.get("/repertoire/{song_id}", response_class=HTMLResponse)
def repertoire_detail(
    song_id: int, request: Request, db: Session = Depends(get_db)
) -> Response:
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        return RedirectResponse(url="/pages/repertoire", status_code=303)
    user = _current_user(request, db)
    member_vote_count = (
        db.query(SongVote)
        .filter(SongVote.song_id == song_id, SongVote.vote_type == "up")
        .count()
    )
    fan_vote_count = (
        db.query(SongFanVote).filter(SongFanVote.song_id == song_id).count()
    )
    user_voted = False
    user_fan_voted = False
    if user:
        user_voted = (
            db.query(SongVote)
            .filter(SongVote.song_id == song_id, SongVote.user_id == user.id)
            .first()
            is not None
        )
        user_fan_voted = (
            db.query(SongFanVote)
            .filter(SongFanVote.song_id == song_id, SongFanVote.user_id == user.id)
            .first()
            is not None
        )
    comments = (
        db.query(SongComment)
        .options(joinedload(SongComment.user))
        .filter(SongComment.song_id == song_id)
        .order_by(SongComment.created_at.desc())
        .all()
    )
    suggested_by_name = "Unknown"
    if song.suggested_by:
        suggested_by_name = song.suggested_by.display_name or song.suggested_by.username
    return _render(
        request,
        "repertoire_detail.html",
        db,
        song=song,
        member_vote_count=member_vote_count,
        fan_vote_count=fan_vote_count,
        user_voted=user_voted,
        user_fan_voted=user_fan_voted,
        comments=comments,
        suggested_by_name=suggested_by_name,
    )


@router.post("/repertoire/{song_id}/vote")
def repertoire_vote(
    song_id: int, request: Request, db: Session = Depends(get_db)
) -> RedirectResponse:
    user = _current_user(request, db)
    if not user or user.role not in ("admin", "member"):
        return RedirectResponse(url=f"/pages/repertoire/{song_id}", status_code=303)
    existing = (
        db.query(SongVote)
        .filter(SongVote.song_id == song_id, SongVote.user_id == user.id)
        .first()
    )
    if existing:
        db.delete(existing)
    else:
        db.add(SongVote(song_id=song_id, user_id=user.id, vote_type="up"))
    db.commit()
    return RedirectResponse(url=f"/pages/repertoire/{song_id}", status_code=303)


@router.post("/repertoire/{song_id}/fan-vote")
def repertoire_fan_vote(
    song_id: int, request: Request, db: Session = Depends(get_db)
) -> RedirectResponse:
    user = _current_user(request, db)
    if not user:
        return RedirectResponse(url="/pages/login", status_code=303)
    existing = (
        db.query(SongFanVote)
        .filter(SongFanVote.song_id == song_id, SongFanVote.user_id == user.id)
        .first()
    )
    if existing:
        db.delete(existing)
    else:
        db.add(SongFanVote(song_id=song_id, user_id=user.id))
    db.commit()
    return RedirectResponse(url=f"/pages/repertoire/{song_id}", status_code=303)


@router.post("/repertoire/{song_id}/comment")
def repertoire_comment(
    song_id: int,
    request: Request,
    content: str = Form(),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    user = _current_user(request, db)
    if not user:
        return RedirectResponse(url="/pages/login", status_code=303)
    db.add(SongComment(content=content, song_id=song_id, user_id=user.id))
    db.commit()
    return RedirectResponse(url=f"/pages/repertoire/{song_id}", status_code=303)


@router.post("/repertoire/comments/{comment_id}/delete")
def repertoire_comment_delete(
    comment_id: int, request: Request, db: Session = Depends(get_db)
) -> RedirectResponse:
    user = _current_user(request, db)
    comment = db.query(SongComment).filter(SongComment.id == comment_id).first()
    if comment and user and (comment.user_id == user.id or user.role == "admin"):
        song_id = comment.song_id
        db.delete(comment)
        db.commit()
        return RedirectResponse(url=f"/pages/repertoire/{song_id}", status_code=303)
    return RedirectResponse(url="/pages/repertoire", status_code=303)


# ── Items ──


@router.get("/items", response_class=HTMLResponse)
def items_list(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    items = db.query(Item).options(joinedload(Item.category)).all()
    return _render(request, "items.html", db, items=items)


@router.get("/items/new", response_class=HTMLResponse)
def item_new(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    categories = db.query(Category).all()
    return _render(request, "item_form.html", db, item=None, categories=categories)


@router.post("/items/new", response_class=HTMLResponse)
def item_create(
    request: Request,
    name: str = Form(),
    description: str = Form(""),
    category_id: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    item = Item(
        name=name,
        description=description or None,
        category_id=int(category_id) if category_id else None,
    )
    db.add(item)
    db.commit()
    return RedirectResponse(url="/pages/items", status_code=303)


@router.get("/items/{item_id}/edit", response_class=HTMLResponse)
def item_edit(
    item_id: int, request: Request, db: Session = Depends(get_db)
) -> Response:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return RedirectResponse(url="/pages/items", status_code=303)
    categories = db.query(Category).all()
    return _render(request, "item_form.html", db, item=item, categories=categories)


@router.post("/items/{item_id}/edit", response_class=HTMLResponse)
def item_update(
    item_id: int,
    request: Request,
    name: str = Form(),
    description: str = Form(""),
    category_id: str = Form(""),
    is_active: str | None = Form(None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return RedirectResponse(url="/pages/items", status_code=303)
    item.name = name
    item.description = description or None
    item.category_id = int(category_id) if category_id else None
    item.is_active = is_active is not None
    db.commit()
    return RedirectResponse(url="/pages/items", status_code=303)


@router.post("/items/{item_id}/delete")
def item_delete(item_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    item = db.query(Item).filter(Item.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url="/pages/items", status_code=303)


# ── Categories ──


@router.get("/categories", response_class=HTMLResponse)
def categories_list(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    categories = db.query(Category).all()
    return _render(request, "categories.html", db, categories=categories)


@router.get("/categories/new", response_class=HTMLResponse)
def category_new(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return _render(request, "category_form.html", db, category=None)


@router.post("/categories/new", response_class=HTMLResponse)
def category_create(
    request: Request,
    name: str = Form(),
    description: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    category = Category(name=name, description=description or None)
    db.add(category)
    db.commit()
    return RedirectResponse(url="/pages/categories", status_code=303)


@router.get("/categories/{category_id}/edit", response_class=HTMLResponse)
def category_edit(
    category_id: int, request: Request, db: Session = Depends(get_db)
) -> Response:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        return RedirectResponse(url="/pages/categories", status_code=303)
    return _render(request, "category_form.html", db, category=category)


@router.post("/categories/{category_id}/edit", response_class=HTMLResponse)
def category_update(
    category_id: int,
    request: Request,
    name: str = Form(),
    description: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        return RedirectResponse(url="/pages/categories", status_code=303)
    category.name = name
    category.description = description or None
    db.commit()
    return RedirectResponse(url="/pages/categories", status_code=303)


@router.post("/categories/{category_id}/delete")
def category_delete(
    category_id: int, db: Session = Depends(get_db)
) -> RedirectResponse:
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        db.delete(category)
        db.commit()
    return RedirectResponse(url="/pages/categories", status_code=303)
