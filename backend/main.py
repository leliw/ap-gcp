"""Main file for FastAPI server"""

import datetime
import json
from typing import Annotated, List, Optional, Union
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pyaml_env import parse_config

from gcp_oauth import OAuth
from gcp_secrets import GcpSecrets
from gcp_session import SessionManager, SessionData as BaseSessionData
from movies import Movie
from static_files import static_file_response


class SessionData(BaseSessionData):
    login_time: Optional[datetime.datetime] = None


app = FastAPI()
config = parse_config("./config.yaml")
secrets = GcpSecrets(config.get("project_id"))
client_secret = secrets.get_secret("oauth_client_secret")
oAuth = OAuth(config.get("oauth_client_id"), client_secret)
session_manager = SessionManager[SessionData](oAuth, SessionData)


@app.get("/login")
async def login_google(request: Request):
    return oAuth.redirect_login(request)


@app.get("/auth")
async def auth_google(code: str, response: Response):
    user_data = await oAuth.auth(code)
    print(user_data)
    await session_manager.create_session(response, SessionData(user=user_data))
    return user_data


# @app.middleware("http")
# async def verify_token_middleware(request: Request, call_next):
#     return await oAuth.verify_token_middleware(request, call_next)


# async def session_reader(request: Request, response: Response) -> SessionData:
#     try:
#         data = await session_manager(request)
#         return data
#     except InvalidSessionException:
#         pass
#     except HTTPException as e:
#         if e.status_code != 403 or e.detail != "No session provided":
#             raise e
#     user_data = oAuth.verify_token(request)
#     if not user_data:
#         raise HTTPException(status_code=401, detail="Unauthorized")
#     data = SessionData(user=user_data)
#     await session_manager.create_session(response, data)
#     return data


SessionDataDep = Annotated[SessionData, Depends(session_manager.session_reader)]


@app.get("/api/user")
async def user_get(session_data: SessionDataDep):
    return session_data.user


@app.get("/api/config")
async def read_config():
    """Return config from yaml file"""
    return config


@app.get("/api")
async def read_root():
    """Return Hello World"""
    return {"Hello": "World"}


@app.get("/api/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None):
    """Return item_id and q"""
    return {"item_id": item_id, "q": q}


with open("movies.json", "r", encoding="utf-8") as file:
    movies_data = json.load(file)
movies = {f"{movie['title']}_{movie['year']}": Movie(**movie) for movie in movies_data}


@app.get("/api/movies", response_model=List[Movie])
async def get_all_movies(session_data: SessionDataDep):
    print(session_data)
    return [movie for movie in movies.values()]


@app.post("/api/movies", response_model=Movie)
async def add_movie(movie: Movie):
    key = f"{movie.title}_{movie.year}"
    movies[key] = movie.model_dump()
    location = f"/api/movies/{key}"
    return Response(status_code=201, headers={"Location": location})


@app.get("/api/movies/{key}", response_model=Movie)
async def get_movie(key: str):
    if key not in movies:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movies[key]


@app.put("/api/movies/{key}")
async def update_movie(key: str, movie: Movie):
    if key not in movies:
        raise HTTPException(status_code=404, detail="Movie not found")
    movies[key] = movie.model_dump()


@app.delete("/api/movies/{key}")
async def delete_movie(key: str):
    if key not in movies:
        raise HTTPException(status_code=404, detail="Movie not found")
    movies.pop(key)


# Angular static files - it have to be at the end of file
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def catch_all(_: Request, full_path: str):
    """Catch all for Angular routing"""
    return static_file_response("static/browser", full_path)
