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
from app.models.user import User

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
    return _render(request, "home.html", db, members=members)


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
