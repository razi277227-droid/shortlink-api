from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, Field
import secrets
import string
links = {}
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
    while code in links:
        code = "".join(secrets.choice(CODE_CHARACTERS) for _ in range(CODE_LENGTH))
    links[code] = {"url": str(link.url), "clicks": 0}
    return {"code": code, "short_url": f'/r/{code}'}
@app.post("/customlinks", status_code = 201)
def create_custom_link(link: CustomLinkCreate):
    if link.my_code in links:
        raise HTTPException(status_code=409)
    links[link.my_code] = {"url": str(link.url), "clicks": 0}
    return {"code": link.my_code, "short_url": f'/r/{link.my_code}'}
@app.get("/r/{code}", status_code = 200)
def redirect_to_url(code: str):
    if code not in links:
        raise HTTPException(status_code=404)
    links[code]["clicks"] += 1
    return RedirectResponse(links[code]["url"])
@app.get("/links/{code}/stats", status_code = 200)
def get_link(code: str):
    if code not in links:
        raise HTTPException(status_code=404)
    return {"code": code, "url": links[code]["url"], "clicks": links[code]["clicks"]}
@app.delete("/links/{code}", status_code = 204)
def delete_link(code: str):
    if code not in links:
        raise HTTPException(status_code=404, detail="Link not found")
    del links[code]
    return Response(status_code=204)


