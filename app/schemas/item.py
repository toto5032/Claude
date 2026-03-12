from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    category_id: int | None = None


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    category_id: int | None = None


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    category_id: int | None

    model_config = {"from_attributes": True}
