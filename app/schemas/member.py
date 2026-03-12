from pydantic import BaseModel


class MemberCreate(BaseModel):
    name: str
    role_in_band: str
    photo_url: str | None = None
    bio: str | None = None
    sns_links: str | None = None
    sort_order: int = 0
    user_id: int | None = None


class MemberUpdate(BaseModel):
    name: str | None = None
    role_in_band: str | None = None
    photo_url: str | None = None
    bio: str | None = None
    sns_links: str | None = None
    sort_order: int | None = None
    user_id: int | None = None


class MemberResponse(BaseModel):
    id: int
    name: str
    role_in_band: str
    photo_url: str | None = None
    bio: str | None = None
    sns_links: str | None = None
    sort_order: int = 0

    model_config = {"from_attributes": True}
