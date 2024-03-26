"""Simple model for a movie"""

from pydantic import BaseModel


class Movie(BaseModel):
    title: str
    year: int
    studio: str
    director: str
