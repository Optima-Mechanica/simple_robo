"""
Data structures for interaction via REST API.
"""

from pydantic import BaseModel


class PTZRecord(BaseModel):
    pan: int
    tilt: int
    zoom: int


class Focus(BaseModel):
    auto: bool
    value: int | None


class Direction(BaseModel):
    direction: str
    x: int | None
    y: int | None
