from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.routers import auth, categories, items, members, pages, repertoire, users

app = FastAPI(title="Monday Crew", version="0.1.0")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(items.router)
app.include_router(members.router)
app.include_router(repertoire.router)
app.include_router(users.router)
app.include_router(pages.router)


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/pages/")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
