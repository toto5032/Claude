from fastapi import FastAPI

from app.routers import items

app = FastAPI(title="Claude CRUD App", version="0.1.0")

app.include_router(items.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
