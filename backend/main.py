"""Main file for FastAPI server"""

import json
from typing import List, Union
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pyaml_env import parse_config
from movies import Movie

from static_files import static_file_response

app = FastAPI()
config = parse_config("./config.yaml")


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
async def get_all_movies():
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
