from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, Field, AwareDatetime, field_validator
from datetime import datetime, timezone
import secrets
from database import engine
from storage_pg import add_link, get_link, increment_clicks, delete_link, create_user
from security import hash_password
from sqlalchemy.exc import IntegrityError
import string
app = FastAPI()
CODE_LENGTH = 6
CODE_CHARACTERS = string.ascii_letters + string.digits
def utc_now() -> datetime:
    return datetime.now(timezone.utc)
class LinkCreate(BaseModel):
    url: HttpUrl
    expires_at: AwareDatetime | None = None
    @field_validator("expires_at", mode="after")
    @classmethod
    def validate_expires_at(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value <= utc_now():
            raise ValueError("expires_at must be after now")
        return value

class CustomLinkCreate(LinkCreate):
    my_code: str = Field(min_length=3, max_length=20, pattern=r"^[0-9a-zA-Z_-]+$")

class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[a-z0-9_]+$",
    )
    password: str = Field(
        min_length=4,
        max_length=128,
    )

class UserRead(BaseModel):
    id: int
    username: str
    created_at: datetime


@app.post("/links", status_code = 201)
def create_link(link: LinkCreate):
    code = "".join(secrets.choice(CODE_CHARACTERS) for _ in range(CODE_LENGTH))
    while get_link(engine, code) is not None:
        code = "".join(secrets.choice(CODE_CHARACTERS) for _ in range(CODE_LENGTH))
    add_link(engine, code, str(link.url), expires_at=link.expires_at)
    return {"code": code, "short_url": f'/r/{code}'}
@app.post("/customlinks", status_code = 201)
def create_custom_link(link: CustomLinkCreate):
    try:
        add_link(engine, link.my_code, str(link.url), expires_at=link.expires_at)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Code already exists")
    return {"code": link.my_code, "short_url": f'/r/{link.my_code}'}
@app.get("/r/{code}", status_code = 200)
def redirect_to_url(code: str):
    link = get_link(engine, code)
    if link is None:
        raise HTTPException(status_code=404)
    _, original_url, _, _, expires_at = link
    if expires_at is not None and expires_at <= utc_now():
        raise HTTPException(status_code=410, detail="Link has expired")
    increment_clicks(engine, code)
    return RedirectResponse(original_url)
@app.get("/links/{code}/stats", status_code = 200)
def get_link_stats(code: str):
    link = get_link(engine, code)
    if link is None:
        raise HTTPException(status_code=404)
    code, original_url, clicks, created_at, expires_at = link
    expired = expires_at is not None and expires_at <= utc_now()
    return {"code": code, "url": original_url, "clicks": clicks, "expires_at": expires_at, "expired": expired}
@app.delete("/links/{code}", status_code = 204)
def remove_link(code: str):
    if not delete_link(engine, code):
        raise HTTPException(status_code=404, detail = 'Code is not found')
    return Response(status_code=204)
@app.post("/users", status_code = 201, response_model=UserRead)
def register_user(user: UserCreate):
    hashed_password = hash_password(user.password)

    try:
        created_user = create_user(
            engine,
            username = user.username,
            hashed_password = hashed_password,
        )
    except IntegrityError as exc:
        if exc.orig.sqlstate == "23505":
            raise HTTPException(status_code=409, detail="Username already exists")
        raise
    return created_user
