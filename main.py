from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, Field
import sqlite3
import secrets
from storage import init_db, add_link, get_link, increment_clicks, delete_link
DB_PATH = "links.db"
init_db(DB_PATH)
import string
app = FastAPI()
CODE_LENGTH = 6
CODE_CHARACTERS = string.ascii_letters + string.digits
class LinkCreate(BaseModel):
    url: HttpUrl
class CustomLinkCreate(LinkCreate):
    my_code: str = Field(min_length=3, max_length=20, pattern=r"^[0-9a-zA-Z_-]+$")
@app.post("/links", status_code = 201)
def create_link(link: LinkCreate):
    code = "".join(secrets.choice(CODE_CHARACTERS) for _ in range(CODE_LENGTH))
    while get_link(DB_PATH, code) is not None:
        code = "".join(secrets.choice(CODE_CHARACTERS) for _ in range(CODE_LENGTH))
    add_link(DB_PATH, code, str(link.url))
    return {"code": code, "short_url": f'/r/{code}'}
@app.post("/customlinks", status_code = 201)
def create_custom_link(link: CustomLinkCreate):
    try:
        add_link(DB_PATH, link.my_code, str(link.url))
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Code already exists")
    return {"code": link.my_code, "short_url": f'/r/{link.my_code}'}
@app.get("/r/{code}", status_code = 200)
def redirect_to_url(code: str):
    link = get_link(DB_PATH, code)
    if link is None:
        raise HTTPException(status_code=404)
    _, original_url, _, _ = link
    increment_clicks(DB_PATH, code)
    return RedirectResponse(original_url)
@app.get("/links/{code}/stats", status_code = 200)
def get_link_stats(code: str):
    link = get_link(DB_PATH, code)
    if link is None:
        raise HTTPException(status_code=404)
    code, original_url, clicks, created_at = link

    return {"code": code, "url": original_url, "clicks": clicks}
@app.delete("/links/{code}", status_code = 204)
def remove_link(code: str):
    if not delete_link(DB_PATH, code):
        raise HTTPException(status_code=404, detail = 'Code is not found')
    return Response(status_code=204)
