from fastapi import FastAPI

from app.routers import auth, categories, items, users

app = FastAPI(title="Claude CRUD App", version="0.1.0")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(items.router)
app.include_router(users.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
