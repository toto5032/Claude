from datetime import date, datetime, time

from pydantic import BaseModel


class ShowCreate(BaseModel):
    title: str
    venue: str
    address: str | None = None
    show_date: date
    show_time: time | None = None
    description: str | None = None
    ticket_url: str | None = None
    ticket_price: str | None = None
    poster_url: str | None = None
    status: str = "upcoming"


class ShowUpdate(BaseModel):
    title: str | None = None
    venue: str | None = None
    address: str | None = None
    show_date: date | None = None
    show_time: time | None = None
    description: str | None = None
    ticket_url: str | None = None
    ticket_price: str | None = None
    poster_url: str | None = None
    status: str | None = None


class ShowResponse(BaseModel):
    id: int
    title: str
    venue: str
    address: str | None
    show_date: date
    show_time: time | None
    description: str | None
    ticket_url: str | None
    ticket_price: str | None
    poster_url: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SetlistItemCreate(BaseModel):
    song_id: int
    play_order: int = 0
    notes: str | None = None


class SetlistItemResponse(BaseModel):
    id: int
    show_id: int
    song_id: int
    play_order: int
    notes: str | None
    song_title: str | None = None
    song_artist: str | None = None

    model_config = {"from_attributes": True}
